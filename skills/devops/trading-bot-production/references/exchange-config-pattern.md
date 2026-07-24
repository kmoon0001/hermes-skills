# Exchange-Agnostic Data Layer Pattern

Reusable architecture for making a trading/integration project exchange-agnostic.

## Problem

A production codebase has the exchange name hardcoded in 7+ files:
- Data directory paths (`user_data/data/okx/`)
- API calls (`--exchange okx`)
- Display strings (`print("Exchange: OKX")`)
- File lookups (`path = ROOT / "data" / "okx" / f"{symbol}.feather"`)

Switching exchanges means finding and updating every occurrence — error-prone,
especially for non-technical users.

## Solution

Create a single configuration module that every file imports from:

```
production/exchange_config.py:
  get_exchange()       → "okx" / "binance" / "kraken" etc.
  get_data_dir()       → Path to user_data/data/<exchange>/
  get_pairs()          → list of trading pairs
  get_exchange_name()  → display name ("OKX", "Binance")
  set_exchange(name)   → writes exchange_settings.json, creates data dir
  list_supported()     → dict of metadata for all supported exchanges
  --set, --get, --list → CLI for scripts and batch files
```

Persist the current exchange in `production/exchange_settings.json`:
```json
{"exchange": "okx", "pairs": ["BTC/USDT", "ETH/USDT", ...]}
```

## Implementation Steps

### 1. Create the config module

- Define EXCHANGE_INFO dict with name, class_name, supported flag, note, url, default_pairs
- getters read from JSON, fall back to defaults if file missing/corrupt
- set_exchange() validates against EXCHANGE_INFO, creates data directory, prints next steps
- CLI supports --set, --get, --list, --data-dir, --pairs

### 2. Update all production files

Find every file with hardcoded exchange references:

```bash
grep -rn '"okx"\|/okx' production/ --include="*.py" | grep -v exchange_config
```

For each file, replace:
- `ROOT / "user_data" / "data" / "okx"` → `get_data_dir()`
- `["BTC/USDT", ...]` → `get_pairs()`
- `"--exchange", "okx"` → `"--exchange", EXCHANGE`
- `"Exchange:   OKX"` → `f"Exchange:   {get_exchange_name()}"`

Add `import sys; sys.path.insert(0, str(ROOT))` before the import from production.exchange_config in files that run standalone (watchdog.py, validate_data.py).

### 3. Create the non-coder switcher

Build `SWITCH-EXCHANGE.bat`:
1. Show current exchange via `python exchange_config.py --get`
2. List numbered exchanges via `python exchange_config.py --list`
3. User picks number → `python exchange_config.py --set <name>`
4. Offer to download fresh data
5. Old data preserved (not deleted)

### 4. Verify

```bash
# Confirm no hardcoded exchange names remain in production code
grep -rn "'okx'\|'binance'\|'kraken'" production/ --include="*.py" | grep -v exchange_config

# Verify config module works standalone
python production/exchange_config.py --get
python production/exchange_config.py --list
python production/exchange_config.py --set binance  # test switch
python production/exchange_config.py --set okx      # switch back

# Run test suite
python -m pytest tests/ -q
```

## What changes vs what stays

| Changes | Stays the same |
|---------|---------------|
| Data directory path | Trading pairs (BTC/USDT etc. are universal) |
| Download source (Freqtrade CCXT) | Strategy logic (OHLCV-agnostic) |
| Display labels | Stock trading (separate system) |
| | Tests (pass regardless of data source) |

## Pitfalls

1. **sys.path for standalone scripts:** Files like watchdog.py that run via `python production/watchdog.py` don't have the project root on sys.path. Must add `sys.path.insert(0, str(ROOT))` before any `from production.xxx import` statement. Forgetting this causes `ModuleNotFoundError: No module named 'production'`.

2. **Don't change research files:** Research backtest scripts may hardcode exchange paths for historical data. These are NOT production code and should NOT be refactored — add a comment noting they use fixed historical data.

3. **Test files may reference exchange paths:** If tests create mock data at hardcoded paths, they need updating too. Run `grep -rn \"okx\" tests/` to check.

4. **Config drift with Freqtrade:** The `user_data/config.json` has `"name": "okx"` in the exchange section. This controls Freqtrade's CCXT connection. The exchange_config module should match this value. When switching exchanges, update BOTH files.

## Why this pattern works

- **Single source of truth:** One file to change, 6+ files automatically correct
- **Non-coder friendly:** Double-click batch file, pick by number, done
- **Reversible:** Old data preserved, switch back anytime
- **Validated:** Supported exchanges are white-listed, typos rejected
- **Testable:** Config module can be tested in isolation
