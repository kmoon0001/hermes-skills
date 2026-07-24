# Evidence-based crypto strategy research

Use this note when a trading-bot request asks for the “best,” “most successful,” or market-informed strategy. It is a source bank and reasoning checklist, not a recommendation of future returns.

## Authoritative source hierarchy

1. Official bot documentation for executable behavior, assumptions, and validation tools.
2. Peer-reviewed finance research and established working-paper repositories (NBER/SSRN from identifiable authors).
3. Exchange-native public market data for the configured instruments.
4. Reputable secondary synthesis only to locate primary sources.

Do not rank strategies using influencer posts, strategy stores, anonymous GitHub profitability claims, or a single optimized backtest.

## Key evidence

### Crypto momentum as a factor

Liu, Tsyvinski, and Wu, “Common Risk Factors in Cryptocurrency” (NBER Working Paper 25882; later Journal of Finance 77(2), 2022) find that cryptocurrency market, size, and momentum factors capture cross-sectional expected returns in their 2014–2018 sample. One- through four-week momentum long-short portfolios were statistically significant in the study.

Interpretation limits:

- This is cross-sectional factor evidence, not proof that a particular single-asset EMA/RSI rule works.
- The study period, coin universe, long-short construction, rebalancing, and transaction-cost assumptions differ from a long-only spot bot.
- Use it to justify testing a parsimonious momentum/trend hypothesis—not to promise profit.

Primary sources:

- NBER paper: https://www.nber.org/papers/w25882
- Journal of Finance DOI: https://doi.org/10.1111/jofi.13119

### Backtest overfitting

Bailey, Borwein, López de Prado, and Zhu, “The Probability of Backtest Overfitting,” Journal of Computational Finance (2015), explains why choosing the apparent winner from many trials creates false discoveries and why ordinary holdout methods can be unreliable in investment backtests.

Practical implication: freeze a small hypothesis set before testing, record every variant, use regime-separated holdouts/walk-forward tests, and distrust unusually smooth or spectacular results.

Source: https://ssrn.com/abstract=2326253

### Freqtrade validation requirements

Official Freqtrade documentation states that:

- Backtesting requires historical data and includes exchange fees.
- Dynamic pairlists can impair reproducibility; static lists are preferred for reproducible tests.
- Higher-timeframe tests should use detail candles when available to reduce intrabar assumptions.
- Only forward dry-run can confirm whether backtest behavior carries into dry/live operation.
- `lookahead-analysis` detects signals or indicators that improperly use future candles.
- Protections such as `CooldownPeriod`, `StoplossGuard`, `MaxDrawdown`, and `LowProfitPairs` can bound repeated losses and drawdown.

Sources:

- https://www.freqtrade.io/en/stable/backtesting/
- https://www.freqtrade.io/en/stable/lookahead-analysis/
- https://www.freqtrade.io/en/stable/recursive-analysis/
- https://www.freqtrade.io/en/stable/plugins/

## Market-regime analysis checklist

Calculate from the configured exchange’s public data and record the UTC timestamp, timeframe, and available lookback:

- Returns over several non-overlapping horizons.
- Price relative to medium/long moving averages and moving-average slope.
- Trend strength (for example ADX), but do not make it the sole signal.
- Realized or ATR-based volatility as a percentage of price.
- Volume/liquidity and spread; reject illiquid instruments.
- Cross-asset breadth: how many configured pairs share the same trend regime.
- Current drawdown from a recent high.

A positive current regime may permit entries; it does not validate a strategy. A limited exchange OHLCV window is suitable for current-regime diagnostics, not robust historical inference.

## Conservative candidate architecture

For long-only spot paper trading:

- Higher timeframe (for example 1h–4h) to reduce noise and turnover.
- Long-term trend gate (price and faster EMA above slower EMA, with positive slope).
- Momentum recovery/confirmation rather than chasing extremely overbought readings.
- Minimum volume/liquidity and maximum spread filters.
- Volatility-aware stop or conservative fixed stop supported by sensitivity tests.
- Small fixed stake, low maximum concurrent trades, no leverage.
- Cooldown, stop-loss guard, and portfolio drawdown lock.

Keep the model simple. Each extra indicator creates another degree of freedom and increases overfitting risk.

## Minimum evidence before strategy handoff

- Exact strategy file loads as `OK`.
- Config remains `dry_run: true`, spot, localhost-only, and starts stopped.
- Backtest includes realistic fees and reports total return, max drawdown, Sharpe/Sortino where meaningful, exposure, trade count, and per-pair contribution.
- Results are compared with buy-and-hold and a simple baseline.
- Results are stable across assets, time slices, and reasonable parameter perturbations.
- Lookahead analysis reports no bias for exercised signals.
- Recursive analysis does not reveal unstable startup calculations.
- Forward dry-run is required before any live discussion.

If the data is too short or there are too few trades, label the strategy **unvalidated** and continue paper-forward testing. Do not optimize around the deficiency.
