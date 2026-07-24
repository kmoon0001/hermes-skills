# Equity TS MOM — Parameter Sweep Results

Complete results from 40+ variants tested on 8 ETFs (SPY, QQQ, IWM, XLF, XLE, XLK, XLV, XLU) over 2000-2026.

## Baseline: sma_252_binary (WINNER)

| Metric | Value | vs SPY B&H |
|--------|-------|-----------|
| CAGR | +8.73% | +0.48pp |
| Sharpe | 0.622 | +0.211 |
| Vol | 13.45% | -5.85pp |
| Max DD | -27.5% | +27.7pp |
| Calmar | 0.317 | 2.1x better |

## All 7 Core Variants

| Variant | CAGR | Sharpe | DD | Calmar | vs Base |
|---------|:----:|:------:|:--:|:------:|:-------:|
| sma_252_binary | **+8.73%** | 0.622 | -27.5% | 0.317 | — |
| golden_cross vt=0.12 | +7.22% | **0.722** | -16.5% | **0.437** | -1.50pp |
| golden_cross vt=0.10 | +6.32% | **0.730** | **-14.3%** | **0.442** | -2.41pp |
| vote_100_200_300 vt=0.12 | +6.79% | 0.675 | -16.7% | 0.406 | -1.94pp |
| vote_100_200_300 vt=0.10 | +5.89% | 0.682 | -14.2% | 0.415 | -2.84pp |
| vote_50_100_200 vt=0.12 | +4.81% | 0.508 | -18.6% | 0.258 | -3.92pp |
| vote_50_100_200 vt=0.10 | +4.24% | 0.520 | -15.8% | 0.268 | -4.49pp |
| SPY B&H | +8.25% | 0.411 | -55.2% | 0.149 | — |

## Return Boosters (30 additional variants)

### Trend-Strength Weighting

Scales position by % above SMA252. All underperform binary.

| Variant | CAGR | Sharpe | DD | Calmar |
|---------|:----:|:------:|:--:|:------:|
| TS min=0.0 | 7.56% | 0.573 | -25.9% | 0.292 |
| TS min=0.15 | 7.76% | 0.582 | -24.0% | 0.323 |
| TS min=0.3 | 7.89% | 0.566 | -27.0% | 0.292 |

### Fast Re-entry (SMA200 enter / SMA252 exit)

| Variant | CAGR | Sharpe | DD | Calmar |
|---------|:----:|:------:|:--:|:------:|
| Fast re-entry | 7.94% | 0.594 | -25.5% | 0.311 |
| Dual momentum | 7.32% | 0.572 | -20.9% | 0.350 |
| SMA100 enter / 252 exit | 7.19% | 0.525 | -35.5% | 0.203 |

### Sector Momentum Overlays (weekly-rebalanced)

Applied on top of sma_252_binary baseline. Overlay weights based on trailing 6-month return rank.

| Variant | CAGR | Sharpe | DD | Calmar |
|---------|:----:|:------:|:--:|:------:|
| Narrow [0.9,1.1] + cap 0.25 | **+8.84%** | 0.468 | -29.4% | 0.301 |
| Narrow [0.9,1.1] | **+8.99%** | 0.458 | -29.8% | 0.302 |
| Wider [-15%,+15%] | **+9.12%** | 0.385 | -31.9% | 0.286 |

All sector momentum variants boost CAGR modestly (+0.1 to +0.4pp) but degrade Sharpe (0.62 → 0.39-0.47). The CAGR increase is real (weekly-rebalanced, no lookahead bias) but the risk-adjusted tradeoff is negative.

### Expanded Universe (+ TLT, GLD)

Adding TLT (long bonds) and GLD (gold) to the 8-ticker portfolio:

| Variant | CAGR | Sharpe | DD | Calmar |
|---------|:----:|:------:|:--:|:------:|
| vote_50_100_200 vt=0.10 + bonds | ~4.5% | ~0.45 | -12.4% | ~0.36 |
| sma_200_binary + bonds | ~5.0% | ~0.50 | -12.4% | ~0.35 |

Diversification reduces DD significantly but at high CAGR cost. The bond glidepath during 2008/2020 saved drawdown but the persistent low bond returns dragged CAGR below pure-equity strategies.

## Per-Ticker Breakdown (sma_252_binary)

| Ticker | CAGR | Sharpe | DD | Trend ON |
|--------|:----:|:------:|:--:|:--------:|
| XLK | +9.02% | 0.640 | -28.1% | 65% |
| QQQ | +8.22% | 0.605 | -23.7% | 66% |
| SPY | +5.88% | 0.468 | -22.8% | 68% |
| XLE | +4.44% | 0.295 | -40.9% | 61% |
| IWM | +3.85% | 0.283 | -28.3% | 63% |
| XLV | +2.92% | 0.210 | -40.4% | 65% |
| XLU | +2.71% | 0.189 | -33.7% | 66% |
| XLF | +2.62% | 0.178 | -40.6% | 63% |

XLK (tech) is the best single ticker — strong trending, high CAGR. XLF (financials) is the worst — destroyed by 2008 GFC, never fully recovered in trend terms.
