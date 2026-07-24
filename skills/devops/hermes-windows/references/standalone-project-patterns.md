# Standalone Project Patterns

Concrete patterns for converting a Hermes-dependent project into a fully
standalone Windows deployment. Every pattern here was validated on real
Freqtrade trading bot and Copilot Studio projects (July 2026).

## 1. Windows Task Scheduler (replaces Hermes cron)

### Key learnings from battle-testing

- **Do NOT use `/ru SYSTEM`** — requires admin elevation. `schtasks /create` without
  `/ru` runs as the current user with no admin needed.
- **Do NOT use `cmd /c "wrapper.bat"` with quoted paths** — the double-quote nesting
  in `/tr` silently fails. The task creates successfully but produces no output.
- **Direct Python call works reliably:**
  ```batch
  schtasks /create /tn "Task Name" /sc hourly /f /tr "%PY% %PROJECT_DIR%\script.py --flags"
  ```
- **.bat wrappers with `pushd`/`popd` fail in Task Scheduler** — the working
  directory is `C:\Windows\System32` and `pushd ".."` resolves wrong. Use
  `%~dp0`-based absolute path resolution instead.

### Correct schtasks pattern (setup.bat)

```batch
set "PY=%PROJECT_DIR%\.venv\Scripts\python.exe"

REM Daily pipeline
schtasks /create /tn "Freqtrade Daily Pipeline" /sc daily /st 10:00 /f ^
    /tr "cmd /c %PROJECT_DIR%\production\pipeline.bat"

REM Hourly watchdog — direct Python, no .bat wrapper needed
schtasks /create /tn "Freqtrade Watchdog" /sc hourly /f ^
    /tr "%PY% %PROJECT_DIR%\production\watchdog.py --alert-only --restart --notify"

REM Weekly task
schtasks /create /tn "Freqtrade Stock Paper Trade" /sc weekly /d SAT /st 09:00 /f ^
    /tr "%PY% %PROJECT_DIR%\stocks\paper_trade.py"

REM Weekly cleanup
schtasks /create /tn "Freqtrade Log Cleanup" /sc weekly /d SUN /st 03:00 /f ^
    /tr "%PY% %PROJECT_DIR%\production\log_rotation.py"
```

**Key:** The watchdog and cleanup tasks call Python directly — no .bat wrapper needed
when the script is self-contained. For the pipeline task, `pipeline.bat` wraps `bash`
which needs `cmd /c`, but with NO nested quotes on the path.

### .bat wrapper pattern (only when needed — e.g. for bash scripts)

When you must use a .bat wrapper (calling bash, complex setup), use `%~dp0` + `%%~dpA`
for reliable parent-directory resolution:

```batch
@echo off
setlocal

REM Resolve project root from this script's location
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%A in ("%SCRIPT_DIR%") do set "PROJECT_DIR=%%~dpA"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

REM Use absolute paths everywhere — Task Scheduler cwd is unpredictable
"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\production\script.py" --flags
exit /b %ERRORLEVEL%
```

### Verifying tasks work via Task Scheduler

Trigger manually and check:
```batch
schtasks /run /tn "Freqtrade Watchdog"
REM Wait 15-20 seconds, then check heartbeat or log output
```

For silent-when-OK tasks (`--alert-only`), verify by checking the heartbeat file
timestamp — it should update after each run. Or run once with `--verbose` to see
explicit output.

## 2. NSSM Windows Service + Bundling

NSSM (Non-Sucking Service Manager) is **public domain**. You can bundle `nssm.exe`
directly in the project — no download step for the end user.

### Bundling NSSM

```bash
curl -L -o nssm.zip "https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip"
unzip -o nssm.zip "*/win64/nssm.exe"
mv nssm-*/win64/nssm.exe scripts/nssm.exe
rm -rf nssm-* nssm.zip
```

The pre-release build (2.24-101) is recommended for Windows 10+. File is ~368KB.

### Service install pattern

