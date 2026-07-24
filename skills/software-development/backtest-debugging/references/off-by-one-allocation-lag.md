# Off-by-One Allocation Lag — Fix Reproduction

## Found in: `simulate_sleeves()` (Freqtrade custom backtest engine)

### Before (buggy)

```python
prev_target_alloc = 0.0
for t in range(1, n):
    target_alloc = targets[target_key].iloc[t - 1] * dd_mult

    # Close-to-close return
    r = float(closes.iloc[t][pair] / closes.iloc[t - 1][pair])

    # Sleeve NAV grows by position-weighted close-to-close return
    variant_nav[t] = variant_nav[t - 1] * (1.0 + (r - 1.0) * prev_target_alloc)

    # Only charge cost when target allocation changes
    if t > 1 and target_alloc != prev_target_alloc:
        variant_nav[t] *= (1.0 - abs(target_alloc - prev_target_alloc) * cost)

    prev_target_alloc = target_alloc
```

**Bug:** `prev_target_alloc` on line 221 was the allocation from the PREVIOUS loop iteration (T-2). The correct allocation for the T-1→T return is `target_alloc` (T-1). Every bar's return was earned using the wrong allocation.

**Trace:**
- t=1: target_alloc=T0 signal, prev=0.0 → NAV grows by 0% (first bar MISSED)
- t=2: target_alloc=T1 signal, prev=T0 signal → T1→T2 return earned with T0 allocation (LAGGED)

### After (fixed)

```python
prev_target_alloc = 0.0
for t in range(1, n):
    dd_mult = dd_multiplier_series.iloc[t - 1] if dd_multiplier_series is not None else 1.0
    target_alloc = targets[target_key].iloc[t - 1] * dd_mult

    # Close-to-close return: closes[t] / closes[t-1] is the return
    # from t-1 to t. We apply the t-1 decision (target_alloc) to this return.
    r = float(closes.iloc[t][pair] / closes.iloc[t - 1][pair])

    # Sleeve NAV grows by position-weighted close-to-close return.
    # Uses target_alloc (t-1 decision) for t-1→t return, NOT prev_target_alloc.
    variant_nav[t] = variant_nav[t - 1] * (1.0 + (r - 1.0) * target_alloc)

    # Only charge cost on turnover (delta between consecutive target allocations)
    if t > 1 and target_alloc != prev_target_alloc:
        turnover = abs(target_alloc - prev_target_alloc)
        variant_nav[t] *= (1.0 - turnover * cost)

    prev_target_alloc = target_alloc
```

**Fix:** `target_alloc` (T-1 decision) correctly applied to T-1→T return.
`prev_target_alloc` is now used ONLY for the cost turnover comparison (T-1 vs T-2),
not for NAV computation.

## Verification

Simulate with cost=0, vol_scale=1.0, trend=1.0 (always long). The terminal NAV
should match the buy-and-hold return exactly. Before the fix, the first bar's
return was always missed and all subsequent bars lagged by one — producing
NAV systematically below buy-and-hold.

## Impact

This bug was present in `simulate_sleeves()` since the engine was first built
and affected ALL cycles (3-8) that used this function. The reported CAGR values
are systematically understated. The directional comparisons (A vs B vs C)
remain valid since all variants share the same bug, but absolute metrics need
recomputation.
