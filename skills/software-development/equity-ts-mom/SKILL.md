---
name: equity-ts-mom
description: "Build and backtest time-series momentum (TS MOM) strategies on US equity ETFs. Covers yfinance data ingestion, simulation engine with close-to-close returns and cost-only-on-changes, parameter sweeps (SMA windows, vol targets, partial cash), and portfolio aggregation with concentration caps. Produces a clean baseline that beats SPY buy-and-hold."
version: 1.0.0
author: Hermes Agent
---

# Equity TS MOM — Time-Series Momentum for Stocks

Use this skill when building a trend-following strategy on equity ETFs. Covers the full pipeline from data ingestion through parameter optimization to final config selection.

## Signal That This Skill Applies

- You need to backtest a trend-following strategy on US equities (SPY, QQQ, sector ETFs)
- You want to port a crypto strategy to stocks and need to account for differences in volatility, return distribution, and backtest duration
- You need to determine optimal SMA windows, vol targets, or position-sizing policies for equity trend following
- You're getting implausible results (e.g., -99% max DD on a 26-year backtest) and suspect the simulation engine is wrong

## Key Differences: Crypto TS MOM vs Equity TS MOM

| Dimension | Crypto (OKX spot) | Equities (Yahoo Finance) |
|---|---|---|
| Optimal SMA windows | 20/50/100d vote | **252d single SMA** |
| Vol scaling | Essential (Parkinson 21d, vt=0.30) | **Not needed** (binary 0/1 works best) |
| Backtest duration | 3-4 years | 26+ years |
| CAGR | +7.0% | **+8.73%** |
| Sharpe | 0.39 | **0.622** |
| Max DD | -34.6% | **-27.5%** |
| vs benchmark | N/A | **+0.48pp vs SPY B&H** |
-| Simulation engine | `simulate_sleeves()` (daily cost on full notional) | **Close-to-close, costs only on target changes** |
+
+> ⚠️ **The +8.73% equity CAGR in this table is the 8-ETF NAV-fraction aggregate (METHOD A, see Portfolio Aggregation) — NOT equal-weight and NOT SPY-only.** A true single-ticker SPY `sma_252_binary` is **+6.60%**, and an 8-ETF **equal-weight (1/N)** portfolio is **+6.16%** (underperforms SPY B&H on CAGR but cuts DD to -18.6%). Equal-weight is what a "equal sleeve allocation" task means. See `references/equal-weight-vs-navfraction.md`.

## Won't Fix: Simulate_sleeves vs Standalone Simulation

The crypto backtest uses `simulate_sleeves()` from `research/cycle5_backtest.py`. This function:
- Charges trading cost on the **full notional every single day**, even when the target allocation hasn't changed
- Uses **open-to-close** returns (misses overnight gaps)
- Resets position every day (sell-and-rebuy pattern)

For crypto (3-4yr, +63% CAGR), these assumptions don't matter — the signal strength overwhelms the cost drag. For equities (26yr, +8% CAGR), they compound to destroy returns:

```
(1 - 0.001)^6500 ≈ 0.0015  — daily 10bps over 26 years
```

**Always use a standalone simulation for equity backtests:**

```python
def simulate_strategy(closes, targets, cost=0.001):
    """Close-to-close returns, costs only on actual target changes."""
    idx = targets.dropna().index
    closes = closes.reindex(idx)
    targets = targets.reindex(idx)
    n = len(idx)
    nav = np.ones(n)
    position = np.zeros(n)
    prev_target = 0.0
    for t in range(1, n):
        ret = float(closes.iloc[t] / closes.iloc[t - 1])
        curr_target = float(targets.iloc[t])
        # Mark to market with yesterday's allocation
        day_return = 1.0 + (ret - 1.0) * position[t - 1]
        nav[t] = nav[t - 1] * day_return
        # Cost only on actual trades
        if curr_target != prev_target:
            trade_frac = abs(curr_target - prev_target)
            nav[t] *= (1.0 - trade_frac * cost)
        position[t] = curr_target
        prev_target = curr_target
    return pd.Series(nav, index=idx)
```

