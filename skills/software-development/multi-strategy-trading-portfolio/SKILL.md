---
name: multi-strategy-trading-portfolio
description: >-
  Design and implement multi-strategy trading portfolios on a single account.
  Covers master allocator architecture, capital allocation between strategies
  (risk parity, equal, regime-dependent), conflict resolution via order netting,
  and complementary strategy selection for low correlation.
version: 1.2.0
author: Hermes Agent
tags: [trading, crypto, multi-strategy, portfolio-construction, capital-allocation, order-netting]
platforms: [windows, macos, linux]
---

# Multi-Strategy Trading Portfolio

## When to Use This Skill

Use when the user asks to:
- Run multiple trading strategies in parallel on a single account
- Combine a proven strategy with complementary ones that profit in different regimes
- Split capital between strategies (risk parity, equal, weighted)
- Resolve conflicts when two strategies want opposite trades the same day
- Evaluate whether a candidate strategy adds true diversification to an existing one

This skill bridges **single-strategy research** (what works alone) and **multi-strategy production** (how to combine what works).

## Core Principle: Strategy Sleeves (Master Allocator Pattern)

The fundamental architecture is a **master allocator** that treats each strategy as an independent capital sleeve:

```
┌──────────────────────────────────────────────┐
│                 Master Allocator               │
│  Decides: capital % per strategy (risk parity) │
│  Inputs: strategy returns (rolling 60d)         │
│  Output: strategy capital budgets               │
└──────────┬───────────────────────────┬─────────┘
           │                           │
           ▼                           ▼
┌────────────────────┐   ┌──────────────────────┐
│ Strategy A Sleeve   │   │ Strategy B Sleeve     │
│ Own capital: $600   │   │ Own capital: $250     │
│ Own signals         │   │ Own signals           │
│ Own positions       │   │ Own positions         │
└─────────┬──────────┘   └───────────┬───────────┘
           │                           │
           └─────────────┬─────────────┘
                         ▼
              ┌──────────────────────┐
              │   Order Aggregator    │
              │  ➕ Strategy A: +$100 BTC│
              │  ➖ Strategy B: -$50 BTC │
              │  ─────────────────  │
              │  Net: +$50 BTC       │
              └──────────┬───────────┘
                         ▼
                 Unified Account
```

### Why Sleeves, Not Overlays

- **Overlay** = modifying one strategy's signal with another's (e.g., "reduce TS MOM target when funding is extreme"). Tested exhaustively in Cycles 3-6 research. All overlays on TS MOM hurt CAGR.
- **Sleeve** = each strategy owns segregated capital and operates independently. They only interact at execution time via order netting.

**Rule of thumb:** If you could measure the second strategy's returns independently (as if it ran on its own account), it's a sleeve. If you can't, it's an overlay. Overlays are harder to validate; sleeves are cleaner.

## Capital Allocation Between Strategies

### Method A: Equal Weight (1/N)
- Simplest, most robust to estimation error
- Works well with 2-3 strategies (2: not diversified enough; 4+: equal weight becomes noisy)
- Use for initial deployment before live returns accumulate

### Method B: Risk Parity (Inverse Vol Weighting)
- Each strategy contributes equal portfolio risk
- Smoother equity curve, better Sharpe in theory
- Requires rolling vol estimates (60-day window minimum)

```python
def risk_parity_weights(strategy_returns: dict[str, pd.Series]) -> dict[str, float]:
    """Compute inverse-vol weighted allocation for each strategy."""
    vols = {
        name: series.ewm(span=60).std().iloc[-1] * sqrt(365)
        for name, series in strategy_returns.items()
    }
    inv_vols = {k: 1/v for k, v in vols.items() if v > 0}
    total = sum(inv_vols.values())
    return {k: v/total for k, v in inv_vols.items()}
```

**Cold-start fallback:** Use static weights (e.g. 60/25/15 for 3 strategies) until 60 trading days of live returns accumulate, then transition to risk parity gradually over 20 days.

### Method C: Regime-Dependent
- Shift allocation based on macro regime (bull → favor trend; bear → favor cash strategies)
- Most adaptive but adds parameter risk
- Only justified after 1+ year of live multi-strategy data

### Recommendation Order

