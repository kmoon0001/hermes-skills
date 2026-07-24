# Reproducibility and Data-Lineage Review

Use this checklist for normalized datasets, generated caches, source manifests, experiment inputs, and other artifacts whose identity must remain stable across runs.

## Parser policy versus normalized-schema policy

A source parser may have a documented duplicate policy—for example, collapsing byte-for-byte identical source rows while invalidating conflicting duplicates. Apply that policy before creating normalized records.

The normalized schema should normally require one unique record per declared key and strictly increasing timestamps within each series. Do not silently deduplicate again at the schema boundary; doing so can hide malformed parser output.

## Frozen-manifest invariants

Canonicalize every entry before comparison:

- Reject leading/trailing whitespace and noncanonical URL aliases.
- Require unique source URLs.
- Produce deterministic ordering, normally by canonical source URL.
- When comparing with a frozen manifest, require exact URL-set equality. Missing, added, and substituted archives all fail.
- Compare the complete identity for every archive: canonical URL, retrieval timestamp, byte count, and cryptographic digest.
- Verify every normalized row's archive identity against the validated manifest; cross-row consistency alone is insufficient.
- Reject rows that assign different byte counts or digests to the same source URL.
- Enforce runtime types on identity fields before equality comparison. In Python, `True == 1 == 1.0`, so a positive-only byte-count check plus dataclass equality can let a boolean or float masquerade as an unchanged integer byte count. Require `type(source_byte_count) is int` (or an equivalently strict non-boolean integer policy) before frozen-identity comparison.
- Apply the same fail-closed principle to the rest of the normalized schema, not only lineage fields. A `float` annotation does not stop `True` or `1` from passing `math.isfinite`, and an invalid timestamp object can otherwise leak an `AttributeError` from `.tzinfo` instead of a stable validation error. Add adversarial tests for boolean/integer numeric aliases and wrong runtime timestamp types; reject them with deliberate `ValueError` messages according to the schema's declared coercion policy.
- Treat duplicate manifest URLs as invalid even when their entries are identical. Canonical ordering must not silently collapse cardinality errors.
- Define what a canonical URL is, not merely how raw URL strings are sorted. Reject malformed URLs and noncanonical aliases (case/default-port/path-encoding variants) before uniqueness and frozen-set comparison.
- Reject embedded ASCII whitespace and control characters in the raw URL **before** calling a standard URL parser. Parsers such as Python's `urllib.parse.urlsplit` can strip tabs, newlines, or carriage returns, so a raw alias like `ar\tchive.zip` may parse identically to `archive.zip` while remaining a distinct dictionary/manifest key. A validator that checks only parsed components can therefore accept two identities for one archive and defeat duplicate detection or exact frozen-set comparison.
- When the source contract permits printable ASCII URLs only, a simple fail-closed boundary is to reject every raw character outside `0x21..0x7E` before parsing. Prove the boundary by enumerating all `0x00..0x20` characters plus `0x7F` in a path position, checking that every one is rejected, then separately proving the canonical URL is accepted. If Unicode URLs are part of the contract, do not use this shortcut: define normalization and IDNA policy explicitly and test equivalence classes.
- Adversarially prove both halves of canonicalization: malformed raw spellings are rejected, and no two accepted raw strings normalize or parse to the same URL identity. Include interior space, TAB, CR, LF, NUL/control bytes, mixed host/scheme case, explicit default port, dot segments, and percent-encoded aliases.
- Give URL mutation probes a correct oracle. A changed printable path character can denote a legitimate, distinct archive; accepting it is not evidence of an alias bug. Treat a mutation as blocking only when it violates the declared URL grammar or resolves/normalizes to the same source identity as another accepted spelling. For parser-dangerous controls, explicitly prove the collision (for example, `urlsplit(alias) == urlsplit(canonical)`) and then verify the validator rejects the raw alias before parsing. This prevents false-positive fuzz gates from rejecting valid distinct sources.

If partial-manifest construction is needed, expose it as a separately named operation. Never let permissive subset comparison masquerade as frozen-manifest validation.

## Strict normalizer and selector boundaries

For Python normalizers and as-of selectors, type annotations are not runtime validation. Probe every public boundary with malformed runtime values—especially `bool`, because it aliases `int`—and require deliberate, stable errors rather than incidental `TypeError`/`AttributeError` or a silent “not found” result. At minimum cover the input record/container, source or manifest object, row members, identifiers, timestamps, and numeric fields. Validate before attribute access, membership tests, arithmetic, or filtering so the error contract does not depend on where malformed data happens to fail.

