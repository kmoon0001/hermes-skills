# TS MOM Drawdown Protection & Parameter Optimization

> Research-backed techniques for reducing max drawdown in time-series momentum (TS MOM) strategies applied to crypto spot portfolios.

## The Problem

TS MOM strategies (trend following via SMA vote systems) suffer from two structural drawdown drivers:

1. **Slow flip**: 20/50/100-day SMA lookbacks are slow to turn during prolonged downtrends — by the time all SMAs flip to "below price," portfolio NAV has already lost 50-90%.
2. **Concentration risk**: In a 5-symbol equal-weight crypto portfolio, one asset (SOL in 2021-2024) often drives ~73% of returns. Dropping the dominant asset collapses CAGR from 64% to 17%.

## Three Methods to Fix Momentum Crashes

From Hanauer & Windmueller (2019) *Enhanced Momentum Strategies* (SSRN 3437919):

| Method | Mechanism | Effect |
|--------|-----------|--------|
| Idiosyncratic momentum | Residualize returns, remove systematic exposure | Best risk-adjusted returns |
| Constant volatility-scaling | Position size inversely to realized vol | Sharpe doubles vs raw momentum |
| Dynamic scaling | Adjust size based on vol regime | Reduces skew/kurtosis, normalizes distribution |

For crypto TS MOM, constant volatility-scaling (approach 2) is most practical — we implement this via Parkinson HL volatility targeting.

## Drawdown-Based Risk Management

### Portfolio-Level DD Stop with Hysteresis

Rather than per-variant or per-symbol stops (which miss portfolio-level crashes), apply at the aggregate portfolio NAV level:

| Threshold | Action |
|-----------|--------|
| DD < 25% | Full exposure (dd_mult = 1.0) |
| DD 25-40% | Reduce exposure to 50% (dd_mult = 0.50) |
| DD > 40% | Exit all positions (dd_mult = 0.0) |
| Recovery < 10% | Restore full exposure (dd_mult = 1.0) |

**Key implementation detail**: The DD stop must be computed from actual combined portfolio NAV, not from target proxies. This requires a two-pass approach:
1. First pass: compute NAV without DD stop
2. Compute dd_mult from actual NAV drawdown
3. Second pass: re-run simulation with dd_mult applied

The target proxy approach (averaging per-symbol targets) does NOT work — targets stay high during crashes because SMAs are slow to flip, so the proxy shows no drawdown even as NAV crashes.

### Failed Approaches

- **Binary regime filter at 2x vol**: Never fires in crypto — vol spikes rarely exceed 2x trailing year median.
- **Regime filter at 1.5x with binary shutoff**: Makes DD worse — fires during profitable volatile trends, creating whipsaw losses.
- **Hysteresis regime filter at 1.3x/1.1x**: Marginal Sharpe improvement (+0.006) but no meaningful DD reduction (93.7% → 93.5%).
- **Target-proxy drawdown stop**: Based on average of per-symbol targets rather than actual NAV. Targets stay high during crashes, so the stop never fires.
- **Vol reduction alone (0.20 → 0.15)**: CAGR drops 1.5pp but DD barely moves (93.7% → 93.5%).

### What Actually Helps

- **Per-symbol concentration cap (40%)**: Forces diversification away from dominant asset. Sharpe improves from 0.68 → 0.75.
- **Equity-based position sizing**: Replace fixed stake per trade with fraction of total equity. Limits maximum per-position loss.
- **Vol target at 0.10-0.15**: Conservative approach that limits position size during high-vol periods.

## Parameter Optimization Protocol

### Proven Best Config (5-symbol crypto portfolio, 2021-2024)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| VOLATILITY_TARGET | 0.15 | Lower positions = lower DD |
| OI_DIVERGENCE_REDUCTION | 1.0 (disabled) | Net-negative at any threshold |
| MAX_CONCENTRATION | 0.40 | Per-symbol cap prevents SOL dominance |
| FUNDING_FADE_PERCENTILE | 0.80 | Marginal value, keep at default |
| Regime filter | Inactive | Code available for future tuning |
| Drawdown stop | Portfolio-level 25%/40% | Requires two-pass implementation |

## Production Pipeline Architecture

For daily TS MOM strategies, the research-to-production bridge:

```
research/cycle6_backtest.py  ←─ defines signal functions
        │
        ▼
production/generate_signals.py  ←─ imports research functions, fetches OKX 1d data
        │                             outputs signals.json
        ▼
production/execute_trades.py  ←─ reads signals.json, sizes positions from equity
        │
        ▼
Freqtrade dry-run or CCXT live  ←─ daily @ 10:00 PT via cron
```

**Critical rule**: Production signal generators MUST import research functions directly (e.g. `from research.cycle6_backtest import compute_trend_mom`), not duplicate formulas. Duplication introduces drift.

## Research Pipeline Import Hygiene

When the research package uses mixed import styles (`from research import xxx` alongside bare `from run_cycle5_experiment import yyy`):
- Ensure `research/__init__.py` exists
- Fix lazy imports inside main() to use the `research.` prefix consistently
- Run from project root with `sys.path.insert(0, '.')`

## Bootstrap Interpretation

For crypto TS MOM on 4 years of daily data (n ~1461):
- 95% CI is WIDE: CAGR [-25.9%, +489.7%], Sharpe [-0.30, +1.82]
- Zero is inside both intervals → not statistically significant at 95%
- Median is strong (+108% CAGR) but high variance
- Treat as promising but fragile

## References

- Hanauer & Windmueller (2019). "Enhanced Momentum Strategies." SSRN 3437919.
- Moskowitz, Ooi, & Pedersen (2012). "Time series momentum." JFE 104(2), 228-250.
- Quantpedia (2019). "Three Methods to Fix Momentum Crashes."
- Alpha Architect (2015). "Avoiding the Big Drawdown with Trend-Following."
