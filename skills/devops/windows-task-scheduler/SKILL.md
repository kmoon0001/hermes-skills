---
name: windows-task-scheduler
description: Deploy Python scripts as Windows Task Scheduler jobs — schtasks syntax, path resolution, permission models, testing patterns, and pitfalls.
category: devops
triggers:
  - "schedule this script on Windows"
  - "set up a Windows scheduled task"
  - "run daily on Windows"
  - "Windows cron replacement"
  - "schtasks"
  - "Task Scheduler"
  - "background job on Windows"
---

# Windows Task Scheduler — Python Script Deployment

Deploy and debug Python scripts as Windows scheduled tasks. Use this instead of Hermes cron, Linux cron, or third-party schedulers when the target machine is Windows and the user doesn't run Hermes.

## Quick Decision Tree

```
Does the user have Hermes? → Use cronjob (no agent needed)
Does the user need cross-platform? → Use cronjob or OS-native scheduler
Is the target Windows, no Hermes? → Use this skill
```

## Core Pattern: `schtasks /create`

```cmd
schtasks /create ^
    /tn "Task Name" ^
    /tr "command to run" ^
    /sc daily ^           # or: hourly, weekly, once
    /st 10:00 ^            # HH:MM (24h)
    /f                     # force overwrite if exists
```

### Schedule Types

| Flag | Value | Meaning |
|------|-------|---------|
| `/sc daily` | — | Every day |
| `/sc hourly` | — | Every hour (at :00 past) |
| `/sc weekly` | `/d SUN,MON` | Specific days |
| `/sc once` | `/st 00:00` | One-shot (test pattern) |

### Command String (`/tr`) — CRITICAL PITFALLS

**PITFALL: Do NOT use `cmd /c ""path"" >> log` redirects in the `/tr` value.** Task Scheduler mangles the quotes and the redirect often fails silently. Instead:

**Preferred: Call Python directly.**
```cmd
schtasks /create /tn "MyTask" /sc hourly /f /tr "C:\project\.venv\Scripts\python.exe C:\project\script.py --flag"
```
This is the most reliable form. No .bat wrapper, no redirect, no quote nesting.

**If you MUST use a .bat wrapper**, the .bat file must do its own path resolution with `%~dp0` (see Path Resolution below). Do not rely on the task's working directory.

**If output capture is needed**, either:
1. Have the Python script write its own log file
2. Use a .bat wrapper that does the redirect internally: `python script.py >> log.txt 2>&1`

### Permission Model

```
/ru SYSTEM    → runs as SYSTEM (requires ADMIN — "Access is denied" without)
(default)     → runs as current user (no admin needed, works for personal tasks)
```

**Rule: Omit `/ru` unless the user explicitly needs SYSTEM context.** Most scheduled Python scripts should run as the current user. Tasks run when the user is logged in ("Interactive only" logon mode).

## Path Resolution in .bat Wrappers

When a .bat file needs to find its project root:

```bat
REM Absolute path to this script's directory (always works, even from Task Scheduler)
set "SCRIPT_DIR=%~dp0"

REM Strip trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Go up one level to project root
for %%A in ("%SCRIPT_DIR%") do set "PROJECT_DIR=%%~dpA"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

REM Now use %PROJECT_DIR% for all absolute paths
"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\script.py"
```

**PITFALL: Do NOT use `pushd`/`popd` with relative paths in Task Scheduler .bat wrappers.** The task's working directory is unpredictable (`C:\Windows\System32` or the user profile). Always resolve to absolute paths with `%~dp0`.

**PITFALL: Do NOT use `cd /d ".."` or `pushd ".."`** — the ".." resolves relative to the task's working directory, not the script's location.

## Testing Tasks

### Create a one-shot test task
```cmd
schtasks /create /tn "Test_Task" /tr "cmd /c echo TEST_RAN >> C:\path\to\out.txt" /sc once /st 00:00 /f
schtasks /run /tn "Test_Task"
REM Wait 10-15s, then check C:\path\to\out.txt
```

