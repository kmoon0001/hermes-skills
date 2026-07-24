# Exact-Snapshot Review for High-Assurance Work

Use this mode for research engines, financial simulations, migrations, security-sensitive changes, or any plan that requires independent approval before results or deployment.

## Why

A reviewer approval is meaningful only when it identifies the exact bytes reviewed. Reviewing a moving working tree—or committing before review and then amending—breaks that chain of custody.

## Per-task sequence

1. Implement with tests-first development.
2. Run focused tests, related regressions, formatting, linting, strict typing, compilation, and whitespace checks as applicable.
3. Stage only the files declared for the task. Do not commit yet.
4. Require no unstaged tracked changes in the reviewed files.
5. Record the exact snapshot:

```bash
git diff --cached --check
git diff --cached --stat
git write-tree
git diff --cached --binary | sha256sum
```

6. Dispatch two read-only reviewers against `git diff --cached`:
   - specification/protocol compliance;
   - adversarial correctness, security, and test adequacy.
7. Give reviewers the original task text, frozen constraints, exact commands they may run, and an explicit prohibition on edits, staging, resets, or commits.
8. While review runs, only perform read-only prerequisite discovery for later tasks. Do not modify the staged snapshot or begin code that touches the same files.
9. On rejection, reproduce each blocking finding, add a regression test, fix, rerun all gates, restage, record a new identity, and repeat both reviews. Prior approvals do not transfer to changed bytes.
10. Commit only after both reviewers approve.
11. Verify the commit contains the reviewed tree:

```bash
reviewed_tree=<tree-from-step-5>
git commit -m "..."
test "$(git rev-parse HEAD^{tree})" = "$reviewed_tree"
```

## Reviewer output contract

Require a deterministic verdict such as:

```text
APPROVED
<concise evidence>
```

or:

```text
REJECTED
- <blocking finding with file:line and reproduction>
```

Do not treat a self-review, passing tests, HTTP success, or a reviewer’s unverified summary as independent approval.

## Context and tool-budget discipline

Long plans can exhaust an agent’s tool-iteration budget before a review returns. Preserve rigor without spending one call per trivial observation:

- Batch independent reads and searches.
- Group closely related adversarial cases into one parameterized RED test, then implement the common validation path and rerun that group.
- Keep separate RED/GREEN evidence for materially different behavior boundaries.
- Use one staged task checkpoint at a time; do not carry several uncommitted tasks.
- Record todo state, test counts, tree identity, and the exact continuation point after every task gate.
- Do not consume time by polling background reviewers; perform read-only preparation that cannot invalidate the stage.

### Controller-discovered defects while review is pending

The controller may discover a blocking defect through a synthetic probe while reviewers are still bound to the staged snapshot. Treat that as a known rejection without mutating the bytes under review:

1. Record the exact input and observed behavior as a queued RED regression.
2. Keep the staged tree unchanged until all dispatched reviewers return; their reports may reveal additional defects that belong in the same remediation snapshot.
3. Do not claim the old snapshot is approvable merely because its ordinary test/lint/type gates pass.
4. After all verdicts arrive, add the smallest grouped RED tests, prove they fail for the intended reason, implement the common fix, and rerun the complete gate.
5. Restage and compute a new tree/diff identity. Both independent approvals must be repeated against those new bytes.

Distinguish a **behavioral defect** from a **coverage-only gap** with a no-file synthetic probe when possible. Queue a regression test for both, but do not misreport correct behavior as a code defect.

If the platform forces a stop, report the exact staged tree/diff identity, known queued defects, and pending review state. Never claim approval, completion, or commit status that was not observed.