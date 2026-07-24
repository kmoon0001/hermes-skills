---
name: audit-verification
description: Systematic verification of fix/audit report claims against actual source files, OR standalone data integrity audits of data files, run scripts, and job configurations. Use when a user asks you to QA, verify, or audit claims in a fix report, audit document, remediation plan, change log, OR to run an independent data integrity audit with no pre-existing claims document. Domain-agnostic — works for Copilot Studio agents, configs, codebases, or any file-backed project.
category: software-development
---

# Audit & Fix Report Verification

Use this skill when a user asks you to verify that claims in a fix report, audit document, or remediation plan actually match the current state of the files on disk, OR to run a standalone data integrity audit from scratch.

There are two entry points:

- **Entry A — Claims Verification** (you have a report/plan to check): follow the workflow below.
- **Entry B — Standalone Data Integrity Audit** (no pre-existing claims document): load `references/standalone-data-integrity-audit.md` for the checklist and methodology instead.

---

## Entry A: Claims Verification Workflow

### Step 1: Read the Fix Report (or Audit Doc)

Read the full report to understand:
- What files were modified (specific paths)
- What specific changes were claimed (added, removed, changed)
- What issues were explicitly NOT addressed (the "known remaining issues" list)
- Any quantitative claims (e.g., "N files modified", "X bytes saved")

### Step 2: Map Claims to Verification Actions

For each claim, pick the right verification method:

| Claim Type | Verification Method | Tool |
|---|---|---|
| *"X was added to file Y"* | Search for X in file Y — confirm ≥1 match | `search_files(content)` |
| *"X was removed from file Y"* | Search for X in file Y — confirm 0 matches | `search_files(content)` with output_mode='content' |
| *"X was changed to Y"* | Check Y is present AND X is absent | Two `search_files` calls |
| *"N files were modified"* | Count files matching a pattern / check timestamps | `search_files(files)` |
| *"All files validate"* | Run parser on every file, independently | `terminal` with `python3 -c "import yaml; ..."` |
| *"Structural change"* (e.g. EndDialog added) | Read the relevant section of the file | `read_file` + grep for pattern |
| *"Boilerplate removed from N files"* | Spot-check a representative sample for the removed pattern | `search_files(content)` across all target files |
| *"This issue was NOT addressed"* | Re-check the issue against current file content | Per issue, same method as above |

### Step 3: Batch Independent Reads

Files and searches that don't depend on each other should be requested in the same turn. This is especially important for audit verification — you'll often need to verify 5+ files simultaneously.

### Step 4: Run Format and Change-Set Validation Independently

Do NOT trust the report's own validation results. Run your own.

When verifying uncommitted or pre-commit code, first load `references/staged-diff-verification.md`. It covers untracked-file visibility, safe triage of unexpected lock/cache artifacts, exact-path staging, fail-closed security scans, asynchronous reviewer snapshot identity, independent reruns, and the required RED→GREEN→restage→fresh-review loop for blocking findings. A reviewer verdict is valid only for the exact staged patch it inspected. Run `scripts/scan_staged_added_lines.py` for a cross-platform, fail-closed first-pass security scan that does not echo matched secrets. For a strictly read-only fingerprint of both the index tree and staged binary patch, run `scripts/read_only_index_identity.py` before and after the review; unlike `git write-tree`, it does not write Git objects. For narrow Python mutation checks, use `scripts/probe_staged_python_mutant.py`; it baseline-checks one pytest node, injects one exact staged-source mutation in memory, and reports killed/survived/error without editing the repository.

For generated caches, normalized datasets, frozen source manifests, experiment inputs, feature normalizers, or as-of selectors, also load `references/reproducibility-and-lineage-review.md`. It covers exact manifest-set equality, row-to-manifest consistency, deterministic ordering and tie handling, strict timestamp grammars, malformed runtime-type probes, mutant-resistant selector tests, parser-versus-schema duplicate policy, binary fixtures, and directory-level artifact ignores.

For one-shot download/build/freeze pipelines, also load `references/one-shot-artifact-builder-review.md`. It covers TOCTOU no-overwrite races, owner-scoped cleanup, redirect-before-contact policy, bounded network/ZIP memory, adversarial adapter tests, exact Arrow schemas, and field-by-field manifest/quality verification.

For **independent security, concurrency, and specification correctness reviews** of a git commit — not a report-claim verification — load `references/independent-security-review.md`. It covers lock lifecycle path-matrix auditing, resource-leak closure tracing, transient/permanent error classification, the structured three-tier verdict format (APPROVE / APPROVE_WITH_NOTES / REJECT), and temp-file cleanup traps. Load this whenever the user asks for an independent audit of a commit (e.g. "review commit X for correctness, concurrency safety, and security"), not a compare-against-report workflow.

For a **from-scratch production pipeline audit** — no pre-existing report to verify, just find every bug and methodology mismatch — load `references/production-pipeline-audit.md`. It covers the full 7-phase workflow: mapping the production surface, locating research ground truth, line-by-line comparison against research, data flow and state audit, silent failure mode search, dashboard audit, and report compilation. Use this when the user asks "audit this pipeline" or "find what's wrong with production."

