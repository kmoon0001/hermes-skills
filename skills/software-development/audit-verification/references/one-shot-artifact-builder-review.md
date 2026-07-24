# One-Shot Artifact Builder Review

Use this checklist for builders that download many immutable inputs and publish a cache plus tracked manifest/quality evidence.

## Immutability and publication

A startup `path.exists()` check followed later by `os.replace()` is a TOCTOU race, not a no-overwrite guarantee. Two builders can both pass the check, overwrite each other, publish mixed generations, or have one run's exception cleanup delete the other's successful outputs.

Review for:

- an exclusive lock or atomic claim acquired before output-existence checks and expensive work;
- build-unique temporary outputs scoped to the owning run;
- atomic no-replace commit logic (for example, same-volume hard-link publication) that cannot replace an already-published final artifact;
- no automatic path-based deletion of published final artifacts during exception cleanup: even `stat()`/identity checks followed by `unlink()` retain a TOCTOU window;
- fail-closed interruption behavior that preserves partial publication for inspection and lets it block the next build, with stale-lock/partial-output recovery performed explicitly rather than guessed;
- multi-file publication semantics: publish the completion marker/manifest last so incomplete generations are distinguishable, and prevent consumers from treating partial output as complete.

Treat the race as blocking when the contract promises immutable/no-overwrite output or explicitly asks for concurrency safety, even if ordinary single-process tests pass. A lock does not justify overwrite-capable publication, and “owner-scoped” final-file cleanup is not truly owner-safe when ownership is checked by pathname before unlinking.

### Prefer persistent OS advisory locks over disposable token locks

A create-exclusive token file that is later checked with `stat()`/`read()` and then removed with `unlink()` still has a check-to-delete race: another process can replace the path after the ownership check, and the old owner can delete the replacement. The simplest durable design is often a **persistent lock file whose pathname is never deleted by normal builds**, with ownership represented by an OS advisory lock on the open descriptor:

- create/open the known lock path once (`O_CREAT | O_RDWR`), ensure a lockable byte exists, and acquire a nonblocking byte-range lock on Windows or `flock(LOCK_EX | LOCK_NB)` on POSIX;
- hold the descriptor for the complete build, including output-existence checks and manifest-last publication;
- release the OS lock and close the exact descriptor in `finally`, but do not `stat`, reread, rename, or unlink the lock pathname;
- keep the persistent lock file in a generated/ignored location and do not interpret mere path existence as an active or stale owner—the OS lock state is authoritative;
- reject a second builder when lock acquisition fails, while allowing immediate reacquisition after success, exception, or process death.

This removes stale-token cleanup and lock-replacement deletion from the state machine. Descriptor ownership begins immediately after `open`: initialization steps such as `fstat`, writing the lock byte, `fsync`, or `lseek` must also be inside a cleanup guard, not only lock acquisition and the yielded critical section. Inject an initialization failure and assert the exact descriptor is closed; otherwise a failure before acquisition leaks a handle and may keep the persistent path unusable on Windows.

The acquisition phase needs a **BaseException-safe close guard**, too. Catching only `OSError` to translate contention while leaving `ImportError`, `KeyboardInterrupt`, or another non-`OSError` raised during platform import/lock acquisition outside cleanup leaks the descriptor. Close on every exceptional exit, translate only genuine contention to the public “another builder” error, and preserve unexpected failures after cleanup. Also verify that short/failed initialization writes cannot leave an unusable lock byte.

Regression tests should prove: barrier-synchronized simultaneous contenders permit exactly one owner; an initialization or acquisition failure closes the descriptor; an exception after acquisition releases the lock; reacquisition reuses the same path identity; and normal release preserves the lock bytes. At least one contention test must use **separate processes**, not only threads: a process-local mutex (optionally combined with a persistent marker file) can satisfy every same-process thread test while allowing two real builders to enter concurrently. On Windows, do not require a second handle to read a byte while that byte range is actively locked—verify bytes after release instead.

