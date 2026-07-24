---
name: cycle6-next-steps-roadmap
description: "Cycle 6 TS MOM bot — next steps roadmap based on Codex research including DD audit, B-only production switch, and Cycle 8 preregistration."
version: 1.0.0
author: Hermes Agent
---

# Cycle 6 TS MOM — Next Steps Roadmap

Trigger: User asks about next steps for the Cycle 6 TS MOM bot, drawdown problems, or what to research next.

## Context

The TS MOM (20/50/100d vote 2/3) + Parkinson 21d vol strategy (B sleeve) has a proven edge (OOS 0.85 Sharpe, 28% DD on 2024). The funding/OI overlays (C sleeve) are noise (C-minus-B -0.08% IS / -1.60% OOS). Production pipeline runs daily at 10am PT on OKX dry-run $1,000.

## ✅ NAV Stop Audit — Completed (2026-07-19)

**Root Cause: The passive P sleeve (buy-and-hold benchmark) drives the 92% combined DD, not the active strategy.**

The experiment runner's `simulate_sleeves` includes a P sleeve that tracks buy-and-hold for each asset (hardcoded — not reducible by the DD stop). It starts at 20% per asset and grows unchecked. During the 2021-2024 bull, P grew to dominate the portfolio:

| Asset | P % of combined NAV (end) | P sleeve maxDD | B sleeve maxDD |
|-------|--------------------------|----------------|----------------|
| BTC   | 57.6%                    | 76.6%          | 24.2%          |
| ETH   | 67.5%                    | 79.3%          | 24.8%          |
| SOL   | **91.3%**                | **96.3%**      | 18.5%          |
| XRP   | 78.6%                    | 83.2%          | 30.3%          |
| ADA   | 63.4%                    | 91.8%          | 25.4%          |

**The B sleeve (TS MOM + Parkinson vol + regime filter) has maxDD of only 18-30%.** That's healthy for crypto.

### How We Found It: Decompose the Aggregate

