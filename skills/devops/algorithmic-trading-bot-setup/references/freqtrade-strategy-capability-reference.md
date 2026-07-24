# Freqtrade Strategy Capability Reference

> Authoritative source: https://www.freqtrade.io/en/stable/ — specifically the Strategy Customization, Strategy Callbacks, Advanced Strategy, Stoploss, and FreqAI docs.
> Last verified: 2026-07-18

This reference catalogs what is *actually* possible inside a Freqtrade strategy without fighting the framework. It covers the callback and decorator surface area, not indicator math.

---

## 1. Core Strategy Anatomy

A strategy file defines:

```python
class MyStrategy(IStrategy):
    INTERFACE_VERSION = 3  # current

    # --- Config constants ---
    timeframe = '5m'
    can_short = False
    startup_candle_count = 400
    stoploss = -0.10
    trailing_stop = False
    use_custom_stoploss = False
    use_custom_roi = False
    position_adjustment_enable = False
    max_entry_position_adjustment = -1  # unlimited

    # --- Mandatory vectorized methods ---
    def populate_indicators(self, dataframe, metadata) -> DataFrame: ...
    def populate_entry_trend(self, dataframe, metadata) -> DataFrame: ...
    def populate_exit_trend(self, dataframe, metadata) -> DataFrame: ...
```

**Key constraint for `populate_*` methods:** They receive the full dataframe at once during backtesting. Use vectorized operations (`df.loc[...]`, `df.shift()`), never `df.iloc[-1]` (safe only in callbacks). See lookahead-analysis and recursive-analysis commands for bias detection.

---

## 2. Custom Exit Signal — `custom_exit()`

```python
def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
```

Called every bot iteration (≈5s live) for each open trade until closed. Return a string (named exit reason) or `True` to exit, `None` to do nothing.

**Can branch on:**
- `current_profit` — profit ratio
- `trade.open_date_utc` — time-based exits (e.g., "unclog" after 1d at loss)
- `trade.enter_tag` — exit differently per entry signal
- `trade.get_custom_data('key')` — custom state persisted across bot restarts
- Last candle indicators via `self.dp.get_analyzed_dataframe(pair, self.timeframe)`

**Limitations:**
- Not called if `use_exit_signal = False`
- Do NOT use as a proxy for stoploss — `custom_stoploss()` supports exchange-level stoploss orders
- Rate-based exits in backtesting can be imprecise

---

## 3. Custom Stoploss — `custom_stoploss()`

```python
use_custom_stoploss = True

def custom_stoploss(self, pair, trade, current_time, current_rate,
                   current_profit, after_fill, **kwargs) -> float | None:
```

Return a float (ratio relative to `current_rate`, e.g. `-0.05` = 5% below). Return `None` = no change. The traditional `stoploss` value serves as absolute lower bound.

**Capabilities (all from official docs):**

| Pattern | Example |
|---|---|
| Time-based trailing | First 60min: 10%, after 120min: 5% |
| Per-pair | ETH/BTC → 10%, LTC/BTC → 5% |
| Stepped profit | >40% profit → 25% above open; >25% → 15% above |
| Indicator-based (absolute price) | `stoploss_from_absolute(parabolic_sar_price, current_rate, ...)` |
| ATR trailing | `stoploss_from_absolute(current_rate + (side * candle["atr"] * 2), ...)` |
| After-fill widening | `after_fill=True` param (if function signature includes it) allows widening stoploss after DCA fill |
| Leverage-aware | Multiply return by `trade.leverage` on futures |

**Helper functions:**
- `stoploss_from_open(open_relative_stop, current_profit, is_short, leverage)` — express stoploss relative to *entry* price instead of current price
- `stoploss_from_absolute(stop_price, current_rate, is_short, leverage)` — absolute price → relative ratio

**Constraint:** Stoploss can only ever move upward (tighter), except in `after_fill=True` calls.

---

## 4. Position Adjustment / DCA — `adjust_trade_position()`

```python
position_adjustment_enable = True

def adjust_trade_position(self, trade, current_time, current_rate, current_profit,
                          min_stake, max_stake, entered_stake_after_adjust, **kwargs):
```