For a **cross-cutting codebase audit** — checking formula correctness, error propagation, mutable defaults, type conflicts, and security in a codebase **before** making any changes (no existing report to verify) — load `references/cross-cutting-codebase-audit.md`. It defines a five-category checklist (numerical accuracy, error propagation, mutable defaults, type conflicts, security) with correct formulas, detection tools, severity guidance, and report structure. Use this when the user says "read every Python file and look for [specific categories of issues]" without a pre-existing claims document.

For **fix implementation** after the audit is complete — systematically applying surgical patches to the pipeline without cascading breakage — load `references/production-pipeline-fix-implementation.md`. It covers read-everything-first planning, data-file reality checks, backward-compatible field renames, consumer update sweeps, and before/after documentation. Use this when the audit findings are known and the user says "fix all the issues."

For **cross-cutting formula fixes** — when the same numerical bug (e.g., log-return Sharpe vs simple-return Sharpe) appears in multiple files and must be fixed at the source — load `references/cross-cutting-formula-fix.md`. It covers the find-defining-vs-importer classification, handling different formula styles (pct_change, NAV-diff, bootstrap, raw-equity loops), keeping CAGR/MaxDD unchanged, dependent-importer verification, and bootstrap-specific pitfalls.

When two independent reviewers return conflicting verdicts (APPROVE vs REJECT) on the same frozen snapshot, load `references/reviewer-conflict-reconciliation.md`. It covers freezing the exact identity, mapping each alleged blocker to its governing requirement, independent inspection, RED → GREEN regression for confirmed blockers, artifact regeneration, new identity capture, and fresh approval — all without treating conflict as a voting problem.

```bash
# YAML
python3 -c "import yaml; yaml.safe_load(open('path/to/file'))"

# JSON
python3 -c "import json; json.load(open('path/to/file'))"

# XML
python3 -c "import xml.etree.ElementTree as ET; ET.parse('path/to/file')"
```

Batch all files into a single command (one loop) rather than one call per file.

### Step 5: Re-check Each "Not Addressed" Issue

The fix report's "remaining issues" section should be treated as testable claims:
- Does issue X still exist in the files?
- Is the root cause still present?
- Has a partial fix been applied that the report didn't claim?

### Step 6: Audit Statistical, Promotion, and Data-Gate Claims

When the report concerns a backtest, experiment, or model-promotion decision, load `references/statistical-backtest-audit.md`. In particular:

- distinguish failure to demonstrate superiority from proof of a harmful/negative true effect;
- reconcile bootstrap method names, estimands, dependence assumptions, and interval language;
- identify partial temporal slices created by warm-up periods;
- separate realized tail-risk improvement from lower-exposure effects;
- verify per-asset P&L attribution is additive before using breadth/concentration gates;
- keep diagnostics, preregistered gates, and search-adjusted final promotion decisions distinct.

When development, validation, or holdout periods are sealed, also load `references/sealed-data-codebase-audits.md`. It covers safe inventory, the mixed-file read-before-filter trap, point-in-time joins, common-support comparisons, synthetic causality tests, and precise closeout claims.

### Step 7: Compile the QA Report

First honor any explicit output contract. If the user requires an exact line count, field order, delimiter, or machine-readable schema, that contract overrides the default report below. Emit exactly the requested lines and nothing else—no preface, Markdown fence, evidence appendix, or trailing explanation. Recompute every identity field immediately before the verdict, and copy the verified values exactly.

Otherwise, structure as:

```
# QA Report: [Project Name] — [Loop/Fix]
## QA Summary (table: Check × Status)
## Per-Check Details
### 1. [Check Group 1]
- Claim from report
- What you found (exact evidence: line numbers, search results, validation output)
- PASS/FAIL verdict
### 2. [Check Group 2] ...
## Remaining Issues (still open)
- Re-verified against files
## Final Assessment
- % readiness estimate
- What blocks eval/go-live
```

---

## Pitfalls

- **Trust but verify** — the fix report is a claim, not evidence. Always cross-check against actual files.
- **Check both presence AND absence.** For "X was changed to Y", verify Y exists AND X does not.
- **Zero matches is meaningful.** When verifying something was removed, use `search_files` with `output_mode='content'` and confirm `total_count: 0`.
- **Run validation independently.** The report says "all pass" — run the parser yourself. They sometimes miss files.
- **Check for side effects.** A fix to topic A may reference files in topic B that no longer exist, or the fix may have been applied inconsistently across related files.
- **Don't stop at the claimed scope.** If the report says "5 topics fixed", check whether related topics (system topics, backup files, src/ files) also need the same fix.
- **Count matters.** If the report says "14 files cleaned", verify by counting pattern matches across all files — don't just spot-check.
- **Watch for .bak files.** If the fix went wrong, the .bak file might contain the pre-fix state. Compare when something looks wrong.
- **False positive detection rule for comparative experiments.** When auditing a claim that variant C outperforms variant B (e.g. C-minus-B > 0), first verify that when the differentiating feature is set to its neutral value (fade=1.0, veto=False, identical parameters), C and B produce IDENTICAL results to machine precision. A non-zero C-minus-B with neutral features is always a bug (e.g. shared-NAV accumulation in simulation loops), never a real signal. Run this neutral-feature check before inspecting any variant-comparison metric.