| Situation | Method |
|---|---|
| First 60 days | Static weights (initial guess based on backtest Sharpe) |
| 60-250 days live | Risk parity (inverse vol weighting) |
| 250+ days live | Consider regime-dependent, but only if regime detection is itself validated OOS |

## Conflict Resolution: Order Netting

Since all strategies share one account and all positions are long-only spot, **the only conflict is the same asset being partially bought and partially sold on the same day**.

### Netting Rules (Simple)

1. Collect all strategy-level trades for each asset
2. Sum the dollar amounts (positive = buy, negative = sell)
3. Execute one market order for the net amount
4. If net = $0, do nothing

```python
def net_orders(strategy_orders: list[dict]) -> dict:
    """Net orders across strategies. Returns {pair: net_stake}."""
    net = defaultdict(float)
    for s in strategy_orders:
        for pair, order in s.items():
            if order["side"] == "long":
                net[pair] += order["stake"]
            elif order["side"] is None:
                net[pair] -= order.get("current_stake", 0)
    return {k: v for k, v in net.items() if abs(v) > 1.0}
```

### Why This Works on Spot

- Spot has only one position per asset (you're long or you're not)
- There's no concept of "Strategy A is long 0.1 BTC and Strategy B is short 0.05 BTC" — the net is long 0.05 BTC
- Per-strategy P&L must be tracked **off-chain** (in a database or JSON) since the exchange only shows one aggregated position

### Per-Strategy P&L Tracking Design

```json
{
  "strategy_a": {
    "capital": 600.00,
    "positions": {"BTC/USDT": {"stake": 350.00, "entry_price": 67000, "size_btc": 0.00522}},
    "cash": 250.00,
    "pnl_realized": 12.45,
    "pnl_unrealized": 3.20
  },
  "strategy_b": {
    "capital": 250.00,
    "positions": {"BTC/USDT": {"stake": 120.00, "entry_price": 67500, "size_btc": 0.00178}},
    "cash": 130.00,
    "pnl_realized": -2.10,
    "pnl_unrealized": 1.50
  }
}
```

Each strategy tracks its own fractional BTC holding. When executed, the trade executor must assign fills pro-rata to each strategy's order.

## Selecting Complementary Strategies

### What to Look For

| Property | Good Candidate | Bad Candidate |
|---|---|---|
| Correlation to existing | < 0.5 rolling 60d | > 0.7 (too similar) |
| Profit in | Different regime (e.g., mean reversion in chop) | Same regime (e.g., another trend strategy) |
| DD overlap | Peaks at different times | Peaks at exactly same times |
| Drawdown | Lower than existing | Higher than existing |

### Strategy Families Tested for Crypto Spot

| Family | Works? | Notes |
|---|---|---|
| Time-series momentum (SMA vote + vol scaling) | ✅ Validated | Best config: 20/50/100 vote ≥ 2, Parkinson vol target 0.30, no overlays |
| Portfolio-level vol targeting | ❌ NO-GO (tested) | 2024 OOS: existing per-asset vol scaling already keeps portfolio vol below target. Portfolio-level scalar never engages — correlation 0.997-1.0. Redundant layer. |
| SRR Statistical Range Recovery (5th %ile of 60d) | ❌ NO-GO (tested) | 2024 OOS: only 3 trades/year across 5 assets. 20% cash sleeve mechanically halves CAGR and MaxDD equally — Sharpe flat. Signal too sparse on daily large-cap crypto. |
| Regime cash management (SMA50/SMA100 on BTC) | 🔬 Untested | Faster crash exit than TS MOM (which uses 20/50/100d). Needs verification. |
| Cross-sectional relative strength | ❌ Failed | 84d leadership underperformed equal-weight. Shorter lookbacks unverified. |
| Weekly TS MOM (28/84/168) | ❌ Failed | -33% vs always-long control. |
| Mean reversion (1h Bollinger) | ❌ Failed | -16% to -36% across variants. |
| Grid breakout (Donchian) | ❌ Failed | Best PF 1.04, p=0.82 — noise. |
| Funding rate fade overlay | ❌ Hurt returns | -5.6% C-minus-B across 6-cycle research. |
| OI divergence overlay | ❌ Hurt returns | Aggressive reduction fires too often in strong trends. |

### Equity Trend-Following Variants (Parameter Sweep, 30 variants)

The same base TS MOM logic was ported to equities (8 US ETFs, 2000-2026). Key differences from crypto:

