# Reviewer-Conflict Reconciliation

Use this when two or more independent subagent reviews return **conflicting verdicts** (e.g. one APPROVE, one REJECT) on the same frozen snapshot identity.

Do NOT treat a tied vote as needing a tiebreaker. Conflicts are evidence that the reviewers inspected different aspects or had different standards. Resolve by direct, reproducible evidence.

---

## Workflow

### 1. Freeze the exact identity under dispute

Record both the committed tree and the staged/working-tree patch SHA-256 that both reviewers were asked to inspect. Confirm the reviewers actually inspected the same bytes:

```bash
git rev-parse HEAD^{tree}  # committed tree
git diff --cached --binary --full-index --no-ext-diff | sha256sum  # staged patch
```

If the two reviewers were dispatched against different snapshots (e.g. one against staged, one against working tree), that is the root cause — no reconciliation needed. Re-dispatch both against the same identity.

### 2. Map each alleged blocker to its governing requirement

The REJECT verdict contains specific allegations with file:line locations. For each allegation:

- **Identify the governing specification or protocol requirement.** If the allegation claims "resource leak" — what exactly says handles must be closed? If "mutation gap" — what says the tests must catch that mutant?
- **Distinguish objective defects from subjective style.** "Lock descriptor not closed on KeyboardInterrupt" is objective. "Could add more error handling" is subjective.
- **Flag allegations that are missing a requirement reference.** A blocker with no spec anchor is a reviewer opinion, not a defect.

### 3. Inspect every alleged blocker independently

Do not trust either reviewer's characterization. Read the source code at the cited line numbers yourself:

- Search for the exact alleged pattern (e.g. missing `fp.close()`, bare `except OSError`)
- Read 20 lines of context before and after
- Check whether the alleged defect can actually occur in a real execution path
- For resource leaks: trace every `return`, `raise`, and fall-through exit before the next close/release point
- For mutation gaps: write the smallest mutant by hand in memory and run the test (see `scripts/probe_staged_python_mutant.py`)

### 4. Convert every confirmed blocker into a RED regression test

For each objective, confirmed blocker:

1. Write the smallest test that demonstrates the defect (RED)
   - For resource leaks: instrument a close-tracking fake and assert the handle was closed even on the failure path
   - For concurrency: use a monkeypatched seam that injects the failure
   - For mutation gaps: write the test that would catch the mutant
2. Run the focused test and confirm it fails for the expected reason
   - `F` on the specific assertion, not a collection error or broken fixture
3. Apply the minimal production fix
4. Confirm the test passes (GREEN)

### 5. Rerun the full suite after all blocker fixes

After all blockers have RED→GREEN:

```bash
python -B -m pytest <target> -q --tb=short
```

One expected failure may be the frozen-identity test (if the fix changed the builder source hash, the manifest's builder SHA will mismatch). That is expected and is resolved by regeneration.

### 6. Regenerate frozen artifacts and verify new identity

```bash
# Remove only the exact owned outputs
rm research/generated/<cache> research/<manifest> research/<quality>

# Rebuild
python -m research.<module> --build --start <start> --end <end>

# Run full suite — identity test must pass
python -B -m pytest <target> -q
```

### 7. Capture the new frozen identity

```bash
git add -A
git commit -m "Task N: reconcile reviewer conflicts — <summary>"
printf 'COMMIT=%s\n' "$(git rev-parse HEAD)"
printf 'TREE=%s\n' "$(git rev-parse HEAD^{tree})"
printf 'PATCH_SHA256=%s\n' "$(git diff HEAD~1..HEAD --binary --full-index --no-ext-diff | sha256sum | cut -d ' ' -f 1)"
```

### 8. Obtain fresh approval for the new identity

Dispatch an independent reviewer against the new commit (not the old one). The previous APPROVE and REJECT verdicts apply only to the old identity and are superseded.

---

## Distinguishing real blockers from false positives

| Allegation | Likely real if | Likely false if |
|---|---|---|
| Resource leak (unclosed handle) | All exit paths from the guard are not traced; a `finally` or `try/except`/`except BaseException` would catch it | The handle is closed in a `finally` that runs or the handle is owned by a context manager already in use |
| Mutation gap (test too weak) | The smallest plausible mutant passes the test suite | The mutant changes semantics so drastically that any real implementation would never produce it |
| Concurrency race | Two processes can actually enter the critical section simultaneously | The test uses threads only and the production code has a file-system-based lock |
| Wrong error classification | A permanent error gets retried or a transient error raises without retry | The classification matches stdlib/OS semantics (e.g. SSLCertVerificationError is permanent, ETIMEDOUT is transient) |

## Pitfalls

- **Do not keep the old identity.** After any source change, the frozen tree and patch SHA change. Re-running the identity test against the old manifest is expected to fail.
- **Do not manually patch the manifest hash.** Regenerate, don't edit.
- **Do not combine findings from two different snapshots.** If one reviewer inspected staged and another inspected working tree, their findings are incommensurable.
- **A REJECT with plausible-sounding but unsubstantiated claims is not actionable.** Require file:line evidence and a spec/requirement reference for each blocker.
- **An APPROVE that missed real defects is not a valid approval.** The conflict means at least one reviewer was wrong — resolve by evidence, not by counting votes.
