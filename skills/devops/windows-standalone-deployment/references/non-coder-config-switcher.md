# Non-Coder Config Switcher Pattern

Reusable pattern for letting non-technical users change configuration
by double-clicking a .bat file and picking a number from a menu.

## Pattern Components

### 1. Single JSON config file

Store the mutable setting in a small, well-documented JSON file:

```json
{
  "exchange": "okx",
  "pairs": ["BTC/USDT", "ETH/USDT", ...]
}
```

### 2. Python config module

A Python module that reads/writes the JSON and exposes a clean API:

```python
# config_module.py
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "settings.json"
KNOWN_OPTIONS = {
    "option_a": {"name": "Option A", "note": "Best for X"},
    "option_b": {"name": "Option B", "note": "Best for Y"},
}

def get_setting():
    return json.loads(CONFIG_FILE.read_text())["setting_key"]

def set_setting(value):
    if value not in KNOWN_OPTIONS:
        raise ValueError(f"Unknown: {value}")
    data = {"setting_key": value}
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
    return True
```

### 3. Batch menu launcher

Double-clickable .bat file with numbered choices:

```bat
@echo off
setlocal enabledelayedexpansion
set "PY=.venv\Scripts\python.exe"

:menu
cls
echo  ============================================================
echo    Config Switcher
echo  ============================================================
echo.
echo  Current setting:
"%PY%" config_module.py --get
echo.
echo    [1] Option A — Best for X
echo    [2] Option B — Best for Y
echo    [0] Cancel
echo.
choice /c 120 /n /m "  Select: "

if errorlevel 3 goto :cancel
if errorlevel 2 set "VAL=option_b" && goto :confirm
if errorlevel 1 set "VAL=option_a" && goto :confirm

:confirm
echo  Switching to: %VAL%
echo  This will: (explain what changes)
choice /c YN /m "  Proceed"
if errorlevel 2 goto :cancel

"%PY%" config_module.py --set %VAL%
if errorlevel 1 (echo [FAIL] & pause & goto :menu)

echo  [OK] Switched!
echo  Next step: (suggest action, e.g. run data download)
choice /c YN /m "  Run next step now"
if errorlevel 2 goto :done

REM Run follow-up action
"%PY%" follow_up.py

:done
echo  All done.
pause

:cancel
echo  No changes made.
pause
```

## Critical Patterns

### choice /c returns errorlevel in REVERSE order

The highest-numbered choice returns errorlevel N. Check from HIGH to LOW:

```
choice /c 1230 /n /m "Pick: "
if errorlevel 4 goto :cancel    # 0 → errorlevel 4
if errorlevel 3 goto :opt3      # 3 → errorlevel 3
if errorlevel 2 goto :opt2      # 2 → errorlevel 2
if errorlevel 1 goto :opt1      # 1 → errorlevel 1
```

Getting this wrong is the #1 .bat menu bug — option choice 2 fires the handler
for option 1 because `errorlevel >= 1` is true for both.

### setlocal enabledelayedexpansion

Required at the top of any .bat that:
- Mutates variables inside if/for blocks
- Uses `!var!` syntax (deferred expansion)

Without it, `set VAL=foo` inside an `if` block won't stick.

### Python import path for standalone scripts

The config module needs `sys.path.insert(0, str(ROOT))` before importing from
sibling modules, or users need to run it from the project root.

### Old data preservation

Never delete the user's old state when switching config. Save the new config
alongside the old one, not over it. The user can switch back.

In the exchange switcher: old `user_data/data/okx/` stays, new data goes to
`user_data/data/binance/`. Both coexist.

## Real Example: Freqtrade Exchange Switcher

See `C:\Users\kevin\Desktop\freqtrade\` for a complete implementation:

- `production/exchange_config.py` — config module with 6 supported exchanges
- `production/exchange_settings.json` — current exchange + pairs
- `SWITCH-EXCHANGE.bat` — double-click menu for non-coders

The exchange switcher demonstrates all patterns above plus:
- Validation: rejects unknown exchanges with helpful error
- Auto-creation: creates the data directory on switch
- Action prompt: offers to download data immediately after switch
- Idempotent: switching to the same exchange is a no-op