## Redirect and download boundaries

`urllib.request.urlopen()` follows redirects by default. Checking `response.geturl()` rejects a changed final URL, but it happens after the client has already contacted the redirected origin. If the contract requires canonical-origin-only egress, install a no-redirect handler or reject redirects before following them.

### Redirect and HTTP-error handle ownership

Rejecting a redirect inside `HTTPRedirectHandler.redirect_request(...)` has a subtle resource boundary: stdlib `http_error_302` calls `redirect_request` **before** its own `fp.read()` / `fp.close()` cleanup. If the override raises immediately, that cleanup is bypassed and the redirect response can remain open through the exception traceback. Close the supplied `fp` in a `finally`-safe rejection path without draining an untrusted body. Test with a closable fake response and assert closure; passing `None` as `fp` and checking only the exception merely mirrors the handler and cannot detect the leak.

Likewise, every caught `HTTPError` is itself a response object. Explicitly close it before retrying or re-raising, including permanent statuses and the exhausted final retry. Do not rely on reference counting or cyclic GC: `last_error`, chained exceptions, tracebacks, and `Future` objects can retain the response and its socket. Success-response tests should also assert context-manager closure so removing the `with` cannot survive.

Do not label blanket `except (URLError, OSError)` handling “transient-only.” `URLError.reason` and `OSError` subclasses include permanent TLS certificate, DNS-name, filesystem/configuration, and argument failures. Classify retryable transport reasons explicitly (timeouts, temporary DNS, selected connection errno values), fail permanent reasons immediately, and test both classes plus exhausted attempt/backoff counts.

Also check:

- canonical scheme, host, port, path grammar, query, and fragment before the request;
- bounded compressed download size (stream and stop at a hard limit rather than unbounded `response.read()`);
- bounded ZIP member uncompressed size and compression ratio before `archive.read()`;
- exact member count/name and no duplicate member names;
- explicit timeout/retry policy with permanent versus retryable errors;
- cleanup and cancellation behavior when one worker fails;
- concurrency limits that do not multiply unbounded reads into memory exhaustion.

Implement retries from a **small explicit transient HTTP allowlist**, not from a short permanent-error denylist. A denylist containing familiar permanent codes can still retry statuses such as 405 or 422. Regressions should cover several permanent codes outside the obvious set, at least one allowlisted transient status that succeeds after retry, and exact attempt/backoff counts.

For Python `ThreadPoolExecutor`, `executor.map(...)` inside a normal `with` block is not automatically fail-fast: on one yielded exception, context-manager shutdown waits for queued/running futures unless pending work is explicitly cancelled. Merely replacing `map` with a list of futures and calling `future.result()` in submission order still delays detection when a later-submitted task fails before an earlier slow task. For prompt cancellation, consume futures in **completion order** (for example, `as_completed`), store successful results back into their frozen task-order slots, and on the first observed exception cancel every future and call `shutdown(wait=True, cancel_futures=True)` before re-raising. Waiting for running work to stop prevents network tasks from escaping the build lock; `cancel_futures=True` prevents queued work from starting.

For a thousands-of-archives builder, require a regression where the failing task is deliberately *not* the first submitted task, an earlier task is held, and the test proves most queued tasks never start while the correct worker error is observed in completion order. Avoid a short `Event.wait(timeout=...)` plus a weak assertion such as `started < total - 1`: a submission-order loop can wait out that timeout, start only a handful of extra tasks, and still pass. Use deterministic coordination instead—for example, run the coordinator in a separate thread, hold the earlier worker on an event, make the later worker fail immediately, observe pending-future cancellation through an instrumented executor/future seam, then release the running worker so `shutdown(wait=True)` can complete. Mutation-check `as_completed(futures)` to submission-order iteration and require the test to fail.

