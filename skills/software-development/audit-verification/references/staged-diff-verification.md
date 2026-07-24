# Staged-Diff Verification

Use this when verifying uncommitted code before commit or asking an independent reviewer to approve an exact change set.

## 1. Establish the real scope

Start with:

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

Ordinary `git diff` does **not** include untracked files. A clean-looking diff can therefore omit the main implementation. Read every intended untracked file directly before staging it.

For a pre-commit gate, stage only the exact reviewed paths:

```bash
git add path/one path/two
```

Do not use `git add -A` until scope is verified. If the engagement is strictly read-only, do not stage; render an untracked file with `git diff --no-index -- /dev/null path/to/file` instead.

## 2. Freeze the review snapshot

Inspect the staged snapshot:

```bash
git diff --cached --stat
git diff --cached --check
git diff --cached
```

When a reviewer runs asynchronously, do not alter staged files while it reviews them. For a strong identity check, record the staged patch digest before dispatch and compare it after the verdict:

```bash
git diff --cached --binary --full-index --no-ext-diff --no-textconv | sha256sum
```

Make every byte-affecting option explicit. In particular, do not rely on `--binary` implicitly enabling `--full-index`: Git installations can emit different patch bytes when `--full-index` is omitted, producing a different SHA-256 for the same index tree. The expected digest contract must name the options, and both the helper script and any manual cross-check must use that exact option set.

When the requested contract names both an **index tree** and a staged patch digest, fingerprint both. Avoid `git write-tree` in a no-write audit because it can create tree objects. Use `scripts/read_only_index_identity.py`, which reconstructs Git tree objects in memory from `git ls-files --stage -z`, supports the repository's declared object format, hashes the exact binary patch bytes, and writes nothing. Record the staged file list at the same time.

A verdict applies only to the exact tree and patch reviewed. If either digest or the staged path set changes, rerun the reviewer.

### Detect and stop mixed-snapshot reviews

Concurrent agents or users can mutate the index while a review is reading files. This can produce internally contradictory evidence—for example, an earlier diff shows one test body while a later search shows newly added cases. Treat any such contradiction as a snapshot-drift signal, not as a tool inconsistency.

1. Re-run the read-only index identity immediately, before any more source reads or tests.
2. If the tree, patch digest, or staged path set differs from the frozen identity, stop the review phase. Do not combine line numbers, test results, or findings from the old and new snapshots.
3. Mark every unrun gate as unresolved rather than failed or passed. Tests executed after drift apply only to the new snapshot and cannot validate the requested one.
4. When the request names an exact expected identity, return a fail-closed rejection for identity drift. Report any separate code defect only when it was conclusively captured from the original snapshot, and label it as belonging to that original identity.
5. Treat requirement summaries in the reviewer prompt as claims, not authority. Independently derive frozen constants (universe members, periods, source families, thresholds) from the named protocol/config/audit artifacts. If prompt and artifact disagree, the artifact wins and the snapshot is rejected; otherwise multiple reviewers can faithfully approve the same implementer transcription error.
6. Start a fresh review from scope discovery for the replacement snapshot; do not merely continue from the point where drift was noticed.

For long reviews, fingerprint at phase boundaries (after scope capture, after source/test reads, after executable checks, and before the verdict), not only at the beginning and end. Recheck immediately **before** any worktree-based test or import whose output will support the verdict; a test started after drift applies only to the replacement snapshot. This prevents a plausible-looking verdict assembled from multiple staged states.

Treat a changed test count, collection count, parametrization count, or test name set between nominally equivalent invocations as a snapshot-drift signal—even when every invocation passes. Do not explain the discrepancy as a pytest/plugin quirk until identity is rechecked. This is especially important for in-memory mutation probes: they import worktree code and may begin after another process has restaged a replacement snapshot. Bracket mutation campaigns with read-only index fingerprints, and discard every mutation result after the last matching fingerprint when drift is found.

### Serialize repository-state checkpoints around executable gates

Do not run `git status`, identity capture, or scope checks in parallel with pytest, imports, build tools, mutation harnesses, or other executable gates. Parallel execution destroys the temporal evidence needed to prove the repository was clean immediately before the gate or to identify when drift began—even if the executable is configured not to write caches.

