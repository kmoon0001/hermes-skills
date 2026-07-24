# Complementary Strategy Research Methodology

## Source Session: Mean Reversion / Drawdown Recovery Research (2026-07-19)

This file documents the methodology used to research strategies that complement an existing TS MOM long-only crypto portfolio. Future sessions researching complementary strategies should follow this sequence.

---

## The Core Problem

A strategy has a blind spot — a specific market regime where it consistently loses money. The complementary strategy must:
1. Profit in that exact blind spot regime
2. Stay in cash during the regimes where the primary strategy already works
3. Be fundamentally different from already-failed approaches

---

## Step-by-Step Methodology

### 1. Understand the Primary Strategy's Exact Failure Mode

Load all cycle results from `research/` to build a complete picture of what's been tested:

- **CYCLE n_RESULT.md** files — which cycles passed/failed and why
- **CYCLE n_RESEARCH_RECOMMENDATION.md** — research rationale for each cycle
- **cycle n_expanding_window_results.json** — CAGR/Sharpe/DD per expanding window
- **CYCLE n +_RESEARCH_REPORT.md** — broader survey documents like CYCLE7_PLUS

Key questions to answer:
- Which expanding window(s) show negative CAGR?
- What market regime corresponded to that window? (Bull/bear/range/post-crash)
- What specific mechanism caused the loss? (SMA whipsaw, trend reversal, cash drag)
- What prior cycles tested related strategies and were closed? (Must not retest)

**Freqtrade-specific path pattern:** `research/CYCLE{n}_RESULT.md`, `research/cycle{n}_backtest.py`

### 2. Survey Academic Literature

Search for papers on the specific strategy class. The search pattern for each paper:

```
web_search("crypto <strategy type> daily <key terms> profitability")
```

For each relevant paper, extract:
- Full citation (authors, year, journal)
- Key quantitative finding (Sharpe, CAGR, win rate if given)
- Asset universe tested (large-cap vs all-crypto)
- Timeframe tested
- Whether the result held OOS (out-of-sample)
- The economic mechanism the paper identifies

Cross-reference each finding against your specific asset universe. A paper finding "reversal works in small-cap crypto" does NOT support reversal in BTC — this mismatch kills many proposed strategies quietly.

**Key papers for mean reversion / drawdown recovery:**
- Zaremba et al. (2021) — Short-term reversal is weak in large-cap crypto
- Quantpedia (2024) — MIN (buy lows) failed 2022-2024 OOS for BTC
- Jääskeläinen (2022) — BB mean reversion didn't beat B&H for daily BTC
- Padysak & Vojtko (2022) — MAX (buy highs) beats MIN (buy lows) OOS

### 3. Identify the Gap Precisely

Don't say "the strategy has a bear market problem." Instead, use expanding window results to identify the EXACT period:

```
Window 4 (2.5 years, ending 2023-H1): CAGR -2.7%
→ This is the post-FTX crash range-bound period (Jun 2022 - Jun 2023)
→ BTC traded $16k-$30k, TS MOM was in cash as SMAs declined
→ The market chopped sideways with 10-15% bounces — TS MOM missed all
```

The gap is: **range-bound oscillation after a crash**. The complementary strategy must profit from bounces in that regime.

### 4. Design Strategies with Specificity

For each proposed strategy, define ALL of these:

| Element | What to Write | Example |
|---------|--------------|---------|
| Name | Descriptive acronym | CRC (Crash Recovery Capture) |
| Rationale | Why should this work economically? | "Post-crash markets exhibit mean reversion due to forced liquidation exhaustion and dip-buying." |
| Entry rules | ALL conditions, use precise numbers | "Drawdown from 90d high >= 25% AND close > SMA(5) AND vol < 2x median AND TS MOM in cash" |
| Exit rules | FIRST to trigger | "Close >= entry x 1.15 OR 60d time stop OR close <= entry x 0.85 hard stop OR TS MOM re-enters" |
| Sizing | Sleeve % and caps | "Full 20% sleeve; combined 40% NAV cap across all assets" |
| When it profits | Which regime? | "Post-crash range-bound markets (TS MOM's worst regime)" |
| When it loses | Which regime? | "Crash continuation (stop-loss), strong trend (no signals)" |
| Est. trigger frequency | How many trades/year? | "3-8 entries/year across 5 assets" |
| Est. win rate | Rough % | "40-60%" |
| Est. annual return | Rough CAGR | "+5%" |

