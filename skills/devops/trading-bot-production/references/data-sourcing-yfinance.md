# Expanded Crypto Data — yfinance for Pre-2021 History

Date: 2026-07-23
Problem: Exchange APIs limit historical data. OKX goes back to 2022-06. Binance
is geo-blocked from US IPs. The experiment runner needs data back to 2017 for
proper multi-cycle backtesting.

## Solution: yfinance

yfinance provides free BTC-USD and ETH-USD daily data back to 2017 (BTC) and
2017-11 (ETH). USD ≈ USDT for backtest purposes — the prices are effectively
identical at daily resolution.

```python
import yfinance as yf
import pandas as pd
from pathlib import Path

for symbol in ['BTC-USD', 'ETH-USD']:
    ticker = yf.Ticker(symbol)
    df = ticker.history(start='2017-01-01', end='2026-07-22', interval='1d')
    if not df.empty:
        pair_name = symbol.replace('-', '/')
        out_path = Path(f'user_data/data/okx/{pair_name.replace("/", "_")}-1d.feather')
        df_out = pd.DataFrame({
            'date': df.index,
            'open': df['Open'],
            'high': df['High'],
            'low': df['Low'],
            'close': df['Close'],
            'volume': df['Volume'],
        })
        df_out.to_feather(str(out_path))
```

## Critical: Back Up Existing Data

BEFORE overwriting exchange data files, back up the originals:

```python
import shutil
dst = Path('user_data/data/okx/BTC_USDT-1d.feather')
backup = Path(str(dst) + '.okx_backup')
if dst.exists() and not backup.exists():
    shutil.copy2(dst, backup)
```

The `.okx_backup` suffix makes it clear these are original exchange data,
not yfinance data. This is important for reproducibility — if someone
questions the numbers, they can restore the original data and re-run.

## Coverage

- BTC-USD: 2017-01-01 → present (~3,500 bars, 9.5 years)
- ETH-USD: 2017-11-09 → present (~3,200 bars, 8.7 years)
- Other pairs (SOL, XRP, ADA): Only available from 2021+ — these tokens
  either didn't exist or had very thin markets before 2020-2021.

The experiment runner handles this naturally: it checks if data exists for
each pair and skips those without data. Early years (2017-2020) will only
have BTC+ETH, while 2021+ will have all 5 pairs.

## Limitation

yfinance data should be treated as supplementary. The primary data source
is the exchange (OKX/Kraken/etc.). Pre-2021 yfinance data fills a gap that
exchange APIs can't cover, but the data quality may differ slightly from
exchange data (closing price conventions, volume calculations).