Use a strict sequence:

1. Capture index identity, staged paths, unstaged paths, and `git status --short --untracked-files=all`.
2. Only if that checkpoint is clean for the declared scope, run one executable gate.
3. Immediately recapture identity and full status before starting another gate.
4. On any new tracked, unstaged, or untracked path, stop; in a no-write review, do not inspect, delete, or attribute the artifact, and mark all later gates unresolved.

A passing test result next to a dirty post-gate checkpoint may be reported as historical evidence, but it cannot produce approval. Never parallelize these checkpoints merely to save time; temporal ordering is part of the review contract.

When the original tree object already exists, preserve exact old-snapshot evidence without modifying the index:

- verify it with `git cat-file -t <tree>`;
- inspect exact files with `git show <tree>:path`;
- recover changed paths with `git diff --name-only <recorded-HEAD> <tree>`;
- reconstruct the patch using the recorded base and identical options, e.g. `git diff --binary --full-index --no-ext-diff --no-textconv <recorded-HEAD> <tree> | sha256sum`;

A patch digest depends on both the tree and its base commit, so record `HEAD` at review start and never reconstruct against a later `HEAD`. In a strict no-write audit, syntax-check or probe an old blob by piping `git show <tree>:path` into a parser or compiling it into an isolated in-memory module with synthetic inputs. This can conclusively demonstrate an old-snapshot defect, but it does not make normal worktree test results applicable to that old tree. Report old-snapshot findings and current-index drift separately, and require a fresh review for the new identity.

## 3. Run security scans fail-closed

Scan added lines, but distinguish these outcomes:

- exit 0: scan ran and found nothing;
- exit 1: findings exist;
- exit 2 or diagnostics: scanner failed, so the result is **not clean**.

Do not wrap a complex `grep` in a shell conditional that can swallow quoting or regex errors and then print “clean.” Use the packaged scanner from the repository root:

```bash
python path/to/audit-verification/scripts/scan_staged_added_lines.py
```

Resolve the installed skill path with `skill_view(name='audit-verification')` when needed. The scanner is cross-platform, handles Git errors explicitly, reports finding categories/counts without echoing matched secrets, and exits `0` only when clean (`1` findings, `2` scanner/Git failure). Treat any nonzero result as blocking. Treat an empty staged diff as a separate scope error rather than evidence that no vulnerabilities exist.

At minimum scan for hardcoded credentials, shell injection, dynamic execution, unsafe deserialization, and query string interpolation. A regex scan is only one gate; it does not replace a dedicated secret scanner for publication.

## 4. Verify independently

Run the project’s focused tests, full relevant regression suite, compilation/type/lint checks when installed, formatter **check mode**, and `git diff --check`. Lint success does not imply formatter success (for example, `ruff check` and `ruff format --check` are separate gates). Run formatter checks before freezing the staged snapshot; any subsequent auto-formatting changes the reviewed artifact and requires restaging plus a fresh patch-identity check. Do not accept a worker’s self-reported pass without rerunning the commands.

### Audit whether tests actually prove the frozen requirement

Passing tests are not sufficient evidence when their fixtures would also pass a plausible incorrect implementation. For each mandatory behavior, identify the smallest realistic mutation and confirm the staged test would fail under it:

- For “latest by timestamp,” use reversed or shuffled input so `rows[-1]` / last-write-wins cannot pass accidentally.
- For strict temporal boundaries, test equality and the first instant on each side of the boundary.
- When the specification explicitly names prohibited periods or categories (for example, both 2024 and 2025), cover every named case directly at the public parser/loader boundary; a generic lower/upper sample or an internal-schema test is not a substitute.
- For required source fields, prove the audited field is used, missing audited input fails, and forbidden substitutes cannot rescue the record. Enumerate each explicitly prohibited substitute or alias named by the governing plan/protocol; a generic stand-in does not kill a mutant that falls back only to a specifically named predicted/legacy field.
- For lineage preservation, compare every identity field end-to-end rather than asserting only that a row was created.