### 5. Write Falsifiable Hypotheses

Each strategy must have pre-registered pass/fail conditions:

```python
# Example falsifiable hypothesis block for a research report
hypothesis = {
    "positive_cagr_over_full_period": True,
    "positive_in_n_of_m_years": ">= 2 of 4",
    "max_trades_per_year": "<= 30 across all assets",
    "sharpe_gt_zero": True,
    "avg_trade_return_gt_2x_cost": True,
    "failure_condition": "If all 3 strategies have negative CAGR, close entire branch"
}
```

### 6. Build the Regime Analysis Matrix

Create a 4x3 table showing each strategy's expected behavior in each regime:

| Regime | TS MOM | CRC | RSI Bounce | SRR |
|--------|--------|-----|------------|-----|
| Strong bull (2021) | +30-60% | +2-5% | +5-10% | +1-3% |
| Range-bound (2022 H2) | -2 to -5% | +8-12% | 0% (cash) | +5-8% |
| Sustained bear (2022 H1) | -10% | -5 to +5% | 0% (cash) | +2 to -3% |
| Slow recovery (2023) | +5-10% | +3-8% | +3-5% | +3-5% |

This matrix ensures the complementary strategy covers the primary's blind spot.

### 7. Document Branch-Closing Conditions

If the evidence is strong enough, explicitly state what would close the entire research branch:

> "If none of these three strategies produce positive returns over 2021-2024, the combined evidence definitively closes the drawdown recovery branch for large-cap crypto at daily frequency. The market is efficiently trending even at extremes."

This prevents the same research question from being re-asked in a future cycle.

---

## Academic Sources Referenced in This Session

| Paper | Key Finding | Relevance |
|-------|-------------|-----------|
| Zaremba et al. (2021) *IRFA* | Last-day return predicts next day; reversal strong in small-cap, weak in large-cap | Explains why Cycle 2 BB mean reversion failed — wrong asset class |
| Quantpedia (2024) | MIN (buy 10d lows) failed 2022-2024 OOS; MAX (buy highs) worked | Buying lows has decayed post-2022 |
| Jääskeläinen (2022) LUT Thesis | BB mean reversion optimal params = 1000d SMA (effectively trend, not MR) | Standard BB doesn't work at daily for BTC |
| Padysak & Vojtko (2022) | MAX strategy beats MIN strategy OOS | Trend > mean reversion for BTC |
| Guo, Sang, Tu & Wang (2021) SMU | Cross-coin reversal exists at minute frequency, not daily | Reversal is intraday, not daily, for large-cap |

---

## Key Pitfalls (Specific to This Class of Work)

- Do NOT propose a strategy that fires in the same regime as the primary. Gate with `trend_votes < 2` or equivalent check.
- Do NOT retune a closed branch. If Cycle 2 already closed "1h BB mean reversion," don't propose "1h BB mean reversion with RSI filter."
- Do NOT claim academic support without specifying asset class. "Zaremba found reversal works" is wrong if the user's assets are large-cap and Zaremba's result is for small-cap.
- Do NOT propose frequent trading strategies (>50 trades/year). Frequent mean reversion in large-cap crypto is negative expectancy. Only rare, extreme-event strategies have a chance.
- Do NOT forget to cross-reference with the existing cycle results. A strategy that looks promising in isolation may already have been tested and closed in Cycles 1-7.
