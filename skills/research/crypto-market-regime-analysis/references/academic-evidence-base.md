# Academic Evidence Base — Crypto Trading Strategies

## Compilation Date: July 2026
## Source Session: "evidence-backed crypto trading strategy methods" research brief

This file condenses findings from 15+ academic papers and institutional reports on crypto trading strategies. It exists so strategy development and regime analysis under this skill can reference documented edges rather than operating on guesswork or backtest-only invention.

---

## Landmark Papers (Compulsory Reading)

### 1. Crypto Three-Factor Model
**Paper:** Liu, Tsyvinski & Wu (2022) — *Journal of Finance* 77(2), 1133–1177
**Data:** Weekly, CoinMarketCap, 2014–2020
**Cited by:** 924+

**What it found:**
- Three factors explain the cross-section of crypto returns: **market, size, and momentum**
- **Weekly momentum produces ~3%/week** — far stronger than equity momentum
- Crypto momentum decays fast: optimal lookback is **1–4 weeks, NOT 1–12 months** (this is why Grobys & Sapkota 2019 found nothing using monthly data)
- Size effect: small-cap cryptos outperform
- The factors are distinct from equity factors — crypto is its own asset class

### 2. Crypto Factor Anatomy
**Paper:** Wu / Sparkline Capital (Feb 2024) — "Crypto Factor Investing"
**Data:** CoinMarketCap, 7/2017–2/2024

**What it found:**
- Four-factor model: market, size, momentum, **intangible value**
- Market Sharpe: 0.37 (same ballpark as 100-year equity/bond indexes)
- **Intangible value strongest in small-caps** — small-cap value +28.7% vs small-cap growth -25.8%
- **Momentum strongest in LARGE-caps** (opposite of equities) — large-caps dominate attention, correlate with macro, support leverage
- Intangible value acts as a natural quality filter (screens out tokens with <30 daily active addresses)
- References AQR "Value and Momentum Everywhere" (2013) — crypto is the 9th asset class where these factors work

### 3. Crypto Carry
**Paper:** Schmeling, Schrimpf & Todorov (2026) — *Management Science* (forthcoming)
**Authors:** Goethe University + Bank for International Settlements + CEPR

**What it found:**
- Crypto carry (perpetual futures funding rate collection) generates a **historical Sharpe ratio of 6.45**
- Different mechanism from FX carry: perpetual funding (longs pay shorts) vs. interest rate differentials
- **Profits are decaying post-2024** as the market matures and funding rates compress

### 4. Momentum Crash Analysis
**Paper:** Grobys, Kolari, Sandretto et al. (2025) — *Financial Markets and Portfolio Management* 39, 443–476

**What it found:**
- Large-cap crypto momentum suffers **severe crashes** — a single coin can destroy portfolio returns
- Worst single weekly return observed: **-255.28%**
- **Volatility management mitigates crash risk** — scaling by inverse volatility significantly improves risk-adjusted returns
- Caveat: vol-scaling has known issues (look-ahead bias debate in Liu et al. 2019; real-time degradation in Cederburg et al. 2020)

### 5. Survey Paper
**Paper:** Borri, Liu, Tsyvinski & Wu (2026) — *Annual Review of Financial Economics* Vol. 18
**Title:** "Cryptocurrency as an Investable Asset Class: Coming of Age"

**Seven stylized facts of crypto:**
1. Risk-adjusted performance broadly comparable to traditional assets
2. Cross-section captured by 3-factor model
3. Carry Sharpe = 6.45 (citing Schmeling et al.)
4. Jumps are frequent and large
5. Blockchain information drives prices
6. Data quality issues remain significant
7. Regulatory environment evolving

---

## What Works (Documented Edge)

| Method | Key Papers | Reported Sharpe | Caveats |
|---|---|---|---|
| **Crypto Carry (perpetual funding)** | Schmeling et al. 2026 | ~3.0–6.45 | Decaying post-2024; needs derivatives |
| **Volatility-Managed Trend Following** | Grobys et al. 2025, Bui 2026 | ~1.5–2.5 | Parameter sensitive; vol-scaling controversies |
| **Large-Cap Weekly Momentum** | Liu et al. 2022, Sparkline 2024 | ~0.7–1.5 conditional | Crash-prone; one coin can wipe returns |
| **Intangible Value (small-cap)** | Sparkline 2024 | ~0.8–1.2 backtest | Illiquidity risk; scaling uncertainty |
| **Microstructure (short-horizon)** | Easley et al. 2024, Bieganowski & Ślepaczuk 2026 | ~0.6–1.0 after costs | Tick data required; high turnover; capacity-limited |

## What Does NOT Work

