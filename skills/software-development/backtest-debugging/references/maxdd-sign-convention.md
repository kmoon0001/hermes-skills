# MaxDD Sign Convention Fix — July 2026

## The Bug

Research JSONs stored `max_drawdown` as a **positive** number (e.g., `0.3459`) while stock JSONs and industry convention use **negative** (e.g., `-0.3459`). When any downstream tool, comparison script, or summary generator reads both sets of files, the sign mismatch produces silent nonsense — a DD of 34.6% appears as +34.6%, which looks like a *gain* rather than a *loss*.

## Why It Happens

The `compute_metrics` function in the backtest engine computes drawdown as:

```python
peak = np.maximum.accumulate(nav)
drawdown = (nav - peak) / peak
max_drawdown = float(-np.min(drawdown))
```

The double-negative: `np.min(drawdown)` is negative (worst trough), `-np.min(drawdown)` flips to positive. Mathematically correct but **conventionally wrong** for financial reporting. When written to JSON, downstream consumers expect negative DD.

## Detection Pattern

Run a recursive check across all JSON result files:

```python
def check_maxdd_sign(data):
    positives = []
    def walk(obj, path=""):
        if isinstance(obj, dict):
            if "max_drawdown" in obj and isinstance(obj["max_drawdown"], (int, float)):
                if obj["max_drawdown"] > 0:
                    positives.append((path, obj["max_drawdown"]))
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")
    walk(data)
    return positives
```

Also check `"calmar"` (Calmar = CAGR / |MaxDD| — depends on sign-correct DD).

## Fix Script Pattern

Recursive JSON walker that negates positive max_drawdown in-place:

```python
def negate_maxdd(obj):
    if isinstance(obj, dict):
        if "max_drawdown" in obj and isinstance(obj["max_drawdown"], (int, float)):
            if obj["max_drawdown"] > 0:
                obj["max_drawdown"] = -obj["max_drawdown"]
        for v in obj.values():
            negate_maxdd(v)
    elif isinstance(obj, list):
        for item in obj:
            negate_maxdd(item)
```

## Files Fixed (July 2026)

| File | Occurrences | Notes |
|------|-------------|-------|
| `cycle3_results.json` | 16 | A/B/C/D sleeves × cost=10/20/30bps + delayed |
| `cycle5_results.json` | 2 | result + root-level |
| `cycle6_results.json` | 2 | result + root-level |
| `cycle6_results_2024.json` | 1 | Single-result |
| `cycle6_expanding_window_results.json` | 14 | 7 windows × 2 levels |
| `cycle7_results.json` | 2 | result + root-level |
| `cycle8_srr_results.json` | 3 | ts_mom, srr, combined |
| `cycle8_portfolio_vol_results.json` | 4 | baseline + 3 pvt variants |
| `cycle8_vs_cycle6_summary.json` | 5 | Raw-data sections (summary values were already negative) |

**Skipped:** `cycle4_results.json` (already negative), `stocks/*.json` (already correct).

## Root Cause Fix (July 2026)

The band-aid approach (post-hoc JSON negation) works but every new consumer of `compute_metrics` will reintroduce the bug. The permanent fix: change the source function.

**In `compute_metrics` (e.g., `cycle5_backtest.py:312`):**

```python
# BEFORE (wrong — returns positive):
max_drawdown = float(-np.min(drawdown))

# AFTER (correct — returns negative, per financial convention):
max_drawdown = float(np.min(drawdown))
```

**Cascading effects of root cause fix:**

1. **All local copies must be fixed too.** `run_cycle9_experiment.py` had its own `_compute_metrics` with the same `float(-np.min(drawdown))` bug.
2. **Tests that assert positive DD must be flipped.** Pattern: `assert metrics["max_drawdown"] > 0.0` → `assert metrics["max_drawdown"] < 0.0`.
3. **Any consumer doing post-hoc negation will now double-negate.** If a runner had `result["max_drawdown"] = -abs(result["max_drawdown"])` to correct the old positive output, it must be removed after the root fix.
4. **Stored JSONs become inconsistent.** Old JSONs written with positive DD need a one-time sign-fix pass (see Fix Script Pattern above). New runs produce negative directly.

**Verification checklist after root cause fix:**
- [ ] Fix `compute_metrics` in the defining module
- [ ] Find and fix ALL local copies of the same formula (grep for `float(-np.min(drawdown))`)
- [ ] Update ALL tests that assert on max_drawdown sign
- [ ] Remove any post-hoc negation wrappers in consumers
- [ ] Re-run experiment runners to produce new negative-signed JSONs
- [ ] Run sign-fix walker on any old JSONs that won't be re-generated

## The Partial-Fix Trap

Summary JSONs often contain both:
- **Rounded summary values** already manually negated
- **Raw data reference values** copied verbatim from source (still positive)

The recursive fixer must visit ALL nested keys. Pre-negotiated values are not a signal the file is clean. Always run the full recursive check after fixing.

## Verification

Run the detection script after fixing. Confirm zero positives across all research JSONs. Spot-check known values (e.g., cycle6 baseline DD = -0.3459 ≈ -34.6%).