### Trigger an existing task on demand
```cmd
schtasks /run /tn "Task Name"
```

### Check task status and last result
```cmd
schtasks /query /fo list /v | findstr /C:"TaskName" /C:"Last Result" /C:"Next Run"
```
Last Result `0` = success. `267011` = never run.

### Delete a task
```cmd
schtasks /delete /tn "Task Name" /f
```

## Debugging Silent Failures

When a task "runs" but produces no output:

1. **Test the command directly in a terminal first.** If `python script.py` works but the scheduled task doesn't, the issue is environment/path, not the script.

2. **Simplify to a bare echo test.** Create a task that runs `cmd /c echo hello >> file.txt`. If that works, the scheduler works — the issue is in your command.

3. **Use absolute paths everywhere.** Task Scheduler doesn't inherit your PATH, working directory, or venv activation.

4. **Check "Last Result" in task properties.** `0x1` = generic failure, `0xC0000135` = DLL/executable not found (path issue).

5. **Try running Python directly instead of through a .bat wrapper.** This eliminates the wrapper as a failure point.

## Setup Script Pattern

For one-click deployment, use a `setup.bat` that:
1. Resolves its own location to find the project root
2. Validates prerequisites (venv exists, config present)
3. Deletes old tasks (idempotent)
4. Creates all tasks with `schtasks /create`
5. Reports success/failure per task

Template: see `templates/setup.bat` in this skill.

## Windows Toast Notifications

For alerting without external dependencies, send Windows 10/11 toast notifications via PowerShell:

```python
import subprocess

def send_windows_toast(title: str, message: str) -> bool:
    ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
$textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AppName").Show($toast)
'''
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True, timeout=10
    )
    return result.returncode == 0
```

## NSSM — Python as a Windows Service

For auto-start on boot and auto-restart on crash:

```cmd
nssm install ServiceName C:\project\.venv\Scripts\python.exe "script.py --args"
nssm set ServiceName AppDirectory C:\project
nssm set ServiceName Start SERVICE_AUTO_START
nssm set ServiceName AppExit Default Restart
nssm start ServiceName
```

**Preferred: Bundle NSSM in the project.** Download the 64-bit `nssm.exe` from https://nssm.cc (public domain, no license restrictions) and place it in `scripts\nssm.exe`. Then `install_service.bat` references the local copy — zero external downloads for the end user. Latest pre-release (2.24-101, 2017) recommended for Windows 10+.

Download URL: `https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip` — extract `win64/nssm.exe` (~368KB).

## Python Import Ordering Pitfall

When writing standalone scripts (not invoked via `python -m`), sibling-package imports fail if `sys.path` is set AFTER the import:

```python
# BROKEN — import runs before sys.path is set
from mypkg.util import helper
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# FIXED — path setup FIRST, then import
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mypkg.util import helper
```

Tests pass because test runners set up the path before importing test modules. The bug only surfaces when running scripts directly. Fix: always `sys.path.insert` before any sibling-package import. Also verify `import sys` is present — scripts that previously only imported from stdlib may be missing it.

## Windows vs Unix Pitfalls

**`os.statvfs` is Unix-only.** On Windows, use `shutil.disk_usage()`:

```python
# Unix-only — AttributeError on Windows
usage = os.statvfs(path)
free_gb = (usage.f_frsize * usage.f_bavail) / (1024**3)

# Cross-platform — works everywhere
import shutil
usage = shutil.disk_usage(path)
free_gb = usage.free / (1024**3)
```

**`subprocess.Popen` on Windows:** Use `creationflags=subprocess.CREATE_NO_WINDOW` to prevent console windows from popping up when launching background processes from a scheduled task.

**`sys.platform` check:** Use `sys.platform == "win32"` to guard Windows-specific code paths (toast notifications, NSSM commands, taskkill).

## Related Patterns

- `references/freqtrade-watchdog.md` — full production watchdog + pipeline example using this skill
- `templates/setup.bat` — reusable one-click Task Scheduler setup template