| Equity Variant | CAGR | Max DD | Calmar | Notes |
|---|---|---|---|---|
| **sma_252_binary** (close > 252d SMA) | **+8.73%** | -27.5% | 0.317 | Only variant that beats SPY B&H (+8.25%). AQR 12mo lookback. |
| **golden_cross** (SMA50 > SMA200, vt=0.12) | +7.22% | -16.5% | **0.437** | Best risk-adjusted. 3× B&H Calmar. |
| **vote_100_200_300** (vote≥2, vt=0.12) | +6.79% | -16.7% | 0.406 | Balanced, lowest vol. |
| **vote_50_100_200** (vote≥2, vt=0.12) | +4.81% | -18.6% | 0.258 | Similar pattern to crypto's 20/50/100 but shifted right by 30d. |
| **vote_20_50_100** (vt=0.12) | +3.85% | -21.4% | 0.180 | Crypto's baseline — fails for equities (-4.4pp vs B&H). |

**Key insight:** Crypto uses shorter lookbacks (20/50/100d) because trends are faster and more pronounced. Equities need longer lookbacks (252d single SMA or 100/200/300 vote) to filter noise. The close-to-close cost model for equities is also critical — see Pitfall #8.

See `references/equity-ts-mom-parameter-sweep.md` for full sweep results.

### Most Promising Multi-Strategy Combinations

Based on the comprehensive 6-cycle research:

| Combo | Expected Correlation | Rationale |
|---|---|---|
| TS MOM + Portfolio Vol Target | 0.997-1.0 | Tested 2024 OOS — PVT doesn't engage because per-asset vol scaling already does the job. No diversification benefit. |
| TS MOM + SRR (Statistical Range Recovery) | 0.0-0.2 | Tested 2024 OOS — SRR is cash 99% of year (only 3 trades). Mechanically halves CAGR and MaxDD equally — Sharpe flat. Signal too sparse to help. |
| TS MOM + Regime Cash Sleeve | 0.5-0.6 | Untested. Both trend-based but regime uses faster lookbacks on BTC only. |
| TS MOM + Relative Strength (30d rank-weighted) | 0.4-0.5 | Different mechanism (time-series vs cross-sectional). Higher risk — Cycle 4 failure. |

## Backtest Discipline for Multi-Strategy

When adding a new strategy to an existing portfolio, the validation protocol must prevent lookahead:

1. **Gate on unseen data first.** If 2021-2023 dev data is consumed, test the new strategy on 2024 alone before touching dev data.
2. **Correlation gate.** Require 60d rolling correlation < 0.7 to existing strategy. Compute on both backtest and live data.
3. **Joint backtest.** Run both strategies together with the master allocator. The combined portfolio must have higher Sharpe and lower max DD than the existing strategy alone.
4. **Bootstrap.** 20k-block bootstrap on combined vs single-strategy CAGR difference. Positive in >80% of replicates.
5. **No re-tuning.** If the new strategy fails the gate, do not tune parameters and retest on the same data.

## Research-to-Implementation Pipeline for Crypto Strategies

When developing a new complementary strategy from scratch, use this 3-stage pipeline:

### Stage 1: Research Subagent (Independent)

Dispatch a research subagent BEFORE implementation. The research subagent:
- Reviews academic literature and known strategy archetypes
- Audits all prior cycle results from the repo (Cycle 1-N research reports)
- Identifies what's genuinely untested vs what's already been closed
- Proposes concrete, falsifiable strategies with entry/exit rules

**Do NOT skip research even for "simple" ideas** — this repo has 6 cycles of prior work. Almost every simple idea (Bollinger bands, RSI 30, SMA200, funding fade, OI divergence, weekly momentum, cross-sectional) has been tried and failed.

### Stage 2: Review Meeting

When the research subagent returns:
1. Read the proposals in the main session
2. Evaluate complementarity — does the new strategy profit in a regime where the existing strategy loses?
3. Check the failure conditions — are they falsifiable? If it fails, does it close the branch?
4. Decide which proposals to implement

### Stage 3: Shared Dependency → Parallel Implementation

After review, **identify the shared dependency first**:

```
1. Shared dependency? (e.g., refactoring codebase to support multi-strategy)
   → Handle it yourself in the main session (create dirs, base classes, __init__.py)

2. Independent strategies?
   → Dispatch one implementation subagent per strategy, in parallel
```

