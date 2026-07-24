# Equity TS MOM — Parameter Sweep Results

**Date:** 2026-07-19  
**Repository:** `C:\Users\kevin\Desktop\freqtrade\stocks\`  
**Data:** Yahoo Finance daily OHLCV, 2000-01 to 2026-07  
**Universe:** SPY, QQQ, IWM, XLF, XLE, XLK, XLV, XLU  
**Cost model:** close-to-close returns, costs only on target changes, 10 bps per trade

## Top Variants (30 tested)

### Winner: sma_252_binary — Only variant that beats B&H on CAGR

| Metric | Strategy | SPY B&H | Diff |
|--------|----------|---------|------|
| CAGR | **+8.73%** | +8.25% | +0.48pp ✓ |
| Sharpe | **0.622** | 0.411 | +0.211 |
| Max DD | **-27.5%** | -55.2% | **nearly halved** |
| Calmar | **0.317** | 0.149 | 2.1× better |
| Corr vs SPY | 0.881 | — | — |

**Signal:** `close > SMA(252)` — binary, no vol scaling. Classic AQR 12-month lookback.

### Runner-up: golden_cross — Best risk-adjusted (Calmar 0.44)

| vt | CAGR | Sharpe | Max DD | Calmar |
|----|------|--------|--------|--------|
| 0.10 | +6.32% | 0.730 | -14.3% | **0.442** |
| 0.12 | +7.22% | 0.722 | -16.5% | 0.437 |

**Signal:** `SMA(50) > SMA(200) × vol_scale(vt)`

### Third: vote_100_200_300 — Balanced, lowest vol

| vt | CAGR | Sharpe | Max DD | Calmar |
|----|------|--------|--------|--------|
| 0.10 | +5.89% | 0.682 | -14.2% | 0.415 |
| 0.12 | +6.79% | 0.675 | -16.7% | 0.406 |

## How Each Equities Variant Maps to Crypto Parameters

| Equity Signal | Crypto Equivalent | Works? | Why Different |
|---|---|---|---|
| sma_252_binary | sma_20_50_100 vote | ✅ (CAGR winner) | 12mo lookback avoids whipsaw; crypto needs shorter windows because trends are faster |
| golden_cross (50/200) | Not tested in crypto | ✅ (best Calmar) | Slower cross captures regime shifts; crypto's SMA50/SMA100 regime filter was untested |
| vote_50_100_200 | vote_20_50_100 (crypto) | ⚠️ (CAGR +4.8%, weak vs B&H) | Same pattern shifted right by 30d — equities need longer lookbacks |
| 20/50/100 vote | Baseline crypto signal | ❌ (-16% CAGR equities) | Drastically fails — equity noise-to-signal much higher at short lookbacks |

## Key Finding: Equity Backtests Need a Different Cost Model

The `cycle5_backtest.simulate_sleeves()` charges daily cost on full notional. For crypto backtests (3-4 yr, 63% CAGR) this is manageable. For 26-year equity backtests it compounds to -99.9% NAV destruction.

**Fix:** Custom simulation with close-to-close returns and costs only on actual target changes (not every day).

```python
def simulate(closes, targets, cost=0.001):
    nav = 1.0; pos = 0.0; prev_t = 0.0
    for t in range(1, len(closes)):
        r = closes[t] / closes[t-1]
        ct = targets[t]
        nav *= (1.0 + (r - 1.0) * pos)
        if ct != prev_t:
            nav *= (1.0 - abs(ct - prev_t) * cost)
        pos = ct; prev_t = ct
    return nav
```

## Files

- `stocks/backtest.py` — main backtest (default: sma_252_binary)
- `stocks/parameter_sweep.py` — the 30-variant sweep runner
- `stocks/sweep_results.json` — full sweep output (all variants)
- `stocks/results.json` — top 7 variants
