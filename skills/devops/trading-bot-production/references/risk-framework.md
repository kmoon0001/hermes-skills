# Risk Controls & Thresholds Reference

## Portfolio-Level

| Risk | Threshold | Action |
|------|-----------|--------|
| Portfolio vol > target | >15% annualized | Reduce position sizes proportionally |
| Combined drawdown | 0-15%: full exposure | 1.0x position size |
| | 15-25%: reduce | Linear 1.0→0.5x |
| | 25-30%: aggressive reduce | Linear 0.5→0.25x |
| | >30%: emergency | 0.10x, new entries blocked |
| Cross-asset correlation | >0.70: warning | Alert only |
| | >0.60: reduce crypto | Scale crypto allocation down |
| Rebalance drift | >5% from target | Signal rebalance needed |

## Position-Level (Crypto)

| Risk | Threshold | Action |
|------|-----------|--------|
| Single position | >25% of portfolio | Reduce to 25% |
| Single position | >40% of portfolio | CRITICAL alert |
| Stoploss | -6% from entry | Force exit |
| Max positions | 5 | No new entries if at limit |
| Drawdown circuit breaker | >25% DD | Block all new entries |

## Position-Level (Stocks)

| Risk | Threshold | Action |
|------|-----------|--------|
| Concentration | >40% per ticker | Warning alert |
| | >50% per ticker | Critical alert |
| Signal exit | Close < SMA210 | Exit to cash |

## Data Freshness

| Data | Warning | Critical |
|------|---------|----------|
| Signals.json | >36h old | Pipeline likely stalled |
| Market data (feather) | >48h old | Data download may have failed |
| Stock snapshot | >10 days old | Weekly script may have stalled |
| Watchdog heartbeat | >2h old | Watchdog may be down |

## System

| Check | Threshold | Action |
|-------|-----------|--------|
| Disk free space | <10GB: warning | Alert |
| | <5GB: critical | Block new trades |
| Bot API ping | No response | Critical — attempt auto-restart |
| Pipeline status | PARTIAL | Warning — some steps failed |
| | FAIL | Critical — all steps failed |

## Academic References

- Almgren, Thum, Hauptmann, Li (2005) — "Direct Estimation of Equity Market Impact"
- Faber (2007) — "A Quantitative Approach to Tactical Asset Allocation" (SMA10-month crossover)
- Markowitz (1952) — "Portfolio Selection" (Modern Portfolio Theory)
- Moskowitz, Ooi, Pedersen (2012) — "Time Series Momentum" (TS MOM)
- Qian (2005) — "Risk Parity Portfolios" (PanAgora, inverse volatility weighting)
