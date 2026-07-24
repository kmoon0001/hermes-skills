---
name: windows-standalone-deployment
description: Make a Python project fully self-contained on Windows — Task Scheduler, NSSM services, .bat wrappers, one-shot installer. No admin, no cloud, no agent frameworks. Gift-ready for non-technical users.
---

# Windows Standalone Deployment

Turn any Python project into a self-contained Windows application that a
non-technical user can install with one double-click.

## When to use

- You're handing a Python project to someone who doesn't use terminals
- You need scheduled tasks but can't rely on cron/cloud/agent frameworks
- The project must survive reboots and auto-restart on crash
- The user should never need to open a command prompt

## Architecture

```
project/
├── install.bat              # One-shot: venv, pip, tasks, service
├── uninstall.bat            # Clean removal of everything
├── requirements.txt         # Pinned deps (use >= for portability)
├── production/
│   ├── watchdog.py          # Health monitor with exit codes
│   ├── watchdog.bat         # Task Scheduler wrapper (or call python directly)
│   ├── pipeline.bat         # Daily/weekly job wrapper
│   └── run_pipeline.sh      # Hardened pipeline (retry, per-step errors)
├── scripts/
│   ├── nssm.exe             # Bundled service manager (public domain)
│   └── install_service.bat  # Service installer
└── setup.bat                # Task Scheduler only (if venv exists)
```

## Windows Task Scheduler (replaces cron)

### Creating tasks without admin

Drop `/ru SYSTEM` — tasks run as the current user. No admin required.

```
schtasks /create /tn "MyApp Daily" /sc daily /st 10:00 /f /tr "path\to\python.exe path\to\script.py"
```

For hourly tasks:
```
schtasks /create /tn "MyApp Watchdog" /sc hourly /f /tr "python script.py --alert-only"
```

### Pitfall: schtasks command quoting

Do NOT use nested double quotes in the `/tr` value. Task Scheduler mangles them.
Call Python directly (not through a .bat wrapper) when possible:

```
# WRONG — nested quotes fail silently:
/tr "cmd /c ""path\to\wrapper.bat"" >> log.txt"

# RIGHT — call Python directly:
/tr "C:\path\.venv\Scripts\python.exe C:\path\script.py"
```

### Pitfall: .bat wrappers in Task Scheduler

If you must use .bat wrappers, avoid `pushd`/`popd`. Task Scheduler runs from
`C:\Windows\System32` and `pushd ".."` resolves differently. Use absolute paths
derived from `%~dp0`:

```bat
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%A in ("%SCRIPT_DIR%") do set "PROJECT_DIR=%%~dpA"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\script.py"
```

### Checking if tasks ran

Task Scheduler tasks that produce no output (like a watchdog with `--alert-only`
that exits 0 when OK) will appear to have "never run" — no log file, no output.
This is CORRECT behavior. Verify by checking a side effect (heartbeat file,
database write, etc.):

```
schtasks /run /tn "MyApp Watchdog" && sleep 15 && cat .watchdog_heartbeat
```

**Pitfall:** `schtasks /run` returns "SUCCESS: Attempted to run..." immediately,
but the task runs asynchronously. Always wait 10-20s before checking output.
If the log file never appears, create a minimal smoke test:

```
schtasks /create /tn "SmokeTest" /tr "cmd /c echo OK > C:\path\test.txt" /sc once /st 00:00 /f
schtasks /run /tn "SmokeTest" && sleep 10 && type C:\path\test.txt
```

### Verifying all tasks are configured

```bat
schtasks /query /fo list /v | findstr "TaskName" | findstr "MyApp"
schtasks /query /tn "MyApp Daily" /fo list | findstr "Next Run"
```

Last Result codes: 0=success, 1=not yet run, 267011=task created but never
triggered (normal for newly-created scheduled tasks).

## NSSM Windows Service (auto-start + auto-restart)

NSSM (Non-Sucking Service Manager) wraps any executable as a Windows service.
It's public domain — bundle `nssm.exe` in your project.

### Download URL

Pre-release for Windows 10/11:
`https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip`

Extract `win64/nssm.exe` (368KB) into `scripts/`.

### Install pattern

```bat
set "NSSM=%PROJECT_DIR%\scripts\nssm.exe"
"%NSSM%" install MyService "%PYTHON%" "-m myapp"
"%NSSM%" set MyService Start SERVICE_AUTO_START
"%NSSM%" set MyService AppExit Default Restart
"%NSSM%" set MyService AppThrottle 60000
"%NSSM%" set MyService AppNoConsole 1
"%NSSM%" start MyService
```

