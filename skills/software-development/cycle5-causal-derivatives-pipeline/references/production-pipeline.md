# Cycle 6 Production Pipeline Reference

## Architecture

```
Daily cron (10:00 PT)
  └── run_cycle6_full.sh
      ├── generate_signals.py
      │   ├── Download latest 1d OHLCV from OKX via `freqtrade download-data`
      │   ├── Import research.cycle6_backtest functions:
      │   │   - compute_trend_mom(close, windows=(20,50,100), vote=2)
      │   │   - compute_parkinson_volatility(high, low, window=21)
      │   │   - compute_vol_scale_from_parkinson(vol, target=0.15)
      │   └── Output: production/signals.json
      │       └── Per-pair: {target, trend, mom_vote, vol_scale, trend_started, trend_ended}
      │
      ├── execute_trades.py
      │   ├── Read signals.json
      │   ├── Position sizing: target × equity × (1/active_positions)
      │   ├── Per-position cap: 20% of equity
      │   ├── Output: production/positions.json
      │   └── Dry-run: log only. Live: execute via CCXT
      │
      ├── trade_logger.py
      │   ├── Reads positions.json and previous trade_history.json
      │   ├── Detects new entries and exits (compares current vs last known positions)
      │   ├── Fetches current prices from OHLCV feather data
      │   ├── Tracks: equity curve, per-trade P&L, open positions with unrealized P&L
      │   ├── Idempotent: re-running same day skips without duplicates
      │   └── Output: production/trade_history.json
      │       └── {equity_history, trades, open_positions}
      │
      └── check_alerts.py
          ├── Reads trade_history.json + signals.json + positions.json
          ├── Drawdown check: warning at 25%, critical at 30%
          ├── Signal change detection: new entries, exits, vote shifts
          ├── Stale data check: signals older than 36h
          └── Output: production/alert_log.json (rolling last 100 alerts)

Monitor cron (every 6h)
  └── check_alerts.py (standalone — same script, just signal/saleness checks)
```

## Key Files

| File | Purpose |
|------|---------|
| `production/generate_signals.py` | Daily signal computation |
| `production/execute_trades.py` | Position sizing and execution |
| `production/trade_logger.py` | P&L tracking with trade history and equity curve |
| `production/check_alerts.py` | Drawdown thresholds, signal change detection, staleness |
| `production/monitor_status.py` | Dashboard showing equity, P&L, drawdown, positions, trade history |
| `production/run_cycle6_full.sh` | Full pipeline runner (all 4 steps in sequence) |
| `production/signals.json` | Current live signals (auto-generated) |
| `production/positions.json` | Current position sizing (auto-generated) |
| `production/trade_history.json` | Running trade history and equity curve (auto-generated) |
| `production/alert_log.json` | Rolling alert log (auto-generated) |
| `user_data/config.json` | Freqtrade config (OKX, USDT pairs, dry-run) |

## Research-to-Production Import Pattern

The signal generator imports research functions directly to avoid formula drift:

```python
sys.path.insert(0, str(ROOT))
from research.cycle6_backtest import (
    compute_parkinson_volatility,
    compute_trend_mom,
    compute_vol_scale_from_parkinson,
)

# Data must be prepared with proper index before calling research functions
df = pd.read_feather(path)
df["date"] = pd.to_datetime(df["date"], utc=True)
df = df.sort_values("date").set_index("date", drop=False)

close = df["close"]
high = df["high"]
low = df["low"]

df["trend"] = compute_trend_mom(close)
df["parkinson_vol"] = compute_parkinson_volatility(high, low)
df["vol_scale"] = compute_vol_scale_from_parkinson(df["parkinson_vol"], target=0.15)
df["target_b"] = df["trend"].astype(float) * df["vol_scale"]
```

The research functions require:
- Timezone-aware UTC DatetimeIndex (not naive)
- Monotonically increasing, no duplicates
- `.date` column must be datetime (pd.Timestamp), not string

## Production Refactor: Strategy Module

After Cycle 6 validation, the strategy logic was extracted into a `production/strategies/` package:

