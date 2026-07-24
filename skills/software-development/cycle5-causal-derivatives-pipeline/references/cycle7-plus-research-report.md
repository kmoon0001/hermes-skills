# Cycle 7+ Research Report — Condensed Knowledge Bank

Source: `research/CYCLE7_PLUS_RESEARCH_REPORT.md` — comprehensive 8-dimension report.

## What Changed (post-Cycle 6 bugfix)

| Finding | Detail |
|---------|--------|
| **TS MOM + Parkinson vol baseline validated** | B variant: **+63.8% CAGR**, 0.65 Sharpe over 2021-2023 |
| **Funding fade hurts in 2021-2023** | C-minus-B = **-5.7% CAGR** — reducing exposure during extreme funding cost more than it saved |
| **Pre-bugfix +6.3% was an artifact** | simulate_sleeves shared-NAV bug: later variants got larger base NAV |
| **Critical bug fixed** | Each sleeve tracks independent cumulative NAV. Verified: with fade=1.0, C=B to 1e-15 |
| **SMA200 replaced** | TS MOM (20/50/100d vote) captures crypto's faster trend regimes |
| **2024 out-of-sample: PASS** | TS MOM + vol on 2024: **+30.3% CAGR, 0.77 Sharpe, 33.6% max DD** — better risk-adjusted than 2021-2023 |
| **Feature cache underutilized** | 1.38M rows of funding/OI/premium — only funding ever consumed |
| **OI divergence ready** | `compute_oi_divergence_factor()` in cycle6_backtest.py — ~40 LOC to add to runner |
| **Multi-signal fade ready** | `compute_multi_signal_fade()` in cycle6_backtest.py — three-level conditional fade |

## What Remains Untested (priority order)

1. **Two-sided funding** — add longs when funding extremely negative (flush buying)
2. **OI divergence** — reduce when price up + OI down (weak trend)
3. **Multi-signal conditional** — funding fade only when OI confirms
4. **Premium duration** — consecutive hours of positive premium as crowding measure
5. **Multi-threshold** — P75/P85/P90 sensitivities

## Key Code References

| Component | File | Key Lines |
|-----------|------|-----------|
| TS MOM trend | `cycle6_backtest.py` | 49-70 |
| Parkinson volatility | `cycle6_backtest.py` | 78-95 |
| Funding fade | `cycle6_backtest.py` | 113-144 |
| Feature cache join | `cycle6_backtest.py` | 152-235 |
| Target builder (C6) | `cycle6_backtest.py` | 243-285 |
| OI divergence | `cycle6_backtest.py` | 289-310 |
| Multi-signal fade | `cycle6_backtest.py` | 312-365 |
| Target builder (C7) | `cycle6_backtest.py` | 367-420 |
| Sleeve simulation (bugfixed) | `cycle5_backtest.py` | 170-253 |
| 2024 validation | `research/CYCLE6_PLUS_STATUS.md` | Full report |

## Results Summary

| Strategy | Period | CAGR | Sharpe | Max DD |
|----------|--------|------|--------|--------|
| SMA200 + vol (Cycle 5, fixed) | 2021-2023 | +66.7% | 0.70 | 85.9% |
| TS MOM + Parkinson vol (Cycle 6 B) | 2021-2023 | **+63.8%** | **0.65** | 87.6% |
| TS MOM + Parkinson vol (2024 OOS) | **2024** | **+30.3%** | **0.77** | **33.6%** |
| C-minus-B (funding fade) | 2021-2023 | -5.7% | — | — |

**2024 result is the key finding**: the TS MOM + Parkinson vol strategy passes its first genuine out-of-sample test with better risk-adjusted metrics (0.77 Sharpe, 33.6% max DD). The lower but more consistent CAGR (+30.3% vs +63.8%) is actually healthier — it suggests the strategy isn't dependent on the 2021 bull run or 2023 recovery.

## Data Inventory

| Dataset | Location | Ready? |
|---------|----------|--------|
| OKX 1h spot (5 pairs) | `user_data/data/okx/*-1h.feather` | ✅ through 2026-07 |
| Binance funding cache | `research/generated/cycle5_features.feather` | ✅ (2021-2023 only) |
| Binance OI cache | Same feather — `feature_family == 'open_interest'` | ✅ (unused) |
| Binance premium cache | Same feather — `feature_family == 'premium_pressure'` | ✅ (unused) |
| 2024 cache | Not yet built — URL validation rejects 2024 | ❌ Needs cache builder refactor |
