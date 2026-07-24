---
name: backtest-debugging
description: "Systematic methodology for debugging backtest engines: decompose aggregate metrics, trace NAV/DD state machines, identify sleeve contamination, and verify risk controls."
version: 1.5.0
author: Hermes Agent
---

# Backtest Debugging Methodology

## Systematic Audit Methodology (5-Category Framework)

When auditing a backtest engine for simulation bugs — not just debugging a metric that looks wrong, but proactively verifying the engine itself — use this five-category framework. Each category corresponds to a class of bug that can invalidate reported metrics.

### Category A: Cost Handling Errors
- **Check:** Is cost charged on full notional every day, or only on turnover (delta)?
- **Check:** Is cost applied equally to all sleeves / variants?
- **Check:** Does cost interact with regime-sensitive parameters (vol target, position scaling) in unexpected ways?
- **Check:** Is the turnover comparison using exact float equality (`!=`) or a tolerance threshold? Exact equality can fire spuriously when targets involve division.
- **Check:** What happens when `cost = 0` — does the NAV match buy-and-hold × target?
- **Risk:** Buggy cost inflates drag 6–30× (see Pitfall 7); anti-volatility bias distorts risk-adjusted metrics (see M1 in references); float equality can silently overcharge (see Pitfall 18).

### Category B: NaN / Missing Data Edge Cases
- **Check:** What fill value is used for each signal (trend, vol, funding, OI)?
- **Check:** Are fill values conservative (bear/zero) or optimistic (false positives)?
- **Check:** What happens when an entire day or asset has NaN across all signals?
- **Check:** Is `fillna(0)` vs `fillna(1.0)` vs `fillna(False)` appropriate for each context?
- **Check:** Does the aggregation function (e.g., `_cap`) silently mask data gaps?
- **Risk:** Optimistic fills overstate returns; masked gaps hide trading halts.

### Category C: Simulation / Methodology Mismatches
- **Check:** Does the execution model match the strategy's intended trading frequency?
- **Check:** Are decisions based on T-1 close signals but executed at T open? (Causality)
- **Check:** Are sleeve weights normalized correctly (no double-compounding)?
- **Check:** Is the passive benchmark filtered when the strategy has no passive allocation?
- **Check:** Are all sleeves subject to the same risk controls?
- **Risk:** Sleeve contamination (Pitfall 1); SLEEVE_WEIGHT double-compounding (Pitfall 0); P-sleeve ignoring target_p (see references).

### Category D: State Management & Architecture
- **Check:** Are module constants mutated via `setattr` or monkey-patching (fragile, non-reentrant)?
- **Check:** Are RNG seeds deterministic across runs?
- **Check:** Does the simulation support multiple independent calls in the same process?
- **Check:** Is timezone handling consistent (all UTC-awareness)?
- **Check:** Are index constraints validated (sorted, unique, tz-aware) at entry points?
- **Risk:** Walk-forward scripts corrupt state when run concurrently; hidden nondeterminism.

### Category E: Data Integrity / Sign Convention
- **Check:** Are all `max_drawdown` values in result JSONs stored as NEGATIVE numbers? A positive value (e.g., `0.3459`) is ambiguous — it looks like a gain rather than a loss.
- **Check:** Is `max_drawdown` sign convention consistent across ALL result files (research JSONs, stock JSONs, summary files)?
- **Check:** If a `compute_metrics` function outputs `-np.min(drawdown)`, the sign flip produces a positive number — this must be negated before writing to JSON.
- **Check:** Is the `calmar` computation (CAGR / |max_drawdown|) still valid after sign changes?
- **Check:** Do summary files that re-quote metrics from source JSONs inherit the sign convention?
- **Check:** Are there archived "fixed" JSONs that still carry the OLD sign convention? Files named `*_fixed.json` are especially dangerous — they were generated AFTER an engine fix but BEFORE the sign convention changed, so downstream consumers that pick the latest-mtime file may load stale positive-MaxDD data. The recursive walker must scan ALL JSONs, not just "current" ones.
- **Risk:** Silent metric corruption when comparing or aggregating across files with mixed conventions; downstream tools misinterpret positive DD as a gain; "fixed" archives become poison if accidentally used as canonical. See `references/maxdd-sign-convention.md` for a full fix reproduction.

### When to Run Each Category

| Trigger | Categories to Run |
|---------|------------------|
| First audit of a new backtest engine | A + B + C + D (full sweep) |
| Metric looks implausible (too high/too low) | A + C (cost + methodology) |
| Risk controls seem ineffective | C (sleeve contamination, DD scope) |
| Strategy works in crypto but fails in equities | A (cost regime) |
| Walk-forward results are unstable | D (state mutation) + B (NaN fill chain) |
| MaxDD sign seems inconsistent or comparisons across systems disagree | E (data integrity) |

### Category-to-Pitfall Mapping

| Category | Relevant Pitfall(s) |
|----------|-------------------|
| A (Cost) | Pitfall 7 (full-notional daily cost), Pitfall 18 (float equality in turnover), M1 anti-volatility interaction |
| B (NaN) | Pitfall 4 (_cap fillna artifacts), NaN fill policy (bear/zero fills — see signal builders in compute_trend_mom, compute_vol_scale, compute_funding_fade) |
| C (Methodology) | Pitfall 0 (SLEEVE_WEIGHT double-compound), Pitfall 1 (sleeve contamination, P-sleeve root cause), Pitfall 9 (event-driven dilution), Pitfall 13 (off-by-one allocation lag), Pitfall 16 (feature backtest NAV field selection) |
| D (Architecture) | Pitfall 10 (global state mutation), yfinance handling (Pitfall 8) |
| E (Data Integrity) | Pitfall 11 (MaxDD sign convention), Pitfall 17 (post-hoc sign flip fragility) |

### Additional Verification Passes

For a complete audit beyond the 5 categories above, add these orthogonal passes:

**Pass F — Numerical Formula Audit:**
Independently verify every formula produces the expected output — don't just read the code, trace through a small sample:
- CAGR: Confirm `(nav_end/nav_start)^(1/years) - 1` matches the code's `exp(mean(log_returns) * N) - 1`.
- Sharpe: Is it `mean(simple_returns) / std(simple_returns) * sqrt(N)` or `mean(log_returns) / std(log_returns) * sqrt(N)`? The latter biases Sharpe downward for high-volatility assets (Pitfall 12).
- MaxDD: Is it global (peak-to-trough) or rolling-window? Rolling understates.
- Annualization: 252 (stocks) vs 365 (crypto) consistent across all files?
- Risk-free rate: `annual_rf / 365` (wrong — simple division) vs `(1 + annual_rf)^(1/365) - 1` (correct — geometric compounding)?

**Pass G — Security Audit:**
- Hardcoded API keys, tokens, or temp-file paths that could be stale/malicious. Also check for `jwt_secret_key`, `ws_token`, `db_url` (embedded credentials) — these are commonly missed.
- Command injection vectors — any user input reaching `subprocess.run`, `os.system`, or shell. Also check for code-as-string patterns: `sys.executable -c` with `%` or f-string formatting (research param sweep scripts are frequent offenders).
- `eval` / `exec` / `pickle.load` usage
- `setattr` overwriting module constants from unvalidated external files
- Path traversal via unvalidated file paths
- XSS via unsanitized HTML dashboard generation — grep for `f"<` in monitoring/dashboard code without `html.escape()`
- See `references/production-security-audit-patterns.md` for concrete grep commands and fix recipes for each pattern

**Pass H — Error Propagation Chain:**
Trace the full dependency chain end-to-end:
- What happens when upstream fails (yfinance down, corrupt JSON, missing file)?
- Are JSON writes atomic (write to .tmp → rename) or direct (partial writes produce corrupt files)?
- Are all JSON reads wrapped in try/except? (Missing error handling on reads causes cascading failures.) Pay special attention to reads at the END of a pipeline after data has already been written — a crash here leaves stale output that looks like a successful run.
- Does a failed step leave a partial output that poisons the next step?
- Is there a stale-state hazard (e.g., `alert_log.json` reading old `last_state` that no longer matches current signals)? Also check for the "append-overwrite" anti-pattern: any writer that appends to a shared JSON file but only writes its own keys, silently wiping another component's stored state.
- See `references/production-security-audit-patterns.md` for concrete detection recipes (crash-after-write, append-overwrite, non-atomic dashboard writes)

**Pass I — Type Safety & Mutable Defaults:**
- Any `def fn(items=[])` or `def fn(config={})` that mutates the default?
- Any implicit `or` trap: `value = x.get("key") or default` — masks `0.0` and `False` as missing?
- Any `float + str` or `int + None` that silently produces wrong results?

