---
name: code-quality-sweep
description: "Use when the user asks for a comprehensive code quality pass — fix everything (lint, types, docstrings, bugs, duplication), loop back until clean, and harden CI/CD gates. NOT for single-issue fixes."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-quality, linting, docstrings, type-annotations, deduplication, refactor, audit, ci-cd]
    related_skills: [requesting-code-review, simplify-code, codebase-inspection]
---

# Code Quality Sweep

Systematic, comprehensive code quality improvement across an entire codebase.
Fix everything a senior engineer would flag on review, then loop back and
re-scan until the scanner returns clean. Finally, harden CI/CD to enforce
every gate permanently.

**Core principle:** Bugs first, then structural, then cosmetic. One pass finds
one category. Re-scan after every pass until zero issues.

## When to Use

- User says "fix all the [quality] errors", "clean up the codebase", "make this pass code review", "address all findings completely"
- After rapid iteration has accumulated technical debt
- Before handing off a project — ensure it passes senior-engineer review
- When user asks "what else would a senior engineer flag?"
- When user says "do a final QA sweep"

## The Sweep — Priority Order

### Pass 0: Comprehensive Audit (17 dimensions)
When Kevin asks "any other things a sr engineer would flag" or "address all
findings completely", run the full 17-point audit:
1.  Runtime bugs (F821 undefined names, F722 bare excepts)
2.  Docstrings — all public functions
3.  Type annotations — return types + params
4.  Lint — ruff E,F,N,UP → 0 violations
5.  Duplication — consolidate copy-pasted utils into shared module
6.  Security — hardcoded secrets, HTTP timeouts, Dependabot, .env.example
7.  Stability — retry logic, error handling, health checks
8.  Maintainability — ARCHITECTURE.md, version pins, code comments
9.  Profitability/risk — stoploss, daily loss breaker, position sizing
10. Strategy research — walk-forward, bootstrap, CSCV overfitting, regime detection
11. CI/CD gates — all green on ubuntu+windows
12. Integration/smoke tests
13. Recovery procedures — RECOVERY.md
14. Research→production promotion checklist — PROMOTION_CHECKLIST.md
15. Hardcoded paths — replace with Path(__file__) or env vars
16. Backtest overfitting detection — CSCV (Bailey et al. 2017)
17. Auto-healing — stale signals auto-refresh in watchdog

Default answer to "any other things?" is YES — scan all 17. Don't stop at what the user named.

### Pass 1: Runtime Bugs (fix immediately)
```bash
ruff check . --select=F821 --output-format=concise  # undefined names
ruff check . --select=E722 --output-format=concise  # bare excepts
```
Fix these FIRST. They crash production code.

### Pass 2: Docstrings
Scan with AST for public functions missing docstrings. For 100+ missing,
dispatch 2-3 parallel subagents by directory. Skip trivial `pass`/`return`.

### Pass 3: Linting (auto-fix then manual)
```bash
ruff check . --select=E,F,N,UP --ignore=E501 --fix       # auto-fix
ruff check . --select=E,F,N,UP --ignore=E501,F401,F841,N802  # check remaining
```
Common fixes: E402→add #noqa, N806→lowercase, E741→descriptive names, UP031→f-strings (see pitfalls).

### Pass 4: Type Annotations
Scan with AST for missing return types and param types. Skip test files.
For large codebases, dispatch a subagent.

### Pass 5: Duplicated Code
Find copy-pasted utility functions. Consolidate into shared module.
Update all callers. Run tests after each batch.

### Pass 6: Hardcoded Paths & Secrets
```bash
grep -rn "'C:/\\|'/home/\\|'/Users/" --include="*.py" .
grep -rn "secret\\|password\\|api_key\\|token" --include="*.py" . | grep -v "environ\\|getenv\\|\\.env"
```

### Pass 7: Loop Back
Re-run ruff + pytest. Fix anything new. Repeat until "All checks passed!" and all tests green.

### Pass 8: CI/CD Enforcement
Build `.github/workflows/ci.yml` with hard-fail gates: ruff lint, bare-except check,
undefined-name check, deduplication scan, test matrix (ubuntu+windows), type check,
coverage (informational). Add `.pre-commit-config.yaml`.

