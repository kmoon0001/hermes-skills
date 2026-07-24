# CI/CD Patterns — GitHub Actions for Python Projects

Patterns proven on the freqtrade-cycle5-research trading bot codebase.
Covers lint gates, test gates, CI-compatible code patterns, and common CI
failure modes.

## GitHub Actions Workflow Template

Minimal CI pipeline with four jobs: lint (hard gates), test (pytest),
typecheck (mypy, informational), build (verification).

### Lint Job — Hard Quality Gates

```yaml
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.11' }
    - run: pip install ruff

    # Full codebase lint — hard fail
    - run: ruff check . --select=E,F,N,UP --ignore=E501,F401,F841,N802 --no-cache

    # Specific enforcement gates (separate steps for clear failure messages)
    - name: No bare excepts
      run: |
        bare=$(ruff check . --select=E722 --output-format=concise --no-cache 2>&1 | grep -c "E722" || true)
        if [ "$bare" -gt 0 ]; then
          ruff check . --select=E722 --no-cache
          exit 1
        fi

    - name: No undefined names
      run: |
        undef=$(ruff check . --select=F821 --output-format=concise --no-cache 2>&1 | grep -c "F821" || true)
        if [ "$undef" -gt 0 ]; then
          ruff check . --select=F821 --no-cache
          exit 1
        fi

    - name: No duplicated utilities
      run: |
        python -c "
        import os, ast, sys
        from collections import Counter
        dup_targets = {'load_json', 'now_pt', 'now_iso', 'atomic_write', 'atomic_write_json'}
        counts = Counter()
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != '.venv']
            for f in files:
                if not f.endswith('.py'): continue
                path = os.path.join(root, f)
                try:
                    tree = ast.parse(open(path).read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name in dup_targets:
                            counts[node.name] += 1
                except: pass
        violations = {k: v for k, v in counts.items() if v > 1}
        if violations:
            for name, count in sorted(violations.items()):
                print(f'FAIL: {name} defined {count}x')
            print('Move to production/util.py and import from there.')
            sys.exit(1)
        print('PASS: no duplicated utility functions')
        "
```

### Test Job — Standalone Tests Only

```yaml
test:
  needs: lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.11' }
    - run: pip install pytest pytest-timeout numpy pandas pyarrow scipy python-dateutil pytz yfinance
    - run: |
        python -m pytest tests/ \
          -v --tb=short \
          --ignore=tests/test_cycle2_mtf_strategies.py \
          --timeout=120 \
          -p no:warnings
```

Only install the minimal packages needed by the test suite. Heavy framework
dependencies (freqtrade, ccxt, TA-Lib) are NOT installed — tests that need
them must either skip gracefully or the code must use conditional imports.

## CI-Compatible Code Patterns

### Pattern 1: Conditional Import with Fallback

When a module imports a heavy library that isn't available in CI:

```python
try:
    import talib.abstract as ta
except ImportError:
    ta = None  # CI fallback — TA-Lib not available
```

Then guard usage sites:

```python
if ta is not None:
    sma = ta.SMA(dataframe, timeperiod=w)
else:
    sma = dataframe["close"].rolling(w, min_periods=w).mean()
```

### Pattern 2: Stub Base Class

When inheriting from a framework class unavailable in CI:

```python
try:
    from freqtrade.strategy import IStrategy
except ImportError:
    class IStrategy:
        """Stub for CI — accepts the same args as the real class."""
        def __init__(self, config: dict | None = None):
            self.config = config or {}
```

The stub class must accept the same constructor arguments as the real class,
so tests that instantiate the strategy don't break.

### Pattern 3: What NOT to Do

DON'T use `pytest.importorskip` when the import error comes from a dependency
of the module under test, not the test module itself. Example:

```python
# WRONG — skips too broadly, hides regressions in other test classes
pytest.importorskip("freqtrade")

# RIGHT — fix the module under test to handle missing deps
```

DON'T use `|| true` after lint commands — it silently swallows failures.

## Common CI Failures and Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'talib'` | Strategy imports talib at module level | Conditional import (Pattern 1) |
| `TypeError: X() takes no arguments` | Stub base class is `object` | Define stub with proper `__init__` (Pattern 2) |
| `ModuleNotFoundError: No module named 'freqtrade'` | Production import in test path | Conditional import + stub class (Pattern 2) |
| `ImportError: cannot import name 'X' from 'Y'` | Function was renamed/moved but caller not updated | Update all callers; grep for the old name |
| `F811 Redefinition of unused X` | Imported X from util.py but also defined locally | Remove local definition, use the import |

## Debugging CI Failures

```bash
# List recent runs
gh run list --limit 5

# View failed job logs
gh run view <run-id> --log-failed

# View specific job
gh run view <run-id> --job <job-id> --log

# Check all job conclusions
gh run view <run-id> --json jobs -q '.jobs[] | "\(.name): \(.conclusion)"'
```
