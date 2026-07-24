---
name: crypto-market-regime-analysis
description: Assess live crypto regimes and evaluate systematic crypto strategies using causal backtests, walk-forward validation, multiple-testing controls, and conservative spot risk filters. Use for current BTC/ETH outlooks, regime classification, or crypto strategy robustness research.
version: 1.10.0
author: Hermes Agent
tags: [crypto, bitcoin, ethereum, market-regime, breadth, volatility, etf-flows, macro, research]
platforms: [linux, macos, windows]
---

# Crypto Market Regime Analysis

## Research Evidence Base

This skill's `references/academic-evidence-base.md` contains condensed findings from 15+ academic papers on crypto trading strategies (Liu-Tsyvinski-Wu 2022 *Journal of Finance*, Schmeling-Schrimpf-Todorov 2026 *Management Science*, Easley-O'Hara 2024, and others). Load that file when you need to ground a strategy recommendation or regime call in documented academic edge rather than guesswork. Key takeaways:

- **What works**: crypto carry (Sharpe ~3–6), volatility-managed trend following (~1.5–2.5), large-cap weekly momentum (~0.7–1.5), small-cap intangible value (~0.8–1.2 backtest), microstructure features (~0.6–1.0 after costs)
- **What doesn't**: classical 3-12 month monthly momentum, simple breakout without vol management, mean reversion (fails OOS), pure market making (adverse selection risk)
- Recommend combining: intermediate-frequency trend signal + volatility scaling + market-cap-aware filtering

Use this reference when evaluating a proposed strategy or making regime-based recommendations — cite the evidence rather than relying on backtest-only claims.

---

Use this skill in three related modes:

1. **Live regime analysis:** classify current conditions across several horizons, cite timestamped live data, explain conflicting signals, and recommend filters rather than directional certainty.
2. **Historical strategy robustness:** evaluate whether a crypto trading rule survives causal execution, walk-forward testing, realistic costs, multiple-testing correction, and falsification. Do not confuse a backtest winner with a regime forecast.
3. **Complementary strategy research:** research and design strategies to pair with an existing portfolio. Use when the current strategy has a known weakness (e.g., loses money in range-bound markets) and you need a strategy that covers that blind spot. Follow the workflow in section 8 below.

For historical strategy work, load `references/strategy-robustness-protocol.md` before designing grids or judging results. It contains fixed-family examples, holdout design, execution rules, inference methods, trade-count heuristics, and falsification tests.

For multi-asset daily or weekly sleeve simulations, also load `references/portfolio-backtest-accounting.md`. It defines causal observation/decision/execution clocks, drift-aware event accounting, matched four-cell attribution, transaction-cost invariants, and deterministic tests that prevent hidden daily rebalancing.

When a strategy search has accumulated several failed families or is approaching a final development cycle, load `references/research-cycle-provenance-and-stop-rules.md`. It defines the one-cycle budget, protocol/engine/result commit order, exact estimand freezing, staged immediate-stop gates, final-liquidation accounting, reliable experiment logging, machine-readable provenance, safe GitHub publication, and end-of-cycle verification.

For TS MOM parameter optimization and drawdown protection, load `references/tsmom-drawdown-protection.md`. It covers vol target sweeps, OI divergence tuning, concentration caps, three academic methods for fixing momentum crashes, the portfolio-level DD stop pattern, and a proven best config reference.

When researching strategies to complement an existing portfolio, load `references/complementary-strategy-research.md`. It contains the step-by-step methodology for gap analysis, academic literature surveying, falsifiable hypothesis design, and regime analysis — as used in the mean reversion/drawdown recovery research session.

When ordered research tasks require independent approval before commit, also load `references/immutable-research-task-review.md`. It defines explicit-file staging, HEAD/tree/staged-patch identities, dual read-only review, approval invalidation after any change, clean-test execution, and the final identity check before commit.

Before admitting historical funding, open interest, premium, liquidation, or basis data—or building an immutable development-only derivatives cache—load `references/derivatives-archive-causal-audit.md`. It defines the six-clock point-in-time model, exchange-archive inventory procedure, checksum/revision limits, Binance USD-M schema mappings and source-verified numeric adapters, atomic cache/manifest/quality artifact design, decision-time cache rules, duplicate-conflict and missingness handling, true-basis requirements, liquidation rejection tests, and executable data gates.