Preserve diagnostic precedence when adding broad fail-closed guards. A reliable order is: container/member type; required-field presence; field-specific symbol/timestamp/numeric validation; payload-wide representation validation; then duplicate/conflict grouping. Otherwise a generic “payload must contain strings” error can mask the more useful “timestamp unsupported” or “numeric field invalid” contract. After adding a broad guard, rerun the complete malformed-field matrix, not only the new guard test.

When cadence is part of the frozen source contract, validate grid alignment during normalization rather than assuming the archive is regular. For five-minute observations, reject nonzero seconds and minutes not divisible by five. This makes an “exact 288 intervals” lag semantically meaningful and prevents two equally off-grid endpoints from passing a 24-hour subtraction test.

Timestamp parsers must enforce the declared lexical grammar, not merely semantic parseability. Python `datetime.strptime` accepts some non-zero-padded fields and treats format whitespace permissively, including repeated spaces, TAB, CR, or LF. When only fixed-width audited formats are supported, prevalidate with an anchored ASCII regex or parse and require an exact round trip. Test the canonical text, each supported epoch-unit form, precision residues, leading/trailing and embedded whitespace/control characters, variable-width fields, and immediately out-of-window timestamps.

### Bind lineage to row semantics

Preserving a source URL and digest is not enough: prove that the source identity is semantically compatible with the normalized row. For archive families whose path encodes venue, product family, symbol, cadence, and period, parser-specific validation must bind all of them to the row. Reject a BTC archive relabeled as ETH, a funding parser pointed at an arbitrary `/data/*.zip`, and a February event attributed to a January archive. Generic host/path validation belongs at the manifest boundary; family/symbol/period binding belongs at the source parser boundary.

Identifiers governed by a closed universe must be exact canonical members, not merely nonblank strings. Probe interior ASCII whitespace and controls, NUL, zero-width Unicode, confusables, mixed case, and surrounding whitespace. A `.strip()` check alone still accepts values such as `BTC\nUSDT` or `BTC\u200bUSDT`, which can create invisible parallel series and break joins or coverage counts.

Derive the closed universe independently from the authoritative frozen artifacts before implementation and again during review. Prefer the machine-readable protocol when it is the declared companion, then cross-check prose and source-semantics/audit files for agreement. Do not copy a universe from memory, an earlier research cycle, a reviewer prompt, or a nearby fixture. Tests must prove both directions: every declared member is accepted with matching lineage, and representative nonmembers—including plausible neighboring assets—are rejected. A negative-only test can miss an omitted valid member; a positive-only test can miss an accidentally substituted member.

### Preserve exact payload identity until conflicts are resolved

If source duplicate/conflict policy depends on exact numeric payloads, do not convert arbitrary-precision decimal text to binary `float` before resolving same-key duplicates. Distinct accepted decimals can round to the same float and be misclassified as identical. Either retain/compare the canonical source representation or `Decimal` through conflict resolution, or restrict the accepted lexical precision/range to a documented audited contract that guarantees injective normalization. Add a collision regression using two distinct accepted decimal strings that map to the same float, along with overflow, zero-underflow, and smallest accepted nonzero boundary cases.

“Exact payload” also requires runtime-type-sensitive identity. Python mapping equality considers `True`, `1`, and `1.0` equal; unvalidated mappings can therefore collapse distinct source payloads. When the source reader contract yields strings (for example, `csv.DictReader`), require exact string keys and values before constructing a deterministic sorted raw-payload identity. Compare every payload column, not only the normalized signal: a difference in an ancillary source column must still tombstone the timestamp when the protocol says any differing payload is conflicting.

### Prove numeric and timestamp injectivity at the declared identity level

Do not use “injective” ambiguously. First decide whether identity is lexical (the exact source spelling) or semantic (the exact numeric value or instant). Two supported timestamp spellings that denote the same UTC instant are not a collision when the contract deliberately canonicalizes to instants; they are a collision when exact source lexemes must remain distinguishable.

For a Decimal-to-float boundary, the acceptance rule `isfinite(f) and Decimal(str(f)) == d` gives a useful semantic injectivity proof: if two accepted Decimal values map to the same float `f`, both equal `Decimal(str(f))`, so they are numerically equal. Still test overflow, nonzero-to-zero underflow, the smallest accepted nonzero magnitude, signed-zero policy, and lexical grammar. If scale, trailing zeros, or source spelling are part of identity, Decimal equality is insufficient—retain the canonical lexeme or Decimal through conflict resolution.

