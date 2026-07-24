# Cycle 8 Research — Detailed Results

## Background

Cycle 8 tested two multi-strategy additions to the Cycle 6 TS MOM baseline (CAGR +7.0%, Sharpe 0.39, DD -34.6%). Both tested on 2024 OOS data only, covering BTC/ETH/SOL/XRP/ADA at 0.20% cost.

## Strategy 1: Statistical Range Recovery (SRR)

**File:** `research/cycle8_srr.py`

Mean-reversion sleeve designed to profit when TS MOM is in cash.

### Entry Conditions (ALL must fire)

1. **Price in bottom 5th %ile** of 60d range (deep oversold)
2. **Range width ≥ 15%** (wide enough to trade meaningfully)
3. **Parkinson 21d vol < 90th %ile** of trailing 252d (no extreme vol regime)
4. **TS MOM trend is bearish** (trend_votes < 2 of 3 SMAs) — so it only acts when TS MOM is out

### Exit Conditions (first to trigger)

- 25th %ile breach (price recovers into normal range)
- +8% take-profit
- 30-day max hold
- 95th %ile vol spike (vol explosion)
- -15% stop-loss

### Portfolio Structure

20% sleeve per asset (SRR), 80% TS MOM (B-only). Combined = equal-weighted average of the two sleeves.

### Results (2024 OOS)

| Sleeve | CAGR | Sharpe | Max DD | Avg Trade Return |
|--------|:----:|:------:|:------:|:----------------:|
| TS MOM (B-only, standalone) | +6.0% | 0.355 | -22.9% | — |
| SRR sleeve (standalone) | +0.0% | 0.000 | -1.5% | +2.7% |
| **Combined (80/20)** | **+3.07%** | **0.351** | **-12.4%** | — |

### Why It Failed

**Only 3 trades in all of 2024** across all 5 assets:
- BTC/ADA/XRP on July 5, all exited July 7 at 25th %ile with gains of +1.9%–+3.5%
- Every other day the SRR sleeve was in cash

The problem: the conditions are too strict. Price at 5th %ile AND wide range AND normal vol AND existing trend off — this intersection barely ever fires on daily data for large-cap crypto that has tight bid-ask spreads and continuous institutional flow.

**Consequence:** 20% of capital sat in cash 99% of the time. This mechanically halves CAGR and max DD equally, leaving Sharpe unchanged. The combined portfolio (3.07%/0.35) is indistinguishable from running TS MOM with a fixed 20% cash reserve.

**Verdict:** Signal too sparse. The strategy needed 5-10 trades/year per asset to overcome the cash drag of its own sleeve. It delivered 0.6 trades/asset/year.

## Strategy 2: Portfolio-Level Volatility Targeting (PVT)

**File:** `research/cycle8_portfolio_vol.py`

Adds a uniform portfolio-wide vol scalar on top of per-asset TS MOM signals.

### Mechanism

1. Compute each asset's daily log return from its sleeve NAV
2. Equal-weight portfolio daily return = mean of 5 asset returns
3. Rolling 21d annualized std of portfolio returns → portfolio_vol
4. portfolio_scale = min(1.0, target / portfolio_vol)
5. Multiply ALL target positions by this scalar

### Results (2024 OOS)

| Variant | CAGR | Sharpe | Max DD | Corr w/ Baseline | Scale Mean | Scale Min |
|---------|:----:|:------:|:------:|:-----------------:|:----------:|:---------:|
| Baseline (no PVT) | +4.80% | 0.324 | -23.9% | — | — | — |
| PVT vt=0.20 | +1.55% | 0.111 | -23.4% | 0.997 | 0.979 | 0.773 |
| PVT vt=0.25 | +4.76% | 0.322 | -23.9% | 1.000 | 0.9997 | 0.954 |
| PVT vt=0.30 | +4.80% | 0.324 | -23.9% | 1.000 | 1.000 | 1.000 |

### Why It Failed

**Portfolio vol never got high enough to matter.** The 21d rolling portfolio vol stayed well below 0.25 annualized for nearly the entire period. At vt=0.30 (matching per-asset vol target), the scalar was 1.0 every single day — completely inert.

At vt=0.20, the scalar DID engage (mean 0.979, min 0.773 during vol spikes), but the result was catastrophic: CAGR collapsed from +4.80% → +1.55% while max DD barely budged (23.9% → 23.4%). The Sharpe more than halved (0.324 → 0.111).

The root cause: per-asset vol scaling (Parkinson 21d, vt=0.30) already does the job. By the time individual asset positions are scaled to target vol, the portfolio aggregate is already bounded well below any meaningful threshold. Adding a second compression layer on top either does nothing (vt≥0.25) or destroys return without improving risk (vt=0.20).

**Gates for all PVT variants: FAILED.** None beats baseline Sharpe. Correlation with baseline ≈ 1.0 — the scalar adds no independent variation.

## Combined Comparison vs Cycle 6 Baseline

| Metric | Cycle 6 (2021-2024) | Cycle 8 SRR Combined (80/20) | Cycle 8 PVT vt=0.20 (worst) | Cycle 8 PVT vt=0.25 (best) |
|--------|:-------------------:|:----------------------------:|:---------------------------:|:--------------------------:|
| **CAGR** | **+7.0%** | +3.07% | +1.55% | +4.76% |
| **Sharpe** | **0.39** | 0.351 | 0.111 | 0.322 |
| **Max DD** | -34.6% | **-12.4%** | -23.4% | -23.9% |
| **Note** | Best overall | Pyrrhic — DD cut by sitting in cash | Return destroyed, risk same | Inert — scalar never engaged |

## Bootstrap Uncertainty (Baseline, 2024 only)

- CAGR 95% CI: [-27.0%, +63.9%]
- Sharpe 95% CI: [-2.45, +3.00]
- Only 1 year of OOS data → extremely wide confidence intervals

These CIs are a reminder that 1-year OOS on crypto is barely informative. Neither strategy can be confidently rejected on statistical grounds — but the mechanism of failure (SRR: too few trades; PVT: redundant) is structural, not statistical.

## Lessons for Future Multi-Strategy Research

1. **Signal density gate first.** If a strategy triggers < 5 trades/year per asset with ≤ 20% sleeve, don't bother testing — the cash drag guarantee outweighs any possible benefit. Compute: `trades_per_year * avg_trade_return * sleeve_pct`. If this is < baseline_CAGR * sleeve_pct, the strategy is a net loser by construction.

2. **Portfolio-level vol targeting is redundant when per-asset vol scaling already exists.** Check the 95th %ile of 21d rolling portfolio vol at baseline. If below (target - margin), the second layer cannot engage.

3. **Only test on 1-year OOS for quick pass/fail, but beware the uncertainty.** A strategy that fails structurally (SRR: no trades) is reliable. A strategy that fails statistically (PVT vt=0.20: bad 2024) might work in a different year with higher vol. Use mechanism failure to reject, not statistical failure.

4. **The Cycle 6 baseline is hard to beat on risk-adjusted terms.** Two independent Cycle 8 attempts failed to improve Sharpe. This doesn't mean no strategy can beat it — but it means the low-hanging fruit is gone. Future research needs genuinely different regimes (cash during crashes, not cash during chop).