**Key rule — DO handle the shared dependency yourself before dispatching:**
- Creating the `strategies/` directory structure and base abstract classes
- Extracting existing production logic into the new `strategies/` module
- Verifying existing code still runs after refactor
- This is usually ~10 minutes of mechanical work that saves the subagents from race conditions

**Key rule — DON'T dispatch subagents for:**
- Long-running backtests that will exceed the 600s (10 min) subagent hard timeout
- Multi-parameter sweeps (dispatch as a background terminal process instead)
- Tasks that share the same output file name (conflict risk)

### Subagent Timeout Risk for Backtesting

Crypto backtests with bootstrap CI take 3-5 minutes per single-parameter run. A subagent testing 3 parameter values × 2 variants = 6 runs × ~3 min = 18 minutes. **This will hard-timeout at 600s.**

Workarounds:
- **Option A:** Keep each implementation subagent to ONE parameter value run (single pass). File the results and let the main session decide about parameter sweeps.
- **Option B:** Use `terminal(background=true, notify_on_complete=true)` in a script subagent that runs the backtest as a shell script (no 600s limit).
- **Option C:** Structure the implementation subagent to create a Python script that can be run as a background process, then have it write results to JSON. The main session reads the JSON when the script finishes.

### Files Created Per Pipeline Cycle

```
research/
├── cycle8_portfolio_vol.py    ← Subagent A: portfolio vol target
├── cycle8_srr.py              ← Subagent B: statistical range recovery
├── cycle8_portfolio_vol_results.json
└── cycle8_srr_results.json

production/                    ← Shared refactor (done in main session)
└── strategies/
    ├── __init__.py
    ├── base.py                ← BaseStrategy abstract class
    ├── strategy_tsmom.py      ← TS MOM extracted from generate_signals.py
    ├── strategy_portfolio_vol.py  ← Future (from subagent)
    └── strategy_srr.py         ← Future (from subagent)
```

### Integrated Example

```
User: "Research and implement a drawdown recovery strategy and a portfolio vol target"

1. DISPATCH RESEARCH: Two parallel research subagents
   (Research A: drawdown recovery; Research B: multi-strategy architecture)
   → Both return proposals (~3 min)

2. REVIEW: Read both proposals in main session, select SRR + Portfolio Vol Target
   → User reviews, decides go-ahead

3. HANDLE SHARED DEP: Refactor production/strategies/ dir, base classes
   → Main session, ~10 min

4. DISPATCH IMPLEMENTATION: Two parallel implementation subagents
   (Implement A: cycle8_portfolio_vol.py; Implement B: cycle8_srr.py)
   → Both return with results JSON + stdout metrics (~3-5 min each)
```

## JSON Pipeline Integration

When adding multi-strategy to an existing single-strategy JSON pipeline (`signals.json` → `execute_trades.py`):

### Signals Format Extension

```json
{
  "generated_at": "2026-07-20T17:00:00+00:00",
  "equity": 1000.00,
  "strategies": {
    "ts_mom": {
      "weight": 0.60,
      "capital": 600.00,
      "signals": {"BTC/USDT": {"target": 0.54, "trend": true}}
    },
    "regime_cash": {
      "weight": 0.25,
      "capital": 250.00,
      "btc_regime": "bull",
      "signals": {"BTC/USDT": {"target": 1.0, "side": "long"}}
    }
  },
  "master_allocation": {
    "strategy_weights": {"ts_mom": 0.60, "regime_cash": 0.25, "port_vol_target": 0.15},
    "portfolio_exposure": 0.79,
    "cash_reserve": 210.00
  }
}
```

### Suggested File Layout

```
production/
├── generate_signals.py         ← Orchestrates all strategy generators
├── allocate_capital.py         ← NEW: risk parity weights + cash reserve
├── execute_trades.py           ← Extended: net orders, execute
├── strategies/
│   ├── __init__.py
│   ├── strategy_tsmom.py       ← Extracted from generate_signals.py
│   ├── strategy_regime_cash.py ← NEW
│   └── strategy_portfolio_vol.py ← NEW
├── signals.json                ← Extended format above
├── allocation.json             ← NEW: per-strategy budgets
└── positions.json              ← Net positions
```

