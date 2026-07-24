# Complementary Strategy Candidates — TS MOM + Drawdown Recovery

**Date:** 2026-07-19
**Context:** Research subagent output for the Cycle 6 OKX spot TS MOM portfolio ($1,000 dry-run, 5 pairs, daily at 10am PT).

## Key Finding

The academic evidence that *continuous* mean reversion (RSI 30, BB lower band, funding fade) fails for large-cap crypto is overwhelming — Zaremba (2021), Jääskeläinen (2022), Quantpedia (2024), and internal Cycles 2 & 6 all converge. **But none tested rare, condition-gated drawdown recovery targeting the specific regime TS MOM fails.**

## The TS MOM Blind Spot

TS MOM (20/50/100 SMA vote + Parkinson vol scaling) is positive in 6/7 expanding windows. The sole negative window is W4 (2.5 years ending 2023-H1, CAGR -2.7%) — the **post-crash range-bound regime** after FTX (Nov 2022 → Jun 2023). During this period:
- TS MOM is mostly cash (SMAs above price)
- The market oscillates in a $16k-$30k range
- Multiple 10-15% bounces occur that TS MOM misses

## Strategy 1: Statistical Range Recovery (SRR) — Primary Recommendation

**Hypothesis:** Price at ≤5th percentile of 60d range predicts recovery to ≥25th percentile.

### Entry Rules (ALL must be true)
1. `(close - 60d_low) / (60d_high - 60d_low) ≤ 0.05` — 5th percentile of 60d range
2. Parkinson 21d vol < percentile-90 of trailing 252d history — no vol cascade
3. `(60d_high / 60d_low - 1) ≥ 0.15` — minimum range width for mean reversion room
4. `TS MOM trend_votes < 2` — only deploy when TS MOM is cash

### Exit Rules (FIRST triggers)
1. Close ≥ 25th percentile of 60d range
2. Close ≥ entry × 1.08
3. 30 calendar days elapsed
4. Parkinson 21d vol > 95th percentile (vol cascade)
5. Close ≤ entry × 0.85 (hard stop)

### Expected Performance
- **CAGR:** +2-5%
- **Trigger frequency:** 5-8/year across 5 assets
- **Win rate:** 45-55%
- **Best regime:** Range-bound chop (TS MOM's worst)
- **Worst regime:** Trending bear (vol cascade filter mostly keeps cash)

### Why SRR First
- Lowest parameter sensitivity (pure statistical threshold, not optimized indicator)
- Clearest complementarity (only triggers when TS MOM is cash)
- Directly falsifiable market efficiency hypothesis
- Easy to cross-validate across lookbacks (30d, 45d, 60d, 90d)

## Strategy 2: Crash Recovery Capture (CRC) — Secondary

**Hypothesis:** After a ≥25% drawdown from 90d high, buying stabilization captures the bounce.

### Entry Rules
1. `close / 90d_high - 1 ≤ -0.25` — 25%+ peak-to-trough decline
2. Close > SMA(5) — first stabilization signal
3. Parkinson 21d vol < 2× trailing 252d median vol — no falling knife
4. TS MOM trend_votes < 2 — only when TS MOM is cash

### Exit Rules
1. Close ≥ entry × 1.15 (15% bounce target)
2. 60 calendar days elapsed
3. Close ≤ entry × 0.85 (15% stop)
4. TS MOM re-entry (trend_votes ≥ 2)

### Expected Performance
- **CAGR:** +5%
- **Trigger frequency:** 3-8/year
- **Win rate:** 40-60%
- **Best regime:** Post-crash sideways
- **Worst regime:** Strong bull (blocked by rule 4 — TS MOM already active)

## Strategy 3: RSI Bounce — Exploratory

**Hypothesis:** RSI(14) < 25 + SMA200 upward filter captures dip-buying in healthy trends.

### Entry Rules
1. RSI(14) < 25 (more extreme than standard 30)
2. Close > SMA(200) — long-term uptrend still intact
3. Volume > 20d median volume (panic confirmation)
4. TS MOM trend_votes < 2

### Expected Performance
- **CAGR:** +2-6%
- **Key limitation:** SMA200 filter means this is cash during bear markets (2022) — it does NOT cover TS MOM's worst regime

## Failure Conditions (Pre-registered)

From the research report, the entire drawdown recovery branch is closed if:
1. All 3 strategies have negative standalone CAGR over 2021-2024
2. Combined TS MOM + recovery CAGR ≤ TS MOM standalone CAGR + 1pp
3. The best recovery strategy has Sharpe < 0.1

## Key Implementation Detail

All three strategies **require TS MOM cash status** (trend_votes < 2) as entry condition. This ensures:
- Zero overlap with TS MOM (never both active on the same asset at the same time)
- Pure complementarity (covers the regime TS MOM misses)
- Natural capital allocation (when TS MOM is fully invested, SRR/CRC are cash; when TS MOM is cash, SRR/CRC may deploy)

---

## 2024 OOS Test Results (Cycle 8)

**SRR was tested on 2024 OOS data** via `research/cycle8_srr.py`. Results:

| Metric | TS MOM alone | SRR sleeve | Combined |
|--------|-------------|------------|----------|
| CAGR | +6.00% | 0.00% | +3.07% |
| Sharpe | 0.355 | 0.000 | 0.351 |
| Max DD | 22.95% | 1.50% | 12.42% |
| Volatility | 16.43% | 3.31% | 8.60% |

**Trade log — only 3 triggers across all 5 assets in 2024:**
| Pair | Entry | Exit | Return | Reason |
|------|-------|------|--------|--------|
| BTC/USDT | 2024-07-05 ($57,050) | 2024-07-07 | +1.88% | 25th %ile reached |
| XRP/USDT | 2024-07-05 ($0.433) | 2024-07-07 | +3.50% | 25th %ile reached |
| ADA/USDT | 2024-07-05 ($0.362) | 2024-07-07 | +2.15% | 25th %ile reached |

**Verdict: NO-GO.** SRR works when it triggers (100% win rate, +1.9-3.5%), but triggers are too rare on daily data. The 20% cash sleeve mechanically halves CAGR from 6% to 3% while halving MaxDD from 23% to 12%. Sharpe is flat at 0.35 — the same risk-adjusted return as holding 20% cash permanently with no strategy complexity. **The SRR branch is closed for large-cap crypto at daily frequency.**
