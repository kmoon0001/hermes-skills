# Windows Task Scheduler (schtasks) Cheatsheet

## Create tasks

### Daily task (no admin)
```cmd
schtasks /create /tn "TaskName" /sc daily /st 10:00 /f /tr "command"
```

### Hourly task
```cmd
schtasks /create /tn "TaskName" /sc hourly /f /tr "command"
```

### Weekly task (specific day)
```cmd
schtasks /create /tn "TaskName" /sc weekly /d SAT /st 09:00 /f /tr "command"
```
Days: MON, TUE, WED, THU, FRI, SAT, SUN

### One-time task (useful for testing)
```cmd
schtasks /create /tn "TestTask" /sc once /st 00:00 /f /tr "echo hello"
```
WARNING: Will warn "may not run because /ST is earlier than current time" — ignore, then trigger manually.

## Manage tasks

### List all tasks matching a prefix
```cmd
schtasks /query /fo list /v | findstr "Freqtrade"
```

### Run a task immediately
```cmd
schtasks /run /tn "TaskName"
```

### Delete a task
```cmd
schtasks /delete /tn "TaskName" /f
```

### Check last run result
```cmd
schtasks /query /tn "TaskName" /fo list /v | findstr "Last Result"
```
Result codes: 0 = success, 1 = general error, 267011 = hasn't run yet

## Quoting rules

### CORRECT — call Python directly:
```cmd
schtasks /create /tn "Watchdog" /sc hourly /f /tr "C:\path\.venv\Scripts\python.exe C:\path\script.py --alert-only"
```

### WRONG — nested quotes fail silently:
```cmd
schtasks /create /tn "Watchdog" /sc hourly /f /tr "cmd /c ""C:\path\script.bat"" >> log.txt"
```

### If you must use cmd /c:
```cmd
schtasks /create /tn "Task" /sc daily /st 10:00 /f /tr "cmd /c C:\path\script.bat"
```
No inner quotes. No redirects in the /tr value. Have the .bat file handle its own logging.

## Debugging

### Task triggered but no output?
1. The command might produce no output by design (e.g., --alert-only with OK status)
2. Check for side effects: heartbeat file, database write, log file
3. Test the exact command from a terminal first
4. Try without `>> log.txt` redirection in the /tr value

### Task not running?
1. Check Logon Mode: `schtasks /query /tn "Task" /fo list /v | findstr "Logon"`
2. If "Interactive only" — task only runs when user is logged in
3. If you need it to run regardless: add `/ru SYSTEM` (requires admin)

### "Access is denied" on create?
Remove `/ru SYSTEM` — it requires administrator privileges. Tasks run as current user by default.