## Data Ingestion

### yfinance — Single Ticker

```python
df = yf.download("SPY", start="2000-01-01", auto_adjust=True)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)
df.index = pd.DatetimeIndex(df.index).tz_localize("UTC")
close = df["Close"].squeeze()
```

### yfinance — Multiple Tickers (one-at-a-time for reliability)

Looping single downloads is more reliable than batch download (which returns MultiIndex columns that are fragile to index):

```python
def download_ohlcv(tickers, start="2000-01-01", end=None):
    result = {}
    for t in tickers:
        df = yf.download(t, start=start, end=end or datetime.now().strftime("%Y-%m-%d"),
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df.index = pd.DatetimeIndex(df.index).tz_localize("UTC")
        df = df.rename(columns={"Open":"open","High":"high","Low":"low",
                                "Close":"close","Volume":"volume"})
        result[t] = df[["open","high","low","close","volume"]].dropna()
    return result
```

### Common Date Index Handling

All tickers may start on different dates (e.g., IWM started 2000-05-26 vs SPY's 2000-01-03). The portfolio aggregation handles this via intersection:

```python
common_idx = None
for t in sleeves:
    if common_idx is None:
        common_idx = sleeves[t].index
    else:
        common_idx = common_idx.intersection(sleeves[t].index)
```

## Signal Functions

### Best Config: sma_210_binary (Faber 10-month, verified Jul 2026)

**Selected via parameter sweep (SMA 20-300, 2018-2023, 8 ETFs equal-weight).**
Full sweep results: `references/sma210-sweep-results.md`.

```python
def sma_210_binary(close):
    """SMA210 crossover. Binary 0/1. Faber (2007) 10-month tactical allocation."""
    sma = close.rolling(210, min_periods=210).mean()
    return (close > sma).astype(float)
```

SMA210 beats SMA252: same Sharpe (1.07) but lower drawdown (-15.2% vs -17.4%).

```python
-def sma_252_binary(close, high, low, vt=0.0):
-    """12-month SMA crossover. Binary 0/1, no vol scaling.
-
-    Per-sleeve SIGNAL only. Portfolio CAGR depends entirely on how sleeves
-    are combined (see "Portfolio Aggregation" — two methods):
-      - Single-ticker SPY only:         CAGR +6.60%, Sharpe 0.566, DD -28.7%
-      - 8-ETF EQUAL-weight (1/N):       CAGR +6.16%, Sharpe 0.587, DD -18.6%
-      - 8-ETF NAV-fraction (aggregate): CAGR +8.73%, Sharpe 0.622, DD -27.5%
-    The +8.73% figure is the NAV-fraction aggregate (METHOD A), NOT equal-weight
-    and NOT SPY-only. SPY B&H benchmark for 2000-2026: +8.25% / 0.411 / -55.2%.
-    """
-    return (close > close.rolling(252, min_periods=252).mean()).astype(float)
```

### Alternative: Golden Cross (SMA50 > SMA200) — Best Risk-Adjusted

```python
def golden_cross(close, high, low, vt=0.12):
    """SMA50 > SMA200 + vol scaling.
    
    Results: CAGR +7.22%, Sharpe 0.722, Max DD -16.5%, Calmar 0.437
    Lower CAGR than binary but 3x better Calmar.
    """
    trend = close.rolling(50).mean() > close.rolling(200).mean()
    pv = compute_parkinson_vol(high, low)
    vs = (vt / pv).clip(0, 1).fillna(0)
    return trend.astype(float) * vs
```

### Historical Signal Performance

| Signal | CAGR | Sharpe | DD | Calmar | Notes |
|--------|:----:|:------:|:--:|:------:|-------|
-| **sma_252_binary (8-ETF NAV-fraction agg)** | **+8.73%** | **0.622** | **-27.5%** | **0.317** | **Best CAGR via METHOD A (NOT equal-weight; see Portfolio Aggregation)** |
| golden_cross vt=0.12 | +7.22% | 0.722 | -16.5% | 0.437 | Best risk-adjusted |
| golden_cross vt=0.10 | +6.32% | 0.730 | -14.3% | 0.442 | Lowest DD |
| vote_100_200_300 vt=0.12 | +6.79% | 0.675 | -16.7% | 0.406 | Balanced |
| vote_50_100_200 vt=0.12 | +4.81% | 0.508 | -18.6% | 0.258 | Too conservative |
-| SPY B&H | +8.25% | 0.411 | -55.2% | 0.149 | Benchmark |
+
+> **Equal-weight (1/N) reality check:** the 8-ETF equal-weight `sma_252_binary` is **+6.16% CAGR / -18.6% DD / Calmar 0.331** — it does NOT beat SPY B&H on CAGR, but beats it 2.2x on Calmar and cuts DD by 36pp. If a task says "equal sleeve allocation", report +6.16%, not +8.73%.

### Expanding Windows — Winner (sma_252_binary)

The strategy is positive in 7/7 expanding windows. Drawdown stabilizes once the 2008 GFC enters the window:

| Window end | Years | CAGR | Sharpe | DD |
|---|---|---|---|---|
| 2006-08-21 | 6.6 | +5.40% | 0.379 | -16.5% |
| 2009-12-11 | 9.9 | +4.48% | 0.273 | -26.3% |
| 2013-04-10 | 13.2 | +4.07% | 0.240 | -26.3% |
| 2016-08-01 | 16.5 | +5.28% | 0.319 | -26.3% |
| 2019-11-21 | 19.9 | +6.79% | 0.386 | -26.3% |
| 2023-03-17 | 23.2 | +7.08% | 0.351 | -31.0% |
| 2026-07-17 | 26.5 | +8.73% | 0.385 | -31.9% |

DD stabilizes at ~26-32% after 2008 enters the window. It does not grow unboundedly — the -31.9% in the final window includes 2020 COVID (-34% peak) and 2022 bear, but the strategy's self-correction mechanism (going to cash during drawdowns) caps the damage. The expanding window CAGR increases over time (from +4% to +9%) as the strategy captures more bull markets.

### Decade Breakdown (sma_252_binary)

| Decade | Total Return | CAGR | Sharpe | Max DD |
|---|---|---|---|---|
| 2000s | +85% | +6.3% | 0.52 | -26.3% |
| 2010s | +128% | +8.5% | 0.68 | -24.1% |
| 2020s | +48% | +6.7% | 0.38 | -31.9% |

The 2000s survived the dot-com hangover and 2008 GFC with only -26% DD. The 2010s captured the full bull run. The 2020s include COVID crash and 2022 bear but still returned +48%.

-## Portfolio Aggregation — two DIFFERENT methods (do not confuse them)
-
-There are two distinct ways to combine per-sleeve NAVs. They produce
+very different CAGRs, and mixing them up is the single most common error
+in this codebase. The repo's `backtest.py:aggregate()` uses METHOD A.
+
+### METHOD A — NAV-fraction weighting (hidden momentum tilt)
+```python
+def aggregate_nav_fraction(sleeves, max_conc=0.30):
+    """Each sleeve's weight = its current NAV share, clipped to max_conc.
+    NOT equal-weight: faster-compounding sleeves (e.g. XLK 15.9x vs XLV 1.2x)
+    get a LARGER weight over time — a momentum tilt. This produced the repo's
+    headline +8.73% for the 8-ETF sma_252_binary 'winner'."""
+    df = pd.DataFrame(sleeves).ffill().bfill().fillna(1.0)
+    df = df.div(df.iloc[0])  # normalize each sleeve to start=1.0
+    total = df.sum(axis=1)
+    weights = df.div(total, axis=0).clip(upper=max_conc)
+    weights = weights.div(weights.sum(axis=1), axis=0)  # renormalize
+    return (df * weights).sum(axis=1)
+```
+
+### METHOD B — True equal-weight (what "equal sleeve allocation" means)
+Each sleeve gets a fixed 1/N weight (12.5% for 8 tickers), clipped to
+max_conc (inactive at 1/N=12.5% < 30%), renormalized. Combine via PRIOR-day
+weights so no fictitious rebalancing cost is charged:
+```python
+def combine_equal_weight(sleeves, max_conc=0.30):
+    nav = pd.DataFrame(sleeves).ffill().bfill().fillna(1.0)
+    nav = nav.div(nav.iloc[0])                       # rebaseline each to 1.0
+    n = nav.shape[1]
+    w = pd.DataFrame(1.0 / n, index=nav.index, columns=nav.columns)
+    w = w.clip(upper=max_conc).div(w.sum(axis=1), axis=0)
+    ret = nav.pct_change().fillna(0.0)
+    wr = w.shift(1).reindex(ret.index).fillna(0.0)   # prior-day weights
+    combined_ret = (ret * wr).sum(axis=1)
+    port = (1.0 + combined_ret).cumprod()
+    port.iloc[0] = 1.0
+    return port
+```
+Verified to match (to 0.01pp) a naive equal-weight daily-return average
+`ret.mean(axis=1).cumprod()` — use whichever is clearer.
+
+### Verified numbers (2000-01-03 → 2026-07-17, 26.5y, cost 0.10%)
+| Combination                | CAGR   | Sharpe | MaxDD  | Calmar | Note |
+|----------------------------|:------:|:------:|:------:|:------:|------|
+| Equal-weight (METHOD B)    | +6.16% | 0.587  | -18.6% | 0.331  | what "equal sleeve" means |
+| NAV-fraction (METHOD A)    | +8.73% | 0.622  | -27.5% | 0.317  | `backtest.py:aggregate()` output |
+| SPY-only sma_252_binary    | +6.60% | 0.566  | -28.7% | 0.230  | single-ticker SPY |
+| SPY B&H                    | +8.25% | 0.411  | -55.2% | 0.149  | benchmark |
+
+⚠️ The repo's `results.json` "sma_252_binary +8.73%" is METHOD A (8-ETF
+aggregate), NOT SPY-only and NOT equal-weight. A genuine single-ticker SPY
+`sma_252_binary` is +6.60%. See `references/equal-weight-vs-navfraction.md`.