## Cross-Asset Unified Portfolio (Crypto + Stocks)

When running crypto and equity strategies in the same project, they MUST share a
unified portfolio layer — NOT operate as independent silos. The pattern:

### Architecture

```
production/portfolio_manager.py   ← Single source of truth
    ├── Reads crypto state (signals.json, trade_history.json)
    ├── Reads stock state (paper_trade_history.json)
    ├── Computes combined equity, cross-asset correlation
    ├── Risk parity target weights (inverse vol per asset class)
    ├── Portfolio-level vol targeting
    ├── Drawdown circuit breaker (scale exposure as DD increases)
    └── Outputs portfolio_state.json → consumed by watchdog
```

### Risk Controls at Portfolio Level

| Control | Method | Threshold |
|---------|--------|-----------|
| Volatility targeting | Scale total portfolio to target annualized vol | 15% default |
| Drawdown circuit breaker | Reduce exposure as combined DD increases | 15%→1.0x, 25%→0.5x, 30%+→0.1x |
| Correlation scaling | Reduce higher-vol asset when cross-asset corr spikes | Corr > 0.60 → reduce crypto allocation |
| Asset class floor/ceiling | Prevent extreme concentration in one asset class | Crypto 20-60% of portfolio |
| Rebalance signal | Alert when drift exceeds threshold | 5% drift |

### Watchdog Integration

The watchdog reads `portfolio_state.json` (written by portfolio_manager.py at the
end of every pipeline run) and adds a unified portfolio check alongside individual
asset checks. This gives a single view: total equity, risk level, combined drawdown,
cross-asset correlation warning, and rebalance signals.

### Key Pitfall: Siloed Subsystems

When a project has crypto and stock bots in the same repo sharing Task Scheduler
and watchdog infrastructure, it's tempting to call it "done." But without a unified
portfolio layer, there's no awareness of:
- Total portfolio risk (are both fully invested simultaneously?)
- Cross-asset correlation (is diversification actually working?)
- Aggregate drawdown (could be worse than either individually)
- Rebalancing opportunities (one asset class outperforming)

**Rule:** If two trading subsystems share a repo and scheduler, they MUST share a
portfolio manager. This is not optional for production-grade delivery.

## Pitfalls

### 1. Confusing Sleeves with Overlays
- A sleeve has its OWN capital and makes independent decisions.
- An overlay modifies an existing signal.
- Tested overlays (funding fade, OI divergence, regime filter) ALL hurt TS MOM CAGR. Sleeves are the correct architecture for adding new strategies.

### 2. Testing Strategy Sleeves with Insufficient Signal Density
- A strategy that triggers 3-8 times per year across 5 assets may work in theory but produce zero net benefit in practice because the cash drag from waiting dominates.
- **Check signal density first:** if a strategy averages < 1 signal per asset per quarter with a 20% sleeve, the Sharpe benefit from being cash most of the time cannot exceed the CAGR cost of being 20% permanently in cash.
- Rule of thumb: rare-event strategies need at least **5-10 trades/year across the portfolio** to overcome the cash drag of their sleeve. Below that, the strategy is equivalent to holding a fixed 20% cash allocation — with complexity but no benefit.
- **Concrete test (from SRR 2024 OOS backtest):** A strategy that triggers exactly 3 trades/year across 5 assets, all profitable, will mechanically produce:
  - CAGR ≈ 50% of baseline (because 20% sleeve is cash 99% of time)
  - Max DD ≈ 50% of baseline (same mechanism)
  - Sharpe ≈ unchanged (CAGR and volatility scale together)
  - **Result:** No risk-adjusted improvement. The strategy is indistinguishable from a fixed 20% cash reserve.
- **Falsifiable test:** compute `combined_sharpe / baseline_sharpe`. If ≈ 1.0 and CAGR dropped, the strategy adds nothing.

### 3. Portfolio-Level Vol Targeting Is Redundant with Per-Asset Vol Scaling
- If each asset is already scaled by `vol_target / rolling_vol` (individual), the portfolio's combined vol is already bounded. Adding another portfolio-wide layer on top is redundant — it cannot engage because per-asset scaling already keeps each leg below portfolio target.
- **Check before implementing:** measure the 95th percentile of portfolio vol at the baseline. If it's already below the portfolio-level target, the second layer does nothing.

