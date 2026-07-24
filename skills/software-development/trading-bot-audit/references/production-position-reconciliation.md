# Production Position Reconciliation Pattern

## Problem

A daily signal-generation pipeline that produces buy/sell signals for all pairs
without awareness of which positions are currently open. Every day, the bot
would "buy" every pair with a signal — even if already holding it. This causes:

- Phantom re-buys: positions opened on day 1 are "re-bought" on day 2
- No exit tracking beyond signal-loss threshold
- Inflated position sizing from duplicate entries
- Trade history drifts from actual open positions

## Solution: Four-State Reconciliation

Read open positions from `trade_history.json` before generating orders.
For each pair, check both the current signal AND whether the pair is
already held:

| Already Held? | Signal Active? | Action |
|:---:|:---:|:---|
| No | Yes | **ENTRY** — new position with stake sizing |
| Yes | Yes | **HELD** — maintain, no re-buy, stake=0 in order |
| Yes | No | **EXIT** — signal lost, generate explicit close |
| No | No | No action (no_signal) |

## Helper: `_get_open_positions()`

```python
def _get_open_positions() -> set[str]:
    """Return set of pairs currently held (from trade_history.json)."""
    if not TRADE_HISTORY_PATH.exists():
        return set()
    try:
        th = json.loads(TRADE_HISTORY_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return set()
    return {op["pair"] for op in th.get("open_positions", []) if op.get("pair")}
```

## Integration Into Signal Loop

```python
open_positions = _get_open_positions()

for pair, sig in targets.items():
    already_held = pair in open_positions

    if stoploss_hit:
        positions[pair] = {"side": None, "stake": 0, "reason": "STOPLOSS"}
    elif already_held and sig["target"] > ENTRY_THRESHOLD and sig["trend"]:
        positions[pair] = {"side": "long", "stake": 0, "reason": "HELD"}
    elif already_held and not (sig["target"] > ENTRY_THRESHOLD and sig["trend"]):
        positions[pair] = {"side": None, "stake": 0, "reason": "EXIT"}
    elif not already_held and sig["target"] > ENTRY_THRESHOLD and sig["trend"]:
        stake = compute_position_size(equity, sig, num_active)
        positions[pair] = {"side": "long", "stake": stake, "reason": "ENTRY"}
    else:
        positions[pair] = {"side": None, "stake": 0, "reason": "no_signal"}
```

## Why Not "net" Orders?

A naive approach would be to compute "net" orders (target - current = order size).
This breaks for multi-strategy pipelines where multiple strategy sleeves each own
their own capital. A net order would conflate sleeve accounting.

The reconciliation approach keeps each strategy's capital distinct: Strategy A
might hold BTC while Strategy B doesn't, and the pipeline needs to know which
strategy's holdings are which. For single-strategy pipelines, netting works fine.

## Pitfalls

- **`_get_open_positions()` must use the SAME trade_history.json** that the
  trade_logger writes to. Two competing history files → reconciliation misses
  positions.
- **Entry dedup key**: Use `{pair}::{entry_date}` as the position key to prevent
  the same pair being opened twice on the same day (idempotency).
- **Stale state**: If `trade_history.json` is corrupted or missing, fall back to
  treating all pairs as "not held" (no crash, just missed reconciliation).
