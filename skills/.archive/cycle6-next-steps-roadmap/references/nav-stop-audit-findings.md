# NAV Stop Audit — Full Findings

## Date: 2026-07-19

## General Technique: Decompose Aggregate Metrics

This audit used a general-purpose debugging technique applicable to any system where a combined/composite metric is suspicious:

1. **List every component** that feeds into the aggregate
2. **Compute the metric per-component** — don't just look at the combined value
3. **Compare component-level values** — the component with a disproportionate value is the likely root cause
4. **Verify component controls** — check that each component is actually affected by the controls you think are in place

In this case: the combined maxDD was 92%, but B sleeve had only 24% DD. The P sleeve was the outlier — and it wasn't affected by the DD stop. This technique applies to portfolio-level metrics, aggregated test results, combined performance benchmarks, or any system where a composite number hides a component-level problem.

## Specific Finding

The `simulate_sleeves` function in `cycle5_backtest.py` includes a passive P sleeve (buy-and-hold) that dominates the combined portfolio NAV and drives the reported 92% drawdown. The active B sleeve individually has maxDD of only 18-30%.

## The Bug

In `simulate_sleeves` (cycle5_backtest.py:240-243):
```python
# P and PV sleeves (passive buy-and-hold)
passive = np.zeros(n, dtype=np.float64)
passive[0] = SLEEVE_WEIGHT
for t in range(1, n):
    passive[t] = passive[t - 1] * (closes[pair].iloc[t] / closes[pair].iloc[t - 1])
result["sleeve_p"] = pd.Series(passive, index=targets.index)
```

The P sleeve:
1. Starts at SLEEVE_WEIGHT (0.20) per asset
2. Tracks spot price — compound growth during bull markets
3. Is NOT scaled by dd_mult (the DD stop)
4. Is NOT rebalanced or reduced

Meanwhile the DD multiplier (`dd_mult`) only scales target allocations for A/B/C sleeves:
```python
dd_mult = dd_multiplier_series.iloc[t - 1] if dd_multiplier_series is not None else 1.0
target_alloc = targets[target_key].iloc[t - 1] * dd_mult
```

## How It Was Found

**Step 1:** Initial B-only audit showed only 33% DD — not 92%. This was a red flag.

**Step 2:** Full pipeline trace (with feature cache, regime filter, funding fade) confirmed 93.5% DD on pass 1. Per-sleeve decomposition revealed:
- Sleeve B: final=1.04, maxDD=21.3%
- Sleeve P: final=24.78, maxDD=93.8%
- Combined: maxDD=93.5%

**Step 3:** The P sleeve was 91.3% of SOL's combined NAV by end of period. Since the DD stop doesn't touch P, it barely helps.

## Two-Pass Stop Impact

The two-pass DD stop (commit 4a5e60c) reduced DD from 93.5% → 92.0% — only 1.5pp improvement. This is because it only reduced active sleeve exposure while P continued to suffer full drawdowns.

## Fix Options

1. **Evaluate on B-only (recommended):** Exclude P sleeve from strategy metrics
2. **Apply DD stop to P:** Modify simulate_sleeves to scale P notional by dd_mult
3. **Remove P entirely:** If P is only a benchmark, don't include it in combined NAV

## Key Code Locations

- `research/cycle5_backtest.py:240-243` — P sleeve (hardcoded buy-and-hold)
- `research/cycle5_backtest.py:218-222` — DD multiplier applied to A/B/C only
- `research/run_cycle6_experiment.py:260-261` — Combined NAV = sum of all sleeves including P
- `research/p_sleeve_dominance.py` — Full per-sleeve decomposition script
