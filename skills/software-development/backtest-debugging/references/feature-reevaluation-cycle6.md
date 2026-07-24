# Cycle 6 — Post-Fix Feature Re-Evaluation (July 2026)

## Context

The P-sleeve NAV contamination bug was discovered: `result["nav"]` (used by
feature backtest harness) included passive buy-and-hold P-sleeve that inflated
NAV during bull markets and dampened active-strategy drawdowns. The experiment
runner uses `result["sleeve_b"] / SLEEVE_WEIGHT` (B-only, normalized). After
fixing the harness, all feature decisions had to be re-evaluated.

## Old vs New Results (2021-2024, B-only baseline)

| Feature | Old CAGR | Old ΔCAGR | New CAGR | New ΔCAGR | Decision Change |
|---------|:--------:|:---------:|:--------:|:---------:|:--------------:|
| baseline | 4.01% | — | **17.81%** | — | — |
| correlation_sizing | 3.68% | -0.34pp | 16.53% | **-1.28pp** | ACCEPT → **REJECT** |
| mtf_confirmation | 2.97% | -1.03pp | 15.55% | **-2.26pp** | REJECT → revisit → **REJECT** |
| regime_vol_target | 4.05% | +0.04pp | 18.06% | +0.24pp | REJECT (stable) |

## Feature-by-Feature Analysis

### Correlation Sizing — ACCEPTED → REJECTED

**Old:** -0.34% CAGR, +0.03 Sharpe, -2.2pp DD. Accepted as marginal improvement.
**New:** -1.28% CAGR, +0.02 Sharpe, -2.3pp DD. Cost 4x larger than thought.
**Verdict:** The DD reduction (2.3pp) doesn't justify the CAGR cost (1.28pp).
Previously accepted because the contaminated baseline showed a tiny CAGR, making
the -0.34% look like noise. The real baseline is 17.81%, so -1.28% is material.

### MTF Confirmation — REJECTED → Revisit → REJECTED

**Old:** -1.03% CAGR, modest Sharpe gain. Rejected.
**New:** -2.26% CAGR, +0.13 Sharpe, **-8pp DD**. Flagged for revisit — the
risk/reward tradeoff is real.

**Expanding window follow-up** (7 windows, B vs MTF):

| Window | B DD | MTF DD | ΔDD |
|--------|:----:|:------:|:---:|
| W1 1yr | -9.4% | -9.9% | -0.5pp |
| W2 1.5 | -12.1% | -13.6% | -1.5pp |
| W3 2yr | -23.8% | -16.9% | +6.9pp |
| W4 2.5 | -24.3% | -17.1% | +7.3pp |
| W5 3yr | -25.0% | -17.1% | +8.0pp |

The entire -8pp DD reduction comes from the 2022 bear market entering the window
at W3. In bull-only windows (W1-W2), MTF provides ZERO DD benefit while
destroying 12-22% CAGR. **Final verdict: REJECTED — DD reduction is
regime-dependent, not structural.**

### Regime Vol Target — REJECTED (stable)

**Old:** +0.04% CAGR, within noise. Rejected.
**New:** +0.24% CAGR. Still within ±0.3% noise band.
**Verdict:** No change. Noise-level effect across both engines.

## Cycle 9 — Risk Parity (2021-2024)

After extending Cycle 9 from 2021-2023 to 2021-2024:

| Weighting | CAGR | Sharpe | MaxDD |
|-----------|:----:|:------:|:-----:|
| Equal-weight | **+17.81%** | **1.036** | **-25.0%** |
| Risk parity | +14.51% | 0.778 | -34.3% |
| Δ | -3.30pp | -0.258 | +9.3pp |

**Verdict: Risk parity REJECTED.** Equal-weight with 40% concentration cap
beats inverse-vol risk parity on every metric. Consistent with Pitfall 15
(risk parity underperforms when high-vol = high-Sharpe).

## All Overlays — Consistent Negative

| Overlay | Effect | Status |
|---------|--------|--------|
| Funding fade (two-sided) | -4.81pp CAGR | REJECTED |
| OI divergence | -3.47pp CAGR | REJECTED |
| Multi-signal fade | -6.80pp CAGR | REJECTED |
| Correlation sizing | -1.28pp CAGR | REJECTED |
| MTF confirmation | -2.26pp CAGR | REJECTED |
| Regime vol target | +0.24pp (noise) | REJECTED |

**Bottom line:** B-only baseline (TS MOM trend + Parkinson vol, vt=0.30,
equal-weight, 40% cap) is the proven edge. Every overlay tested in Cycles 5-9
has destroyed CAGR without providing structural risk reduction.
