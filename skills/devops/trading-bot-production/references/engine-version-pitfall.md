# Engine Version Compatibility — Critical Pitfall
# Engine Version Compatibility — Critical Pitfall

## The Problem
The Crypto Cycle 5/6 backtest engine was **fixed on July 21, 2026** (engine commit
6f40c7df). The fix corrected:
- Off-by-one NAV lag (CAGR understated by ~12pp)
- P-sleeve contamination (P sleeve compounded B&H despite target_p=0)

Numbers from BEFORE and after this fix are **NOT comparable**. The old engine
systematically understated returns.

## Two Module Override Bugs (Fixed 2026-07-22)

The experiment runner uses `cycle5_backtest.VOLATILITY_TARGET` (default 0.15),
NOT `cycle6_backtest.VOLATILITY_TARGET` (default 0.30). When testing different
vt values, you MUST override BOTH:

```python
c5.VOLATILITY_TARGET = vt  # THIS controls the actual simulation
c6.VOLATILITY_TARGET = vt  # this is for the sweep tool
```

Symptom of overriding only c6: ALL vt values produce IDENTICAL results — the
override silently failed and the backtest used 0.15 for every run.

**Second bug:** state caching in the experiment runner. Running `main()` twice
in the same Python process with different vt values causes:
```
ValueError: Length mismatch: Expected axis has 1093 elements, new values have 1007 elements
```
This happens because different vt values produce different sleeve coverage.
**Solution:** run each vt in a FRESH subprocess (`subprocess.run` with inline code).

**Third bug (also fixed):** `run_cycle5_experiment.py:222` used
`combined_result.index = all_results[0].index` which crashes when sleeves have
different date ranges. Fixed to use index intersection with reindex+fillna.

## Correct Sweep Methodology

See `references/vol-target-sweep.md` for the full protocol and results.
Quick pattern:
```python
for vt in values:
    code = f"""
import sys, json; sys.path.insert(0, '.')
import research.cycle5_backtest as c5
import research.cycle6_backtest as c6
c5.VOLATILITY_TARGET = {vt}
c6.VOLATILITY_TARGET = {vt}
import research.run_cycle5_experiment as c5_exp
result = c5_exp.main()
print('RESULT_JSON:' + json.dumps(...))
"""
    subprocess.run([sys.executable, "-c", code], ...)
```

## Verified Results (2026-07-22)

The sweep was successfully re-run on the current engine using the corrected
methodology. Results at `research/vol_target_sweep_full.json`.

| vt | CAGR | Sharpe | MaxDD |
|:--:|:----:|:------:|:-----:|
| 0.30 (old baseline) | 28.2% | 0.835 | -26.2% |
| **0.40 (selected)** | **29.6%** | **0.837** | **-27.4%** |

vt=0.40 IS verified better: +1.4% CAGR, marginally higher Sharpe, marginally
worse drawdown. The earlier claim that vt=0.40 was unverified was CORRECT at
the time — we couldn't prove it without a clean sweep. Now we can.

## Verification Checklist

1. Override BOTH `c5.VOLATILITY_TARGET` AND `c6.VOLATILITY_TARGET`
2. Run each value in a fresh subprocess (no shared state)
3. Parse RESULT_JSON marker from stdout (ignore stderr pyarrow warnings)
4. Save with engine metadata for future comparison
5. NEVER compare results across different engine commits
