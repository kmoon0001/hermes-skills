---
name: hermes-update-with-blocking-processes
description: "Handle Hermes updates when processes are blocking the update"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
---

# Handling Hermes Updates with Blocking Processes

## Problem
When attempting to update Hermes Agent using `hermes update`, you may encounter an error indicating that another hermes.exe process is running and blocking the update. On Windows, this typically manifests as:

```
✗ Another hermes.exe is running:
    PID 7724  hermes.exe

  Updating now would fail to overwrite C:\\Users\\kevin\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts\\hermes.exe because
  Windows blocks REPLACE on a running executable.

  Close Hermes Desktop, exit any open `hermes` REPLs, and
  stop the gateway (`hermes gateway stop`) before retrying.
```

## Solution Steps

### 1. Identify Running Hermes Processes
First, identify the running hermes processes:
```bash
# On Windows:
tasklist | findstr hermes

# On Linux/macOS:
ps aux | grep hermes
```

### 2. Stop the Blocking Processes
Kill the blocking processes:
```bash
# On Windows:
taskkill /pid <PID> /f

# On Linux/macOS:
kill -9 <PID>
```

### 3. Retry the Update
After stopping the blocking processes, retry the update:
```bash
hermes update
```

### 4. Alternative Approach for Windows Git-Bash / MSYS
Hermes terminal on Kevin's Windows machine runs through Git-Bash/MSYS, not cmd.exe. MSYS rewrites arguments like `/PID` into paths such as `C:/Program Files/Git/PID`, so plain `taskkill /PID <PID> /F` can fail.

Use one of these instead:
```bash
# Prevent MSYS path conversion for Windows-style switches
MSYS_NO_PATHCONV=1 taskkill.exe /PID <PID> /F

# Or use PowerShell, which avoids the slash-conversion problem entirely
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command 'Stop-Process -Id <PID> -Force'
```

Do not use `find /I` from Git-Bash; it invokes POSIX `find` and errors like `find: '/I': No such file or directory`. Use:
```bash
tasklist | findstr /I hermes.exe
```
or PowerShell process queries.

If the only remaining `hermes.exe` is the active CLI session, Windows still blocks replacing `venv/Scripts/hermes.exe`. In that case, launch a deferred updater in a separate PowerShell window that waits for the active PID to exit, then runs `hermes update`.

## Prevention
To avoid this issue in the future:
- Always exit any running Hermes sessions before attempting an update
- Stop the gateway service if running: `hermes gateway stop`
- Close any Hermes Desktop applications before updating

## Troubleshooting
If you continue to have issues:
- Check for any background processes or cron jobs running Hermes
- Make sure no terminals have active Hermes sessions running
- Consider restarting your system if processes appear stuck