Treat direct constructors for immutable batches, normalized rows, evidence objects, and conflict tombstones as public trust boundaries—not as harmless test helpers. The parser may enforce an invariant while a direct constructor silently accepts impossible state that a selector later trusts. Mirror the parser's critical invariants in constructor validation and test both entry paths. For timestamp grids, check minute modulus **and** zero seconds/microseconds. For source lineage, vary digest, byte count, retrieval time, URL, and symbol/date bindings independently; a hash-only test will not kill an implementation that ignores other lineage fields. For positive-only endpoints, include zero and negative values on both current and lag sides so a `<= 0` → `== 0` mutant cannot survive.

When a review identifies a test-strength gap but current production code already behaves correctly, add the durable regression and prove its value with a focused mutant. A GREEN test alone does not show that the assertion guards the intended predicate.

Treat missing mutation-resistant coverage as blocking when the frozen plan explicitly requires TDD or says tests “must verify” the behavior, even if static inspection suggests the current implementation is correct. Ad-hoc reviewer probes can confirm present behavior, but they do not replace a staged regression: the verdict must still reject when the exact index lacks required durable coverage. Cite both the requirement and the insufficient staged test locations so the finding is actionable.

### Prove a surviving mutant without changing the repository

When a suspected test gap is subtle, execute a narrowly defined mutant **in memory** rather than editing the worktree:

1. Set `PYTHONDONTWRITEBYTECODE=1` and disable the pytest cache provider.
2. Read the reviewed source, assert the target text occurs exactly once, and replace only that expression in memory.
3. `exec(compile(mutated_source, original_path, "exec"), imported_module.__dict__)` before pytest collection so tests import the mutated definitions.
4. Run the exact staged focused suite. If it passes, report the mutant, requirement it violates, and test locations that failed to kill it.
5. Recheck status and both staged identities afterward.

This is especially useful for temporal semantics. Equality plus a happy case ten minutes later does **not** prove “eligible at every instant strictly after”; an unauthorized one- or five-minute embargo may survive. Probe the first representable instant after the boundary. Keep the probe read-only and never describe an in-memory mutant as a repository modification.

Use `scripts/probe_staged_python_mutant.py` for repeatable targeted Python probes. It verifies that the source and selected test have no unstaged split, runs the exact baseline node first, reads the source from the index with `git show :path`, preloads the single mutated module through `sys.modules`, disables bytecode and pytest cache output, and distinguishes **killed** (pytest exit 1) from **survived** (exit 0) and infrastructure errors (all other exits). Bracket the script with `read_only_index_identity.py` and full status checkpoints; a killed mutant does not override snapshot or untracked-file drift.

When the script is installed outside the repository (for example, under a Hermes profile on Windows), Python may put the script directory—not the repository root—first on `sys.path`. For dotted project modules such as `research.module`, run from the repository root with `PYTHONPATH=.` so the in-memory preload can import the parent package. This is a launch-context fix, not evidence that the mutant or test failed. Keep the usual post-gate identity/status checkpoint after any infrastructure-error attempt before retrying.

Example:

```bash
PYTHONPATH=. python path/to/audit-verification/scripts/probe_staged_python_mutant.py \
  --module package.module \
  --source-path package/module.py \
  --test-node 'tests/test_module.py::test_first_instant_after_boundary' \
  --old 'row.available_at >= decision_time' \
  --new 'row.available_at + timedelta(minutes=1) >= decision_time'
```

For a strictly read-only commit gate, inspect the index rather than assuming the worktree is identical. Reject split index/worktree states (`MM`, `AM`, etc.) or explicitly account for them, and render exact staged content with line numbers when findings must cite the reviewed artifact:

```bash
git show :path/to/file | nl -ba
```

### Honor exact isolated-invocation contracts

When the review request supplies an exact test command or environment contract, execute that command verbatim as its own tool call. Do not wrap it with status checks, append shell operators, substitute a default interpreter, add extra pytest nodes, or run mutation probes through a different pytest invocation. Put the pre-gate identity/status checkpoint in one call, the exact command alone in the next, and the post-gate checkpoint immediately afterward. This preserves both command fidelity and temporal evidence.