For integer epoch timestamps converted through floating-point seconds, fixed digit width alone is not proof. Bound the accepted calendar window, compare the float ULP and `datetime` rounding resolution with the smallest source unit, and test adjacent source ticks at the beginning and end of the permitted window. Prefer integer/timedelta arithmetic when practical. State explicitly whether textual and epoch forms that resolve to the same instant are intentional aliases.

As-of selectors must enforce or explicitly declare every feature-family invariant they rely on. A generic normalized-row schema may allow `measurement_time`, `event_time`, and `available_at` to differ, while a specific feature requires equality. If freshness is measured from settlement/event time, rejecting or validating that invariant is mandatory; otherwise a delayed `available_at` can make a 20-hour-old settlement appear four hours old and pass a 12-hour age gate. Tests must construct semantically malformed rows directly at the selector boundary, not only parser-produced happy paths.

As-of selectors must be deterministic under input permutations. For every “latest eligible” assertion, exercise at least two orders: one with the latest row first and one with it last (or an equivalent complete permutation set). A single reversed fixture can kill a last-write/`rows[-1]` mutant while still allowing a first-eligible/`next(iter(...))` mutant to survive. Also test shuffled valid rows, mixed symbols/families, no-match cases, equality at the causal boundary, exact staleness and one tick beyond, and multiple rows tied at the latest eligible timestamp. Never rely on `max(..., key=timestamp)` alone when ties can differ in value or lineage: either prove upstream validation as an explicit API precondition, reject ambiguity, or define a stable complete tie-break key. A selector that silently returns the first tied row is order-dependent even though ordinary sorted fixtures pass.

For ratio-derived logarithmic features, test extreme finite positive endpoints. `log(current / lag)` can overflow or underflow before `log` runs even though each endpoint is valid and finite. Prefer the algebraically equivalent `log(current) - log(lag)` when the protocol permits it, and include a regression asserting the result remains finite at extreme representable endpoints.

Test adequacy adversarially, not only by running the suite. Identify plausible incorrect implementations from both input-order directions—especially “first eligible input row” and “last eligible input row”—plus ignored symbol/family filters, `<=` instead of `<`, or first-wins ties, and verify an existing test would fail each one. If any mutant would survive, add the missing regression before approval. When a command contract forbids additional mutation-test invocations, prove the survivor by exhaustive static mapping from the mutant to every relevant staged test and label it as inspection-based rather than executed.

Do not mutate the live candidate snapshot to prove test adequacy. For a multi-mutant campaign, use a detached temporary Git worktree, copy the current candidate implementation and tests into it, run a green baseline, and apply one uniquely anchored textual mutant at a time. Restore the original source between mutants and remove the worktree in `finally`. This preserves the candidate identity and protects concurrent reviewers. After mutation work, rerun formatter, static checks, and the real suite because mutation proof does not validate the live files. For a single narrow staged Python mutant, prefer `scripts/probe_staged_python_mutant.py`.

### Triage realistic survivors without inventing blockers

Mutation review should be strict but not speculative. Treat a survivor as realistic when it is a small, locally plausible implementation mistake—normally one changed operator, boundary, field, filter, ordering choice, fallback, or validation omission—and it violates a frozen requirement. Do not reject correct code for an arbitrary adversarial branch that would require several coordinated edits or special-case logic written solely to evade the staged tests.

For each candidate survivor, record four facts before calling it blocking:

1. the exact frozen requirement it violates;
2. the smallest plausible source mutation;
3. every staged test that appears relevant and why none kills it;
4. whether the survivor was executed in memory or established by static test-to-mutation mapping.

Use a compact domain matrix for hardened parsers/selectors: closed universe; source family, symbol, and archive-period binding; exact numeric conversion/collision policy; timestamp grammar and runtime types; strict causal inequality; first representable instant after the boundary; latest selection in both input orders; inclusive freshness equality and one tick beyond; future truncation; duplicate/conflict behavior; lineage preservation; reserved periods; and malformed public-boundary inputs. A passing suite plus an empty matrix is not an adversarial review; an approval should mean every domain was mapped to a killing test or directly verified implementation invariant.

