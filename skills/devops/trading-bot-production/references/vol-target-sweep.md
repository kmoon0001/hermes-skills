# Vol Target Sweep — Correct Methodology

## The Bug

Two bugs prevented clean vol target comparison:

1. **Wrong module override:** The experiment runner (`run_cycle5_experiment.py`)
   imports `from research import cycle5_backtest` and calls
   `cycle5_backtest.simulate_sleeves()`. The vol target that actually controls
   the backtest is `cycle5_backtest.VOLATILITY_TARGET` (default 0.15), NOT
   `cycle6_backtest.VOLATILITY_TARGET` (default 0.30). Overriding c6 has zero
   effect. Must override BOTH: `c5.VOLATILITY_TARGET = vt` AND
   `c6.VOLATILITY_TARGET = vt`.

2. **State caching in same process:** Running the experiment twice in the same
   Python process produces different-length results (different sleeves active at
   different vt levels), causing `ValueError: Length mismatch: Expected axis has
   N elements, new values have M elements`. The fix is to run each vt value in
   a FRESH subprocess with no shared module state.

3. **Index alignment bug:** `run_cycle5_experiment.py:222` assumed all pairs
   produce identical indices. Fixed to use intersection of all result indices
   with `common_index.intersection()`.

## Correct Sweep Methodology

For each vt value, spawn a FRESH subprocess:

```python
code = f"""
import sys, json
sys.path.insert(0, '.')
import research.cycle5_backtest as c5
import research.cycle6_backtest as c6
c5.VOLATILITY_TARGET = {vt}
c6.VOLATILITY_TARGET = {vt}
import research.run_cycle5_experiment as c5_exp
result = c5_exp.main()
...
"""
r = subprocess.run([sys.executable, "-c", code], capture_output=True, ...)
```

The marker line `RESULT_JSON:` in stdout provides reliable parsing even when
pyarrow FutureWarnings flood stderr.

## Results (2021-2024, current engine)

| vt | CAGR | Sharpe | MaxDD | ES |
|:--:|:----:|:------:|:-----:|:--:|
| 0.15 | 25.7% | 0.823 | -24.6% | -3.2% |
| 0.20 | 26.5% | 0.828 | -25.1% | -3.3% |
| 0.25 | 27.3% | 0.832 | -25.7% | -3.4% |
| 0.30 | 28.2% | 0.835 | -26.2% | -3.5% |
| 0.35 | 28.9% | 0.836 | -26.8% | -3.6% |
| **0.40** | **29.6%** | **0.837** | **-27.4%** | **-3.6%** |
| 0.45 | 30.3% | 0.839 | -27.8% | -3.7% |
| 0.50 | 30.8% | 0.839 | -28.3% | -3.8% |

Selected: vt=0.40 — +1.4% CAGR over baseline (0.30) with only -1.2% additional
drawdown. Marginal gains diminish after 0.45.

## Regime Breakdown

| Regime | vt=0.30 | vt=0.40 | Effect |
|--------|:-------:|:-------:|--------|
| Bear 2022 | -4.6% | -4.8% | Slightly worse (-0.2%) |
| Sideways 2024 | -4.0% | -4.2% | Slightly worse (-0.2%) |

Higher vt amplifies everything — gains AND losses. Over the full period, bull
market gains outweigh bear losses by ~7:1 ratio. Classic leverage tradeoff.

## Files

- `research/run_vt_sweep.py` — automated sweep script (8 values, fresh subprocess each)
- `research/run_vt_regime.py` — sub-period regime analysis (bull/bear/recovery/sideways)
- `research/vol_target_sweep_full.json` — saved sweep results
