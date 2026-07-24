# Live Data Methodology for Crypto Regime Analysis

This note captures reusable source and calculation patterns. Endpoints are examples; always query them live and timestamp the response.

## Prices and global market state

### CoinGecko

- Live BTC/ETH price, market cap, 24h change, update time:
  `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_market_cap=true&include_24hr_change=true&include_last_updated_at=true`
- Global capitalization, volume, and dominance:
  `https://api.coingecko.com/api/v3/global`
- Top-100 breadth universe:
  `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=7d,30d,1y`

CoinGecko top-100 lists increasingly contain stablecoins, tokenized Treasury products, tokenized credit, gold tokens, and wrapped duplicates. Build and disclose an exclusion list before calling it “crypto breadth.” Report both sample size and number excluded.

## Daily candles and trend

Coinbase Exchange public candles work without authentication:

- `https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400`
- `https://api.exchange.coinbase.com/products/ETH-USD/candles?granularity=86400`
- `https://api.exchange.coinbase.com/products/ETH-BTC/candles?granularity=86400`

Responses are usually reverse chronological. Sort by timestamp ascending. Treat the latest UTC candle as incomplete and exclude it from returns, moving averages, and realized volatility.

For completed close `C_t`:

- N-day return: `(C_t / C_(t-N) - 1) * 100`
- SMA distance: `(C_t / SMA_N - 1) * 100`
- Daily log return: `ln(C_t / C_(t-1))`
- Annualized realized volatility: `stdev(log_returns) * sqrt(365) * 100`

When an exchange blocks by region, switch to another reputable exchange/API rather than turning the temporary restriction into a durable rule.

## Implied volatility

Deribit volatility-index endpoint:

`https://www.deribit.com/api/v2/public/get_volatility_index_data`

Parameters:

- `currency=BTC` or `ETH`
- `start_timestamp` and `end_timestamp` in Unix milliseconds
- `resolution=3600` for hourly OHLC

Return the latest close and a recent high/low range. DVOL is a forward-looking options index and should be compared, not conflated, with backward-looking realized volatility.

## ETF flows

Primary convenient tables:

- BTC: `https://farside.co.uk/btc/`
- ETH: `https://farside.co.uk/eth/`

Parse daily totals and calculate latest five-session and month-to-date sums. Parentheses represent negative values. The newest row may be incomplete: dashes or zeros can mean “not populated,” especially when another aggregator already reports provisional numbers. Explicitly disclose discrepancies.

## Macro sources

Prefer:

- Federal Reserve monetary-policy reports and FOMC releases
- BLS CPI release pages
- Federal Reserve H.15 rates
- CME FedWatch for market-implied probabilities
- Reuters for same-day synthesis and geopolitical context

Distinguish a reduction in hike odds from an easing cycle. Core inflation above target, rising oil, a stronger dollar, or higher short yields can offset a favorable CPI surprise.

## Example interpretation pattern

A recurring mixed regime can look like:

- BTC/ETH above 20d and 50d averages
- both below 100d and 200d averages
- strong 24h and 7d breadth
- fewer than half of screened assets positive over 30d
- moderate/falling DVOL
- one positive ETF day but negative rolling five-session flow

Label this “short-term relief rally inside an intermediate downtrend” or “transition/repair regime,” not “bull market confirmed.”

## Citation practice

Cite the actual API/page used, the retrieval date/time, and identify any calculations as your own. Raw API links are acceptable citations when paired with a short methodology statement. Prices are snapshots, not end-of-day facts.