## Core Principle

A one-day rally is not a regime change. Separate:

1. **Short-term impulse:** 1–7 days
2. **Intermediate trend:** 30–100 days
3. **Primary trend:** 200-day / weekly structure
4. **Participation:** breadth and BTC/ETH relative strength
5. **Risk conditions:** realized and implied volatility
6. **Flow/liquidity:** ETF flows, stablecoin/liquidity conditions, macro rates

Describe disagreement among these layers explicitly. Useful labels include:

- confirmed risk-on trend
- short-term relief rally inside an intermediate downtrend
- transition / repair regime
- broad risk-off trend
- high-volatility capitulation

Do not convert a mixed regime into a confident bull/bear forecast.

## Source Hierarchy

Prefer primary or machine-readable sources:

1. Exchange/API data for prices and candles
2. Derivatives venue data for implied volatility
3. Official ETF-flow tables
4. Official central-bank/statistical releases
5. Reuters or similarly strong reporting for live catalyst context
6. Crypto publications for market color, checked against primary data

Useful endpoints and calculation details are in `references/live-data-methodology.md`.

A reusable deterministic probe is in `scripts/crypto_regime_probe.py`.

## Workflow

### 1. Timestamp the snapshot

Record UTC time before collecting data. Crypto trades continuously, so every price, breadth, and volatility statement must be tied to a snapshot time.

### 2. Measure BTC, ETH, and ETH/BTC trend

For BTC-USD, ETH-USD, and ETH-BTC:

- live price and 24-hour change
- completed-candle returns over 7, 30, 90, and 180 days
- distance from 20-, 50-, 100-, and 200-day simple moving averages
- optionally weekly-close structure

Use completed UTC candles for indicators; do not mix an incomplete current-day candle into moving averages. Explain if live price and last completed close differ.

Interpretation pattern:

- Above 20/50d but below 100/200d = short-term repair, not confirmed primary uptrend
- Above a rising 200d on weekly closes = stronger trend confirmation
- ETH/BTC above short averages but below 200d = tactical ETH strength, not durable alt leadership

### 3. Measure volatility in two ways

Calculate annualized realized volatility from log returns for 7, 30, and optionally 90 days. Compare with a live implied-volatility index such as Deribit DVOL.

Do not call volatility “low” in absolute terms merely because it fell from a panic high. Prefer:

- calm/non-stressed relative to recent history
- elevated but falling
- rising stress
- panic/extreme

State methodology because ATM IV, DVOL, and realized volatility are not interchangeable.

### 4. Measure breadth

Use a large-cap universe, normally the top 100 by market capitalization. Report:

- advancing vs. declining assets over 24h, 7d, and 30d
- percentage advancing
- median return

Exclude stablecoins, tokenized cash/funds, wrapped duplicates, and commodity-backed tokens when assessing investable crypto breadth. Document that the exclusion screen is subjective. A useful pattern is:

- strong 24h/7d breadth + weak 30d breadth = rebound, not durable broad trend
- positive 30d median + >60% advancing for multiple weekly observations = healthier participation

Do not lean on an “altcoin season” index alone.

### 5. Evaluate ETF flows as a series

Never infer institutional direction from one day. Calculate:

- latest daily net flow
- rolling five-session total
- month-to-date total
- persistence: number of consecutive positive/negative sessions

Check whether different aggregators have completed the same session. If one table is blank while another reports a number, label the latest figure provisional rather than silently choosing one.

### 6. Separate macro and crypto-specific catalysts

Macro checklist:

- latest CPI/PCE and core measure
- current policy range and next FOMC date
- market-implied near-term hike/cut probabilities
- 2-year yield, dollar, oil, and geopolitical supply risks

Crypto checklist:

- BTC/ETH ETF flows
- major regulatory legislation or enforcement changes
- digital-asset treasury issuance/sales and mNAV conditions
- protocol upgrades or staking/product changes when material
- derivatives positioning, funding, basis, liquidations

Separate **constructive catalysts** from **offsetting risks**.

### 7. Produce a conservative spot framework

