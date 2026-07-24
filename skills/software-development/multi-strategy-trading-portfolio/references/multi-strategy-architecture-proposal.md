# Session: Multi-Strategy Architecture for TS MOM + Complementary Strategies

**Date:** 2026-07-19  
**Context:** Adding 2-3 parallel strategies to an existing OKX spot TS MOM strategy ($1,000 dry-run, daily at 10am PT cron).  
**Codebase:** `C:\Users\kevin\Desktop\freqtrade\` — Freqtrade-based, 6 completed research cycles.

## Existing Strategy (TS MOM) Config

| Parameter | Value |
|---|---|
| Trend signal | 20/50/100d SMA vote (≥ 2 = trend on) |
| Vol estimator | Parkinson HL 21-day |
| Vol target | 0.30 |
| Symbols | BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT, ADA/USDT |
| Sleeves | 5 independent 20% sleeves (fixed, never redistributed) |
| Overlays | None (all overlays hurt returns: funding fade -5.6%, OI divergence -5.6%, regime filter, DD stop) |
| Pipeline | `generate_signals.py` → `execute_trades.py` (JSON files) |
| Execution | Daily at 10am PT via cron |

## Research History (6 Cycles)

| Cycle | What | Result |
|---|---|---|
| 1 | Donchian breakout grid | Best PF 1.04, p=0.82 — noise |
| 2 | 4h regime + 1h triggers | Both H1/H2 negative |
| 3 | Weekly TS MOM (28/84/168) | -33% vs always-long vol-scaled control |
| 4 | Cross-sectional 84d leadership | Underperformed equal-weight control |
| 5 | SMA200 + vol + binary veto | -29% CAGR (veto never joined) |
| 6 | TS MOM + Parkinson + P80 funding fade | C-minus-B = -5.6% (overlay hurt) |

**Best config:** B-only (pure TS MOM + Parkinson vol, no overlays, vol_target=0.30)

## What This Session Added

### Architecture: Master Allocator with Strategy Sleeves

Proposed shift from "overlay on one strategy" to "parallel independent strategy sleeves." Each strategy:
- Owns its own capital budget (set by master allocator)
- Computes its own signals independently
- Has its own P&L tracked off-chain (not on exchange)
- Only interacts with other strategies via order netting at execution time

### Most Promising New Strategies

1. **Portfolio-Level Vol Targeting** (genuinely untested, ~30 lines)
   - Different from per-asset vol scaling (which already exists)
   - Compute equal-weight portfolio Parkinson vol from all 5 assets
   - Apply uniform: `scale = min(1.0, target / rolling_portfolio_vol)`
   - Reduces total exposure during high-vol regimes (bear markets)
   - Expected correlation to TS MOM: 0.3-0.4

2. **Regime Cash Sleeve** (simple, new hypothesis)
   - BTC SMA50/SMA100 state machine: bull (100%) / transition (70%) / bear (40%)
   - Faster crash exit than TS MOM's 50d slowest flip
   - Expected correlation to TS MOM: 0.5-0.6

3. **Relative Strength Rotation** (new twist on Cycle 4)
   - 30-day cross-sectional ranking with gradual weight (not binary top-2)
   - Higher risk — Cycle 4 closed the cross-sectional branch

### Recommended Capital Allocation

| Phase | Method |
|---|---|
| First 60 days | Static: 60% TS MOM / 25% Regime / 15% Port Vol |
| 60+ days | Risk parity (inverse-vol weighting from live returns) |

### Key Backtest Discipline

2021-2023 dev data is fully consumed. New strategies gate on 2024 first (now authorized for validation per CYCLE7+ Appendix C). 2025 holdout remains sealed.

### Conflict Resolution

Order netting per-asset: sum dollar amounts across strategies, execute one net order. Per-strategy P&L tracked in JSON with pro-rata fill attribution.

## Files Created This Session

- `production/MULTI_STRATEGY_PROPOSAL.md` — full 10-section architecture proposal

### Follow-up Session (2026-07-19)

**What was done:**
1. Reviewed two completed research subagent reports (multi-strategy architecture + drawdown recovery)
2. Refactored production codebase: created `production/strategies/` directory with BaseStrategy abstract class, TSMOMStrategy class, and module __init__.py
3. Dispatched two parallel implementation subagents:
   - **Subagent A:** Portfolio-level vol targeting → `research/cycle8_portfolio_vol.py`
   - **Subagent B:** SRR Statistical Range Recovery → `research/cycle8_srr.py`
4. Both subagents run independent backtests on 2024 OOS data only
5. Refactored files: `production/strategies/base.py`, `production/strategies/strategy_tsmom.py`, `production/strategies/__init__.py`

## Key References in Codebase

| File | Purpose | Result |
|---|---|---|
| `research/CYCLE6_RESULT.md` | TS MOM validated at +63.8%/0.65 Sharpe | — |
| `research/FINAL_DECISION.md` | Best config: B-only, vol_target=0.20 | — |
| `research/CYCLE67_RESULTS.md` | Combined Cycle 6+7 findings | — |
| `research/CYCLE7_PLUS_RESEARCH_REPORT.md` | Exhaustive 8-dimension research | — |
| `research/cycle6_backtest.py` | Core signal logic | — |
| `research/cycle8_portfolio_vol.py` | PVT backtest (2024 OOS) | **NO-GO** — CAGR: 4.80% (baseline) vs 4.76% (PVT 0.25) / 1.55% (PVT 0.20). Correlation 0.997-1.0. Per-asset vol scaling already does the job. |
| `research/cycle8_srr.py` | SRR backtest (2024 OOS) | **NO-GO** — Only 3 trades in 2024. MaxDD halved from 23% to 12% but CAGR halved from 6% to 3%. Sharpe flat at 0.35. Signal too rare on daily large-cap crypto. |
| `production/generate_signals.py` | Daily signal computation | — |
| `production/execute_trades.py` | Trade execution | — |

### Cycle 8 Results Detail

**Portfolio-Level Vol Targeting (PVT):**
| Variant | CAGR | Sharpe | Max DD |
|---------|------|--------|--------|
| Baseline TS MOM | 4.80% | 0.324 | 23.9% |
| PVT target=0.20 | 1.55% | 0.111 | 23.4% |
| PVT target=0.25 | 4.76% | 0.322 | 23.9% |
| PVT target=0.30 | 4.80% | 0.324 | 23.9% |

Root cause: existing per-asset vol scaling keeps portfolio vol below 0.20 most of the time. The second layer never engages.

**Statistical Range Recovery (SRR):**
| Metric | TS MOM alone | SRR sleeve | Combined |
|--------|-------------|------------|----------|
| CAGR | +6.00% | 0.00% | +3.07% |
| Sharpe | 0.355 | 0.000 | 0.351 |
| Max DD | 22.95% | 1.50% | 12.42% |
| Volatility | 16.43% | 3.31% | 8.60% |

3 trades only (BTC/XRP/ADA, all triggered July 5 2024, +1.9-3.5% each, exited in 2 days via 25th percentile target). The 20% cash sleeve mechanically dilutes returns — same effect as holding 20% permanently in cash with no strategy.