Do not claim that mutation probes were run when the engagement allowed only one exact pytest invocation. In that case, say the mutation analysis was inspection-based, run only the supplied command verbatim, and reserve executable mutant claims for a later review that explicitly permits them.

## Deterministic serialization and fixtures

Equivalent logical input must produce byte-identical or canonically equivalent output regardless of input ordering. Test multiple input permutations.

For JSON or similar artifacts, define ordering explicitly instead of relying on insertion order. For binary fixtures such as ZIP files, fix embedded metadata—including member timestamps, compression type, member names, platform, permissions, flags, and extra fields where relevant. Construct fixture bytes once per helper invocation so repeated digest calculations compare the same bytes. If the digest must be portable across Python/zlib versions, fixed metadata alone is not enough for DEFLATE output; prefer stored members, checked-in fixture bytes, or a separately versioned compressor contract.

## Generated artifacts versus tracked evidence

Ignore the complete generated-artifact directory, not only today's expected filename. Keep compact manifests, schemas, and audit summaries outside the ignored directory so they remain tracked evidence.

### Metadata-only verification when binary reads are prohibited

A review may explicitly forbid opening, hashing, parsing, importing, or test-loading a generated binary while still requiring proof that the tracked evidence points to the intended ignored artifact. Honor that boundary instead of silently reading the file through a checksum tool: hashing is a content read.

Use only metadata and Git-index checks for the prohibited binary:

1. Confirm the manifest names the exact expected generated path and records byte count, digest, row count, and any schema/protocol binding required by the contract.
2. Check existence and filesystem byte-count metadata (`stat`/`Path.stat`) without opening the file; compare the size to the manifest.
3. Prove the binary is untracked with `git ls-files --error-unmatch -- <path>` and ignored with `git check-ignore -v --no-index -- <path>` plus ignored-status output when useful.
4. Validate canonical serialization and independently recompute hashes only for the tracked manifest, source, and quality/evidence files that the scope permits reading.
5. Do not claim the binary digest, schema, row content, or semantic lineage was reverified. Classify those fields according to the stated audit contract: they may be intentionally out of scope in a static blocker re-audit, but they remain unresolved if the requested verdict requires fresh binary-content verification.

This split permits a precise claim such as “manifest-bound artifact exists, its size metadata matches, and it is ignored/untracked” without implying that prohibited payload bytes were inspected.

Test ignore behavior with multiple representative generated filenames and verify that the evidence manifest is not ignored. Make the test fail closed: for `git check-ignore`, only return codes 0 (ignored) and 1 (not ignored) are semantic results; status 128 or any other code is an infrastructure/error condition, not evidence that a path is unignored. Use `--no-index` when the policy must also be checked for an already tracked evidence file.

## Minimum adversarial tests

- Earliest and latest permitted timestamps
- Timestamp immediately outside each boundary
- Repeated normalized key
- Same source URL with conflicting row lineage
- Manifest input permutations
- Missing frozen archive
- Added or substituted archive
- Changed retrieval time, byte count, or digest
- URL with leading/trailing whitespace, malformed syntax, and equivalent noncanonical aliases
- Duplicate manifest URL with identical as well as conflicting identity
- Runtime identity-type substitutions that compare equal in Python (`True`, `1`, `1.0`)
- Row lineage that is internally consistent but disagrees with the frozen manifest
- Source URL family/symbol/period that disagrees with the normalized row
- Closed-universe identifiers containing interior controls, zero-width Unicode, confusables, or case aliases
- Feature-family rows whose measurement/event/availability relationship violates selector assumptions
- Distinct accepted decimal payloads that collide after float conversion
- Numeric overflow, zero-underflow, and the smallest accepted nonzero value
- Deterministic binary-fixture digest across repeated construction
- Multiple files under the generated directory are ignored
- Tracked manifest/evidence path remains unignored, including with `git check-ignore --no-index`
- Ignore-check command errors are rejected rather than interpreted as “not ignored”

## Independent reviewer prompts

Ask explicitly:

1. Is logical equivalence deterministic across input permutations?
2. Are frozen inputs compared by exact set and full identity?
3. Does every normalized row agree with its manifest entry?
4. Is source-specific cleanup being improperly repeated at the normalized-schema boundary?
5. Can generated or temporary artifacts escape ignore rules?
6. Were every universe member, period, source family, and threshold independently derived from the authoritative frozen artifacts rather than trusted from the implementer/reviewer prompt?