**Critical:** Never use `|| true` on quality gates. Iterate until green — don't accept yellow.

## Subagent Dispatch Pattern

For 100+ changes across many files, dispatch 3 parallel subagents:
```python
delegate_task(tasks=[
    {"goal": "Add docstrings to all production files", "context": "Project root: C:\\Users\\kevin\\Desktop\\<project>\n\nFile list:\n  file1.py: func1, func2\n  file2.py: func3, func4\n\nAdd triple-quoted docstrings. Match existing style. No logic changes."},
    {"goal": "Add docstrings to research + stocks files", "context": "..."},
    {"goal": "Add docstrings to test files", "context": "..."},
])
```
- 3 tasks max (Kevin's config)
- Each gets full context (exact file paths, function names, what to add)
- Background dispatch — consolidated result re-enters conversation
- Check live_transcripts to monitor progress
- Subagents timeout at 600s — finish remaining items yourself

## Common Pitfalls

1. **Variable renaming breaks references everywhere.** When renaming `W`→`width`
   or `MAX_CONCENTRATION`→`max_concentration`, update ALL uses: f-strings,
   expressions, and downstream references. Re-run ruff after every rename batch.

2. **E402 imports are intentional after `sys.path.insert`.** Don't move them —
   add `# noqa: E402`.

3. **Subagent timeout at 600s is real.** For 200+ items, split into 2-3 parallel
   subagents by directory. Check their progress and finish remaining items yourself.

4. **f-string quote conflicts from UP031 %→f-string conversion.** Dict access
   `data["key"]` inside `f"..."` creates a conflict — use single-quote outer:
   `f'...{data["key"]}...'`. Method calls in format specs like `{nav.min():.3f}`
   are also ambiguous; extract to variables first. Always syntax-check converted
   files with `py_compile.compile(path, doraise=True)`.

5. **Framework-heavy files need conditional imports for CI.** Production files
   importing talib/freqtrade/tensorflow at module level break CI. Wrap in
   try/except ImportError with stubs. **Crucially:** stub base classes must
   accept the same constructor args. `IStrategy = object` fails because
   `object.__init__` accepts zero args. Define:
   ```python
   class IStrategy:
       def __init__(self, config=None):
           self.config = config or {}
   ```

6. **Coverage scoping: `--cov=.` measures everything.** Scope to source dirs
   (`--source=production,research,stocks`) not the entire repo. Measuring `.`
   includes tests, dead scripts, and `.venv`.

7. **pytest-cov + coverage CLI both conflict with numpy C extensions.** On
   Python 3.11, both trigger `ImportError: cannot load module more than once
   per process`. Run coverage as a separate `continue-on-error: true` job.
   Never gate CI on coverage when numpy is a dependency.

8. **Windows CI runner defaults to PowerShell.** Multiline `run: |` blocks
   with `\` continuation fail with `ParserError` on Windows — pwsh uses
   backtick (`) not backslash. Always add `shell: bash` to cross-platform
   CI steps.

9. **`patch` tool escape-drift on quotes.** When old_string contains `\"`,
   the tool can reject. Use `execute_code` with `content.replace()` instead.

10. **Not every same-named function is duplicated.** `compute_metrics` in 3 files
    had different signatures serving different domains. Check signatures before
    consolidating.

11. **CI iteration requires patience.** Expect 5-8 pushes to get all gates green:
    install deps → syntax errors → coverage scoping → shell:bash →
    numpy conflicts. Each iteration teaches one fix. Don't give up at yellow.

## Verification Checklist

- [ ] ruff: 0 errors on all selected rules
- [ ] No bare excepts (ruff E722)
- [ ] No undefined names (ruff F821)
- [ ] Full test suite passes (all OSes in CI)
- [ ] No duplicated utility functions
- [ ] CI workflow: all hard gates green (no yellow)
- [ ] .pre-commit-config.yaml exists
- [ ] Docstring coverage ≥ 95% on public functions
- [ ] Type annotation coverage ≥ 95%
- [ ] Security: Dependabot, .env.example, no hardcoded secrets
- [ ] Docs: ARCHITECTURE.md, RECOVERY.md, PROMOTION_CHECKLIST.md