Called every bot iteration per open trade. Return:
- **Positive `stake_amount`** → add to position (buy more on long, sell more on short)
- **Negative `stake_amount`** → partial exit
- **Tuple** `(stake_amount, "tag")` to label the adjustment order
- `None` or 0 → no action

**Critical guards needed to avoid infinite re-entries (called every ~5s live):**
```python
# Check for existing open orders before adding
if trade.has_open_orders:
    return None
# Check last filled order time
last_fill = trade.select_filled_orders(trade.entry_side)[-1].order_filled_timestamp
if current_time - last_fill < timedelta(hours=1):
    return None
```

**Limitations:**
- Backtest calls once per candle; live can call many times per candle → divergence possible
- Cannot change leverage on adjustments
- `max_entry_position_adjustment` caps additional entries (default -1 = unlimited)
- Many adjustments = higher memory usage; avoid 100+ orders on long-lived trades

---

## 5. Dynamic / Custom ROI — `custom_roi()`

```python
use_custom_roi = True

def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs) -> float | None:
```

Returns a minimum profit threshold (ratio, e.g. `0.05` = 5%). Competes with `minimal_roi` — whichever is lower triggers exit.

| Pattern | Example |
|---|---|
| Per-side | Long → 5%, Short → 2% |
| Per-pair | BTC → 2%, ETH → 3%, default → 1% |
| Per-entry-tag | breakout → 8%, reversion → 3% |
| Indicator-based | `atr / close` as dynamic target |

---

## 6. Informative Pairs — Two Approaches

### Approach A: `@informative()` decorator (preferred)

```python
from freqtrade.strategy import IStrategy, informative

class MyStrategy(IStrategy):
    # Same-timeframe higher timeframe
    @informative('1h')
    def populate_indicators_1h(self, dataframe, metadata):
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    # External pair (BTC dominance) — automatically named btc_usdt_rsi_1h
    @informative('1h', 'BTC/{stake}')
    def populate_indicators_btc_1h(self, dataframe, metadata):
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    # Cross-pair
    @informative('1h', 'ETH/BTC')
    def populate_indicators_eth_btc_1h(self, dataframe, metadata):
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    # Custom column format
    @informative('1h', 'BTC/{stake}', '{column}_{timeframe}')
    def populate_indicators_btc_custom(self, dataframe, metadata):
        dataframe['rsi_upper'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe
```

Column naming auto-format: `{base}_{quote}_{column}_{timeframe}` (with asset) or `{column}_{timeframe}` (without asset). Supports `{BASE}`, `{QUOTE}`, `{asset}`, `{column}`, `{timeframe}`, `{stake}`.

### Approach B: Manual `informative_pairs()` + `merge_informative_pair()`

Use when the decorator is too limiting (need to chain informative pairs).

```python
def informative_pairs(self):
    return [
        ("ETH/USDT", "5m", ""),           # default candle type
        ("ETH/USDT", "5m", "spot"),        # force spot candles
        ("BTC/TUSD", "15m", "futures"),    # futures candles
        ("BTC/TUSD", "15m", "mark"),       # mark candles
        ("PAIR", "1h", "funding_rate"),    # funding rate data
    ]
```

Then use `merge_informative_pair()` in `populate_indicators()` to combine timeframes safely.

### DataProvider — runtime data access

```python
# Available in populate_indicators (not populate_entry_trend)
self.dp.ticker(pair)           # current ticker (bid/ask/last/etc.)
self.dp.funding_rate(pair)     # current funding rate
self.dp.orderbook(pair, 1)     # best bid + ask
self.dp.current_whitelist()    # dynamic whitelist (VolumePairlist)
self.dp.market(pair)           # fees, limits, precisions, activity
self.dp.get_analyzed_dataframe(pair, timeframe)  # analyzed df + timestamp
```

### External data (Fear & Greed, etc.)

Not built in, but fetchable at startup/loop-start:

```python
# In bot_start() or bot_loop_start() — works live/dry but NOT during backtesting
import requests
self.fear_greed = requests.get("https://api.alternative.me/fng/?limit=1").json()
```

---

## 7. FreqAI — ML Integration

FreqAI is a parallel training/inference pipeline, not just a callback. It trains models on feature sets derived from indicators.

### Feature Engineering Functions