A first-task-only test can pass an implementation that still notices later failures too late. Separately force completion iteration into reverse task order and assert the returned tuple/list remains in frozen task order; failure detection belongs to completion order, but deterministic artifact assembly belongs to specification order. A bounded per-response `read(limit + 1)` does not compensate for an unbounded queue of unnecessary requests.

## ZIP/CSV adapter tests

Happy-path acceptance is insufficient for a new source adapter. Durable tests should cover:

- wrong digest or byte count;
- malformed ZIP, extra/duplicate/wrong member, invalid UTF-8, malformed CSV, wrong header, and wrong row width;
- every intentionally accepted source lexical exception;
- near-miss spellings that must remain rejected (case, sign, exponent width/scale, unsupported nonzero notation);
- proof that canonicalization does not bypass lower-level validation or accidentally collapse conflicting raw payloads.

For scientific-zero adapters, keep **lexical identity** separate from the parsed numeric value. If the audited exception is `0E-8`, do not use a broad pattern such as `0E-[1-9][0-9]*` unless every negative scale is explicitly allowed. More importantly, do not replace `0E-8` with `0` in the mapping used for exact duplicate/conflict detection: two rows that differ only by those raw spellings are not byte-identical payloads. Preserve the original row for payload identity, parse a separate canonical value for normalization, and add two regressions: unsupported exponent scales fail closed, and `0E-8` versus `0` at one timestamp produces a conflict rather than an exact-duplicate collapse.

## Mutation-resistant infrastructure tests

Do not accept a test merely because its name matches the required control. Check that it kills the smallest realistic regression:

- **Redirect wiring:** calling a redirect-handler method directly is insufficient. Exercise the opener factory or inspect/intercept its handler chain so replacing the no-redirect opener with default `urlopen()` fails. Download tests that monkeypatch the request-opening seam cannot prove that seam is wired safely.
- **Retry classification:** a transient-success test proves retries occur, not that retries are limited to transient failures. Add permanent HTTP, redirect, malformed-header, and exhausted-retry cases; assert attempt and sleep counts.
- **Response/ZIP bounds:** assert the exact `limit + 1` argument at both read seams. A ZIP fixture whose declared `file_size` already exceeds the limit only tests the metadata precheck; an unbounded `ZipExtFile.read()` mutant can still survive. Instrument or wrap the member handle to observe its requested read size.
- **Concurrent exclusion:** acquiring a lock while another lock is already held does not test the startup race. Use a barrier to release two contenders simultaneously and prove exactly one reaches source work/publication. A check-then-create mutant must fail.
- **Lock release and ownership:** choose the assertion from the design. For a disposable token lock, replace/remove-recreate the pathname during the critical section and prove the old owner cannot delete the replacement. For a persistent advisory lock, path absence is wrong: verify the file identity/bytes survive release, OS ownership is released after exceptions, and immediate reacquisition succeeds. In both designs, inject failures after each publication step to prove published finals remain, unique temporaries are removed, and a partial generation blocks the next build.
- **No-overwrite publication:** cover both a pre-existing destination and a destination created at the publication boundary; verify original bytes and final path identity remain unchanged. A pre-existing-only test does not kill `if destination.exists(): raise; os.replace(temp, destination)`: that check-then-replace mutant passes until another actor creates the destination between the check and replace. Introduce a hook/monkeypatch at the commit seam so the competing file appears after temporary output is ready but immediately before final publication, and require preservation.

When these controls are explicit acceptance requirements, surviving mutants or missing durable regressions are blocking even if static production code currently looks correct.

## Artifact and quality gate strength

A hash proves identity, not correctness. For each manifest/quality field, map a staged assertion or independent recomputation. In particular verify:

- exact manifest keys, paths, schema version, counts, timestamps, and count/list consistency;
- every source URL and full lineage identity;
- exact Arrow field order, physical types, timezone/precision, and schema metadata—not just pandas column names;
- deterministic row ordering and unique normalized keys;
- every quality column, including first/last times, archive counts, duplicate/conflict counts, nonpositive counts, window counts, and monotonicity;
- the quality row-count field and source-archive-count field agree with actual artifacts.