If the staged snapshot is intentionally dirty because the reviewed files are staged, describe the post-gate state precisely as **clean outside the frozen staged scope**: list the intended staged paths, prove the unstaged and untracked sets are empty, and prove the scoped worktree equals the index. Do not ambiguously call the whole repository clean when `git status` correctly shows staged modifications.

When the user requests only an approval/rejection plus blocking findings, keep the verdict fail-closed and concise: lead with `APPROVED` or `REJECTED`; for approval state `Blocking findings: none`, then provide only required identity, test, and clean-status evidence. Do not add nonblocking suggestions under a findings heading.

Prevent test-runner artifacts where supported. For Python/pytest, prefer:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider <focused-tests> -q
```

For syntax-only verification, consume staged source through stdin (for example, `git show :file.py | python -c 'import ast,sys; ast.parse(sys.stdin.read())'`) instead of invoking a compiler that may emit bytecode.

Inspect candidate related tests before running them when sealed data or sensitive artifacts exist. Confirm they read only permitted source/configuration/synthetic fixtures, then run focused and related suites separately so the report carries exact per-suite pass counts. Do not run broad globbed suites merely because their names look relevant; audit their transitive reads first.

Use a fresh reviewer for logic/security. Give it the staged diff or direct it explicitly to `git diff --cached`; tell it to return a fail-closed structured verdict. Reconfirm the staged patch identity after the verdict and before commit. Re-run `git status --short --untracked-files=all` after testing to prove no cache, bytecode, log, result, lock, or other artifact escaped the read-only gate. Index-tree and staged-patch identities do not cover untracked files, so an unchanged fingerprint does not override a dirty final status. If a new artifact appeared during the review, report the path and timing without claiming which process created it unless causality was actually established; do not inspect or delete an out-of-scope artifact during a no-write audit.

### Bound reviewer work so it returns a verdict

A broad reviewer prompt can consume its entire runtime exploring the repository or redundantly rerunning tests, then time out without a usable summary. Make exact-snapshot reviews deliberately bounded:

- name the only staged files and authoritative requirement sections it may inspect;
- provide the expected base HEAD, index identity, and patch digest, but require the reviewer to recompute the patch digest independently;
- when executable evidence has already been produced by the implementer, say **do not rerun tests** and ask the reviewer to assess test substance from the staged diff;
- prohibit network access, writes, staging, sealed-data access, and unrelated repository exploration;
- set an investigation budget such as “finish within 8 tool calls”;
- require a compact result containing `VERIFIED_PATCH_SHA256`, `VERDICT=APPROVE|REJECT`, `BLOCKERS`, and `NONBLOCKING`.

When the request supplies an exact machine-readable verdict schema, treat it as an output contract rather than a formatting suggestion. Return only the requested fields, in the requested order, with no Markdown fence, preamble, evidence appendix, or trailing commentary. If the schema includes both tree and patch identities, reproduce the independently verified values exactly; never substitute a nearby identity command whose byte options differ from the requested digest command.

If a reviewer times out or returns no verdict, narrow the scope and redispatch that independent lens. Do not keep expanding the timeout prompt, infer approval from completed tool calls, or count a different reviewer’s PASS as a substitute.

For specification-compliance reports, lead with `PASS` or `FAIL`, order findings by severity, and cite exact staged `file:line` locations. A PASS should explicitly state that there are no findings, report the independent checks and patch identity, and disclose whether prohibited data or result-bearing artifacts were accessed.

### Safely triage unexpected artifacts after review

A read-only reviewer should report an unexpected lock, cache, log, or generated directory without deleting it. After the reviewer returns, the implementer may clean it up only after establishing that it is not live or user-owned:

1. Record `git status --short --untracked-files=all` and the staged identity before cleanup.
2. Inspect narrow metadata first: exact path, type, size, and modification time. If the artifact may contain sensitive or sealed data, do not read its contents merely to decide whether it is generated.
3. For a lock file, check for a relevant repository/application process or lock owner. Do not treat an unrelated OS process whose name happens to contain words such as `dashboard` as ownership evidence.
4. Enumerate the containing directory and prove the candidate is the only disposable artifact before removing a directory. Never use a broad wildcard, recursive delete, `git clean`, or `git add -A` as cleanup.
5. If the artifact is zero-byte/stale, has no relevant owner, and lies in a known generated location, remove only the exact file. If ownership or purpose is uncertain, leave the gate blocked and ask the user.
6. Verify the postcondition directly: the exact path is absent, no unrelated file disappeared, the worktree/index relationship is unchanged, and `git status` is clean outside the intended staged paths. A cleanup command can return nonzero because another process concurrently removed an already-empty directory; judge success from the verified postcondition while still surfacing any unrelated error.
7. Rerun artifact/status checks immediately before the fresh reviewer and before commit. Do not hide a recurring artifact with a local exclude rule merely to make the gate appear clean; identify its producer or keep the commit blocked.

Untracked cleanup does not by itself change the staged patch digest, but any tracked edit made during remediation does. Behavioral findings still require RED → GREEN, restaging, a new identity, and fresh reviewers.

## 5. Remediate blocking findings with RED → GREEN → fresh review

A failed review is not merely a checklist to edit against. Convert every valid behavioral blocker into an executable regression:

1. Recover the complete reviewer output before editing; if a summary was truncated, read the saved full result.
2. Triage every finding against the governing specification. Fail closed on uncertain blockers.
3. Write regression tests first. Run the focused target and confirm each new test fails for the reported defect—not from collection errors, typos, or broken fixtures.
4. Apply the smallest production correction.
5. Rerun focused tests, specification tests, the full suite, lint/type/compile checks, `git diff --check`, and security scans.
6. Restage all corrected paths. `git status --short` must not show split index/worktree states such as `MM` or `AM` for the review target.
7. Record a new staged-patch digest and dispatch fresh reviewers against that exact snapshot.
8. Commit only after all blocking lists are empty and every required reviewer passes.

For material changes, use two independent lenses: a specification-compliance reviewer and a logic/security reviewer. Passing tests do not supersede either review, and dispatching an asynchronous review is not approval—the gate remains unresolved until the completed verdict is available and parsed. A timeout, crash, missing summary, or unparseable response is **no verdict**, never an implicit PASS; rerun that lens or keep the commit blocked. Likewise, a PASS from one lens cannot compensate for a missing required lens.

Independent approval also does not overrule a valid defect found later by the implementer. Convert the self-found defect into a RED regression, apply the smallest fix, rerun all gates, restage, record a new patch digest, and obtain a fresh independent verdict. Prior PASS reports belong to the old digest and become historical evidence only.

If a finding concerns normalized data, frozen manifests, generated caches, or binary fixtures, also apply `reproducibility-and-lineage-review.md` when writing the RED regressions.

## 6. Communicate long asynchronous gates clearly

A long reviewer run can look like a hang or completed work to the user. Status updates should state, in this order:

1. whether a commit has actually been made;
2. the latest reviewer verdict and the concrete blocker, if any;
3. what was changed and which RED/GREEN checks now pass;
4. the exact staged digest under review;
5. which independent verdicts are still missing.

Do not describe a dispatched reviewer as approval, and do not lead with large test counts while hiding that the commit is still blocked. If the user asks “what happened?”, answer with the last failed gate and current commit state first, then supporting verification. Keep the update concise; the detailed evidence belongs in the final gate report.

## 7. Common failure patterns

- **Review findings patched without RED:** the code changed, but no regression proves the defect or prevents recurrence.
- **Corrected files not restaged:** the reviewer inspects an older index while tests run against newer working-tree files.
- **Async dispatch treated as approval:** work is committed before the reviewer completes.
- **Untracked implementation omitted:** `git diff` showed only a small config change.
- **False-clean static scan:** malformed quoting produced a grep diagnostic, but shell flow still printed success.
- **Stale reviewer verdict:** implementation changed after the asynchronous review began.
- **Scope creep:** `git add -A` staged unrelated logs, caches, generated data, or credentials.
- **Self-verification:** the implementer’s test summary was accepted without fresh execution.
