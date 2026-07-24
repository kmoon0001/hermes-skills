# Off-by-One NAV Allocation Lag Bug

## Pattern

A simulation loop where `prev_target_alloc` (initialized to 0.0) is used
for NAV computation instead of the freshly-computed `target_alloc`. The
intent is: "day T's allocation decision earns day T→T+1's return." But
the bug means day T's return is earned using day T-1's allocation —
systematically lagging by one bar.

## Root Cause

```python
prev_target_alloc = 0.0                       # correct: day 0 = all cash
for t in range(1, n):
    target_alloc = targets.iloc[t - 1] * dd_mult  # T-1 decision
    r = closes[t] / closes[t-1]                   # T-1→T return
    nav[t] = nav[t-1] * (1 + (r-1) * prev_target_alloc)  # BUG: uses PREV
    prev_target_alloc = target_alloc
```

On iteration t=1:
- `target_alloc` = targets[0] (correct T=0 decision)
- `prev_target_alloc` = 0.0 (still cash)
- NAV uses 0.0 → first bar's return is MISSED entirely

On iteration t=2:
- `target_alloc` = targets[1] (T=1 decision)
- `prev_target_alloc` = targets[0] (from previous iteration)
- r = closes[2] / closes[1] (T=1→T=2 return)
- NAV uses targets[0] → T=0 decision earns T=1→T=2 return → OFF BY ONE

## Fix

Use `target_alloc` (the current T-1 decision) for the T-1→T return:

```python
nav[t] = nav[t-1] * (1 + (r - 1.0) * target_alloc)
```

The cost check already correctly compares `target_alloc` (current) vs
`prev_target_alloc` (previous), so no change needed there.

## Detection

- Run with `cost=0` and `target=1.0` (always long). NAV should exactly
  match buy-and-hold. Any deviation reveals the lag.
- Per-bar attribution: print `target_alloc` vs the return it's applied to.
  If the allocation at bar T is the allocation from bar T-1, the bug is
  present.
- Symptom: CAGR is significantly understated (10-15pp in crypto, more in
  long-duration backtests). Sharpe is also depressed since the lag adds
  noise. Max DD improves artificially (lag delays entries into drawdowns).

## Impact

Found in `research/cycle5_backtest.py` simulate_sleeves. Cost ~12pp of
annualized CAGR by delaying every entry and exit by one bar. Affected
all research Cycles 3-8. Fixed in commit `8f034fe`.