**When to run additional passes:**
| Trigger | Passes |
|---------|--------|
| First audit of a codebase with live money | F + G + H + I (full additional sweep) |
| Crypto strategies | F (Sharpe log-return bias is material for crypto) |
| Production pipeline deployment | H (error propagation) |
| After subagent fix batches | H (verify fix didn't break error handling) |

---

## Standard Debugging Flow

When a combined metric (CAGR, Sharpe, max DD) seems wrong — too high, too low, or inconsistent with the strategy's design — follow this systematic decomposition approach.

## Signal That This Skill Applies

- A combined metric (max DD, CAGR, Sharpe) looks implausible
- Risk controls (stop-loss, DD stop, drawdown limit) don't seem to have the expected effect
- The backtest produces different results than a manual sanity check
- Expanding-window validation shows a structural metric that doesn't vary with window size
- This is the first audit of a backtest engine

## Core Technique: Decompose the Aggregate

The fundamental debugging pattern is **decomposition**:

1. **List every component** feeding into the aggregate metric
2. **Compute the metric per-component** (not just combined)
3. **Compare components** — the one with a disproportionate value is the likely root cause
4. **Verify controls** — does each component actually respond to the risk controls you think are in place?

### Worked Example: P-Sleeve Contamination (Cycle 6 TS MOM Bot)

A portfolio-level DD of 92% was reported despite a 40% NAV hard stop. Per-sleeve decomposition revealed:

```
PASS 1: No DD Stop
Combined NAV maxDD: 93.5%

Per-Sleeve maxDD:
  Sleeve A (raw trend):       70.8%
  Sleeve B (vol-scaled):      21.3%
  Sleeve C (funding fade):    20.2%
  Sleeve P (passive B&H):     93.8%  ← ROOT CAUSE
  Sleeve PV (vol-scaled B&H):  0.0%

Active sleeves only (A+B+C):  58.2%
Passive only (P):             97.0%
```

**Root cause:** The P sleeve (passive buy-and-hold benchmark) is hardcoded in `simulate_sleeves` to track spot prices — it **cannot be reduced by the DD stop**. The DD stop only scales target allocations for A/B/C sleeves via `dd_multiplier_series`. During bull runs, P grows to dominate the portfolio weight (SOL's P reached 91.3% of that pair's combined NAV), and during crashes it suffers full spot drawdowns.

**Fix applied:** Changed the combined NAV computation to use `r["sleeve_b"] + r["sleeve_c"] + r["sleeve_pv"]` instead of `r["nav"]` (which included P). Result: maxDD dropped from 92% → 19.7%.

## DD Stop State Machine Tracing

When a DD stop seems ineffective, trace the state machine step by step:

```
def trace_dd_stop(portfolio_nav):
    dd_mult_vals = []
    reduced = False
    for d_val in dd:
        if d_val > HARD_STOP:          # e.g. 0.40 → 0.0x exposure
            reduced = True
            dd_mult_vals.append(0.0)
        elif d_val > SOFT_STOP:         # e.g. 0.25 → 0.50x exposure
            reduced = True
            dd_mult_vals.append(SCALE_DOWN)
        elif reduced and d_val < RECOVER:  # e.g. 0.10 → restore full
            reduced = False
            dd_mult_vals.append(1.0)
        elif reduced:
            dd_mult_vals.append(SCALE_DOWN)
        else:
            dd_mult_vals.append(1.0)
    return dd_mult_vals
```

Key questions to answer:
- **When does the stop first trigger?** Compare to the peak-to-trough timeline.
- **Does the stop ever reach the hard exit threshold?** If not, it's confined to the soft-stop band.
- **What are the NAV, DD, and multiplier values at each trigger point?** Print this timeline for the ±30 days around each trigger.
- **Are the trigger dates from PASS 1 (no stop) valid for PASS 2 (with stop)?** The two-pass approach computes DD state from pass 1's NAV but applies it in pass 2 where the actual NAV diverges. For daily rebalancing this is approximately correct; for intraday or high-frequency it breaks.

## Common Pitfalls

### 0. SLEEVE_WEIGHT Double-Compounding (Allocation Architecture Bug)

**Symptom:** Vol target sweep shows non-monotonic or paradoxical results (higher vol_target → lower CAGR). Strategy CAGR is in the low single digits despite adequate risk budget.

**Cause:** The sleeve-comparison architecture gives each variant its own SLEEVE_WEIGHT (typically 0.20 = 20% of capital). The vol_target then further reduces this:
```
Effective exposure = SLEEVE_WEIGHT(0.20) × vol_scale(~0.25)
                   = 5% per asset per variant
                   = ~15% total deployed capital
```
80-85% of capital sits in cash, making the strategy mathematically incapable of capturing meaningful returns regardless of vol_target.

**Detection:** Log the average `target_b` value across all decision days. If mean < 0.10 and SLEEVE_WEIGHT < 1.0, you have this bug.

**Fix:** Normalize the combined NAV by dividing by SLEEVE_WEIGHT:
```python
# Before (underallocated):
nav_df = pd.DataFrame({f"s{i}": r["sleeve_b"] + r["sleeve_c"] + r["sleeve_pv"] for i, r in enumerate(all_results)})
# After (normalized to vol_target as direct allocation target):
SLEEVE_WEIGHT = 0.20
nav_df = pd.DataFrame({f"s{i}": (r["sleeve_b"] + r["sleeve_c"] + r["sleeve_pv"]) / SLEEVE_WEIGHT for i, r in enumerate(all_results)})
```

**Verification:** After the fix, a vol_target sweep should produce a **monotonic** progression — higher vol_target = higher CAGR AND higher DD.

**Corrected sweep (B-only, SLEEVE_WEIGHT normalized):**
| vt | CAGR | Sharpe | MaxDD |
|:--:|:----:|:------:|:-----:|
| 0.08 | +0.9% | 0.21 | 11.8% |
| 0.10 | +1.2% | 0.23 | 14.5% |
| 0.12 | +1.5% | 0.24 | 17.0% |
| 0.15 | +2.2% | 0.27 | 20.5% |
| 0.20 | +3.4% | 0.31 | 25.9% |
| 0.25 | +5.0% | 0.35 | 30.6% |
| 0.30 | +7.0% | 0.39 | 34.6% |

Sharpe RISES with vol_target (0.21→0.39), meaning the strategy captures more trend at higher allocation before risk controls fire. Apply BOTH fixes (exclude P + normalize SLEEVE_WEIGHT) before interpreting metrics.

### 1. Sleeve Contamination  
**Symptom:** Combined portfolio DD is >2× any individual sleeve's DD.  
**Cause:** A passive/benchmark sleeve with full spot exposure dominates the portfolio weight.  
**Root cause (P-sleeve bug):** The P-sleeve in `simulate_sleeves` ignores `target_p` entirely:
```python
passive[0] = SLEEVE_WEIGHT
for t in range(1, n):
    passive[t] = passive[t - 1] * (closes[pair].iloc[t] / closes[pair].iloc[t - 1])
```
Even when `target_p` is set to a Series of 0.0 (which it is in `build_targets` and `build_targets_c6`), the P-sleeve compounds as a full buy-and-hold position. It should hold cash (flat) when target_p = 0.
**Check:** `per-sleeve maxDD` table. The passive sleeve's DD will equal the underlying asset's max drawdown.  
**Fix — root cause:** Make P-sleeve respect target_p. When target_p == 0 (the default for all strategy builders), hold cash flat — do NOT zero out the sleeve:
```python
target_p_series = targets.get("target_p", pd.Series(0.0, index=targets.index))
passive[0] = SLEEVE_WEIGHT
for t in range(1, n):
    if target_p_series.iloc[t - 1] > 0:
        passive[t] = passive[t - 1] * (closes[pair].iloc[t] / closes[pair].iloc[t - 1])
    else:
        passive[t] = passive[t - 1]  # cash, flat at SLEEVE_WEIGHT — NOT zero
```
The prior workaround of `SLEEVE_WEIGHT * target_p_series.iloc[t - 1]` zeroes the sleeve when target_p=0.0 instead of holding cash flat — this compounds the error by erasing capital rather than preserving it.
**Fix — workaround (if changing simulator is not possible):** Exclude the passive sleeve from combined NAV:
```python
# Before (contaminated):
nav_df = pd.DataFrame({f"s{i}": r["nav"] for i, r in enumerate(all_results)})
# After (active only):
nav_df = pd.DataFrame({f"s{i}": r["sleeve_b"] for i, r in enumerate(all_results)})
```
**Watch out:** If you use the workaround, the active-only NAV denominators are wrong (the nav column includes P, but individual sleeves are correct). Use per-sleeve values directly rather than the sum.
**Cycle 5-specific impact:** `run_cycle5_experiment.py` aggregates `r["nav"]` which includes the buggy P sleeve — all Cycle 5 metrics are inflated.

### 2. DD Stop Not Applied to All Sleeves
**Symptom:** DD stop improves metrics by <5pp despite aggressive thresholds.  
**Cause:** The stop only targets a subset of sleeves. Check the simulation loop — are all sleeve variants multiplied by `dd_mult`?  
**Fix:** Apply `dd_mult` to all managed sleeves, or exclude unmanaged sleeves from the combined NAV.

### 3. Two-Pass DD Stop Divergence
**Symptom:** Pass 2 DD is close to pass 1 DD despite the stop being active.  
**Cause:** The DD state was computed from pass 1 (no stop) NAV but applied in pass 2 (with stop). The pass 2 NAV diverges from pass 1 after the stop fires, meaning the stop state no longer matches the actual drawdown path.  
**Fix:** For daily systems the error is small (~1-2 pp). For higher frequencies, use a single-pass approach with properly integrated stop logic.

### 4. _cap Function Artifacts
**Symptom:** Combined NAV values seem inflated.  \\\
**Cause:** The `_cap` function uses `fillna(1.0)` which pretends missing days had full value. For multi-asset portfolios, this can mask early-period losses.  \\\
**Fix:** Require all assets to have data from day 1, or use a `fillna(0.0)` with proper cash accounting.

### 5. Portfolio-Level Scalar Never Fires (Saturation Detection)
**Symptom:** Adding a portfolio-level vol target or uniform scalar produces identical or near-identical metrics to the baseline. Correlation > 0.99.  \\
**Cause:** The existing per-asset vol scaling already keeps portfolio realized vol below the target. The scalar computes `min(1.0, target / realized_vol)` and realized_vol ≤ target → scalar is always 1.0.  \\
**Detection:**
```python
portfolio_returns = asset_return_df.mean(axis=1)  # equal-weight
portfolio_vol = portfolio_returns.rolling(21).std() * np.sqrt(365)
print(f"Portfolio vol: median={portfolio_vol.median():.2%}, range=[{portfolio_vol.min():.2%}, {portfolio_vol.max():.2%}]")
for target in [0.20, 0.25, 0.30]:
    active_days = (target / portfolio_vol).clip(0, 1).lt(1.0).mean()
    print(f"  target={target:.2f}: scalar active {active_days:.1%} of days")
```
**Fix:** If the scalar never fires, the layer is redundant — remove it. This is a useful negative result confirming existing controls work. If you still want portfolio-level protection, use a lower target (e.g., 0.15) so it actually triggers, or remove per-asset vol scaling and let the portfolio scalar be the sole control.

### 7. Simulation Assumption Mismatch — Cost on Full Notional Every Day

**Symptom:** A strategy that works well in crypto backtests (3-4yr, +63% CAGR) produces catastrophic -99% DD and -16% CAGR when ported to equities (26yr). Every trend-following variant tested loses money regardless of parameters.

**Cause:** The `simulate_sleeves()` function from crypto backtest infrastructure charges trading cost on the **full notional every single day**, regardless of whether the target allocation actually changed. It does not check for position stability.

Over 26 years (~6,500 trading days) at 10 bps cost, total costs = 0.001 × 6,500 = 6.5× starting capital. Compounds to destroy all returns: (1 - 0.001)^6500 ≈ 0.0015.

This is invisible in short crypto backtests because 3-4 year windows have ~1,000 trading days (costs ≈ 1× capital), and 63% CAGR overwhelms the cost drag. Also, open-to-close returns miss overnight gaps which contribute most equity returns.

**Detection:** Simulate with cost=0 and target=1.0 (always long). If the result differs materially from `closes / closes.iloc[0]`, the simulation has this bug.

**Fix for equities/long-duration backtests:** Build a standalone simulation with:
1. **Close-to-close returns** — hold positions overnight
2. **Costs only on actual target changes** — no daily cost when target is unchanged
3. **Carry-forward position tracking** — don't sell-and-rebuy same allocation daily

```python
def simulate_strategy(closes, targets, cost=0.001):
    """Close-to-close, costs only on target changes."""
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
        day_return = 1.0 + (ret - 1.0) * position[t - 1]
        nav[t] = nav[t - 1] * day_return
        if curr_target != prev_target:
            trade_frac = abs(curr_target - prev_target)
            nav[t] *= (1.0 - trade_frac * cost)
        position[t] = curr_target
        prev_target = curr_target
    return pd.Series(nav, index=idx)
```

**Anti-volatility cost bias (M1 interaction):** Because daily cost = `sleeve_nav × target_alloc × cost_rate` and `target_alloc = trend × vol_scale`, the bug creates a *regime-dependent* distortion:

- **Low realized vol** → vol_scale ≈ 1.0 → target ≈ 1.0 → HIGH daily cost (market trending calmly)
- **High realized vol** → vol_scale ≈ 0.0 → target ≈ 0.0 → LOW daily cost (market crashing)

The strategy pays **more** cost during the best trending periods and **less** during protective periods. This overstates the true cost of trend-following and understates Sharpe more than CAGR (the cost adds noise as well as drag). The effect compounds across long backtests.

**Detection:** Simulate with cost=0 and compare period-by-period cost drag. If cost drag is higher during low-vol windows than high-vol windows, the anti-volatility bias is active. Fix by adopting turnover-based cost (see below).

**When crypto `simulate_sleeves` IS safe:** Backtest ≤ 5yr, CAGR ≥ 30%, comparing variants (same cost applies to all).  
**When to use standalone simulation:** Equity/multi-decade backtests, low-return strategies (<10% CAGR), comparison against buy-and-hold benchmark, or when `trading_days × daily_cost > 0.10`.

### 8. yfinance Multi-Index DataFrame Handling

**Symptom:** After `yfinance.download(tickers, ...)` (multiple tickers), `df["Close"]` returns a DataFrame with MultiIndex columns.

**Cause:** yfinance returns MultiIndex columns (column_name × ticker). Single-ticker access returns a DataFrame, not a Series.

**Fix:**
```python
raw = yf.download(tickers, ...)
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.droplevel(1)
# Also fix timezone for compatibility with crypto infrastructure:
raw.index = pd.DatetimeIndex(raw.index).tz_localize("UTC")
```

For single-ticker: `close = df["Close"].squeeze()` ensures Series.

### 9. Event-Driven vs Continuous Sleeve Simulation
**Symptom:** A secondary strategy that triggers rarely (crash recovery, range bounce) mechanically dilutes the primary strategy's CAGR with no Sharpe improvement.  \\
**Cause:** Event-driven strategies have low signal density. A 20% sleeve sitting in cash 98% of the year just drags CAGR by ~20% proportionally.  \\
**Detection:** If CAGR drops proportionally to cash allocation (~primary × 0.80) and Sharpe is flat, the event-driven sleeve isn't adding value — it's a cash drag with occasional lucky trades.  \\
**Pattern for event-driven backtesting:** Don't use `simulate_sleeves()` (continuous daily signals). Use manual position tracking:
```python
class TradeTracker:
    def __init__(self, capital_weight=0.20, initial_nav=1000):
        self.capital = initial_nav * capital_weight
        self.cash = self.capital
        self.trades = []     # {entry_date, entry_price, exit_date, exit_price, return%, reason}
        self.open_trade = None

    def check_entry(self, date, close, open_price, conditions_all_match):
        if self.open_trade is None and conditions_all_match:
            self.open_trade = {"entry_date": date, "entry_price": open_price,
                               "stake": self.cash, "shares": self.cash / open_price}
            self.cash = 0

    def check_exit(self, date, close, exit_conditions):
        if self.open_trade is None: return
        ret = self.open_trade["shares"] * close / self.open_trade["stake"] - 1
        if any(exit_conditions):
            self.trades.append({**self.open_trade, "exit_date": date, "exit_price": close,
                                "return_pct": ret, "reason": exit_reason})
            self.cash = self.open_trade["stake"] * (1 + ret) * (1 - cost)  # after fees
            self.open_trade = None
```
Combine with primary via: `combined_nav = primary_weight × primary_nav + secondary_weight × secondary_nav`. Use this pattern whenever signals are expected < 20×/year across all assets.

### 14. Copy-Paste Asymmetry — Sibling Code Blocks with Missing Guards

**Symptom:** Two sleeves/variants in the same simulator function behave differently despite having identical target values. One sleeve correctly applies a condition check; the other skips it and produces spurious returns or drawdowns.

**Cause:** The code has two nearly-identical loops or blocks (e.g., P-sleeve and PV-sleeve in `simulate_sleeves`). A guard condition was added to one but not the other. The unguarded block runs an outdated default (typically full buy-and-hold or full allocation) regardless of the actual target value.

**Example — P-sleeve vs PV-sleeve:**
```python
# PV sleeve (CORRECT — checks target_pv before compounding):
for t in range(1, n):
    target_pv = target_pv_series.iloc[t - 1]
    if target_pv > 0:
        passive_vol[t] = passive_vol[t - 1] * (closes[pair].iloc[t] / closes[pair].iloc[t - 1])
    else:
        passive_vol[t] = SLEEVE_WEIGHT * target_pv  # cash

# P sleeve (BUG — same pattern but NO guard, always compounds B&H):
for t in range(1, n):
    passive[t] = passive[t - 1] * (closes[pair].iloc[t] / closes[pair].iloc[t - 1])
# Missing: if target_p_series.iloc[t-1] > 0 else cash
```

**Detection:** When two sleeves show radically different DD despite having identical target values (both set to 0.0 by `build_targets`), one of them is ignoring its target. List all sleeves and their per-sleeve maxDD. If two sleeves with target=0 have DD that differs by >90pp, the higher-DD sleeve has a missing guard.

**Fix:** Compare sibling blocks line by line. Any `if target_x > 0` in one block should have a corresponding check in the sibling. When target is 0 (the default for unused sleeves), hold cash flat — preserve the sleeve's existing NAV, do not zero it out.

**PV-sleeve capital destruction variant:** Even after the P-sleeve guard is added, the PV-sleeve else-branch at `passive_vol[t] = SLEEVE_WEIGHT * target_pv` silently destroys accumulated capital when `target_pv` drops from a positive value to zero. The P-sleeve correctly holds `passive[t] = passive[t-1]` (cash-flat), but the PV-sleeve sets NAV to exactly `0.0` — erasing all prior gains. This creates two bugs in one: (a) NAV is zeroed rather than held at prior value, and (b) if `target_pv` later becomes positive again, the PV-sleeve restarts from zero instead of from its accumulated cash. Fix: change the else-branch to `passive_vol[t] = passive_vol[t-1]` matching P-sleeve semantics. Detection: simulate with target_pv alternating between 0.3 and 0.0 every other day — if terminal PV NAV is zero, the bug is present. See `references/pv-sleeve-capital-destruction.md`.

### 15. Risk Parity Underperforms Equal Weight When High-Vol = High-Sharpe

**Symptom:** Replacing equal-weight sleeves with inverse-volatility risk parity weights makes the portfolio WORSE — lower CAGR, lower Sharpe, higher DD. The result seems paradoxical since risk parity is theoretically superior for diversification.

**Cause:** Risk parity allocates more capital to low-volatility assets and less to high-volatility assets. When the highest-volatility asset ALSO has the highest risk-adjusted return (Sharpe ratio), risk parity systematically underweights the best performer. The correlation structure doesn't save it — with only 5 highly correlated assets, there's no diversification benefit from overweighting the low-vol losers.

**Real example (5 crypto pairs, 2021-2023):**
| Asset | Return | Sharpe | Max DD | Equal Weight | Risk Parity Weight |
|-------|:------:|:------:|:------:|:------------:|:------------------:|
| SOL | +162% | 1.63 | -27% | 20% | ~12% (penalized for high vol) |
| ETH | +24% | 0.44 | -34% | 20% | ~20% |
| ADA | +19% | 0.41 | -39% | 20% | ~25% (rewarded for low vol) |
| BTC | +1% | 0.13 | -34% | 20% | ~22% |
| XRP | -7% | -0.03 | -40% | 20% | ~21% |

SOL's high vol drives a LOW risk parity weight (~12%) despite having by far the best Sharpe (1.63). ADA gets overweighted (~25%) despite a mediocre 0.41 Sharpe. The result: risk parity CAGR -3.8pp, Sharpe -0.27, DD +3.0pp vs equal weight.

**When risk parity DOES help:** With 20+ independent assets where volatility is uncorrelated with expected returns. In crypto with 5 highly correlated majors, it's counterproductive.

**Detection:** Before deploying risk parity, run a per-pair attribution to check whether the highest-vol asset is also the highest-Sharpe. If so, equal weight with a concentration cap (e.g., 40% max per asset) outperforms risk parity.

**Fix:** Stick with equal weight plus a concentration cap. The cap already prevents single-asset dominance without penalizing productive volatility.

### 16. NAV Aggregation Using `result["nav"]` Instead of Active Sleeves

**This affects BOTH feature backtests AND experiment runners.** Any code that aggregates `result["nav"]` (the sum of ALL five sleeves: a, b, c, p, pv) includes P-sleeve and PV-sleeve contributions that have nothing to do with the active strategy.

**Symptom — feature backtests:** Feature backtests (correlation sizing, MTF confirmation, regime vol target) report CAGR values that are suspiciously low (~3-5%) compared to the experiment runner's results (~7% for the same period). Sharpe ratios are inflated relative to the low CAGR. MaxDD values are much lower than expected (8-9% vs 34%).

**Symptom — experiment runners:** Some experiment runners (run_cycle5, run_cycle7) aggregate `r["nav"]` instead of `r["sleeve_b"] / SLEEVE_WEIGHT`. The P-sleeve contributes a constant `SLEEVE_WEIGHT = 0.20` per pair even when inactive (target_p=0, cash-flat), which dilutes active-strategy CAGR and Sharpe by ~25% compared to the B-only normalized approach used by run_cycle6 and run_cycle9.

**Quick check:** `grep -rn 'r\["nav"\]' --include="*.py" research/` — every hit is a potential dilution site. Compare against the canonical pattern `r["sleeve_b"] / SLEEVE_WEIGHT` in run_cycle6_experiment.py.

**Cause:** Code that wraps `simulate_sleeves()` and re-aggregates NAV often defaults to `result["nav"]` — the full combined NAV that includes ALL five sleeves (a, b, c, p, pv). The P-sleeve holds cash at SLEEVE_WEIGHT when target_p=0 (post-fix), contributing phantom capital. The experiment runner correctly uses `r["sleeve_b"] / SLEEVE_WEIGHT` — the B-only sleeve normalized for capital allocation.

**Detection:** Compare the feature backtest helper's NAV aggregation against the experiment runner's. Look for `result["nav"]` vs `r["sleeve_b"]` usage:

```python
# INCORRECT — feature backtest _simulate() helper:
all_navs.append(result["nav"])  # includes P-sleeve, PV-sleeve, etc.
combined = pd.DataFrame({"nav": sum(all_navs) / len(all_navs)})

# CORRECT — experiment runner:
nav_df = pd.DataFrame({
    f"s{i}": r["sleeve_b"] / SLEEVE_WEIGHT  # B-only, normalized
    for i, r in enumerate(all_results)
})
```

If the feature backtest baseline CAGR differs from the experiment runner's CAGR for the same period by >2pp, the feature harness is using a different NAV source. Also check: if MaxDD is dramatically lower in the feature backtest than the experiment runner (e.g., 8% vs 34%), the P-sleeve's cash-like behavior is dampening the active strategy's real drawdown.

**Fix:** Align the feature backtest harness with the experiment runner's NAV aggregation. Replace `result["nav"]` with the per-sleeve column that matches the variant being tested:

```python
# For B-only feature tests:
all_navs.append(result["sleeve_b"] / SLEEVE_WEIGHT)

# For C-sleeve (funding fade) tests:
all_navs.append(result["sleeve_c"] / SLEEVE_WEIGHT)
```

After the fix, the feature backtest baseline should match the experiment runner's result for the same period. Any remaining differences are from aggregation methodology (equal-weight vs concentration-capped), not sleeve contamination.

**When this bites:** Any code that wraps `simulate_sleeves()` for a secondary purpose (feature testing, parameter sweeps, drop-out analyses) and re-aggregates NAV. The bug is especially deceptive because the P-sleeve behaves like a cash position during normal markets (target_p = 0), only ballooning during strong trends — so metrics look "conservative but reasonable" rather than obviously broken.

### 17. Post-hoc Sign Flip Fragility — `compute_metrics` Returns Positive MaxDD

**Symptom:** Some result JSONs have positive max_drawdown (Cycle 9, feature backtests), others have negative (Cycle 5/6). The sign convention is inconsistent across files, making cross-file comparisons silently wrong.

**Cause:** `compute_metrics()` in `cycle5_backtest.py` returns `float(-np.min(drawdown))` — a POSITIVE number (the double-negation produces a positive value from the negative trough). The cycle5/cycle6 experiment runners negate this value AFTER `compute_metrics` returns, before writing to JSON. But the cycle9 runner and feature backtest harness do NOT apply the same post-hoc flip, so their JSONs store the raw positive value.

This creates a fragile two-tier system: `compute_metrics` returns one convention, and each caller is individually responsible for knowing to flip it. New runners inherit the bug unless someone remembers to add the flip.

**Detection:** Compare `compute_metrics` output directly against JSON-stored values:
```python
metrics = compute_metrics(result)  # returns POSITIVE max_drawdown
# If metrics["max_drawdown"] > 0 but cycle6_results.json has max_drawdown < 0,
# a post-hoc flip is happening somewhere. Trace the write path.
```

Also, run the recursive sign walker across ALL result JSONs and flag any positive values:
```python
def find_positive_maxdd(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("max_drawdown", "max_dd") and isinstance(v, (int, float)) and v > 0:
                print(f"POSITIVE at {path}.{k} = {v}")
        for k, v in obj.items():
            find_positive_maxdd(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_positive_maxdd(item, f"{path}[{i}]")
```

**Fix — root cause:** Change `compute_metrics` to return `float(np.min(drawdown))` directly (negative). Update all callers that expect positive values. This is a breaking change — apply the recursive JSON walker to negate all existing positive values before the fix, then verify all result files are consistent.

**Fix — workaround (if changing compute_metrics is not possible):** Add the sign flip to EVERY writer path. In the runner's output dict construction:
```python
metrics = compute_metrics(result)
metrics["max_drawdown"] = -abs(metrics["max_drawdown"])  # force negative
```

**Prevention:** Add a CI lint rule: every JSON file containing `max_drawdown` must have it ≤ 0. Block commits that introduce positive values.

**The duplicated-function trap:** `run_cycle9_experiment.py` has its OWN local `_compute_metrics` function that is a near-identical copy of `cycle5_backtest.compute_metrics`. When the canonical version was fixed (`float(np.min(drawdown))`), the local copy was NOT updated, preserving the old `float(-np.min(drawdown))` bug. Detection: `grep -rn "float(-np.min(drawdown))"` across all `.py` files — zero remaining instances means every copy is fixed. Prevention: never duplicate `compute_metrics` — always import and use the canonical version. If a runner genuinely needs different metric logic, wrap the canonical function rather than copying it. See `references/sign-convention-audit-template.md` for the full cross-file audit table pattern.

**Symptom:** Replacing equal-weight sleeves with inverse-volatility risk parity weights makes the portfolio WORSE — lower CAGR, lower Sharpe, higher DD. The result seems paradoxical since risk parity is theoretically superior for diversification.

**Cause:** Risk parity allocates more capital to low-volatility assets and less to high-volatility assets. When the highest-volatility asset ALSO has the highest risk-adjusted return (Sharpe ratio), risk parity systematically underweights the best performer. The correlation structure doesn't save it — with only 5 highly correlated assets, there's no diversification benefit from overweighting the low-vol losers.

**Real example (5 crypto pairs, 2021-2023):**
| Asset | Return | Sharpe | Max DD | Equal Weight | Risk Parity Weight |
|-------|:------:|:------:|:------:|:------------:|:------------------:|
| SOL | +162% | 1.63 | -27% | 20% | ~12% (penalized for high vol) |
| ETH | +24% | 0.44 | -34% | 20% | ~20% |
| ADA | +19% | 0.41 | -39% | 20% | ~25% (rewarded for low vol) |
| BTC | +1% | 0.13 | -34% | 20% | ~22% |
| XRP | -7% | -0.03 | -40% | 20% | ~21% |

SOL's high vol drives a LOW risk parity weight (~12%) despite having by far the best Sharpe (1.63). ADA gets overweighted (~25%) despite a mediocre 0.41 Sharpe. The result: risk parity CAGR -3.8pp, Sharpe -0.27, DD +3.0pp vs equal weight.

**When risk parity DOES help:** With 20+ independent assets where volatility is uncorrelated with expected returns. In crypto with 5 highly correlated majors, it's counterproductive.

**Detection:** Before deploying risk parity, run a per-pair attribution (see below) to check whether the highest-vol asset is also the highest-Sharpe. If so, equal weight with a concentration cap (e.g., 40% max per asset) outperforms risk parity.

**Fix:** Stick with equal weight plus a concentration cap. The cap already prevents single-asset dominance without penalizing productive volatility. Only consider risk parity when the asset universe exceeds ~15 names with low pairwise correlation.

### 16. Feature Backtest NAV Field Selection — Using `result["nav"]` Instead of Active Sleeves

**Symptom:** Feature backtests (correlation sizing, MTF confirmation, regime vol target) report CAGR values that are suspiciously low (~3-5%) compared to the experiment runner (~7% for the same period). Sharpe ratios are inflated relative to CAGR. MaxDD values are much lower than expected (8-9% vs 34%).

**Cause:** The feature backtest helper `_simulate()` aggregates `result["nav"]` — the full combined NAV that includes ALL five sleeves (a, b, c, p, pv). During bull markets, the P-sleeve (passive buy-and-hold) grows to dominate portfolio weight, inflating the combined NAV with spot returns that have nothing to do with the feature being tested. The experiment runner correctly uses `r["sleeve_b"] / SLEEVE_WEIGHT` — the B-only sleeve normalized for capital allocation — but the feature backtest harness uses a different NAV source, making feature-vs-baseline comparisons invalid.

**Detection:** Compare the feature backtest helper's NAV aggregation against the experiment runner's. Look for `result["nav"]` vs `r["sleeve_b"]`:
```python
# INCORRECT — feature backtest _simulate() helper:
all_navs.append(result["nav"])  # includes P, PV sleeves
combined = pd.DataFrame({"nav": sum(all_navs) / len(all_navs)})

# CORRECT — experiment runner:
nav_df = pd.DataFrame({
    f"s{i}": r["sleeve_b"] / SLEEVE_WEIGHT  # B-only, normalized
    for i, r in enumerate(all_results)
})
```
If the feature backtest baseline CAGR differs from the experiment runner's CAGR for the same period by >2pp, the feature harness is using a different NAV source.

**Fix:** Align the feature backtest harness with the experiment runner's NAV aggregation. Replace `result["nav"]` with the per-sleeve column matching the variant being tested:
```python
# For B-only feature tests:
all_navs.append(result["sleeve_b"] / SLEEVE_WEIGHT)
```

### 17. Post-hoc Sign Flip Fragility — `compute_metrics` Returns Positive MaxDD

**Symptom:** Some result JSONs have positive max_drawdown (Cycle 9, feature backtests), others have negative (Cycle 5/6). Sign convention is inconsistent across files, making cross-file comparisons silently wrong.

**Cause:** `compute_metrics()` returns `float(-np.min(drawdown))` — a POSITIVE number. The cycle5/cycle6 experiment runners negate this AFTER `compute_metrics` returns, before writing JSON. But the cycle9 runner and feature backtest harness do NOT apply the same post-hoc flip, so their JSONs store the raw positive value. This creates a fragile two-tier system where each caller is individually responsible for knowing to flip the sign. New runners inherit the bug unless someone remembers to add the flip.

**Detection:** Run the recursive sign walker across ALL result JSONs and flag positive values:
```python
def find_positive_maxdd(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("max_drawdown", "max_dd") and isinstance(v, (int, float)) and v > 0:
                print(f"POSITIVE at {path}.{k} = {v}")
        for k, v in obj.items():
            find_positive_maxdd(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_positive_maxdd(item, f"{path}[{i}]")
```

**Fix — root cause:** Change `compute_metrics` to return `float(np.min(drawdown))` directly (negative). Update all callers that expect positive. Apply the recursive walker to negate all existing positive values before the fix, then verify all result files are consistent.

**Fix — workaround (if changing compute_metrics is not possible):** Add sign flip to every writer path: `metrics["max_drawdown"] = -abs(metrics["max_drawdown"])`.

**Prevention:** Add a CI lint rule: every JSON file containing `max_drawdown` must have it ≤ 0. Block commits that introduce positive values.

**The duplicated-function trap:** `run_cycle9_experiment.py` has its OWN local `_compute_metrics` function that is a near-identical copy of `cycle5_backtest.compute_metrics`. When the canonical version was fixed (`float(np.min(drawdown))`), the local copy was NOT updated, preserving the old `float(-np.min(drawdown))` bug. Detection: `grep -rn "float(-np.min(drawdown))"` across all `.py` files — zero remaining instances means every copy is fixed. Prevention: never duplicate `compute_metrics` — always import and use the canonical version. If a runner genuinely needs different metric logic, wrap the canonical function rather than copying it.

## Per-Pair Attribution — Standard Diagnostic

When ANY portfolio-level metric (CAGR, Sharpe, DD) is reported, always decompose it into per-asset contributions. A single asset can drive 80%+ of returns while others bleed — the aggregate hides this.

**Technique:**
```python
per_pair = {}
for pair in PAIRS:
    # Simulate each asset independently with its own signal
    nav = simulate_sleeve(pair, targets, opens, closes)
    # Compute per-asset metrics
    cagr = compute_cagr(nav)
    sharpe = compute_sharpe(nav)
    dd = compute_maxdd(nav)
    trend_on_pct = (target > 0).mean()
    per_pair[pair] = {"cagr": cagr, "sharpe": sharpe, "max_dd": dd, "trend_on_pct": trend_on_pct}

# Check: does one asset dominate?
contributions = {p: d["cagr"] for p, d in per_pair.items()}
total = sum(contributions.values())
dominant = max(contributions, key=contributions.get)
pct = contributions[dominant] / total * 100 if total > 0 else 0
print(f"{dominant} contributes {pct:.0f}% of total CAGR")
```

**When to run:**
- After every backtest — embed in the experiment runner
- Before making portfolio construction decisions (risk parity, concentration limits)
- When a strategy "works" but you can't explain why
- When evaluating whether to add or remove assets from the universe

**Red flags from per-pair decomposition:**
- One asset >50% of returns → concentration risk, check for survivorship bias
- Trend activation wildly different across assets (e.g., 47% vs 12%) → signal may be regime-dependent
- Negative Sharpe in 3+ of 5 assets → strategy only works because of one outlier
- All assets have similar Sharpe → genuine diversified alpha

### 10. Global State Mutation via setattr / Monkey-Patching

**Symptom:** Walk-forward or expanding-window validation produces different results depending on the order windows are run. Results are inconsistent between one-off runs and batch runs.

**Cause:** Scripts mutate module-level constants using `setattr`:

```python
# walkforward_validation.py (and expanding_window.py)
setattr(c6, "VOLATILITY_TARGET", 0.20)
setattr(r6, "START", start_dt)
setattr(r6, "END", end_dt)
```

Python's module caching (`sys.modules`) means the mutated constants persist between calls. If `main()` is called twice in the same process, the second call inherits the first call's mutated state. This makes the simulation **non-reentrant**.

**Detection:**
1. Call `main()` twice in the same process with different parameters.
2. Compare results — if they differ from running each call in a separate process, state mutation is the cause.
3. Test: add `print(c6.VOLATILITY_TARGET)` before and after each call.

**Fix (two options):**

**Option A — Factory function (preferred):**
Refactor the experiment module to accept parameters as function arguments instead of module-level constants:
```python
def main(start="2021-01-01", end="2024-12-31", vol_target=0.30) -> dict:
    ...
```
Callers pass parameters explicitly: `r6.main(start=..., end=..., vol_target=0.20)`.

**Option B — Subprocess isolation (compatible but slower):**
Each window runs in a fresh subprocess so state is never shared:
```python
import subprocess
proc = subprocess.run(
    [sys.executable, "-c", f"setattr(r6, 'START', '{start_dt}'); r6.main()"],
    ...
)
```

**When to use each:**
- **Option A** when you control the experiment module (internal code).
- **Option B** when you don't control the module (third-party, frozen research pipeline).

**Affected patterns:** Expanding-window validation scripts, walk-forward scripts, param sweep runners that iterate by mutating globals. Any script that calls `main()` in a loop with `setattr` between iterations.

**Cycle 6 case study:** `expanding_window.py` runs 7 iterations, each mutating `r6.START`, `r6.END`, and `r6.BOOTSTRAP_REPLICATES`. If any iteration cached data based on these values, subsequent iterations would silently use stale state. The current implementation happens to work because `load_ohlcv_panels` filters by date at call time (reads globals fresh), but there is no enforcement — a future refactor that adds module-level caching would break silently.

### 11. MaxDD Sign Convention Inconsistency

**Symptom:** Downstream comparison scripts compare `max_drawdown` values across research JSONs and stock JSONs and get contradictory results. Reports show average DD of +20% (i.e., an average GAIN of 20% — obviously wrong). Calmar ratios are negative when they should be positive.

**Cause:** The `compute_metrics` function computes `max_drawdown = float(-np.min(drawdown))`. The double-negative (trough is negative, then negated) produces a POSITIVE number. When this was written to JSON files without an explicit sign flip, it propagated the wrong convention.

**Detection:** Recursively walk every JSON result file looking for `"max_drawdown": <positive_number>`. Also check for `"calmar"` values that are negative when CAGR is positive (Calmar = CAGR / |MaxDD|).

**Fix:** Write a recursive JSON walker that negates any positive `max_drawdown` value in-place. Re-run all downstream consumers (summary generators, comparison scripts, report markdown) to refresh any stale references:

```python
import json
from pathlib import Path

def negate_maxdd(obj):
    if isinstance(obj, dict):
        if "max_drawdown" in obj and isinstance(obj["max_drawdown"], (int, float)):
            if obj["max_drawdown"] > 0:
                obj["max_drawdown"] = -obj["max_drawdown"]
        for v in obj.values():
            negate_maxdd(v)
    elif isinstance(obj, list):
        for item in obj:
            negate_maxdd(item)
```

**The partial-fix trap:** Summary JSONs often have both:
- **Rounded summary values** that were already manually negated (e.g., `-0.3459` in a `head_to_head` section)
- **Raw data reference values** copied verbatim from source (still positive)

The recursive walker must visit ALL nested dict values. A pre-negated value at one path does not mean the file is clean.

**Prevention:** Add a CI check that runs the detection script on every JSON result file before commit. Or, change `compute_metrics` to return the negative value directly (`float(np.min(drawdown))` instead of `float(-np.min(drawdown))`).

See `references/maxdd-sign-convention.md` for the full fix reproduction with file-by-file occurrence counts and verification steps.

### 12. Sharpe Ratio Uses Log Returns Instead of Simple Returns (Systematic Bias)

**Symptom:** Sharpe ratios for high-volatility assets (crypto) are systematically lower than expected given the CAGR and maxDD. Risk-adjusted metrics understate the strategy's true efficiency.

**Cause:** `compute_metrics` computes Sharpe as `mean(np.log(1+rets)) / std(np.log(1+rets)) * sqrt(N)`. The standard industry formula is `mean(rets) / std(rets) * sqrt(N)` (simple returns). For crypto daily returns (±2-5%, tails ±15%), log-returns diverge significantly from simple returns, biasing Sharpe downward.

**Detection:** Compare both formulas on the same return series. The ratio `sharpe_simple / sharpe_log` is the understatement factor.

**Fix:** Replace `np.log(1+rets)` numerator/denominator with bare `rets` in every LOCAL copy of `metrics()`. Fix only the DEFINING function, not files that import it. Keep CAGR and MaxDD unchanged. Files with local copies: stocks/backtest.py, stocks/paper_trade.py, stocks/return_boosters.py, stocks/parameter_sweep.py, research/cycle5_backtest.py, research/bootstrap_analysis.py, production/monitor_status.py (also has risk-free-rate division bug).

**Verification:** For crypto (7% CAGR, 35% vol), log-return Sharpe ≈0.39, simple-return Sharpe ≈0.43-0.45.

### 13. Off-by-One Allocation Lag in NAV Simulation Loops

**Symptom:** CAGR is systematically lower than expected even after fixing cost-on-turnover. A vol_target sweep shows the strategy barely captures directional returns. Simulating with cost=0 and vol_scale=1.0 (full trend exposure, no costs) produces results far below buy-and-hold — the first bar's return is always missed, and all subsequent bars lag by one period.

**Cause:** The simulation loop confuses `prev_target_alloc` (the allocation from the PREVIOUS loop iteration, which is the T-2 decision) with the current bar's allocation (the T-1 decision). The day T-1 decision should earn the return from T-1 close to T close, but the code applies the T-2 decision instead:

```python
# BUG: prev_target_alloc from T-2 is applied to T-1→T return
prev_target_alloc = 0.0
for t in range(1, n):
    target_alloc = targets.iloc[t - 1]  # T-1 decision
    r = closes.iloc[t] / closes.iloc[t - 1]  # T-1→T return
    variant_nav[t] = variant_nav[t - 1] * (1.0 + (r - 1.0) * prev_target_alloc)  # WRONG: uses T-2
    prev_target_alloc = target_alloc

# t=1: target_alloc=T0 decision, prev=0.0 → earns 0% return on first bar (MISSED)
# t=2: target_alloc=T1 decision, prev=T0 decision → earns T1→T2 return with T0 allocation (LAGGED)
```

Every bar's return is earned using the PREVIOUS bar's allocation decision. The first bar is always flat. This systematically understates all metrics across all cycles.

**Detection:** Simulate with cost=0, vol_scale=1.0, and trend=1.0 (always long). If the terminal NAV differs from `buy_and_hold_nav`, the loop has this bug. The first bar's return will be completely missed.

**Fix:** Use `target_alloc` (the T-1 decision) for the T-1→T return, not `prev_target_alloc`:

```python
# CORRECT: target_alloc (T-1 decision) applied to T-1→T return
prev_target_alloc = 0.0
for t in range(1, n):
    target_alloc = targets.iloc[t - 1]  # T-1 decision
    r = closes.iloc[t] / closes.iloc[t - 1]  # T-1→T return
    variant_nav[t] = variant_nav[t - 1] * (1.0 + (r - 1.0) * target_alloc)  # CORRECT: uses T-1
    # Cost on turnover: compare to PREVIOUS iteration's target_alloc (T-2)
    if t > 1 and target_alloc != prev_target_alloc:
        variant_nav[t] *= (1.0 - abs(target_alloc - prev_target_alloc) * cost)
    prev_target_alloc = target_alloc  # track T-2 for next iteration's cost check
```

**Why it's hard to spot:** The bug doesn't crash, produce NaN, or create obviously impossible metrics. It produces numbers that look "conservative but plausible" — systematically lower but not clearly wrong. Only a controlled simulation with known parameters (cost=0, fixed allocations) reveals the lag. This bug class is universally applicable to any backtest loop that tracks previous-period allocations — always verify with a no-cost always-long sanity check.

**Stocks cold-start variant:** In `stocks/backtest.py:171`, `pos = np.zeros(n)` and the loop uses `pos[t-1]` for the return at time t. Since `pos[0]=0.0`, the first bar's return is always flat — the target decision at index 0 is never applied. Fix: `pos[0] = float(targets.iloc[0])`. Over multi-year backtests this costs <0.5% CAGR, but it compounds in walk-forward validation. Detection: same cost=0 always-long sanity check — the first bar will show zero return while B&H has a non-zero return.

When a backtest includes both active and passive sleeves, the passive benchmark can dominate combined metrics. Apply this pattern when per-sleeve decomposition reveals one sleeve has a disproportionate impact:

1. **Identify** the contaminating sleeve: run per-sleeve maxDD analysis. The culprit will have DD close to the underlying asset's max drawdown while active sleeves have much lower DD.
2. **Exclude** it from the combined NAV computation. In the experiment runner, replace `r["nav"]` (sum of all sleeves) with `r["sleeve_b"] + r["sleeve_c"] + r["sleeve_pv"]` (or equivalent active-only sum).
3. **Verify** consistency: re-run the expanding window validation and confirm the new maxDD is stable across window sizes.
4. **Report both sets**: label metrics clearly as "strategy" vs "strategy + passive benchmark" so the reader doesn't confuse the two.

### Code Change Example

```python
# Before (contaminated by passive P sleeve):
nav_df = pd.DataFrame({f"s{i}": r["nav"] for i, r in enumerate(all_results)})

# After (active sleeves only):
nav_df = pd.DataFrame({
    f"s{i}": r["sleeve_b"] + r["sleeve_c"] + r["sleeve_pv"]
    for i, r in enumerate(all_results)
})
```

### Verification
The fix should produce a maxDD that is:
- **Stable across expanding windows** (once crash period is included)
- **Close to the max of individual active sleeve DDs** (not multiple times larger)
- **Consistent with the risk control thresholds** (e.g., if there's a 40% hard stop, DD should be <45%)

## Audit Report Format

When delivering an engine audit, use a structured report with:

1. **Scoped files** at the top — what was examined
2. **Findings grouped by audit category** (Cat A-E from the 5-category framework)
3. **Severity tags:** **CRITICAL** (live-money threat, stop trading), **MAJOR** (metric distortion, fix before next run), **MINOR** (edge case, document and defer)
4. **Summary table** at the bottom with every finding + severity + file + line reference
5. **"Clean Bills of Health" table** — areas you verified as correct. This is essential: it proves you checked those areas. An audit that only lists bugs leaves the reader wondering whether you didn't check the clean areas or they passed silently.

See `references/engine-audit-report-template.md` for the structure and `references/freqtrade-engine-audit-july2026.md` for a full worked example applying the 8-category audit to a real freqtrade codebase.

### Pitfall 18 — Float Equality in Cost/Turnover Checks

**Symptom:** A strategy with stable positions shows cost drag on days where the target allocation should be unchanged. Or, less commonly, two nearly-equal float values fail `==` and the cost charge is skipped.

**Cause:** The turnover check uses exact float equality: `if target_alloc != prev_target_alloc: charge_cost()`. For values computed as simple multiplications (e.g., `trend_flag * vol_scale`), this works in practice because 0 × 0.3 = 0.0 exactly. But when targets involve division (`weight = nav / total`), floating-point artifacts can produce `0.30000000000000004 != 0.3`, triggering spurious cost charges.

**Detection:** Run with cost > 0 and check whether cost charges occur on days where the target signal (trend, vol_scale, etc.) is unchanged. Simulate with cost=0 and cost=0.002 — if the cost-drag-per-day spikes on days with constant signals, the float comparison is firing spuriously.

**Fix:** Use a tolerance threshold:
```python
if abs(target_alloc - prev_target_alloc) > 1e-12:
    turnover = abs(target_alloc - prev_target_alloc)
    variant_nav[t] *= (1.0 - turnover * cost)
```

### Pitfall 19 — Engine Patches Can Silently Revert Prior Fixes on the Same File

**Symptom:** After applying a well-intentioned engine fix (e.g., PV-sleeve normalization), the test suite explodes with 23 failures. MaxDD values flip from negative to positive, crash-test thresholds break, and compute_metrics sign convention tests fail. The fix itself was correct — the error was not verifying test suite health afterward.

**Cause:** The backtest engine file (`cycle5_backtest.py`) is the single most heavily patched file in the codebase. Prior fixes live within 50 lines of each other: the sign convention fix (`float(np.min(...))` at ~line 312), the off-by-one allocation fix (~line 228), the P-sleeve guard (~line 246), and the PV-sleeve else-branch (~line 262). A patch that touches any of these regions can silently revert another fix if the patch's `old_string` anchors on code that changed between fixes.

**Real example (July 2026):** A PV-sleeve normalization patch reverted the sign convention from `float(np.min(drawdown))` back to `float(-np.min(drawdown))`, causing 23 test failures. The patch's `old_string` included lines near the compute_metrics function, and the fuzzy matcher picked up the stale sign convention from the pre-fix version.

**Prevention — ALWAYS run the full test suite after ANY patch to cycle5_backtest.py, regardless of how small the change.** If tests fail that were passing before, the patch reverted a prior fix. Do not proceed until all tests pass again.

**Detection:** `grep -n "float.*np.min" research/cycle5_backtest.py` — if it shows `float(-np.min(...))`, the sign convention fix was reverted. `pytest tests/ -q` — if previously-passing tests now fail, a prior fix was reverted.

## Post-Fix Verification Protocol

After fixing ANY engine-level bug (cost, allocation, sleeve contamination, sign convention), the minimum verification is:

1. **Controlled sanity check:** Simulate cost=0, vol_scale=1.0, trend=1.0 (always long, no friction). NAV must exactly match buy-and-hold.
2. **Re-run dev period:** The development window (e.g., 2021-2023). Compare before/after metrics.
3. **Re-run OOS period:** The holdout window (e.g., 2024). Verify edge persists out-of-sample.
4. **Vol target sweep:** Run at least 3 targets (low/med/high). After fix, sweep should be **monotonically increasing** — higher vt = higher CAGR AND higher Sharpe. A paradoxical sweep (CAGR drops at higher vt, or Sharpe reverses) indicates remaining bugs.
5. **Commit corrected results:** Write to versioned JSON files. Never overwrite the old results — keep both for provenance: `cycle6_results_dev_fixed.json` alongside `cycle6_results.json`.

Do NOT make strategy decisions (parameter changes, overlay enable/disable) based on pre-fix metrics. A single engine bug can understate CAGR by 10+ percentage points, which can make a genuinely good strategy look marginal and cause you to abandon it prematurely.

## Two-Pass Stop Architecture (Analyzed)

The two-pass approach works as follows:
1. **Pass 1:** Simulate without any DD stop → compute portfolio NAV → compute DD from the NAV trace → build `dd_mult` series from the DD state machine
2. **Pass 2:** Re-simulate with `dd_mult` applied to target allocations → the reduced exposure during drawdown limits further losses

**Limitation:** The DD state is computed from pass 1's NAV. When pass 2 applies the stop, the actual NAV diverges from pass 1. If the stop was correct in pass 1 but overly conservative for the new pass 2 path, the strategy exits positions earlier than necessary. The error grows with the severity of the drawdown.

**When it's acceptable:** For daily rebalancing with moderate drawdowns (<50%), the error is small (1-2 pp). For intraday, high-LVG, or any system where the stop is the only risk control, use an integrated single-pass approach.

## Vol Target Sweep: Diminishing Returns

When investigating low CAGR alongside acceptable DD, run a vol target sweep to find the optimal risk/return balance. The relationship is NOT linear — higher vol targets can paradoxically *reduce* CAGR due to stop interactions.

### Expected Behavior vs Observed

For a strategy with vol-scaled position sizing:
- **Linear model:** CAGR × (vt₂ / vt₁), DD × (vt₂ / vt₁)
- **Actual in practice:** C-sleeve (funding fade) + regime filter + DD stop create nonlinearities

### Example Sweep (B+C+PV, Active Sleeves, 2021-2024)

| vol_target | CAGR | Sharpe | MaxDD | C-B | Notes |
|:----------:|:----:|:------:|:-----:|:---:|-------|
| 0.15 | +1.8% | 0.25 | 19.7% | +0.29% | Base conservative config |
| **0.20** | **+2.8%** | **0.29** | **24.8%** | +0.53% | **Best risk-adjusted** |
| 0.25 | +1.2% | 0.11 | 28.4% | +0.82% | Pareto-worse: less CAGR, more DD |

At vt=0.25, CAGR **dropped** while DD rose. The non-linearity comes from:
1. Higher allocation → more losses before trend signals flip → DD stop fires harder
2. Regime filter cuts more aggressively during vol spikes (which are common at higher targets)
3. Funding fade has more exposure to fade (C-B widens but from both directions)
4. The 1.0 cap on vol_scale means assets with low Parkinson vol can't scale past full allocation

### B-Only Decomposition (vt=0.20 only)

When the C-sleeve (funding fade) is removed, the B sleeve alone shows:

| Variant | CAGR | Sharpe | MaxDD |
|---------|:----:|:------:|:-----:|
| B+C+PV (experimental runner) | +2.8% | 0.29 | 24.8% |
| B-only (clean alpha) | +18.4% | 0.41 | 59.1% |

The funding fade destroys ~15.6 pp of CAGR. B-only at vt=0.20 is a legitimate trend strategy (18.4% CAGR, 0.41 Sharpe) but the DD is high (59%). The combined B+C+PV result is safe (24.8% DD) but barely profitable (2.8% CAGR).

### Regime Filter vs DD Stop: Independent Attribution

When multiple risk controls are active, decompose their individual contributions before optimizing. The regime filter and DD stop can work at cross purposes.

**Cycle 6 case study (B-only, vol=0.25, 2021-2024):**

| Risk Controls Active | CAGR | MaxDD | Delta CAGR | Delta DD |
|:--------------------|:----:|:-----:|:----------:|:--------:|
| No controls | +7.0% | 34.6% | baseline | baseline |
| DD stop only | +5.0% | 30.6% | -2.0pp | -4.0pp |
| Regime filter only | +3.1% | 32.1% | -3.9pp | -2.5pp |
| Both (current) | +1.1% | 28.2% | -5.9pp | -6.4pp |

**Interpretation:**
- **DD stop costs 2pp CAGR but saves 4pp DD** — net positive (0.5:1 return/risk tradeoff)
- **Regime filter costs 4pp CAGR but saves only 2pp DD** — net negative (2:1 cost/benefit)
- **Combined, they cost 6pp CAGR for only 6pp DD** — the combo is worse than DD stop alone

**Why the regime filter underperforms:** The hysteresis state machine (enter@1.3x, exit@1.1x, crash@2.0x) uses trailing 252-day median Parkinson vol as baseline. In crypto, sustained high-beta regimes (e.g. SOL during 2023-24 bull) keep the ratio above threshold for long periods, causing extended exposure cuts during the strongest trend periods. The filter:
- Misses trend onsets that coincide with vol spikes (common in crypto breakouts)
- Stays in reduced state too long after vol spikes (exit threshold 1.1x is too slow to recover)
- Cuts to 0.25x at the 2.0x crash threshold, which fires during normal vol events

**Sliding vol target (vt=0.20/0.40 on 252d median split) — VERIFIED NO-GO for crypto.** Identical root cause as the regime filter. Reducing vt when Parkinson vol exceeds its trailing median cuts exposure during the most profitable trend periods. Tested 2021-2024 on 5-pair crypto portfolio: CAGR −4.33pp (17.81%→13.48%), Sharpe −0.28 (1.04→0.76), MaxDD +8.39pp (25.0%→33.4%) vs fixed vt=0.30. Script: `research/run_cycle6_sliding_vt.py`. Report: `improvement_sliding_vt.md`. Crypto vol is pro-cyclical — vol spikes at trend ONSETS, so ANY mechanism that dynamically reduces vt during high-vol periods destroys the strategy's edge. The monotonic vt sweep already established higher fixed vt → higher CAGR + higher Sharpe.

**Protocol for testing:**
1. Run the full experiment with ALL controls → record CAGR, DD
2. Remove regime filter (keep DD stop) → record
3. Remove DD stop (keep regime filter) → record
4. Remove both → record
5. Compare the delta-CAGR / delta-DD ratios to decide which controls to keep

**Recommendation: Remove both.** The full 12-way config sweep (vt=0.20/0.25/0.30 × RF on/off × DD on/off) showed that at vt=0.30, the "no controls" config wins on every metric:

| Config | CAGR | Sharpe | MaxDD |
|:-------|:----:|:------:|:-----:|
| vt=0.30 no RF no DD | **+7.0%** | **0.39** | **34.6%** |
| vt=0.30 no RF DD on | +2.1% | 0.28 | 17.9% |
| vt=0.30 RF on no DD | +4.8% | 0.30 | 35.1% |
| vt=0.30 RF on DD on | +2.2% | 0.29 | 17.4% |

The DD stop costs 5pp CAGR for 17pp DD reduction (3.4:1 tradeoff — too expensive). The regime filter costs 2.2pp CAGR and makes DD WORSE by 0.5pp. At vt=0.30, the price of risk control exceeds the benefit.

This conclusion was only reached after running the full 12-way sweep. The earlier recommendation to "keep DD stop, remove regime filter" was based on partial data at vt=0.25 only. Always run the full factorial sweep before committing to control architecture.

### When to Run a Sweep

- **Signal:** Low CAGR despite adequate DD headroom
- **Procedure:** Patch the vol_target constant directly (`patch` tool), not setattr (which hangs when constants are read at import time). Re-run the experiment. Revert with `git checkout` after.
- **Verify:** Run expanding window validation at the best vt to confirm DD is stable

### Interpretation Table

| Sweep Pattern | Likely Cause |
|---|---|
| CAGR increases, DD increases (linear) | Pure scaling — strategy works, just needs calib. |
| CAGR peaks then drops (vt=0.25 worse than vt=0.20) | Stop/wall effects: DD stop fires too aggressively at higher targets |
| DD compresses (non-monotonic) | Regime filter + stop creating path dependency |
| C-B widens as vt rises | Funding fade has more exposure to fade (not necessarily good) |

## Recommended Config After Full Exploration

When the sleeve contamination has been fixed (P excluded, SLEEVE_WEIGHT normalized), run a **12-way config sweep** (3 vol_targets × 2 regime filter states × 2 DD stop states) before picking a final config. The relationship between risk controls and returns is non-obvious.

### Case Study: Cycle 6 TS MOM Full Config Sweep

Full sweep of B-only configs (vt=0.20/0.25/0.30 × RF on/off × DD on/off), ranked by Sharpe:

| Rank | Config | CAGR | Sharpe | MaxDD |
|:----:|:-------|:----:|:------:|:-----:|
| **1** | **vt=0.30, no RF, no DD** | **+7.0%** | **0.39** | **34.6%** |
| 2 | vt=0.25, no RF, no DD | +5.0% | 0.35 | 30.6% |
| 3 | vt=0.20, no RF, no DD | +3.4% | 0.31 | 25.9% |
| 4 | vt=0.30, RF on, no DD | +4.8% | 0.30 | 35.1% |
| 5-12 | any combination with DD stop | 1.4-2.2% | 0.25-0.29 | 11.9-17.9% |

**Key findings:**
- **The "no controls" config wins at every vol_target** — no regime filter and no DD stop produces the best Sharpe AND CAGR at all three vol levels.
- **The DD stop costs ~5pp CAGR for ~17pp DD reduction** — a 3.4:1 tradeoff (too expensive).
- **The regime filter makes DD WORSE** — at vt=0.30, RF on → DD increases from 34.6% to 35.1% while CAGR drops from 7.0% to 4.8%.
- **Sharpe RISES with vol_target** (0.21→0.39 across the sweep) — the strategy captures more trend at higher allocation. This only works when risk controls are not interfering.

**Why the DD stop is counterproductive at higher vol targets:**
The DD stop's 25% threshold is too close to the strategy's natural DD of 34.6%. When the stop fires at 25%, it cuts exposure to 50%, causing the strategy to miss the subsequent recovery. At lower vol targets (0.20), the natural DD is 25.9%, so the stop at 25% fires only briefly. At higher targets, the stop is constantly active during normal drawdowns, destroying returns.

**Why the regime filter is actively harmful:**
Crypto volatility spikes at THE START of bullish trends (high vol = trend onset). The regime filter cuts exposure when the trend is just beginning, missing the best crypto moves. The hysteresis state machine also stays in reduced mode too long after vol spikes (exit threshold 1.1x is too slow to recover).

### Recommended Final Config

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Trend signal | TS MOM 20/50/100d SMA vote (2 of 3) | Proven across 7 expanding windows |
| Vol estimator | Parkinson 21d HL | ~5x more efficient than close-to-close |
| **Vol target** | **0.30** | **Best Sharpe (0.39) and CAGR (+7.0%)** |
| Risk controls | **None** | DD stop and regime filter both destroy more CAGR than the DD they save |
| Per-asset cap | 40% | Prevents single-asset dominance (SOL was 73% of returns) |
| Overlays | **None** | Funding fade, OI divergence, multi-signal fade all tested — destroyed CAGR without improving DD |

### Expanding Window Validation (Final Config)

| Window | Period | CAGR | Sharpe | MaxDD |
|:------:|:-------|:----:|:------:|:-----:|
| W1 | 2021 only | **+24.4%** | 1.42 | **10.0%** |
| W2 | +2022 H1 | +12.4% | 0.84 | **13.8%** |
| W3 | +2022 H2 | +0.4% | 0.03 | **27.0%** |
| W4 | +2023 H1 | -2.7% | -0.18 | **32.7%** |
| W5 | +2023 H2 | **+9.7%** | 0.57 | **34.6%** |
| W6 | +2024 H1 | **+7.7%** | 0.44 | **34.6%** |
| W7 | Full 4yr | **+7.0%** | 0.39 | **34.6%** |

MaxDD stabilizes at 34.6% (structural — the cost of long-only in crypto). CAGR positive in 6/7 windows. The single negative window (W4, includes depths of 2022 bear) is -2.7% — acceptable for a long-only trend strategy.

### Production Deployment Checklist

1. Set `VOLATILITY_TARGET = 0.30` in the backtest module
2. Remove regime filter from `compute_per_pair_signals` (comment out the call to `compute_regime_filter`, set `regime_aligned = 1.0`)
3. Remove all DD stop logic (single-pass simulation, no dd_mult)
4. Remove C sleeve and all funding fade/OI/premium code from the experiment runner
5. Remove SLEEVE_WEIGHT double-compounding: divide combined_nav by SLEEVE_WEIGHT
6. Normalize per-sleeve NAV: combine as `r["sleeve_b"] / SLEEVE_WEIGHT` (not `r["nav"]`)
7. Re-run expanding window to confirm
8. Update `cycle6_results.json` with the new baseline

## Expanding Window Validation

When DD seems structural (same value across window sizes), verify by computing expanding windows. Compare results **before and after** fixing a suspected contamination — the expanding window will tell you whether the fix actually resolved the structural issue.

### Example: Before Fix (P-sleeve contamination)

```
Windows:
- 1 year  (2021): CAGR +552%, DD 47%  (bull market, no crash; P dominated)
- 2 year  (2021-22): CAGR +11%, DD 87% (includes 2022 crash; P crashed)
- 3 year  (2021-23): CAGR +64%, DD 87% (crash + recovery; P=93% DD)
- 4 year  (2021-24): CAGR +64%, DD 87% (stable at crash-level DD)
```

### Example: Final Config (vt=0.30, B-only, no RF, no DD, SLEEVE_WEIGHT normalized)

| Window | Period | CAGR | Sharpe | MaxDD |
|:------:|:-------|:----:|:------:|:-----:|
| W1 | 2021 only | **+24.4%** | 1.42 | **10.0%** |
| W2 | +2022 H1 | +12.4% | 0.84 | **13.8%** |
| W3 | +2022 H2 | +0.4% | 0.03 | **27.0%** |
| W4 | +2023 H1 | -2.7% | -0.18 | **32.7%** |
| W5 | +2023 H2 | **+9.7%** | 0.57 | **34.6%** |
| W6 | +2024 H1 | **+7.7%** | 0.44 | **34.6%** |
| W7 | Full 4yr | **+7.0%** | 0.39 | **34.6%** |

MaxDD stabilizes at 34.6% — structural to the strategy (not a data artifact). CAGR positive in 6/7 windows. The single negative window (W4, depths of 2022 bear) is -2.7% CAGR, which is acceptable for a long-only trend strategy. The strategy generates +24.4% CAGR in the 2021 bull and +9.7% in the 2023-24 recovery.

**Bootstrap 95% CI (20k replicates, W7):** CAGR [-11.2%, +6.9%, +30.8%] — wide interval due to 4-year crypto sample but median positive.

**Interpretation:** If DD stabilizes at the same value once a crash enters the window, it's structural to the strategy (not a data-length artifact). The fix must come from the strategy or risk controls, not from adding more data. If DD changes dramatically after removing a passive benchmark sleeve, the original metric was contaminated.

## Per-Sleeve Risk Decomposition Script

See `scripts/p_sleeve_dominance.py` for a programmatic demonstration of the decomposition technique. It:
- Simulates each sleeve independently for all assets
- Reports per-sleeve final NAV, peak NAV, and maxDD
- Computes the P-sleeve's percentage of combined NAV (revealing dominance)
- Reports portfolio-level metrics with and without the problematic sleeve

See `scripts/risk_control_decomposer.py` for independent attribution of the regime filter vs DD stop — run this when multiple risk controls are active and you need to know which ones to keep.

See `scripts/config_12way_sweep.py` for a skeleton 12-way factorial config sweep (3 vol_targets × 2 regime states × 2 DD states). Run this before settling on a final configuration to ensure you've explored the full control landscape.

See `references/nav-stop-audit-findings.md` for the full trace data from the Cycle 6 audit.  
See `references/vol-target-sweep.md` for corrected sweep results after the SLEEVE_WEIGHT fix.
See `references/numerical-audit-checklist.md` for a complete 9-category audit checklist with copy-pasteable grep/python verification commands — covers all 17 pitfalls plus Passes F–I.
See `references/pv-sleeve-capital-destruction.md` for the reproduction script and fix for the PV-sleeve capital-destruction variant of Pitfall 14.
See `references/backtest-engine-audit-cycle6.md` for the systematic audit checklist and cost interaction details from the Cycle 5/6 backtest engine audit.
See `references/maxdd-sign-convention.md` for the full MaxDD sign convention fix reproduction with file-by-file occurrence counts and verification steps.
See `references/off-by-one-allocation-lag.md` for the before/after fix reproduction of the allocation lag bug in simulate_sleeves.
See `references/sign-convention-audit-template.md` for a reusable cross-file sign audit procedure with the recursive walker and fixer script.
- **`references/pipeline-resilience-testing.md`** — Full catalog of failure nodes to test (missing files, corrupt data, NaN prices, empty inputs, zero volume, negative prices) with test patterns.
- **`references/crash-regime-testing-pattern.md`** — Recipe for crash-regime engine verification using fixed targets + cost=0, with scenario catalog (V-shape, extended bear, flash crash).
See `references/mtf-expanding-window-template.md` for a runnable expanding-window validation script when overlays show DD reduction in full-period results.
See `references/feature-reevaluation-cycle6.md` for a post-engine-fix protocol: re-evaluating all feature decisions when a backtest engine bug is discovered and fixed.

## Related Skills

### 19. Crash-Regime Verification — Use Fixed Targets + cost=0

**Symptom:** Crash-regime tests (V-shape dip, extended bear, 2022-style grind) show implausibly small drawdowns (-5% to -10%) despite synthetic price declines of -35% to -50%.

**Cause:** The TS MOM trend signal requires 100+ days of warmup and a clear uptrend to produce target_b > 0. Synthetic crash data often lacks enough pre-crash trend history for the signal to fire, so the strategy stays flat during the crash. The combined NAV (`result["nav"]`) also dilutes single-asset DD via multi-sleeve summation (5 sleeves × 0.20 base).

**Fix:** Use fixed targets (`target_b=1.0`, always long) and `cost=0.0` for engine verification tests. This isolates engine resilience from signal timing and cost artifacts:
```python
targets = pd.DataFrame(
    {"target_a": 0.0, "target_b": 1.0, "target_c": 0.0,
     "target_p": 0.0, "target_pv": 0.0},
    index=dates,
)
result = simulate_sleeves(targets, pair_opens, pair_closes,
                          pair=pair, cost=0.0)
```
For tests needing asset-level DD, use `result["sleeve_b"]` directly instead of `result["nav"]`.
See `references/pipeline-resilience-testing.md` for the full failure-node catalog and test patterns.
See `references/production-security-audit-patterns.md` for recurring security and error-propagation patterns found in production pipeline audits — append-overwrite anti-pattern, crash-after-write, config secrets, HTML XSS, subprocess code injection, non-atomic writes. Includes copy-pasteable grep commands for each check.
See `references/production-gap-coverage-testing.md` for the TDD gap-coverage workflow with monkeypatching patterns for production file-I/O code.
See `references/crash-regime-testing-pattern.md` for the full recipe with scenario catalog.

### 20. Cross-Frequency NAV Combination — Grid Mismatch Inflates CAGR

**Symptom:** When combining NAV series from two backtests that use different trading calendars (e.g., crypto 365-day vs stocks 252-day), the combined metrics show CAGRs that are implausibly high — 5-10pp above the standalone full-period CAGRs for the same strategies. The overlap period's "years" calculation shows fewer years than the calendar span (e.g., 2.8 years vs 4.0 calendar years).

**Cause:** The crypto NAV is indexed on every calendar day (365/year) while the stock NAV is indexed only on trading days (~252/year). When you intersect the two date indices, the result has only ~1005 dates over 4 calendar years. Crypto returns computed on this intersected grid span multi-day gaps (e.g., Friday→Monday covers 3 calendar days), producing larger per-observation returns. When these larger returns are annualized with 365 (or even 252), the CAGR is inflated because `mean(log_return) * annualization_factor` overstates the true annual rate.

**Detection:** Print the standalone strategies' full-period CAGRs (using their native grids and annualization) and compare to the overlap-period CAGRs. If the overlap-period CAGRs are higher than standalone full-period CAGRs by >3pp for a strategy whose full period includes the overlap, the grid is wrong. Also check: `len(intersection_dates) / 365` should roughly equal the calendar year span. If it's significantly less, you're on a sparse grid.

**Fix — use the lower-frequency grid as the reference, forward-fill the higher-frequency asset:**

```python
# Determine overlap
common_start = max(crypto_nav.index[0], stocks_nav.index[0])
common_end = min(crypto_nav.index[-1], stocks_nav.index[-1])

# Use stock trading days (lower frequency) as reference grid
stock_dates = stocks_nav.loc[common_start:common_end].index
crypto_on_stock_dates = crypto_nav.reindex(stock_dates, method="ffill")
stocks_on_stock_dates = stocks_nav.loc[common_start:common_end]

# Drop dates where forward-fill couldn't reach (before crypto start)
valid = crypto_on_stock_dates.notna() & stocks_on_stock_dates.notna()
crypto_aligned = crypto_on_stock_dates[valid]
stocks_aligned = stocks_on_stock_dates[valid]

# Normalize both to 1.0 at common start
crypto_aligned = crypto_aligned / crypto_aligned.iloc[0]
stocks_aligned = stocks_aligned / stocks_aligned.iloc[0]

# Use the reference grid's annualization factor (252 for stocks)
ann_days = 252
```

**Why forward-fill is correct for crypto:** Crypto trades 24/7. On a stock trading day (e.g., Tuesday), the crypto NAV at the stock's close time is just the crypto's most recent value — forward-fill captures this correctly. On weekends, there's no stock close to sample against, so skipping those dates is fine — the combined portfolio only needs valuation on days when both components can be priced.

**Verification:** After the fix, the overlap-period standalone CAGRs should closely match the full-period standalone CAGRs (±2pp is normal due to different sub-periods). The "years" calculation should match the calendar span (e.g., 1005 trading days / 252 ≈ 4.0 years).

**Anti-pattern — using date intersection:**
```python
# WRONG: intersection produces a sparse grid
common_idx = crypto_idx.intersection(stocks_idx)  # ~1005 dates
crypto_rets = crypto_nav[common_idx].pct_change()  # multi-day gaps!
```

### 21. Pipeline Resilience — Test Every Failure Node

Every production pipeline component must handle missing data, corrupt files, empty inputs, NaN prices, negative prices, zero volume, and single-data-point edge cases without crashing. Construct these tests as unit tests that monkeypatch the failing component rather than creating real corrupt files.

See `references/pipeline-resilience-testing.md` for the full failure-node catalog and test patterns.
See `references/production-security-audit-patterns.md` for recurring security and error-propagation patterns found in production pipeline audits — append-overwrite anti-pattern, crash-after-write, config secrets, HTML XSS, subprocess code injection, non-atomic writes. Includes copy-pasteable grep commands for each check.
See `references/production-gap-coverage-testing.md` for the TDD gap-coverage workflow with monkeypatching patterns for production file-I/O code.
See `references/crash-regime-testing-pattern.md` for the full recipe with scenario catalog.
**Symptom:** An overlay (MTF filter, regime filter, funding fade) shows impressive DD reduction in full-period results (e.g., -8pp DD, +0.13 Sharpe), but expanding-window validation reveals the entire benefit comes from ONE regime (typically a crash event that enters the window only after a certain date).

**Cause:** Full-period statistics aggregate across all regimes. An overlay that filters out positions during one bear market looks great in aggregate but destroys CAGR during all the bull markets that made up the rest of the period. The DD reduction is real but not structural — it depends on one event being in-sample.

**Detection — expanding window decomposition:**

Run the overlay against expanding windows (1yr, 1.5yr, 2yr, 2.5yr, 3yr, 3.5yr, 4yr) and compare DD reduction per window:

```
| Window |   B DD | MTF DD | ΔDD   |
|--------|-------:|-------:|:-----:|
| W1 1yr |  -9.4% |  -9.9% | -0.5pp | ← bull market: ZERO benefit
| W2 1.5 | -12.1% | -13.6% | -1.5pp | ← still no crash in window
| W3 2yr | -23.8% | -16.9% | +6.9pp | ← 2022 crash enters: benefit appears!
| W4 2.5 | -24.3% | -17.1% | +7.3pp |
| W5 3yr | -25.0% | -17.1% | +8.0pp |
| W6 3.5 | -25.0% | -17.1% | +8.0pp |
| W7 4yr | -25.0% | -17.1% | +8.0pp |
```

The DD reduction jumps from ~0pp to ~7pp ONLY after W3 (when the 2022 crash enters the window). Before that, in pure bull markets (W1-W2), the overlay provides ZERO drawdown benefit while costing -12% to -22% CAGR.

**Decision rule:** If the DD reduction is < 2pp in windows that DON'T include a crash event, the overlay is not providing structural risk reduction — it's crash-timing one event, at the cost of destroying returns during trend regimes. REJECT unless you're explicitly optimizing for that specific crash recurrence.

**When to use expanding windows for overlay validation:**
- After ANY overlay shows >2pp DD reduction in full-period results
- Before accepting an overlay that passes full-period gate (e.g., "correlation sizing: ACCEPTED")
- When the full-period DD reduction seems too good to be true compared to the CAGR cost

**Pattern:** Write a standalone expanding-window script that runs the overlay against progressively larger windows and prints per-window B, overlay, ΔCAGR, and ΔDD. See `references/mtf-expanding-window-example.md` for a runnable template.
