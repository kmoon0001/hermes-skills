# PV-Sleeve Capital Destruction — Reproduction

## The Bug

`cycle5_backtest.py:262` — the PV-sleeve else-branch destroys accumulated capital when `target_pv` drops from positive to zero.

```python
# cycle5_backtest.py lines 252-263
target_pv_series = targets.get("target_pv", pd.Series(0.0, index=targets.index))
passive_vol = np.zeros(n, dtype=np.float64)
passive_vol[0] = SLEEVE_WEIGHT * target_pv_series.iloc[0]
for t in range(1, n):
    target_pv = target_pv_series.iloc[t - 1]
    if target_pv > 0:
        passive_vol[t] = passive_vol[t - 1] * (closes[pair].iloc[t] / closes[pair].iloc[t - 1])
    else:
        passive_vol[t] = SLEEVE_WEIGHT * target_pv  # BUG: = 0.20 * 0 = 0
```

Compare with the P-sleeve (correct):

```python
# P-sleeve else-branch (line 249): holds cash flat
else:
    passive[t] = passive[t - 1]  # CORRECT: preserves prior NAV
```

## Reproduction

```python
import numpy as np
import pandas as pd

SLEEVE_WEIGHT = 0.20
n = 5
closes = pd.Series([100, 101, 99, 102, 98])
# target_pv: active (0.3) on days 1-2, zero on days 3-4
target_pv_series = pd.Series([0.3, 0.3, 0.0, 0.0, 0.0])

# Current (buggy) PV sleeve:
passive_vol = np.zeros(n, dtype=np.float64)
passive_vol[0] = SLEEVE_WEIGHT * target_pv_series.iloc[0]  # 0.06
for t in range(1, n):
    target_pv = target_pv_series.iloc[t - 1]
    if target_pv > 0:
        passive_vol[t] = passive_vol[t - 1] * (closes.iloc[t] / closes.iloc[t - 1])
    else:
        passive_vol[t] = SLEEVE_WEIGHT * target_pv  # = 0 at t=3,4

print(f"Buggy PV NAV: {passive_vol}")
# [0.06, 0.0606, 0.0588, 0.0, 0.0]  ← capital destroyed at t=3!

# Fixed (cash-flat):
passive_vol_fixed = np.zeros(n, dtype=np.float64)
passive_vol_fixed[0] = SLEEVE_WEIGHT * target_pv_series.iloc[0]
for t in range(1, n):
    target_pv = target_pv_series.iloc[t - 1]
    if target_pv > 0:
        passive_vol_fixed[t] = passive_vol_fixed[t - 1] * (closes.iloc[t] / closes.iloc[t - 1])
    else:
        passive_vol_fixed[t] = passive_vol_fixed[t - 1]  # cash flat

print(f"Fixed PV NAV:  {passive_vol_fixed}")
# [0.06, 0.0606, 0.0588, 0.0588, 0.0588]  ← capital preserved
```

## Fix

```python
# Line 262: change
passive_vol[t] = SLEEVE_WEIGHT * target_pv
# to
passive_vol[t] = passive_vol[t - 1]
```

## Impact Assessment

**Limited in current usage:**
- Cycle 6 runner uses only `sleeve_b` (ignores PV)
- Cycle 9 runner uses variant-specific sleeves (ignores PV)
- Cycle 5's `build_targets` sets `target_pv = vol_scale.where(trend, 0.0)` — target_pv can be non-zero during uptrends, then drops to 0 when trend flips. The bug destroys PV capital on every trend-flip.

**If PV sleeve is ever activated in a new experiment**, this bug silently zeroes the sleeve on every target_pv=0 day.
