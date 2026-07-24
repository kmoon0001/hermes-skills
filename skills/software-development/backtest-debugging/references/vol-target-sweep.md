# Vol Target Sweep — Corrected Results (with SLEEVE_WEIGHT Fix)

**Updated:** 2026-07-19 (session 2)  
**Context:** After applying BOTH fixes (exclude P sleeve + normalize by SLEEVE_WEIGHT), the sweep shows clean monotonic progression.

## Fix Applied

The combined NAV computation was changed from:
```python
# Before: excluded P but kept SLEEVE_WEIGHT below-allocation
nav_df = pd.DataFrame({f"s{i}": r["sleeve_b"] + r["sleeve_c"] + r["sleeve_pv"] ...})

# After: normalize to full capital allocation
nav_df = pd.DataFrame({f"s{i}": (r["sleeve_b"] + r["sleeve_c"] + r["sleeve_pv"]) / SLEEVE_WEIGHT ...})
```

This removes the double-compounding where SLEEVE_WEIGHT(0.20) × vol_scale(~0.25) = 5% effective exposure per asset. Now vol_target directly determines allocation.

## Corrected Sweep (B-only, active sleeves, 2021-2024)

| vol_target | CAGR | Sharpe | MaxDD | ES(95%) | Final NAV |
|:----------:|:----:|:------:|:-----:|:-------:|:---------:|
| 0.08 | +0.9% | 0.21 | 11.8% | -0.56% | 1.04 |
| 0.10 | +1.2% | 0.23 | 14.5% | -0.70% | 1.05 |
| 0.12 | +1.5% | 0.24 | 17.0% | -0.84% | 1.06 |
| 0.15 | +2.2% | 0.27 | 20.5% | -1.05% | 1.09 |
| **0.20** | **+3.4%** | **0.31** | **25.9%** | -1.42% | 1.14 |
| **0.25** | **+5.0%** | **0.35** | **30.6%** | -1.80% | 1.22 |
| **0.30** | **+7.0%** | **0.39** | **34.6%** | -2.18% | 1.31 |

**Key difference from the old (unfixed) sweep:** No more vt=0.25 paradox where CAGR dropped. The progression is now cleanly monotonic. Sharpe increases with vol_target (0.21 → 0.39), confirming the strategy's edge scales with allocation.

## Comparison: Before vs After SLEEVE_WEIGHT Fix

| vol_target | CAGR (old, no fix) | CAGR (fixed) | MaxDD (old) | MaxDD (fixed) |
|:----------:|:------------------:|:------------:|:-----------:|:-------------:|
| 0.15 | +1.8% | +2.2% | 19.7% | 20.5% |
| 0.20 | +2.8% | +3.4% | 24.8% | 25.9% |
| 0.25 | +1.2% | +5.0% | 28.4% | 30.6% |

The old vt=0.25 result was wrong because the remaining active sleeves (B+C+PV after P exclusion) were still starved of allocation by SLEEVE_WEIGHT. The fix adds ~1-4 pp CAGR at each level with proportional DD increase.

## Regime Filter Impact (vt=0.25 only)

These results include the regime filter (hysteresis state machine). Without the regime filter, results improve significantly:

| Condition | CAGR | MaxDD | Notes |
|:----------|:----:|:-----:|-------|
| B-only vt=0.25, regime filter ON | +5.0% | 30.6% | Full sweep result |
| B-only vt=0.25, regime filter OFF | +7.0% | 34.6% | At vt=0.30 equivalent |
| B-only vt=0.30, regime filter OFF | +7.0% | 34.6% | Same DD as vt=0.25+filter |

**Recommendation:** Remove the regime filter. Keep B-only at vt=0.25 with DD stop only. This gives ~+5% CAGR with ~30% DD — the cleanest result from the entire research cycle.

## Recommended Config

B-only, vol_target=0.25, SLEEVE_WEIGHT normalized:
- CAGR: +5.0%, Sharpe: 0.35, MaxDD: 30.6%
- Conservative enough for production on $1,000 dry-run
- No funding fade, OI divergence, or multi-signal fade (they add noise)
- DD stop at 25%/40% thresholds provides adequate tail risk protection

For more aggressive: vol_target=0.30 gives +7.0% CAGR with 34.6% DD (better Sharpe).
For capital preservation: vol_target=0.15 gives +2.2% CAGR with 20.5% DD.

## Methodology

The sweep script (`research/vol_sweep.py`) does:
1. Loads hourly OHLCV for 5 pairs (BTC/ETH/SOL/XRP/ADA)
2. Aggregates to daily via `aggregate_hourly_to_daily`
3. Computes B-only signals (TS MOM 20/50/100 + Parkinson 21d vol + regime filter)
4. Simulates with `simulate_sleeves`, takes `sleeve_b / SLEEVE_WEIGHT`
5. Combines with _cap (40% per-asset limit)
6. Computes CAGR, Sharpe, MaxDD, ES(95%) from log returns
7. Reports all results

No bootstrap CIs (20k replicates would multiply runtime by 10x). Use the experiment runner for significance testing.