```batch
set "NSSM=%PROJECT_DIR%\scripts\nssm.exe"

"%NSSM%" install FreqtradeBot ^
    "%PROJECT_DIR%\.venv\Scripts\python.exe" ^
    "-m freqtrade trade --config %PROJECT_DIR%\user_data\config.json --strategy Cycle6Strategy"

"%NSSM%" set FreqtradeBot AppDirectory "%PROJECT_DIR%"
"%NSSM%" set FreqtradeBot Start SERVICE_AUTO_START
"%NSSM%" set FreqtradeBot AppExit Default Restart
"%NSSM%" set FreqtradeBot AppThrottle 60000
"%NSSM%" set FreqtradeBot AppNoConsole 1
"%NSSM%" set FreqtradeBot AppStdout "%PROJECT_DIR%\logs\freqtrade_stdout.log"
"%NSSM%" set FreqtradeBot AppStderr "%PROJECT_DIR%\logs\freqtrade_stderr.log"
"%NSSM%" set FreqtradeBot AppRotateFiles 1
"%NSSM%" set FreqtradeBot AppRotateSeconds 86400
"%NSSM%" set FreqtradeBot AppRotateBytes 10485760

"%NSSM%" start FreqtradeBot
```

### Pitfalls

- **Service runs as SYSTEM by default** — make sure log directories are writable
- **Auto-restart works** but has a throttle (AppThrottle) — rapid crash loops are dampened
- **Always include an uninstall path** — `nssm remove ServiceName confirm`
- **Test the service actually starts** — `timeout /t 5 && curl localhost:8080/api/v1/ping`

## 3. One-Shot Installer Pattern

The user should be able to double-click ONE file and have everything configured.
This means the installer handles: Python check, venv creation, pip install,
Task Scheduler setup, and optional service install.

### install.bat structure

```batch
@echo off
title App Installer
setlocal enabledelayedexpansion

REM 1. Resolve project root
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

REM 2. Check Python
python --version >nul 2>&1 || (echo Install Python 3.11+ & pause & exit /b 1)

REM 3. Create venv (skip if exists)
if not exist "%PROJECT_DIR%\.venv" python -m venv "%PROJECT_DIR%\.venv"

REM 4. Install dependencies
"%PROJECT_DIR%\.venv\Scripts\pip.exe" install --quiet -r "%PROJECT_DIR%\requirements.txt"

REM 5. Set up Task Scheduler (idempotent — delete + recreate)
schtasks /delete /tn "App Task 1" /f 2>nul
schtasks /create /tn "App Task 1" ...

REM 6. Offer service install
choice /c YN /m "Install as Windows service"
if errorlevel 1 call "%PROJECT_DIR%\scripts\install_service.bat"

REM 7. Run a quick health check
"%PROJECT_DIR%\.venv\Scripts\python.exe" watchdog.py --verbose
pause
```

### What makes it "one-shot"

- venv creation is conditional — skips if already exists
- pip install uses `--quiet` to reduce noise
- Task Scheduler creation is idempotent (delete + recreate)
- Ends with a visible health check so the user sees "everything is green"
- The user never opens a terminal — just double-clicks

## 4. Windows Toast Notifications (replaces Hermes deliver)

PowerShell toast from Python (stdlib-only, no external deps):

```python
import subprocess, sys

def send_windows_toast(title: str, message: str) -> bool:
    if sys.platform != "win32":
        return False
    ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
$textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("App Name").Show($toast)
'''
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False
```

Pitfalls:
- Only works on Windows 10+. Toast text limit ~250 chars — truncate long messages.
- The app name appears in Windows notification settings (Settings > System > Notifications).
- Works from Task Scheduler (user session context) but NOT from a pure SYSTEM service.

### Watchdog --alert-only + --notify + --restart pattern

The watchdog should combine three flags for full unattended operation:

```python
parser.add_argument("--alert-only", help="Silent when OK, print only on problems")
parser.add_argument("--notify", help="Send Windows toast on WARNING/CRITICAL")
parser.add_argument("--restart", help="Auto-restart bot if DOWN")

# In main():
write_heartbeat()  # touch file on every run

if args.restart and bot_is_down:
    restart_bot()

if args.notify and overall in ("WARNING", "CRITICAL"):
    send_windows_toast(f"Watchdog: {overall}", alert_details[:250])

if args.alert_only and overall == "OK":
    return 0  # silent, exit 0
```

Task Scheduler command: `python watchdog.py --alert-only --restart --notify`

## 5. Pipeline Hardening

### Retry + per-step error handling