### 4. Assuming Low Asset Correlation Means Low Strategy Correlation
- Five crypto majors have pairwise correlation 0.6-0.9.
- Even if two strategies use different mechanisms, if they're both long-only on the same 5 assets, their returns WILL correlate during major drawdowns.
- True diversification requires different *market regimes* (strategies that profit in chop vs trends vs crashes), not just different signal math.

### 5. Order Netting at Wrong Granularity
- Net per-asset, not per-strategy-position.
- If Strategy A wants +$100 BTC and Strategy B wants -$50 BTC, net is +$50 BTC (one order).
- Do NOT execute two separate orders (buy $100, sell $50) — that wastes fees and creates settlement timing risk.

### 6. Per-Strategy P&L Accounting Drift
- When executing netted orders, fills must be attributed pro-rata to each strategy.
- Over time, rounding errors accumulate. Reconcile every 30 days by comparing:
  - Sum of per-strategy cash + position value vs actual account equity
  - If difference > 1%, adjust via a "rounding correction" entry

### 7. Premature Regime-Dependent Allocation
- Do NOT flip between allocation methods based on short-term performance.
- Minimum observation period before changing method: 60 trading days.
- Changing strategy weights weekly based on "which strategy did best last week" is just momentum-chasing and will blow up.

### 8. simulate_sleeves Cost Model Destroys Long-Duration Backtests
- `cycle5_backtest.simulate_sleeves()` charges the full per-trade cost on the **entire notional every single day**, even when the target doesn't change.
- This is fine for short crypto backtests (3-4 years, 63% CAGR, daily cost ~0.06% of NAV → ~22% annual drag, manageable). But for **equity backtests lasting 20+ years**, the cost compounds to destroy returns:
  - 10 bps/day × 6,500 trading days = ~650% in total costs on starting capital
  - A 252d SMA binary strategy with +8.73% true CAGR simulates to -99.9% over 26 years
- **Fix for long-duration or multi-asset backtests:** Build a custom simulation that:
  - Charges cost **only when the target actually changes** (`abs(new_target - old_target) * cost`)
  - Uses **close-to-close returns** (not open-to-close — captures overnight gap)
  - Tracks position fraction separately from NAV (mark-to-market each day)
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
- **Rule of thumb:** Use `simulate_sleeves()` only for crypto backtests < 5 years. For anything longer or for equities, write a custom simulation.

### 9. Subagent Timeout for Multi-Parameter Backtests
- Implementation subagents via `delegate_task` have a 600s (10 min) hard timeout.
- A backtest running 3 parameter values × 2 variants × ~3 min per run needs ~18 min — **will timeout**.
- **Fix:** Structure subagents to run ONE single-pass backtest per invocation. For parameter sweeps, write a standalone script, launch via `terminal(background=true)`, and poll for results.
- **Safest pattern:** Subagent writes the script. Main session launches it via `process(action='wait')` with a long timeout.

### 10. File-Name Collisions Between Parallel Subagents
- Two subagents writing to `research/cycle8_results.json` will overwrite each other.
- **Fix:** Give each subagent a unique output filename in the task context (e.g. `cycle8_portfolio_vol_results.json` vs `cycle8_srr_results.json`). The names must be part of the task spec, not left for the subagent to decide.

## See Also

- `references/cycle8-research-results.md` — Full 2024 OOS results for SRR and PVT, including mechanism analysis, numerical comparison to Cycle 6 baseline, bootstrap CIs, and lessons for future multi-strategy research.
- `references/equity-ts-mom-parameter-sweep.md` — 40+ equity TS MOM variants on 8 ETFs (2000-2026).

## Verification Checklist

Before deploying a multi-strategy setup:

- [ ] Each strategy generates signals independently (no shared state, no cross-calling)
- [ ] Each strategy has its own capital budget that does not change intraday
- [ ] Order netting is verified: sum of strategy orders = net executed order
- [ ] Per-strategy P&L tracks correctly when fills are pro-rated
- [ ] Correlation between strategies is < 0.7 on the most recent 60-day rolling window
- [ ] The combined portfolio has higher Sharpe and lower max DD than the best single strategy
- [ ] Cold-start capital allocation (first 60 days) is documented, not silently defaulted
- [ ] All overlays removed if historically shown to hurt CAGR (don't double-count sleeve + overlay)