Key settings:
- `AppExit Default Restart` — restart on crash
- `AppThrottle 60000` — 60s delay between restart attempts
- `AppNoConsole 1` — no console window pops up

## Watchdog Pattern

A standalone Python script that checks multiple subsystems and exits with
meaningful codes. Design principles:

1. **Stdlib-only** — no project imports, works even if the main app is down
2. **Fast** — completes in <5s, suitable for hourly cron
3. **Exit codes** — 0=OK, 1=WARNING, 2=CRITICAL
4. **Silent-when-OK mode** — `--alert-only` prints nothing on OK, so Task
   Scheduler delivers nothing to logs (clean)
5. **Heartbeat file** — touch a file on every run so a dead man's switch
   can detect if the watchdog itself stopped
6. **Restart capability** — `--restart` flag to restart the main app if down
7. **State backups** — create timestamped backups of critical state files on
   every run (keep last 30, auto-rotate)

### Check functions signature

```python
def check_something() -> tuple[str, str, dict]:
    """Returns (level, message, info_dict)."""
    # level: 'ok', 'warning', 'critical', 'info'
```

### Reading external state from sub-projects

When a watchdog monitors multiple sub-systems (e.g., a stock paper trader
alongside a crypto bot), read their state files directly. Check staleness:

```python
STOCKS_FILE = ROOT / "stocks" / "paper_trade_history.json"

def check_stocks() -> tuple[str, str, dict]:
    if not STOCKS_FILE.exists():
        return "info", "No stock trade history yet", {}
    data = json.loads(STOCKS_FILE.read_text())
    last = data["snapshots"][-1]
    equity = last["equity"]
    age_days = (datetime.now() - datetime.strptime(last["date"], "%Y-%m-%d")).days
    if age_days > 10:
        return "warning", f"Stock snapshot {age_days}d old", {"age_days": age_days}
    return "ok", f"Stocks: ${equity:,.0f}", {"equity": equity}
```

### Sanity guards for bad data

When checks read external state that may have unrealistic values (e.g., test
data with a $34k position on a $1k wallet), add a sanity threshold BEFORE
the real thresholds. Without this, test data triggers false CRITICAL alerts:

```python
if concentration > 500:  # >5x equity = bad test data
    return "info", "Concentration data unavailable — needs review", info
elif concentration > 50:
    return "critical", f"Position at {concentration:.0f}% of equity", info
elif concentration > 40:
    return "warning", f"Position at {concentration:.0f}% of equity", info
else:
    return "ok", f"Max concentration: {concentration:.0f}%", info
```

Rule: highest threshold first, then descending. Sanity check must beat the
real thresholds so bad data never triggers a false alarm.

### State backup pattern

```python
def backup_state(state_path: Path, backup_dir: Path, keep: int = 30) -> None:
    if not state_path.exists():
        return
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(state_path, backup_dir / f"{state_path.stem}_{ts}.json")
    # Rotate old backups
    for old in sorted(backup_dir.glob(f"{state_path.stem}_*.json"))[:-keep]:
        old.unlink()
```

### Windows toast notifications

```python
def send_windows_toast(title: str, message: str) -> bool:
    ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, ...] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(...)
# ... set text, create toast, show
'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], ...)
```

## Pipeline Hardening

### Bash version

For daily batch jobs that run multiple steps in bash/git-bash:

```bash
set -uo pipefail  # NOT -e — we handle errors per-step

FAILED_STEPS=0

# Step with retry
MAX_RETRIES=3
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_RETRIES ]; do
    ATTEMPT=$((ATTEMPT + 1))
    if python step1.py; then
        echo "    [OK] step1 (attempt $ATTEMPT)"
        break
    fi
    if [ $ATTEMPT -ge $MAX_RETRIES ]; then
        echo "    [FAIL] step1 — all retries exhausted"
        FAILED_STEPS=$((FAILED_STEPS + 1))
    fi
    sleep 5
done

# Step without retry
if python step2.py; then
    echo "    [OK] step2"
else
    echo "    [FAIL] step2"
    FAILED_STEPS=$((FAILED_STEPS + 1))
fi

# Summary with machine-parseable markers
if [ $FAILED_STEPS -eq 0 ]; then
    echo "RESULT: PASS"
elif [ $FAILED_STEPS -lt $TOTAL ]; then
    echo "RESULT: PARTIAL"
else
    echo "RESULT: FAIL"
fi
```

Key: `[OK]`/`[FAIL]` per-step and `RESULT: PASS/PARTIAL/FAIL` at the end
so the watchdog can parse pipeline logs and report status.

### .bat version (native Windows, no bash required)

Same hardening pattern in batch. Uses `goto :label` for retry loops:

```bat
set FAILED=0

REM ── Step 1: with 3x retry ──────────────────────────────────────────
set RETRY=0
:retry_signals
set /a RETRY+=1
"%PY%" "%PROJECT_DIR%\production\generate_signals.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo     [FAIL] generate_signals attempt %RETRY%/3 >> "%LOG_FILE%"
    if %RETRY% lss 3 (
        echo     Retrying in 5 seconds... >> "%LOG_FILE%"
        timeout /t 5 /nobreak >nul
        goto :retry_signals
    ) else (
        echo     [FAIL] generate_signals — all 3 attempts failed >> "%LOG_FILE%"
        set FAILED=1
    )
) else (
    echo     [OK] generate_signals (attempt %RETRY%) >> "%LOG_FILE%"
)

REM ── Step 2: no retry ──────────────────────────────────────────────
"%PY%" "%PROJECT_DIR%\production\step2.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo     [WARN] step2 had issues >> "%LOG_FILE%"
    set FAILED=1
) else (
    echo     [OK] step2 >> "%LOG_FILE%"
)

REM ── Summary ────────────────────────────────────────────────────────
if %FAILED% equ 0 (echo RESULT: PASS) else (echo RESULT: COMPLETED WITH WARNINGS)
```

Key: the `goto :label` + counter variable pattern is the .bat equivalent of a while loop.
Use `setlocal enabledelayedexpansion` at the top for variable mutation inside blocks.
The `%RETRY% lss 3` comparison works because enabledelayedexpansion is set.

### Menu-driven one-shot launcher pattern

For projects with multiple subsystems (crypto, stocks, pipeline, watchdog, reports),
use a single .bat file with a `choice /c` menu:

```bat
:menu
cls
echo   [1] Start Crypto    [4] Pipeline
echo   [2] Run Stocks      [5] Watchdog
echo   [3] Full System     [6] Status
echo   [0] Exit
choice /c 1234560 /n /m "  Select: "

if errorlevel 7 goto :exit
if errorlevel 6 goto :status
if errorlevel 5 goto :watchdog
if errorlevel 4 goto :pipeline
if errorlevel 3 goto :full
if errorlevel 2 goto :stocks
if errorlevel 1 goto :crypto
```

**Critical pattern:** `choice /c` returns errorlevel in reverse order (highest match first).
The `if errorlevel` checks must go from HIGHEST to LOWEST number. Getting this wrong
is the #1 .bat menu bug — option 1 fires for choice 2 because both satisfy `>=1`.

**Launcher drift prevention:** When you add a new subsystem (e.g., performance_report.py),
you MUST add it to BOTH the .bat AND the .ps1 launcher. The .bat and .ps1 must stay in
lockstep. If a .bat adds option N, the .ps1 needs the same switch case.

## One-Shot Installer Pattern

```bat
@echo off
title MyApp Installer
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo [1/4] Checking Python...
python --version >nul 2>&1 || (echo Install Python 3.11+ & pause & exit /b 1)

echo [2/4] Setting up environment...
if not exist ".venv" python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

echo [3/4] Creating scheduled tasks...
schtasks /create /tn "MyApp Daily" /sc daily /st 10:00 /f /tr "..."

echo [4/4] Service (optional)...
choice /c YN /m "Install as Windows service"

echo Done.
pause
```

## Common Pitfalls

### Python import path in standalone scripts

Scripts that use `from production.util import foo` need the project root
on `sys.path` BEFORE the import:

```python
# WRONG — import fails when run standalone:
from production.util import atomic_write
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# RIGHT:
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from production.util import atomic_write
```

### requirements.txt portability

Don't ship a raw `pip freeze` dump. It pins exact versions including transitive
deps that may not resolve on different Python versions. Use `>=` pins for
direct dependencies:

```
freqtrade>=2026.6
pandas>=3.0
numpy>=2.4
```

### MSYS/Git-Bash path mangling

When a `.sh` script runs in git-bash on Windows, paths like `/c/Users/...` get
converted by MSYS. Use explicit `C:/Users/...` format or call Python directly
from Task Scheduler to avoid the bash layer entirely.

## Files

- `references/watchdog-template.py` — Reusable watchdog skeleton with all patterns (health checks, toasts, heartbeat, exit codes). Copy, add your own check functions, done.
- `references/schtasks-cheatsheet.md` — Task Scheduler command reference: create, manage, debug, quoting rules, common error codes.
- `references/non-coder-config-switcher.md` — Pattern for letting non-technical users change configuration via a double-click .bat menu (JSON config + Python module + batch menu). Real example: Freqtrade exchange switcher.