Recommend filters and horizon, not certainty. A conservative framework can include:

- weekly rather than intraday decision cadence
- 8–12 week staged entries
- 3–6 month regime-confirmation horizon
- BTC primary-trend filter: weekly close above a rising 200d average
- breadth filter: >60% positive over 30d with positive median for two weekly readings
- ETF-flow filter: positive rolling five-session total sustained across two weeks
- volatility filter: avoid aggressive additions when DVOL is surging
- macro filter: avoid large tranches immediately before CPI/FOMC or when oil, dollar, and 2-year yields rise together
- ETH filter: ETH/BTC holds above its 200d average on weekly closes

Use conditional language: "this rule set permits only starter tranches" or "full planned exposure remains gated." Avoid personalized position sizes unless the user supplies portfolio constraints and risk tolerance.

### 8. Research complementary strategies

Use this when the current strategy has a known weakness (e.g., TS MOM loses in range-bound markets) and you need a strategy that profits in that blind spot. Follow this sequence:

**a) Load past cycle results.** Read existing research documents to understand what's been tested and CLOSED. Branches marked CLOSED must not be retested. Note the key failure modes: did simple mean reversion fail? Did funding fades hurt? Did OI divergence add no value? This prevents retesting already-failed families.

**b) Identify the gap via expanding window analysis.** Run or load expanding-window backtest results for the current strategy. Identify which window(s) had negative CAGR. Cross-reference those windows with market regimes (bull/bear/range). The gap is the regime(s) where the strategy consistently loses. Be precise: "TS MOM loses in W4 (ending 2023-H1) — the post-FTX range-bound period" is far more actionable than "the strategy has a bear market problem."

**c) Search academic literature for relevant evidence.** Use web_search for papers on the specific strategy class (e.g., "crypto mean reversion drawdown recovery daily"). Extract key findings: does the academic evidence show it works, and for which assets? Important: if the literature says the strategy works on small-cap but not large-cap crypto, note this — it may disqualify the approach for your universe.

**d) Cross-reference academic findings with internal results.** If the literature says "mean reversion in large-cap crypto is negative" AND your prior cycles confirm this, the burden of proof is very high. A new strategy must be fundamentally different from what failed — not a retune of the same parameters.

**e) Design specific entry/exit rules.** For each proposed strategy, define:
- Economic mechanism (Why should this work? What market inefficiency does it exploit?)
- Entry rules (ALL conditions must be true — be precise: "RSI(14) < 25", not "RSI oversold")
- Exit rules (FIRST to trigger — profit target, time stop, hard stop, signal reversal)
- Sizing (sleeve percentage, combined exposure caps)
- When it should profit (which regime?)
- When it should lose (which regime?)

**f) Write falsifiable hypotheses.** Pre-register what constitutes success:
- "Positive CAGR over the full test period"
- "Positive in >= N of M calendar years"
- "<= X trades/year per asset" (to verify it's rare, not frequent)
- "Sharpe > 0"
- "Average trade return > costs x 2"
Include explicit failure conditions: if all strategies have negative CAGR, close the entire research branch.

**g) Write a structured research report.** Use the established format matching existing CYCLE n documents:
1. Executive Summary (one-page synthesis of findings)
2. Literature Review (per-paper sections with key findings and relevance)
3. Gap Analysis (what's been tested, what failed, what's open)
4. Proposed Strategies (specific rules for each)
5. Comparison Matrix (when each wins/loses)
6. Regime Analysis (scenario-by-scenario behavior)
7. Concrete Recommendations (which to test first)
8. Falsifiable Hypotheses and Conclusion

Save the report to `research/<TOPIC>_RESEARCH.md` in the freqtrade repo.

**h) Document what would close the branch.** If the literature, internal cycles, and proposed strategies all converge that the strategy class is negative expectancy for this asset class, say so explicitly. "If none of these three strategies produce positive returns, the combined evidence definitively closes the [strategy class] branch for large-cap crypto at daily frequency." This prevents the same question from being re-researched in a future cycle.

## Output Structure

1. Snapshot time and one-sentence regime label
2. BTC/ETH/ETH-BTC trend table
3. Volatility assessment
4. Breadth assessment
5. Constructive and adverse catalysts
6. Conservative timeframe and filter stack
7. Uncertainty and data-quality caveats
8. Source list or inline links