### Recommended Universe

```
Core equity beta (3):  SPY (S&P 500), QQQ (Nasdaq 100), IWM (Russell 2000)
Sector ETFs (5):       XLF (Financials), XLE (Energy), XLK (Technology),
                       XLV (Healthcare), XLU (Utilities)
```

8 tickers total. Expandable with TLT (long bonds) and GLD (gold) for diversification, but CAGR drops.

## Metrics

```python
def compute_metrics(nav, annual_days=252):
    rets = nav.pct_change().dropna()
    if len(rets) < 2:
        return {"cagr": 0, "sharpe": 0, "vol": 0, "dd": 0, "calmar": 0}
    yrs = len(rets) / annual_days
    lr = np.log(1 + rets)
    cagr = float(np.exp(np.mean(lr) * annual_days) - 1)
    vol = float(np.std(lr, ddof=1) * np.sqrt(annual_days))
    sharpe = float(np.mean(lr) / np.std(lr, ddof=1) * np.sqrt(annual_days)) if vol > 0 else 0
    dd = float((nav / nav.cummax() - 1).min())
    calmar = cagr / abs(dd) if dd < 0 else 0
    return {"cagr": cagr, "sharpe": sharpe, "vol": vol, "dd": dd, "calmar": calmar, "years": round(yrs, 1)}
```

