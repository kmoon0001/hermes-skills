# Crypto Strategy Robustness Protocol

Use this reference when the task shifts from describing the live regime to evaluating whether a systematic crypto rule is robust. It applies especially to short samples, correlated major-coin universes, and intraday execution.

## Research posture

- Treat one year of five major coins as pipeline validation and hypothesis screening, not proof of a durable anomaly.
- Thousands of hourly bars are not thousands of independent observations. Aggregate P&L to daily returns for primary inference and resample whole cross-asset day vectors with dependent-data methods.
- Preserve an immutable ledger of every tried lookback, exit, filter, cost model, universe, and abandoned idea. Multiple-testing corrections are invalid if the trial count omits informal experiments.
- Prefer a small, fixed family composite over the best isolated parameter cell. Equal-weighting fixed variants reduces winner selection.
- A sealed holdout is opened once. Failure is recorded; it is not converted into another tuning interval.

## Literature-grounded priors

### Trend and momentum

- Time-series trend is the strongest prior, but general futures and daily crypto evidence does not directly validate hourly rules.
- Cross-sectional crypto momentum evidence is mixed. Five coins are too few for a diversified factor claim; at most test a long-only relative-strength allocation against an equal-weight benchmark.
- Separate directional alpha from volatility management. Compare four cells: always-long unscaled, always-long scaled, signal unscaled, signal scaled.

### Reversal

- Broad daily reversal evidence is concentrated in illiquid cryptoassets; large liquid coins may instead show momentum.
- Give unconditional mean reversion a smaller trial budget. Test only a simple, standardized post-shock reversal with realistic taker costs and latency.

### Regimes

- Regime dependence is economically plausible, but a latent HMM or Markov-switching model fitted on one year adds excessive degrees of freedom.
- Prefer a causal observable state, e.g. BTC above a rising 168-hour EMA for risk-on and trailing 168-hour realized volatility above an expanding past-only percentile for high risk.
- If a latent model is requested, fit it expanding-window only, use filtered rather than smoothed probabilities, and count every state/feature choice as another trial.

## Example fixed hypothesis families

Use completed hourly bars and fill no earlier than the next five-minute open.

1. **Time-series momentum:** long/cash on trailing return over 24, 72, 168, and 336 hours; six-hour rebalance; equal-weight family composite.
2. **Trend filter:** close above EMA and EMA rising over 24 hours; EMA lengths 72, 168, and 336 hours.
3. **Breakout:** close above prior completed-bar high over 24, 72, or 168 hours; linked exit below prior low over 12, 36, or 84 hours.
4. **Trend pullback:** positive 168-hour EMA regime; pullback `(close - EMA24)/ATR24` crossing -1 or -2; exit at zero, trend failure, or 24 hours.
5. **Post-shock reversal:** `r6 / (sigma_hourly72 * sqrt(6))` below -1.5 or -2, with linked six- or 12-hour holding periods.
6. **Long-only relative strength:** daily rank five coins on 24-, 72-, and 168-hour return; hold top two only when positive; compare with exposure- and volatility-matched equal weight.
7. **Volatility ablation:** trailing realized-volatility windows 24, 168, and 720 hours; multiplier `min(1, 0.40/RV)`; no leverage.

These are examples of a deliberately small preregistered grid, not defaults to optimize further. A new filter creates a new hypothesis family and trial.

## Causal execution rules

- Signal on completed 1-hour bar `t`; earliest fill is next available 5-minute open.
- Do not fill at the same close used to create the signal.
- If both exit and stop levels fall inside one five-minute OHLC bar, assume adverse ordering or obtain finer data.
- A touched limit price is not proof of fill or queue priority.
- Use actual historical account/pair fee where available. Assume taker unless a reproducible limit-fill model exists.
- Stress actual fee plus 2.5, 5, and 10 bps one-way slippage. If fee history is unavailable, also show all-in 10, 20, and 30 bps one way.
- Keep one common cash account, explicit allocation across simultaneous signals, and no hidden capital reuse.
- Never forward-fill returns across exchange or data outages; stale data forces cash.

## Walk-forward design for one year

A useful small-sample design is:

- Reserve final 12 weeks as a sealed holdout.
- Use first 40 weeks for development.
- Six expanding folds: train 16/20/24/28/32/36 weeks, then validate on the next four weeks.
- Make every fold-level choice from training only.
- Purge training trades whose outcomes overlap validation by the maximum holding period.
- Keep panel dates together across coins to avoid leaking the common crypto factor.
- Prefer median validation-fold rank or a fixed family composite over maximum full-period Sharpe.