## Pitfalls

- Do not treat 24-hour price change as trend confirmation.
- Do not calculate indicators with the incomplete current daily candle.
- Do not report raw top-100 breadth without explaining stablecoin/tokenized-asset contamination.
- Do not equate declining implied volatility with low absolute risk.
- Do not cite a single ETF-flow day as durable demand.
- Do not hide disagreements between Farside, SoSoValue, exchange feeds, or publishers.
- Do not present moving averages, filters, or prediction-market probabilities as forecasts.
- Do not use price targets when the user requested timeframe and filters.
- Do not infer independent evidence from thousands of correlated intraday bars; use dependent-data inference and joint date blocks.
- Do not select the best lookback from a large grid and report its naive Sharpe or `p`-value.
- Do not let same-bar fills, full-sample regime thresholds, smoothed latent states, or unresolved OHLC ordering leak future information.
- Do not silently attribute volatility-scaling gains to a directional signal; include scaled and unscaled always-long controls.
- Do not reopen, retune on, or relabel a sealed holdout after inspecting it.
- Do not claim a diversified cross-sectional premium from a five-asset major-coin universe.
- Do not equate current archive retrievability or checksum validity with historical event-time availability or original-file immutability.
- Do not collapse same-timestamp derivatives rows until payload equality is verified; conflicting duplicates make that timestamp unusable.
- Do not call premium-index candles true basis, and do not treat a live liquidation snapshot as a complete historical ledger.
- Do not leave “C minus B” undefined: freeze exact CAGR, Sharpe, terminal-P&L, bootstrap, deletion, drawdown, and expected-shortfall formulas in a tested machine-readable protocol.
- Do not create or push a research remote before the final result and repository audit. Scan tracked files/history with redacted output; broad working-directory scans can expose ignored local secrets in logs.
- Do not retest a closed branch. If a prior cycle closed a strategy family (e.g., "mean reversion in large-cap crypto is negative expectancy"), do not propose a new mean reversion strategy with slightly different parameters. The new strategy must be fundamentally different in mechanism — extreme-rare-event gating vs. continuous/frequent signals — not a retune of the same threshold.
- Do not claim academic support for a strategy without citing the specific paper, asset class, and timeframe. "The literature supports mean reversion" is meaningless — Zaremba (2021) finds it works in small-cap but not large-cap crypto. Be precise.
- Do not propose a complementary strategy that fires in the same regime as the primary strategy. If TS MOM is already invested in strong trends, a complementary mean reversion strategy should be in cash — otherwise they overlap and add no diversification benefit. Explicitly gate complementary strategies: "only deploy when TS MOM is in cash (trend_votes < 2)."

## Verification Checklist

Before answering, verify:

- [ ] Snapshot time is stated in UTC
- [ ] Current prices are cited
- [ ] Trend uses completed candles
- [ ] Both realized and implied volatility are addressed
- [ ] Breadth includes methodology and exclusions
- [ ] ETF flows include rolling context
- [ ] Macro data comes from current official/reputable sources
- [ ] Conflicting or incomplete data is disclosed
- [ ] Recommendation is conditional and spot-only if requested
- [ ] Uncertainty is explicit

For historical strategy robustness, also verify:

- [ ] Hypotheses, grids, benchmarks, costs, exact estimand formulas, and selection rules were fixed and contract-tested before holdout access
- [ ] Signals use completed bars and fills occur only on subsequent executable bars
- [ ] Walk-forward dates remain synchronized across all coins
- [ ] Fees, slippage, and intrabar ambiguity are modeled conservatively
- [ ] Scaled/unscaled signal and always-long ablations are all reported
- [ ] Dependence-aware intervals and complete-library multiple-testing controls are included
- [ ] Pair, period, parameter-neighbor, latency, cost, and placebo falsifications were run
- [ ] Sealed holdout and independent replication are distinguished from development results
- [ ] Conclusions say provisional evidence, not future profitability
- [ ] If publishing, tracked content/history were secret-scanned with redacted output, generated data stayed ignored, visibility was explicit or defaulted private, and the remote hash was verified
