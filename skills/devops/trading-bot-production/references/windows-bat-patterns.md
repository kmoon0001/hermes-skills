# Windows Batch File Patterns for Trading Bot Launchers

These patterns were developed for the Freqtrade standalone trading system.
They work on any Windows machine with no external dependencies (no bash, no
PowerShell modules, no admin).

## Pattern 1: Menu-Driven Launcher

```batch
@echo off
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
cd /d "%PROJECT_DIR%"

set "PY=%PROJECT_DIR%\.venv\Scripts\python.exe"

:menu
cls
echo  ============================================================
echo    Title Here
echo  ============================================================
echo    [1] Option One
echo    [2] Option Two
echo    [0] Exit
echo.
choice /c 120 /n /m "  Select [0-2]: "
if errorlevel 3 goto :exit
if errorlevel 2 goto :option_two
if errorlevel 1 goto :option_one

:option_one
echo Running option one...
"%PY%" script_one.py
pause
goto :menu

:option_two
echo Running option two...
"%PY%" script_two.py
pause
goto :menu

:exit
exit /b 0
```

Key points:
- `choice /c` returns errorlevels in REVERSE order (last option = errorlevel 1)
- `setlocal enabledelayedexpansion` needed for `!var!` inside loops
- Trailing backslash strip: `if "%VAR:~-1%"=="\" set "VAR=%VAR:~0,-1%"`
- Always `cd /d` to project root so relative paths work

## Pattern 2: Retry Loop

```batch
set RETRY=0
:retry_label
set /a RETRY+=1
"%PY%" script.py arg1 arg2
if errorlevel 1 (
    echo     [FAIL] attempt %RETRY%/3
    if %RETRY% lss 3 (
        echo     Retrying in 5 seconds...
        timeout /t 5 /nobreak >nul
        goto :retry_label
    ) else (
        echo     [FAIL] all 3 attempts failed
        set FAILED=1
    )
) else (
    echo     [OK] attempt %RETRY%
)
```

Key points:
- `set /a` for arithmetic
- `lss` for less-than comparison
- `timeout /t N /nobreak >nul` for pauses (no user interrupt)
- `set FAILED=1` accumulates failure state

## Pattern 3: Timestamped Log File

```batch
for /f "tokens=1-4 delims=/:.- " %%a in ('echo %DATE%') do (
    set "DS=%%c-%%a-%%b"
)
for /f "tokens=1-2 delims=: " %%a in ('echo %TIME%') do (
    set "TS=%%a-%%b"
)
set "TS=%TS: =0%"
set "LOG_FILE=%LOG_DIR%\name_%DS%_%TS%.log"
```

Key points:
- DATE format depends on locale — this pattern works for mm/dd/yyyy
- TIME may have leading space (e.g. " 9:05") — `%TS: =0%` pads with zero
- Always create log dir first: `if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"`

## Pattern 4: SCRIPT_DIR → PROJECT_DIR Resolution

```batch
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%A in ("%SCRIPT_DIR%") do set "PROJECT_DIR=%%~dpA"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
```

This pattern goes one level UP from the script's directory.
Use when the script is in `production/` and needs the project root.
For a script at the project root, just use `%~dp0` directly.

## Pattern 5: Dual .bat / .ps1 Launcher Pair

The `.bat` file is a 4-line wrapper:
```batch
@echo off
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0SCRIPT.ps1"
if errorlevel 1 pause
```

The `.ps1` file contains the actual logic. The `.bat` exists because
double-clicking a `.ps1` opens it in Notepad by default on Windows.
The `.bat` bypasses this by calling PowerShell explicitly.

**CRITICAL:** Both files MUST stay in sync. When adding an option to
one, add it to the other. Verify with: count menu items in both files,
grep for `--strategy` values, check all Python script paths.

## Pattern 6: Choice With Confirmation

```batch
choice /c YN /m "    Proceed with switch"
if errorlevel 2 goto :cancel
if errorlevel 1 goto :confirmed
```

`choice` returns errorlevel 1 for the FIRST listed option (Y), 2 for the second (N).
Use `/m` for the prompt message, `/c` for allowed keys.

## Anti-Patterns (what NOT to do)

1. **Don't call bash scripts from `.bat`** — creates a hidden dependency.
   `production/pipeline.bat` originally called `bash run_cycle6_full.sh`.
   Fixed by rewriting pipeline.bat in pure batch.

2. **Don't hardcode exchange names** in batch files. Use `exchange_config.py`
   via `"%PY%" production/exchange_config.py --get` to read the current exchange.

3. **Don't hardcode strategy names** without a verification step.
   Always validate against `user_data/config.json` after changing strategies.

4. **Don't use `set` without `setlocal`** — environment variables leak between
   script sections. Always start with `setlocal enabledelayedexpansion`.

5. **Don't forget `cd /d`** — relative paths break when the current directory
   is wrong. Always `cd /d "%~dp0"` at the top of every batch file.