The critical debugging step was **decomposing the combined portfolio NAV into per-sleeve contributions** (see `scripts/p_sleeve_dominance.py`). The combined NAV was summing A+B+C+P+PV sleeves from `simulate_sleeves`, but the P sleeve:
- Cannot be reduced by the DD stop (`dd_mult` only scales target allocations for A/B/C, not P's hardcoded buy-and-hold)
- Exposes the portfolio to full spot drawdowns
- After bull runs, dominates the portfolio weight (SOL's P sleeve reached 91.3% of that pair's combined NAV)

### Fix

**Evaluate on B sleeve only** for strategy metrics. The P sleeve is a comparative benchmark, not an active strategy component. If P must stay, its notional must also be scaled by the DD stop.

### Diagnostic Scripts

- `scripts/nav_stop_audit.py` — Minimal B-only trace (daily feather files, no feature cache)
- `scripts/nav_stop_audit_full.py` — Full pipeline trace (hourly→daily aggregation, feature cache, all signals, DD stop with detailed trigger logging)
- `scripts/quick_p_check.py` — Quick single-pair P-sleeve dominance check
- `scripts/p_sleeve_dominance.py` — Full 5-pair per-sleeve decomposition with per-asset and portfolio-level DD reporting

### See Also
- `references/nav-stop-audit-findings.md` — Full trace data, trigger timestamps, and state machine logs

## Sleeve Architecture → B-only Production

- Run **B-only as production default**
- Funding/OI overlays = diagnostics only (dormant research branch)
- Keep as research-only with immutable feature snapshots
- Do not let overlays trade until they pass preregistered gates (positive OOS C-B in 2+ folds, bootstrap CI excludes negative, survives fees/latency, no DD worsening)

## SOL Concentration

1. Decompose risk, not just return (marginal contribution, worst-10-day loss per asset)
2. Test capped risk-parity sizing (inverse-vol weights) with 40% sleeve cap + portfolio gross cap
3. Do NOT drop BTC/ETH yet — in-sample selection bias
4. Add assets through a liquidity-first universe rule (historical availability, OKX tradability, volume, spread/fees)
5. Preregister: no asset >50% of return OR >50% of expected tail loss over rolling 12-month windows

## Vol Target Math

**NOTE: The 92% DD in the table below was driven by the P sleeve artifact (see NAV Stop Audit above), not by the B strategy alone.** After removing P sleeve contamination, B-only with vol=0.15 has maxDD of only ~30%.

Log-return scaling from 0.15 baseline (reported combined CAGR +106.4%, DD 92.0% — B-only actual DD ~30%):
| Target | Est. CAGR | Est. DD |
|--------|-----------|---------|
| 0.15 | +106% | 92% |
| 0.12 | +79% | 87% |
| 0.10 | +62% | 81% |

Rerun from frozen code **after** stop audit. Lowering vol alone won't fix a broken risk control.

## Cycle 8 Preregistration

**Primary:** Risk architecture + regime attribution, not new alpha signals.

Test these variants against B-only baseline:
1. Equal-weight baseline (frozen)
2. Capped inverse-volatility risk parity
3. Capped covariance-aware risk parity
4. Best of (2)/(3) + BTC-funding market-wide crowding filter

Preregistered market regimes:
- Bull: BTC above 200d SMA + positive 60d return
- Bear: BTC below 200d SMA + negative 60d return
- Range: otherwise

Gates: OOS max DD improves ≥30%, OOS Sharpe no worse than -0.10 from baseline, no asset >50% of tail loss, survives cost perturbations.

Secondary experiments (separate, sequential):
1. Parkinson 21d vs GARCH(1,1)
2. BTC funding as portfolio crowding filter
3. Liquidity-screened universe expansion
4. Alternative trend signals (MACD, RSI, ROC) — only after risk cycle finishes

Do NOT combine multi-exchange, new vol model, new assets, and new trend in one cycle.

## Production Roadmap (Immediate)

1. **B-only pipeline** — funding/OI emit diagnostics only, not orders
2. **Persistent risk state** — daily peak NAV, DD state, stop transitions, raw/final weights, fills, reconciled OKX balances
3. **Pre-trade portfolio checks** — gross exposure cap, per-asset 40% cap, stale-data rejection, fail-closed mode
4. **Post-execution reconciliation** — intended vs submitted vs filled vs actual balances; alert on mismatch
5. **Shadow backtest parity** — same prior-day inputs produce same targets in research and production
6. **Keep $1,000 dry-run** until NAV-stop audit and frozen Cycle 8 baseline pass

## Key Resources
- `C:\Users\kevin\Desktop\freqtrade\research\cycle6_backtest.py` — backtest engine
- `C:\Users\kevin\Desktop\freqtrade\research\run_cycle6_experiment.py` — experiment runner
- `C:\Users\kevin\Desktop\freqtrade\production\generate_signals.py` — daily signal gen
- `C:\Users\kevin\Desktop\freqtrade\production\execute_trades.py` — trade execution
- `C:\Users\kevin\Desktop\freqtrade\research\CYCLE6_RESEARCH_RECOMMENDATION.md` — original Cycle 6 protocol
- `C:\Users\kevin\Desktop\freqtrade\research\CYCLE67_RESULTS.md` — Cycle 6 & 7 full results
- `C:\Users\kevin\Desktop\freqtrade\research\cycle6_results.json` — latest Cycle 6 result (106% CAGR, 92% DD)

## General Debugging Pattern: Decompose Aggregate Metrics

This session's audit technique generalizes beyond this project. When a combined metric seems wrong:

1. List every component feeding into the aggregate
2. Compute the metric per-component (not just combined)
3. Compare — the component with a disproportionate value is the likely root cause
4. Verify that each component is affected by the controls you think are in place

See `references/nav-stop-audit-findings.md` for the full worked example. The `scripts/p_sleeve_dominance.py` script demonstrates the technique programmatically.
