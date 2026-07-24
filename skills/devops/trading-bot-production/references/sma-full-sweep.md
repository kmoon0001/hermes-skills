# SMA Parameter Sweep — Full 26-Year History (2000-2026)

## Methodology

Ran the multi_asset_sma.py backtest (8 ETFs: SPY, QQQ, IWM, XLF, XLE, XLK, XLV, XLU)
across SMA lookbacks from 20 to 252 days, covering 26.5 years and 6,676 trading days.
Benchmark: SPY buy-and-hold over the same period.

## Results

| SMA | CAGR | Sharpe | Max DD | Trades/yr | Calmar vs SPY |
|:---:|:----:|:------:|:------:|:---------:|:-------------:|
| 20 | +1.6% | 0.20 | -43.5% | ~213 | 0.2x (worse!) |
| 50 | +3.9% | 0.39 | -32.3% | ~134 | 0.8x |
| 100 | +4.6% | 0.45 | -32.3% | ~99 | 1.0x |
| 210 | +7.2% | 0.62 | -21.5% | ~59 | 2.2x |
| **252** | **+8.8%** | **0.70** | **-27.5%** | **~52** | **2.1x** |
| SPY B&H | +8.3% | 0.51 | -55.2% | — | 1.0x |

## Key Finding

**SMA20 is the WORST performer over full history** despite looking best in the
2018-2023 bull market window (+12.8% CAGR, Sharpe 1.19). The short lookback gets
whipsawed to death during crash regimes:

- 2000-2002 dot-com: SMA20 generates false entries into declining trends
- 2008 financial crisis: repeated whipsaws at every dead-cat bounce
- 2020 COVID crash: short duration but sharp reversals

**SMA252 is the robust winner**: beats SPY on CAGR (+8.8% vs +8.3%) with HALF
the max drawdown (-27.5% vs -55.2%). Slightly higher drawdown than SMA210 (-27.5%
vs -21.5%) but significantly higher return (+8.8% vs +7.2%).

## Why the 2018-2023 Sweep Was Misleading

The original parameter sweep (AGENTS.md, 2018-2023 dev period) showed SMA20 as
optimal because:
1. 2018-2023 had no major crashes — a persistent bull market with one COVID dip
2. Short lookbacks catch trends faster in trending markets
3. The sweep didn't include the 2000-2002 or 2008 regimes

**Lesson:** Always backtest over at least one full market cycle (bull + bear +
crash) before committing to parameters. A 6-year bull market window is NOT
representative.

## Action Taken

Changed production config from SMA20 to SMA252 on 2026-07-22. Files updated:
- `stocks/paper_trade.py:38` — SMA_PERIOD = 252
- `stocks/paper_trade.py` docstring — updated rationale
- `run_portfolio.py:59` — default sma_period = 252
- `START-FREQTRADE-DRY-RUN.bat/.ps1` — display strings updated
- `AGENTS.md` and `README.md` — documentation updated
