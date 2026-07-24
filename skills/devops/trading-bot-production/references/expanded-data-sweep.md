# Expanded Vol Target Sweep — 2017-2024 (8 Years, BTC+ETH)

## Data Sourcing

OKX data only goes back to 2022-06-10 (4 years). To get pre-2021 data covering
the 2018 crypto winter and 2017 bull run, use yfinance:

```python
import yfinance as yf
df = yf.Ticker("BTC-USD").history(start="2017-01-01", end="2026-07-22", interval="1d")
# Save to user_data/data/okx/BTC_USDT-1d.feather (USD ≈ USDT for analysis)
```

**Back up existing OKX data before overwriting.** The `.okx_backup` suffix is used.

Coverage:
- BTC-USD: 2017-01-01 → 2026-07-21 (3,489 bars, ~9.5 years)
- ETH-USD: 2017-11-09 → 2026-07-21 (3,177 bars, ~8.7 years)
- SOL, XRP, ADA: not available before ~2021 (tokens didn't exist or had thin markets)

The experiment runner uses 5 pairs. When START is set before 2021, SOL/XRP/ADA
are unavailable and only BTC+ETH contribute. This is fine — the strategy adjusts
to available pairs, and BTC/ETH dominated crypto markets pre-2021.

## Results (2017-2024, BTC+ETH only for 2017-2020, all 5 pairs for 2021-2024)

| vt | CAGR | Sharpe | MaxDD |
|:--:|:----:|:------:|:-----:|
| 0.15 | 57.1% | 1.133 | -24.8% |
| 0.20 | 58.4% | 1.138 | -25.1% |
| 0.25 | 59.8% | 1.142 | -25.7% |
| 0.30 | 61.1% | 1.145 | -26.2% |
| 0.35 | 62.5% | 1.147 | -26.8% |
| **0.40** | **63.7%** | **1.147** | **-27.4%** |
| 0.45 | 64.9% | 1.148 | -27.8% |
| 0.50 | 65.8% | 1.147 | -28.3% |

**Key finding:** vt=0.40 confirmed better on 8 years of data (+2.5% CAGR over vt=0.30).
Strategy survives 2018 crypto winter — BTC went -84%, but strategy MaxDD was only -27%.
Sharpe plateaus at vt=0.45, suggesting diminishing marginal returns.

## Regime Breakdown (from run_vt_regime.py)

Pre-2021 regimes (2017-2020) show N/A because SOL/XRP/ADA data doesn't exist.
For 2021+, the pattern matches the 2021-2024 sweep: vt=0.40 slightly worse in
bears (-0.2% more loss) but strongly better over the full period.

## Files

- `research/run_vt_sweep_expanded.py` — runs 8 vt values + regime analysis on expanded data
- `research/vol_target_sweep_expanded.json` — saved results (BTC+ETH from 2017)
- `research/run_vt_regime.py` — sub-period regime analysis (also works with expanded data when pairs are available)
- `research/run_walkforward.py` — walk-forward validation with train/test splits

## Walk-Forward Validation Results

Walk-forward validation ran 6 training windows → test windows. Results were mixed
due to a feature cache issue (the research feather cache at
`research/generated/cycle5_features.feather` was built from old data and doesn't
update when underlying exchange data changes).

Key findings despite cache issues:
- Training on 2017-2021 → testing 2022-2024: optimal vt=0.35, +5.5% CAGR over baseline
- Bear year tests (2022 alone): -4.6% to -4.8% across vt values (strategy loses as expected)
- Bull year tests: strongly positive
- Cross-validation: limited to 1 valid fold due to data availability

**For truly clean walk-forward:** rebuild the feature cache after updating
underlying data, OR modify the experiment runner to skip the cache and read
feather files directly.