| Method | Evidence |
|---|---|
| **Classical 3–12 month monthly momentum** | Korchmar (2022), Grobys & Sapkota (2019) — negative/insignificant |
| **Simple breakout (no vol management)** | Consistent with literature: plain momentum crashes |
| **Mean reversion (buying dips) in large-cap crypto** | Zaremba et al. (2021) — reversal effect is STRONG in small-cap coins but WEAK in large-cap; Zaremba et al. found the last day's return predicts the next day across 3,600+ coins, but the effect is concentrated in illiquid/small-cap coins. Our 5-asset universe (BTC/ETH/SOL/XRP/ADA) is exactly where reversal is weakest. Padysak & Vojtko (2022) OOS — MIN strategy (buy at 10-day minimum) failed 2022–2024 OOS bear-to-recovery transition. Jääskeläinen (2022) — Bollinger band mean reversion on daily Bitcoin produced optimal parameters that were effectively slow trend-following (1000-day SMA), not mean reversion. |
| **Pure market making (liquidity provision)** | Bieganowski & Ślepaczuk (2026) — crushed during flash crashes by adverse selection |
| **Time-series momentum alone** | Korchmar (2022) — not significant in crypto factor models |

## Evidence-Based Strategy Architecture

Combine these three academically-supported mechanisms:

1. **Trend signal at intermediate frequency** (6h–daily, not 1-month+) with dynamic trailing stops (Bui 2026 framework; adaptive trailing stop calibrated to ATR)
2. **Volatility scaling** — position size inversely proportional to recent realized volatility (Grobys et al. 2025; Moreira & Muir 2017 adapted to crypto)
3. **Market-cap-aware asset filtering** — large-cap momentum + small-cap intangible value (Sparkline 2024; Liu et al. 2022)

This triplet attacks: signal quality (right frequency), risk management (vol scaling), and asset selection (size × factor combination).

## Tick-Level / Microstructure Papers

### Easley, O'Hara, Yang & Zhang (2024)
- Microstructure metrics (Roll's measure, VPIN) predict crypto price dynamics
- Cross-market effects between BTC and ETH
- Stable during crypto winter — not bull-market artifact
- Useful for: market making, dynamic hedging, volatility estimation

### Bieganowski & Ślepaczuk (2026) — arXiv:2602.00776
- SHAP analysis on 1-second Binance perpetual data, 5 assets (BTC → ROSE)
- **Order flow imbalance**: most important feature, monotone with concavity at extremes
- **Bid-ask spread**: wider = less predictability (efficient markets)
- **Flash crash test**: taker strategy holds up, maker strategy collapses — validates Glosten-Milgrom adverse selection theory
- Conclusion: portable microstructure representation across crypto cap spectrum

## Full Reference List

| Paper | Authors | Year | Journal | Key Finding |
|---|---|---|---|---|
| Common Risk Factors in Crypto | Liu, Tsyvinski, Wu | 2022 | *J. Finance* | 3-factor model; weekly momentum 3%/wk |
| Crypto Factor Investing | Wu (Sparkline) | 2024 | Sparkline Capital | Intangible value; style boxes; quality filter |
| Crypto Carry | Schmeling, Schrimpf, Todorov | 2026 | *Management Science* | Carry Sharpe 6.45 via perpetual funding |
| Crypto Momentum Has (Not) Its Moments | Grobys et al. | 2025 | *Fin. Mkts & Port. Mgmt* | Vol-managed momentum; crash analysis |
| Crypto as Investable Asset Class | Borri, Liu, Tsyvinski, Wu | 2026 | *Ann. Rev. Fin. Econ.* | 7 stylized facts; comprehensive survey |
| AdaptiveTrend | Bui Thanh Nguyen | 2026 | arXiv | Sharpe 2.41; adaptive trailing stops |
| Microstructure & Market Dynamics | Easley, O'Hara, Yang, Zhang | 2024 | SSRN (Cornell) | VPIN/Roll predict crypto dynamics |
| Explainable Patterns in Crypto Micro. | Bieganowski, Ślepaczuk | 2026 | arXiv | Universal SHAP patterns across 5 cryptos |
| Short-Term Reversal in Crypto | Zaremba, Kizys, Tzouvanas, Ahmed, Niklewski | 2021 | *Intl. Rev. of Fin. Analysis* | Last-day return predicts next day; reversal concentrated in small-cap coins |
| Seasonality, Trend, Mean Rev. in BTC | Padysak, Vojtko | 2022 | SSRN | MAX strategy beats MIN OOS |
| Bitcoin Mean Reversion Thesis | Jääskeläinen | 2022 | LUT Thesis | Bollinger band mean reversion didn't beat B&H on daily BTC |
| Revisiting Trend & Mean Rev in BTC | Quantpedia | 2024 | Quantpedia | MIN (buy 10d lows) failed 2022-2024 OOS; MAX (buy 10d highs) continued working |
| Value & Momentum Everywhere | Asness, Moskowitz, Pedersen | 2013 | *J. Finance* | Foundational: factors in 8 asset classes |
| Value & Momentum in Crypto Factors | Korchmar | 2022 | EUR Thesis | Volume-based momentum works; classical doesn't |
| Crypto Microstructure Systematic Review | Almeida, Gonçalves | 2024 | *Annals of Ops Research* | 138 papers reviewed; taxonomy |

---

*This reference file is a condensed knowledge bank: cited Sharpe ratios are from the papers' own disclosures unless noted as backtest-only. Nothing here constitutes a trade recommendation.*