CSCV/PBO complements chronological validation but does not replace it.

## Metrics and inference

Primary inference should use net daily portfolio excess returns against an exposure- and volatility-matched benchmark.

Always report:

- cumulative return/CAGR, volatility, Sharpe, Sortino, Calmar;
- HAC/Newey-West uncertainty and block-bootstrap confidence intervals;
- maximum drawdown and duration, worst day/week, expected shortfall;
- turnover, exposure, round trips, holding time, hit rate, payoff ratio;
- contribution by coin, month, hour, and regime;
- gross P&L, fees, slippage, and net P&L separately;
- beta/correlation to equal-weight buy-and-hold and scaled always-long.

Use stationary or moving blocks of seven and 14 days as fixed sensitivities. Resample all coins jointly by date.

For search correction:

- Deflated Sharpe Ratio (DSR) using the complete trial ledger;
- Hansen SPA or White Reality Check on all net candidate returns versus the benchmark;
- Probability of Backtest Overfitting / CSCV as a development diagnostic;
- never treat a single naive `p < .05` result as sufficient after model search.

## Operational evidence floors

No trade count proves an edge; dependent observations and effect size matter more. Heuristic floors can still prevent absurd claims:

- development: at least 100 aggregate round trips, 20 per coin, activity in four of five coins;
- each four-week validation fold: at least 10 aggregate round trips, otherwise label underpowered;
- sealed 12-week holdout: at least 30 aggregate round trips and at least five in four of five coins;
- no one coin contributes more than 40% of net P&L;
- net positive in at least four of six validation folds and four of five coins.

Label these as operational heuristics, not universal significance thresholds. If unmet, extend history or reduce frequency rather than relax them.

## Mandatory falsification suite

1. Delay fills by one five-minute bar and then one hour.
2. Multiply fees/slippage across fixed stress cases.
3. Circularly shift signals within coin to create at least 1,000 placebo alignments.
4. Flip signal direction; if both signs appear profitable, suspect exposure, scaling, or accounting.
5. Decompose signal versus always-long, with and without volatility scaling.
6. Leave each coin out, especially BTC.
7. Report every month and walk-forward slice.
8. Require a parameter plateau: one adjacent lookback net-positive and net Sharpe no more than 0.50 below the candidate.
9. Use adverse intrabar ordering when OHLC sequencing is unknown.
10. Search stationary-bootstrap or simple AR/GARCH null paths with the full research process.
11. Shift the UTC rebalance anchor by fixed offsets.
12. Report results excluding the best day, week, and month as diagnostics.
13. Replicate the frozen rule on another exchange or older untouched period.
14. Truncate data at random timestamps and assert earlier signals are bit-identical to a full-data run.
15. Perturb execution latency and next-bar prices.

## Go/no-go rule

A strategy is only a provisional candidate when it has a preregistered rationale, broad walk-forward performance, realistic cost and latency survival, non-dominance by one coin/event, value beyond scaled always-long, acceptable multiple-test diagnostics, a passing sealed holdout, and independent temporal or cross-exchange replication.

Even a pass supports further validation, not a promise of future profitability.

## Primary references

- Time-series momentum: https://doi.org/10.1016/j.jfineco.2011.11.003
- Crypto risks/returns: https://doi.org/10.1093/rfs/hhaa113
- Crypto common risk factors: https://doi.org/10.1111/jofi.13119
- Crypto reversal/liquidity: https://doi.org/10.1016/j.irfa.2021.101908
- Volatility-managed portfolios: https://doi.org/10.1111/jofi.12513
- Out-of-sample volatility management: https://doi.org/10.1016/j.jfineco.2020.04.015
- Time-series momentum and volatility scaling: https://doi.org/10.1016/j.finmar.2016.05.003
- Regime changes: https://doi.org/10.1146/annurev-financial-110311-101808
- White Reality Check: https://www.ssc.wisc.edu/~bhansen/718/White2000.pdf
- Hansen SPA: https://www.jstor.org/stable/27638834
- PBO: https://ssrn.com/abstract=2326253
- Deflated Sharpe Ratio: https://doi.org/10.3905/jpm.2014.40.5.094
- Multiple testing in returns: https://academic.oup.com/rfs/article/29/1/5/1843824