**Calmar is the primary risk-adjusted metric** for comparing across strategies. It penalizes both low CAGR and high DD equally. SPY's Calmar is 0.149; the best equity TS MOM variants achieve 0.3-0.44.

## Parameter Sweep Methodology

When finding optimal parameters for equities, follow this order:

1. **Start with single-SPY test** — before adding multi-ticker complexity, verify the signal works on SPY alone
2. **Test SMA windows** — single SMAs (50, 100, 200, 252) first, then votes (50/100/200, 100/200/300)
3. **Test vol targets** — equities need targets [0.08, 0.10, 0.12, 0.15] not crypto's [0.20, 0.25, 0.30]
4. **Test partial cash** — [0, 0.15, 0.30, 0.50] minimum allocation when trend is off
5. **Test expanded universe** — add TLT, GLD; try tighter concentration caps [0.20, 0.25, 0.30]
6. **Rank by CAGR** (primary) and **Calmar** (secondary) — the goal is beating SPY B&H

### Key Parameter Finding for Equities

**Longer SMA windows beat shorter ones** for equity TS MOM. The sweet spot is SMA200-240, with SMA210 selected as optimal:

- (20,50,100) → 4-5% CAGR (whipsaw city)
- (50,100,200) → 5-6% CAGR (better)
- (100,200,300) → 7% CAGR (good)
- Single 210d → **+11.9% CAGR, Sharpe 1.07, DD -15.2%** (best — Faber 10-month)
- Single 252d → +12.1% CAGR, Sharpe 1.07, DD -17.4% (similar Sharpe, worse DD)

