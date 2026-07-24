# Cross-Cutting Codebase Audit

Use this when the user asks you to audit a codebase for structural, numerical, and safety issues **before** any changes are made — not to verify a fix report (use the main SKILL.md workflow for that) and not to review a git diff (use `independent-security-review.md` for that).

This methodology is complementary to `production-pipeline-audit.md` (which focuses on methodology mismatches between research and production) — this one targets **five specific categories** that apply to any codebase, pipeline or not.

## Category 1 — Formula / Numerical Accuracy

The standard financial metrics are **frequently implemented wrong** in trading bots and backtest engines. Verify each one independently.

### CAGR

Correct: `(end_value / start_value) ** (1 / years) - 1`

Common acceptable implementation via log returns: `exp(mean(log(1+r)) * N) - 1` — this is mathematically equivalent.

**Check for:** Using simple average of returns without compounding (wrong), using price ratio without annualizing, dividing by wrong number of periods.

### Sharpe Ratio

**This is the most commonly wrong formula.** The standard definition uses **simple (arithmetic) returns**, NOT log returns:

```
Sharpe = mean(simple_returns) / std(simple_returns, ddof=1) * sqrt(annualization_days)
```

The log-return version `mean(log(1+r)) / std(log(1+r)) * sqrt(N)` gives DIFFERENT numbers:
- For stock-level daily returns (±0.5%), the difference is small (< 0.5% relative)
- For crypto daily returns (±2-5%, tail ±15%), the difference is material

**Check for:** Any use of `np.log(returns)` in Sharpe computation — flag it. Also verify the denominator uses `ddof=1` (sample std, not population). Verify annualization factor: 252 for stocks, 365 for crypto.

### Max Drawdown

Correct global computation: `(nav / nav.cummax() - 1).min()` — this tracks peak-to-trough over the **entire** history.

**Watch out for:** Rolling-window drawdown (e.g., 252-day lookback) which **understates** the true maximum drawdown from any peak. Also check that the sign is conventional (negative = drawdown).

### Risk-Free Rate (when subtracted)

The daily risk-free rate from an annual rate is: `daily_rf = (1 + annual_rf) ** (1/days) - 1`

**Not** `annual_rf / days` — this is an approximation error that compounds differently. For 5% annual / 365 days: correct ≈ 0.01336%, wrong ≈ 0.01370% (2.5% relative error on the RF term).

## Category 2 — Error Propagation

For every file that feeds into another:

1. **Identify the chain** — map read/write dependencies between files
2. **For each write:** Is it atomic? (temp file → fsync → rename) Or direct `write_text()`? If the latter, the file can be corrupted mid-write.
3. **For each read:** Does it have `try/except` for `json.JSONDecodeError`, `FileNotFoundError`, `OSError`? If not, a single corrupt intermediate file crashes the entire downstream pipeline.
4. **Silent data loss:** If a file can't be written, does it crash (loud, detectable) or silently return with stale data (worse)?

**Tools:**
```bash
# Find all write_text calls
grep -rn "write_text\|\.open(" --include="*.py" target_dir/

# Find unprotected reads
grep -rn "json.loads\|read_text\|\.load(" --include="*.py" target_dir/
```

### Atomic Write Pattern (reference for fixes)

```python
tmp = path.with_suffix(".tmp")
tmp.write_text(json.dumps(data, indent=2))
tmp.rename(path)
```

For more safety:
```python
from tempfile import NamedTemporaryFile
with NamedTemporaryFile(mode="w", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as tmp:
    tmp.write(content)
    tmp.flush()
    os.fsync(tmp.fileno())
Path(tmp.name).rename(path)
```

## Category 3 — Mutable Default Arguments

Classic Python bug: a list or dict as a function default argument is **created once at definition time** and shared across all calls.

```python
def bad(items=[]):           # ← BUG: same list shared across calls
    items.append("x")
    return items

def bad(config={}):           # ← BUG: same dict shared across calls
    config["key"] = "value"
    return config

def good(items=None):         # ✓ correct
    if items is None:
        items = []
    ...
```

**Check for:** Any function signature with `=[]` or `={}` as default. Also check for `=set()` and `=defaultdict(...)` though rarer.

**Tool:**
```bash
grep -rn "def.*\[\]\|def.*\{\}" --include="*.py" target_dir/
```

## Category 4 — Security

### Check list (quick triage)

1. **Hardcoded secrets:** `api_key`, `secret`, `password`, `token` assigned as string literals. Also check `config.json` or `.env` patterns — the key itself is fine if the value comes from an env var, bad if hardcoded.
2. **Command injection:** Anywhere user-controlled string reaches `os.system()`, `subprocess.run(..., shell=True)`, or `subprocess.Popen(..., shell=True)`. Also check string-formatting into `subprocess.run([..., f"..."])` where `f` includes user input.
3. **Path traversal:** File paths constructed from unchecked user input (e.g., `open(f"data/{user_input}.json")`).
4. **Dangerous functions:** `eval()`, `exec()`, `pickle.loads()`, `compile()` with user data.
5. **`yfinance auto_adjust`:** When using yfinance, `auto_adjust=True` adjusts for splits/dividends. This is correct for backtesting but means the adjusted close is NOT the actual close price — ensure downstream code knows which price series it's using.
6. **`setattr` mutations:** Code that uses `setattr(module, name, value)` to override module-level constants at runtime. This can silently change behavior of other code in the same process. Check if the source of the overrides is validated.

## Category 5 — Type Conflicts

### Common patterns to flag

1. **`None` mixing:** `SomeFloat + None` = TypeError. Check for functions that return `None | float` and paths where the result feeds into arithmetic.
2. **String + number:** `"123" + 45` = `"12345"` (concatenation) not `168` (addition). Check for `json.loads` results (always strings for string-type JSON values) and `input()` results.
3. **`or` masking zero:** `float(value or default)` — if `value` is `0.0`, it's falsy, and `default` is used instead, silently hiding a genuine zero.
4. **Dict access vs `.get()`:** `d["key"]` raises `KeyError`; `d.get("key")` returns `None` (or a default). Check paths where a missing key would propagate silently.
5. **int division in Python 3:** `/` always returns float, `//` returns int. This is usually fine, but check when result feeds into an index or range.

### Tool
```bash
# Find potentially problematic patterns
grep -rn "\.get(" --include="*.py" target_dir/ | grep -v "\.get(""$"
grep -rn "or [0-9]" --include="*.py" target_dir/
```

## Writing the Report

Structure as:

```markdown
# Audit: [Repo/Component Name]

## 1. SECURITY
### [Finding Title] — SEVERITY
**File:** `path/to/file.py:NN`
**Issue:** Description
**Fix:** Code or approach

## 2. NUMERICAL ACCURACY
### [Finding Title] — SEVERITY
...

## 3. ERROR PROPAGATION
### [Finding Title] — SEVERITY
...

## 4. MUTABLE DEFAULTS
**Findings:** List or "None found."

## 5. TYPE CONFLICTS
**Findings:** List or "None found."

## Summary
| Category | Count | Severity |
|---|---|---|
```

Severity guide:
- **HIGH:** Output-altering formula error, permanent data loss on crash, injection vector
- **MEDIUM:** Pipe-stage failure on edge case, systematic formula bias under certain ranges, non-atomic writes
- **LOW:** Cosmetic, minor formula discrepancy, edge-case crash unlikely
- **PASS:** Verified correct, reported so you don't re-check
