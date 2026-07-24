# Immutable Review for Frozen Research Tasks

Use this protocol when a causal research plan requires each ordered task to be independently reviewed and committed before the next task begins.

## Snapshot identity

Complete tests, mutation checks, formatting, lint, typing, compilation, diff checks, and secret scanning before staging. Then stage only the task's explicit file allowlist—never `git add -A`—and require a clean worktree outside the index.

```bash
git add -- <explicit task files>
git diff --quiet
test -z "$(git ls-files --others --exclude-standard)"
git diff --cached --check

BASE_HEAD=$(git rev-parse HEAD)
INDEX_TREE=$(git write-tree)
PATCH_SHA256=$(git diff --cached --binary --no-ext-diff | sha256sum | cut -d' ' -f1)
```

Record all three values. `BASE_HEAD` anchors task order; `INDEX_TREE` identifies exact staged content/modes; `PATCH_SHA256` identifies the exact staged binary patch.

## Dual read-only review

When two approvals are required, split responsibilities:

- **Protocol reviewer:** frozen specification, source semantics, causal timing, missingness, lineage, sealed-period boundaries, and economic invariants.
- **Adversarial reviewer:** malformed inputs, tests, mutation resistance, typing, security, regression risk, and vacuous-test detection.

Give both reviewers the repository path, exact identity, authoritative files, scoped staged files, and explicit constraints: no edits, staging, commits, network, generated files, or sealed data. Require each to independently verify the staged patch SHA-256 and return `APPROVE` or `REJECT` with blocking/nonblocking findings.

An architecture audit of an earlier worktree is feedback, not approval. A missing, truncated, or self-reported result without the verified hash is not approval.

## Approval invalidation

Any post-identity change invalidates all approvals: formatting, one-line fixes, restaging, mode changes, test edits, or unrelated staged content. After any change:

1. rerun applicable gates;
2. restage the allowlist;
3. compute a new identity;
4. obtain two fresh approvals of that identity.

## Rejection-remediation loop

If one reviewer approves and another rejects, the snapshot is rejected. Do not preserve or combine the lone approval with a later corrected snapshot. Translate every blocker into both:

1. a production invariant at the public boundary where malformed evidence could enter; and
2. an adversarial test or focused mutation that fails if the invariant is deleted or weakened.

Rerun the focused module first, then the wider regression set, typing/lint/compilation/diff checks, and the reviewer-specific mutation probes. Every source, test, or formatter change creates a new staged identity and requires two fresh approvals.

Guard against vacuous remediation tests. Independently vary each field that the implementation is supposed to compare, exercise both sides of numeric boundaries (for example zero and negative), and construct invalid evidence directly when normalizers would otherwise make the bad state unreachable. A test that only mutates one lineage field does not prove complete lineage equality.

Run mutation probes in isolated temporary repository copies using the real project interpreter and focused test module. Never mutate the authoritative worktree or index. The useful evidence is that every named weakening is killed, not merely that a mutation command ran.

## Final commit gate

Immediately before commit, recheck:

```bash
test "$(git rev-parse HEAD)" = "$BASE_HEAD"
test "$(git write-tree)" = "$INDEX_TREE"
test "$(git diff --cached --binary --no-ext-diff | sha256sum | cut -d' ' -f1)" = "$PATCH_SHA256"
git diff --quiet
git diff --cached --check
git status --short
```

Commit the already-staged snapshot with the frozen task message. Do not restage between this check and commit. Do not begin the next ordered task until the commit exists.

## Clean-test execution

Third-party pytest plugins can contaminate exact-snapshot reviews. Prefer the project interpreter and disable plugin autoload, bytecode, and pytest cache artifacts:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  <project-python> -B -m pytest -p no:cacheprovider ...
```

Verify status before and after tests. Remove generated locks/caches; never ignore or commit them merely to pass the clean-tree gate.

## Tool-limit handling

If execution stops before reviewers return, leave the exact snapshot staged but uncommitted, report its HEAD/tree/patch hash and pending reviews, and do not start the next research task. Resume by verifying identity before accepting delayed approvals.