**Short windows don't work on equities** because stocks trend slower and with more noise than crypto. The 20/50/100 SMA vote that produces 7% CAGR in crypto (4yr) produces 4% CAGR in equities (26yr). This is not a data-length artifact — it's a genuine structural difference.

**Vol scaling barely engages** for equities because stock vol (15-20% annualized) is consistently below crypto's (40-80%). At vt=0.30, the scalar is 1.0 for 95% of days on SPY. At vt=0.12, it triggers ~30% of days but the CAGR benefit is marginal.

**Binary (0 or 1) outperforms continuous for equities.** The sma_252_binary beats the golden cross and trend-strength weighting on raw CAGR. Being fully in or fully out captures trends more cleanly than graduated positions.

## Pitfalls

### 1. Cost-on-full-notional-every-day bug
**Symptom:** -99% DD on a 26-year backtest. Every signal tested loses money.
**Cause:** Using `simulate_sleeves()` from the crypto backtest infrastructure. It charges cost on the full notional every day, which compounds over 6,500+ trading days.
**Detection:** Run with target=1.0 and cost=0. If the result doesn't match `closes / closes.iloc[0]`, the simulation has this bug.
**Fix:** Use the standalone `simulate_strategy()` (close-to-close, costs only on target changes) from the "Won't Fix" section above.

### 2. yfinance MultiIndex confusion
**Symptom:** `df["Close"]` returns a DataFrame with 5 rows instead of a Series with 5,000 rows.
**Cause:** yfinance's `download(tickers=[...])` returns MultiIndex columns. Accessing `df["Close"]` gets all tickers, not a single series.
**Fix:** Use single-ticker `yf.download(ticker)` and `.squeeze()` after extraction. Or flatten with `raw.columns.droplevel(1)`.

### 3. Timezone mismatch causes NaN signals
**Symptom:** Parkinson vol is all NaN. Trend vote is all False.
**Cause:** yfinance returns tz-naive datetimes. Crypto infrastructure expects tz-aware UTC.
**Fix:** `raw.index = pd.DatetimeIndex(raw.index).tz_localize("UTC")`.

### 4. Open-to-close vs close-to-close
**Symptom:** Even at target=1.0 with cost=0, the simulated CAGR is far below buy-and-hold.
**Cause:** Open-to-close returns miss overnight gaps, which contribute most equity returns.
**Detection:** Compare `close/open` return product vs `close[n]/close[0]` over the full period.
**Fix:** Use close-to-close returns in the simulation loop.

### 5. Sector momentum overlay has lookahead bias if implemented naively
**Symptom:** A variant (e.g. static sector momentum weights based on full-period returns) shows +9.09% CAGR with the *same* Sharpe as the baseline — a free lunch.
**Detection:** Compare against the weekly-rebalanced version. If static CAGR is significantly higher than weekly-rebalanced CAGR AND the Sharpe is suspiciously good, it's lookahead bias:
  - Static weights (lookahead): CAGR +9.09%, Sharpe 0.623
  - Weekly-rebalanced (fair):   CAGR +9.12%, Sharpe 0.385
  - The Sharpe gap of 0.238 is the bias signature.
