# Parameter Optimization Sweep — Reference

## Approach

The fastest reliable way to sweep parameters on this codebase is:

1. **Edit the constant directly in the source file**
2. **Run the experiment in-process**
3. **Record results**
4. **Revert edits** (`git checkout`)

Do NOT use `setattr` in-process sweeps (module state corrupts between runs).
Do NOT use subprocess sweeps (cold Python imports add ~30s overhead per run).

## Python Mutable-Default-Arg Trap

```python
# BROKEN — constant baked at definition time
def compute_funding_fade(
    funding_series: pd.Series,
    percentile: float = FUNDING_FADE_PERCENTILE,  # ← evaluated ONCE at import
) -> pd.Series:
    ...

setattr(module, 'FUNDING_FADE_PERCENTILE', 0.95)
compute_funding_fade(series)  # still uses 0.80 (the value at import time)
```

```python
# FIXED — looked up at call time
def compute_funding_fade(
    funding_series: pd.Series,
    percentile: float | None = None,  # ← None is the only safe default
) -> pd.Series:
    if percentile is None:
        percentile = FUNDING_FADE_PERCENTILE  # ← looked up NOW
    ...

setattr(module, 'FUNDING_FADE_PERCENTILE', 0.95)
compute_funding_fade(series)  # uses 0.95 ✅
```

### Functions affected (fixed July 2026)

| Function | Parameter | Constant |
|----------|-----------|----------|
| `compute_vol_scale_from_parkinson` | `target` | `VOLATILITY_TARGET` |
| `compute_funding_fade` | `percentile` | `FUNDING_FADE_PERCENTILE` |
| `compute_oi_divergence_factor` | `reduction` | `OI_DIVERGENCE_REDUCTION` |

## One-Shot Optimization Recipe

```bash
# 1. Edit constants
sed -i 's/VOLATILITY_TARGET = 0.40/VOLATILITY_TARGET = 0.20/' research/cycle6_backtest.py
sed -i 's/VOLATILITY_TARGET = 0.40/VOLATILITY_TARGET = 0.20/' research/cycle5_backtest.py
sed -i 's/OI_DIVERGENCE_REDUCTION = 0.50/OI_DIVERGENCE_REDUCTION = 1.0/' research/cycle6_backtest.py

# 2. Run experiment
python research/run_cycle6_experiment.py

# 3. Read results
cat research/cycle6_results.json

# 4. Revert
git checkout research/cycle6_backtest.py research/cycle5_backtest.py
```

## Winning Config (July 2026)

| Parameter | Default | Optimized | Effect |
|-----------|---------|-----------|--------|
| `VOLATILITY_TARGET` | 0.40 | **0.20** | Reduces funding fade opportunity cost |
| `OI_DIVERGENCE_REDUCTION` | 0.50 | **1.0** (disabled) | Removes OI drag; was firing ~50% of days |

Results: CAGR +64.1%, Sharpe 0.68, DD -87.1%, **C-minus-B +0.17%** (first positive ever).

## References

- Commit 524c0f4 — optimized results saved
- `research/param_sweep.py` — sweep script (subprocess-based, slow on Windows)
- `research/cycle6_backtest.py` — parameter definitions
- `research/run_cycle6_experiment.py` — experiment runner