Hash validation plus partial semantic assertions leaves realistic mutants alive (for example, setting `source_archive_count` to zero while keeping the source list correct).

### Regenerate after every builder-byte change

When the tracked manifest binds the builder source hash, any source edit invalidates the current generation even if normalized values appear unaffected. After the last production change: remove only the exact owned outputs, rebuild the cache/manifest/quality set, run the dedicated artifact gate and full suite against those exact bytes, then restage and freeze a new tree/patch identity. Never keep an artifact built by an earlier builder hash, manually patch the manifest hash, or count approvals issued before regeneration. If regeneration embeds volatile retrieval/build timestamps, expect artifact digests to change and verify source-identity and semantic invariants independently.

## Reproducibility claims with volatile lineage

Distinguish three different guarantees instead of calling all of them “reproducible”:

1. **Source identity reproducibility:** the ordered `(canonical URL, byte count, SHA-256)` tuples match.
2. **Semantic reproducibility:** normalized values and ordering match after excluding intentionally volatile lineage fields.
3. **Byte reproducibility:** complete artifact hashes match.

If cache rows or manifests embed actual `retrieved_at` or `built_at` timestamps, a clean re-download can preserve source identity and semantic content while changing every artifact hash. Never claim byte-for-byte reproducibility unless the governing protocol defines how those volatile timestamps are frozen. Preserve the previous staged manifest or another read-only baseline long enough to compare the complete ordered source-identity set, and report the strongest guarantee actually verified.

## Generated artifacts versus tracked evidence

Treat artifact tracking status as part of the frozen contract. If the authoritative plan labels a large cache or build product **generated/untracked** and its commit recipe omits that path, reject a staged snapshot that force-adds the artifact—even when the review prompt accurately lists it among the candidate files and supplies the expected tree/patch identity. A candidate-file list defines the snapshot to inspect; it does not silently waive an authoritative tracked-versus-generated rule. Cite both the staged path and the governing plan lines. Only accept the deviation when the user explicitly overrides the frozen plan, not merely by describing the current scope.

## Payload-prohibited artifact audits

When the engagement explicitly forbids reading a large binary payload, do not run artifact tests or direct hash/schema readers that open it. Keep the review useful without violating scope:

- verify the staged blob's declared size with `git cat-file -s :path/to/artifact` (metadata only);
- compare manifest path, byte count, row count, and digest to an independently supplied trusted baseline, while clearly labeling fields that were not recomputed from payload bytes;
- fingerprint the staged patch with the exact declared binary-diff options; this establishes snapshot identity but is not a semantic artifact inspection;
- inspect source and tests statically to confirm exact schema metadata/types, ordering, serialization options, and causal assertions;
- use bounded summaries for text manifests and quality tables, and independently reconstruct expected URL/series sets from authoritative protocol files;
- disclose in the verdict that the payload was not inspected.

Do not let an existing frozen binary make weak builder tests look complete. Require durable assertions for every quality field, every intentionally accepted lexical exception, malformed archive classes, and deterministic serialization bindings (field order, metadata, compression/version/chunk options, canonical JSON ordering, and input-order invariance). An old artifact hash can remain green after the current builder regresses.

## Read-only review evidence

For an exact staged review:

1. Freeze HEAD, index-tree identity, patch digest, staged paths, and full status.
2. Inspect staged blobs, not assumed worktree copies.
3. Run the fail-closed added-line security scanner.
4. Bracket each executable gate with identity/status checkpoints.
5. If an ignored generated cache is explicitly in scope, validate its hash/schema/order without staging or modifying it.
6. Recompute quality fields independently where derivable.
7. Treat missing adversarial tests as blocking when they guard an explicit immutability, security, or artifact-correctness requirement.