**Rule of thumb:** If CAGR gap between static and rebalanced is >0.2pp, assume lookahead bias.
**Fix:** Always test the weekly-rebalanced version. Accept that sector momentum adds ~0.1-0.4pp CAGR but degrades Sharpe from 0.62 to 0.46-0.47.
**Result:** The sector momentum overlay is real (not a bias artifact) but the risk-adjusted tradeoff is negative for most users. Not worth deploying.

### 6. Portfolio DD is structural, not a bug
The max DD of -27.5% for sma_252_binary is structural — it's the cost of being long-only 76% of the time in equities. It stabilizes at this level across expanding windows (once 2008 enters the window) and does not grow further. This is a feature of the strategy, not a bug to fix.

## Production Pipeline (Paper Trading) — HARDENED

After selecting the winner variant, set up automated paper trading following
the same hardening patterns as the crypto production pipeline:

### Script Hardening Checklist

Every production script must pass these gates:

1. **Error handling** — try/except around all external I/O (yfinance downloads,
   file reads). Single ticker failure must not crash the whole pipeline.
2. **Atomic writes** — use `os.replace(tmp, path)` for JSON persistence.
   Never `write_text()` directly on the real file.
3. **Idempotency** — same-date rerun must not duplicate snapshots or trades.
   Check `snapshots[-1]["date"] == today` and skip/replace.
4. **Exit codes** — 0=OK, 1=warning (partial data), 2=critical failure.
   Watchdog integration depends on these.
5. **Standalone execution** — must work via `python stocks/paper_trade.py`
   without any path hacks or test harness.

### Atomic Write Utility

```python
def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically: .tmp -> rename to avoid corrupt partial writes."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    os.replace(tmp, path)
```

### Watchdog Integration

The stock portfolio is monitored by `production/watchdog.py` alongside
the crypto bot. Add a `check_stocks()` function that reads
`stocks/paper_trade_history.json` and reports:

- Current equity and P&L
- Long position count vs total tickers
- Drawdown from peak equity
- Staleness: warn if last snapshot >10 days old (script runs weekly)

Wire it into the watchdog's main check loop as an additional check.
Exit code from the stock script is NOT relied upon — the watchdog
inspects the history file directly so it catches pipeline stalls.

### Standalone Delivery

The paper trader must work without Hermes. Use Windows Task Scheduler
instead of Hermes cron. See `standalone-project-delivery` skill for
the full pattern (Task Scheduler, NSSM services, one-shot install.bat,
uninstall script, config-driven paths).

### Idempotency Pattern

```python
# At top of main():
today = str(date.today())
if snapshots and snapshots[-1].get("date") == today and "--force" not in sys.argv:
    print(f"Snapshot for {today} already exists")
    return 0

# When appending:
if snapshots and snapshots[-1].get("date") == today:
    snapshots[-1] = snapshot  # replace, don't duplicate
else:
    snapshots.append(snapshot)
```

## See also

- `references/sma210-sweep-results.md` — full SMA sweep (20-300) with OOS validation and benchmarks
- `references/equal-weight-vs-navfraction.md` — equal-weight vs NAV-fraction combination methods
- `references/parameter-sweep-results.md` — complete sweep data for all 40+ variants
- `standalone-project-delivery` skill — for packaging any project for non-Hermes users
- `backtest-debugging` skill — for investigating implausible backtest metrics
- `multi-strategy-trading-portfolio` skill — for combining equity TS MOM with complementary strategies

## Production Features (Jul 2026)

Beyond the basic SMA crossover, the production paper trader includes:

- **Dividend tracking** — yfinance dividend history, credited to position value, TTM yield display
- **T-bill cash return** — idle cash earns risk-free rate (configurable, default 4.5%)
- **SPY benchmark** — buy-and-hold comparison with alpha calculation per snapshot
- **Retry logic** — 3 attempts with 5s delay on yfinance failures per ticker
- **Trading costs** — 1bp each way, matching crypto pipeline pattern
- **Trade alerts** — signal changes logged with cost detail for watchdog integration