| Function | Auto-expands across |
|---|---|
| `feature_engineering_expand_all()` | `indicator_periods_candles` × `include_timeframes` × `include_shifted_candles` × `include_corr_pairs` |
| `feature_engineering_expand_basic()` | `include_timeframes` × `include_shifted_candles` × `include_corr_pairs` (no period expansion) |
| `feature_engineering_standard()` | Nothing — final pass for non-expanded features |
| `set_freqai_targets()` | Required — defines what the model predicts |

**Convention:** Features prefixed with `%`, targets with `&`.

### Config expansion example
```json
{
  "freqai": {
    "feature_parameters": {
      "include_timeframes": ["5m", "15m", "4h"],
      "include_corr_pairlist": ["ETH/USD", "LINK/USD", "BNB/USD"],
      "label_period_candles": 24,
      "include_shifted_candles": 2,
      "indicator_periods_candles": [10, 20]
    }
  }
}
```
A single `%-rsi-period` feature with the above config produces **108** feature columns: 3 timeframes × 3 corr pairs × 2 shifts × 2 periods × 3 base features in the example.

### Built-in prediction models
LightGBM, XGBoost, CatBoost, Reinforcement Learning (PyTorch), classifiers, regressors, CNN.

### Outlier detection
- **SVM:** `use_SVM_to_remove_outliers: true` — trains on feature space boundaries
- **DBSCAN:** `use_DBSCAN_to_remove_outliers: true` — unsupervised clustering
- **Dissimilarity Index:** `DI_threshold` — measures how far predictions are from training data

### Limitations
- Cannot combine with dynamic `VolumePairlist` (pairs arriving mid-run lack training data)
- Requires `requirements-freqai.txt` extra install (or `:freqai` docker tag)
- GPU available via `:freqaitorch`, `:freqairl` docker tags

---

## 8. Other Callbacks (Quick Reference)

| Callback | Trigger | Purpose |
|---|---|---|
| `bot_start()` | Startup once | Fetch external data (Fear & Greed, macro) |
| `bot_loop_start()` | Every iteration (live) | Per-loop init, remote data refresh |
| `custom_stake_amount()` | Before each entry | Dynamic position sizing; return 0 to skip trade |
| `confirm_trade_entry()` | Before placing entry order | Last chance to abort |
| `confirm_trade_exit()` | Before placing exit order | Can block stoploss — risky |
| `custom_entry_price()` | Entry order placement | Set limit price (e.g., BB lower band) |
| `custom_exit_price()` | Exit order placement | Set limit exit price (e.g., BB upper band) |
| `check_entry_timeout()` | Every open entry order | Custom cancellation logic |
| `check_exit_timeout()` | Every open exit order | Custom cancellation logic |
| `adjust_entry_price()` | Open entry order | Modify price of existing limit order |
| `order_filled()` | Order fills | Logging, set custom data |
| `leverage()` | Before entry | Per-pair/side leverage selection |
| `plot_annotations()` | Chart rendering | Return area/line/point annotations for FreqUI |

### Persistent custom data
```python
# Store per-trade state across bot restarts
trade.set_custom_data(key='entry_type', value='breakout')
trade.get_custom_data(key='entry_type', default=None)
```
Data must be JSON-serializable. Use simple types (bool, int, float, str). Avoid storing large blobs.

---

## 9. What Is NOT Possible (Without Fighting the Framework)

| Can't do | Why |
|---|---|
| Access incomplete candles | Freqtrade does not expose repainting data |
| Use `.iloc[-1]` in `populate_*` methods | Only safe in callbacks via `get_analyzed_dataframe()` |
| Loop-based row processing in `populate_*` | Must use vectorized pandas operations |
| Dynamic pairlists with FreqAI | Training data missing for mid-run pairs |
| External API calls replay in backtesting | `bot_loop_start()` APIs won't return historic data |
| Conflicting `enter_long` + `exit_long` on same candle | Signal collision = ignored entry |
| Leverage changes mid-trade | Fixed at entry |
| Old `custom_info` dict persisted across restarts | Deprecated; use `trade.set_custom_data()` instead |

---

## 10. Strategy Template Command

```bash
freqtrade new-strategy --strategy MyStrategy --template advanced
```

The `--template advanced` flag generates a strategy file with all callback methods pre-stubbed.