```bash
set -uo pipefail  # NOT -e — handle errors per-step
FAILED_STEPS=0

# Step with retry
MAX_RETRIES=3; ATTEMPT=0
while [ $ATTEMPT -lt $MAX_RETRIES ]; do
    ATTEMPT=$((ATTEMPT + 1))
    [ $ATTEMPT -gt 1 ] && sleep 5
    if python step.py; then
        echo "    [OK] step (attempt $ATTEMPT)"; break
    else
        echo "    [FAIL] step attempt $ATTEMPT"
        [ $ATTEMPT -ge $MAX_RETRIES ] && FAILED_STEPS=$((FAILED_STEPS + 1))
    fi
done

# Step without retry (simple)
if python step2.py; then
    echo "    [OK] step2"
else
    echo "    [FAIL] step2"
    FAILED_STEPS=$((FAILED_STEPS + 1))
fi

# Summary with machine-parseable markers
EXIT_CODE=0  # initialize before conditionals (set -u safe)
if [ $FAILED_STEPS -eq 0 ]; then
    echo "RESULT: PASS — all steps succeeded"; EXIT_CODE=0
elif [ $FAILED_STEPS -lt $TOTAL_STEPS ]; then
    echo "RESULT: PARTIAL — $FAILED_STEPS/$TOTAL_STEPS steps failed"; EXIT_CODE=1
else
    echo "RESULT: FAIL — all steps failed"; EXIT_CODE=2
fi
```

### Watchdog parsing of pipeline logs

```python
if "RESULT: PASS" in content:
    return "ok"
elif "RESULT: PARTIAL" in content:
    return "warning"
elif "RESULT: FAIL" in content:
    return "critical"
```

## 6. Dead Man's Switch (heartbeat file)

Two-process pattern — watchdog writes, log rotation checks:

```python
# Watchdog: touch on every run
HEARTBEAT_FILE.write_text(datetime.now(timezone.utc).isoformat())

# Log rotation (runs weekly): check heartbeat age
if not HEARTBEAT_FILE.exists():
    print("CRITICAL: No heartbeat — watchdog may not be running")
else:
    age_hours = (datetime.now().timestamp() - HEARTBEAT_FILE.stat().st_mtime) / 3600
    if age_hours > 2:
        print(f"CRITICAL: Heartbeat is {age_hours:.0f}h old")
```

## 7. Trade History Backup (hourly rotation)

Backup critical state files on every watchdog run:

```python
def backup_trade_history() -> None:
    if not TRADE_HISTORY.exists():
        return
    backup_dir = PRODUCTION / "backups"
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(TRADE_HISTORY, backup_dir / f"trade_history_{ts}.json")
    # Keep last 30
    for old in sorted(backup_dir.glob("trade_history_*.json"))[:-30]:
        old.unlink()
```

## 8. Portable Python Scripts (no hardcoded paths)

All scripts resolve paths relative to themselves:

```python
ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "production"
```

**CRITICAL PITFALL — import-before-path-insert:** `sys.path.insert(0, str(ROOT))` must
come BEFORE any intra-project imports. If the import is at the top of the file and the
path setup is below it, the script works when imported from tests (which already set up
the path) but fails with `ModuleNotFoundError` when run standalone.

```python
# WRONG — fails standalone
from production.util import atomic_write  # ModuleNotFoundError!
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# RIGHT — works both standalone and imported
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from production.util import atomic_write
```

Also requires `import sys` at the top of the file. When retrofitting scripts that
didn't previously need `sys`, adding `sys.path.insert` without `import sys` causes
`NameError: name 'sys' is not defined`.

## 9. Windows-Specific Python Fixes

### os.statvfs → shutil.disk_usage

`os.statvfs` is Unix-only. On Windows, use:

```python
import shutil
usage = shutil.disk_usage(str(ROOT))
free_gb = usage.free / (1024 ** 3)
total_gb = usage.total / (1024 ** 3)
```

### requirements.txt portability

Don't use a raw `pip freeze` dump — it pins exact versions that may not resolve on
different Python patch versions. Use `>=` pins for direct dependencies:

```
freqtrade>=2026.6
pandas>=3.0
ccxt>=4.5
numpy>=2.4
```

## 10. Configuration for Non-Technical Users

### What to bundle vs. document

| Bundle in repo | Document as "if you want" |
|----------------|--------------------------|
| NSSM (public domain, 368KB) | Email/SMS alerting (needs SMTP config) |
| requirements.txt | Custom API keys |
| install.bat (one-click) | Advanced config tweaks |
| uninstall.bat | |

### README for non-technical users

- First line: "Double-click install.bat"
- No terminal commands in the quick start
- No mention of Hermes, cron, venv, pip (those happen inside install.bat)
- Screenshots or simple text showing what success looks like
- Clear uninstall instructions

### Uninstall script

```batch
schtasks /delete /tn "App Task 1" /f 2>nul
schtasks /delete /tn "App Task 2" /f 2>nul
nssm stop ServiceName 2>nul
nssm remove ServiceName confirm 2>nul
echo Done. Delete the project folder to fully remove.
```