```python
# production/strategies/__init__.py
from .base import BaseStrategy
from .strategy_tsmom import TSMOMStrategy

# production/strategies/base.py
class BaseStrategy(ABC):
    """Each strategy produces per-pair {target, side} dicts via compute_signals()."""
    name: str = "base"
    weight: float = 1.0

    @abstractmethod
    def compute_signals(self, ohlcv: dict[str, pd.DataFrame]) -> dict[str, dict]:
        ...

# production/strategies/strategy_tsmom.py
class TSMOMStrategy(BaseStrategy):
    """TS MOM 20/50/100 SMA vote + Parkinson 21d vol scaling."""
    name = "ts_mom"
    # Contains compute_trend_mom, compute_parkinson_volatility, compute_vol_scale
    # as standalone functions plus the strategy class wrapping them
```

This structure makes it straightforward to add new strategies as additional files in `strategies/`.

## Import Issue with Research Package

The `run_cycle6_experiment.py` module uses both `from research import cycle6_backtest` (package import) and `from run_cycle5_experiment import validity_gates` (direct module import). This creates a circular resolution problem when importing from outside the research directory. The fix (commit b17173e):

- Change `from run_cycle5_experiment import ...` to `from research.run_cycle5_experiment import ...`
- Change `from cycle5_backtest import ...` to `from research.cycle5_backtest import ...`
- Ensure `research/__init__.py` exists
- Run from project root with `sys.path.insert(0, '.')`

## Position Sizing Logic

```python
equity = 1000  # wallet balance
tradable_equity = equity * 0.99  # tradable_balance_ratio
num_active_positions = max(1, len(active_signals))
per_position_cap = equity * 0.20  # max 20% per symbol

for pair, sig in signals.items():
    if sig["target"] > 0.15 and sig["trend"]:
        size = min(sig["target"], 1.0)
        stake = min(
            size * tradable_equity * (1.0 / num_active_positions),
            per_position_cap,
        )
        # stake is allocated
    else:
        # no position (or close existing)
```

## Concentration Cap (Research Only)

The 40% per-symbol concentration cap is implemented in `run_cycle6_experiment.py`'s `main()` function:

```python
MAX_CONCENTRATION = 0.40
nav_df = pd.DataFrame({f"s{i}": r["nav"] for i, r in enumerate(all_results)})

def _cap(df):
    d = df.ffill().bfill().fillna(1.0)
    t = d.sum(axis=1)
    w = d.div(t, axis=0).clip(upper=MAX_CONCENTRATION)
    w = w.div(w.sum(axis=1), axis=0)
    return (d * w).sum(axis=1)

combined_nav = _cap(nav_df)
```

This clips any symbol's weight to 40% and renormalizes. Applied to both the aggregate NAV and the C-minus-B sleeve comparison.

## Cron Jobs

### Daily Pipeline (10:00 PT)
- Script: `production/run_cycle6_full.sh`
- Runs: generate_signals → execute_trades → trade_logger → check_alerts
- Scheduled via Hermes cron, no-widget mode
- Workdir: repo root
- Deliver: local

### Monitor (every 6h, 0 */6 * * *)
- Script: `production/check_alerts.py` (standalone — performs signal change and staleness checks alongside drawdown monitoring)
- Runs the same script as the daily pipeline's final step, but independently
- Catches stale data between daily runs and detects signal changes faster

## Trade History Format

Stored in `production/trade_history.json`:

```json
{
  "equity_history": [
    {"date": "2026-07-19", "equity": 1000.00, "day_change": 0.0, "cum_return": 0.0}
  ],
  "trades": [
    {"pair": "BTC/USDT", "entry_date": "...", "entry_price": 60000, "exit_date": "...", 
     "exit_price": 63000, "pnl": 10.0, "return_pct": 5.0}
  ],
  "open_positions": [
    {"pair": "BTC/USDT", "entry_date": "...", "entry_price": 60000, 
     "current_price": 62000, "unrealized_pnl": 3.17}
  ]
}
```

## Alert Format

Stored in `production/alert_log.json`:

```json
{
  "alerts": [
    {"timestamp": "2026-07-19T10:00:00", "level": "info", "message": "BTC/USDT: New entry at $63,000"}
  ],
  "last_state": {
    "generated_at": "...",
    "positions": ["BTC/USDT", "ETH/USDT"],
    "signals": {"BTC/USDT": {"trend": true, "trend_started": false, ...}}
  }
}
```

Alert levels: info (entries/exits), warning (drawdown >25%), critical (drawdown >30%, stale data >36h).
