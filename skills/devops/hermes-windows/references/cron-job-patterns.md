# Cron Job Patterns for Windows

Recurring patterns for Hermes cron jobs on Windows, especially `no_agent=true`
jobs that run project scripts.

## The `--alert-only` watchdog pattern

For monitoring cron jobs (hourly health checks, data freshness, disk space),
the best pattern is:

1. Build a Python script that accepts `--alert-only` flag
2. When everything is OK: exit 0, print nothing
3. When there's a problem: print the alert, exit non-zero
4. Set up cron as `no_agent=true`, `deliver=local`

The cron system delivers stdout on non-zero exit. When the script is silent on
OK, the user only sees output when there's a real problem. No hourly spam.

**Example watchdog structure:**
```python
def main():
    checks = [check_health(), check_data(), check_disk()]
    levels = [c[0] for c in checks]

    if "critical" in levels:
        overall, exit_code = "CRITICAL", 2
    elif "warning" in levels:
        overall, exit_code = "WARNING", 1
    else:
        overall, exit_code = "OK", 0

    if args.alert_only and overall == "OK":
        return 0  # silent

    # Print report
    for name, level, msg in checks:
        print(f"[{level.upper()}] {name}: {msg}")

    return exit_code
```

**Key design rules:**
- Each check returns `(level, message, info_dict)` — level is "ok"/"warning"/"critical"/"info"
- `--alert-only` means: exit 0 + no output when no warnings/criticals
- `--verbose` gives a full report for manual runs
- `--json` gives machine-parseable output for chaining
- Exit codes: 0=OK, 1=WARNING, 2=CRITICAL
- Keep it stdlib-only (no project dependencies) so it works even when the project env is broken

## The venv wrapper pattern

When a cron job runs a Python script that needs a project-specific venv, you
need a `.sh` wrapper because `no_agent=true` `script=` with `.py` runs under
Hermes' Python, not the project venv.

**Correct pattern (Windows, explicit paths):**
```bash
#!/usr/bin/env bash
# Use explicit Windows paths to avoid MSYS path conversion
cd "C:/Users/kevin/Desktop/project" || exit 2
./.venv/Scripts/python.exe my_script.py --alert-only
```

**Wrong pattern (derived paths — MSYS mangles them):**
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
"$PROJECT_DIR/.venv/Scripts/python" "$PROJECT_DIR/my_script.py"
# → "can't open file 'C:\\c\\Users\\...'"
```

**Cron setup:**
```
action: create
name: Project Watchdog
schedule: 0 * * * *
no_agent: true
script: scripts/watchdog_cron.sh
workdir: C:\Users\kevin\Desktop\project
deliver: local
```

The `script` path is relative to `workdir` when `workdir` is set. The shell
wrapper handles venv activation and passes flags to the Python script.

## When to use no_agent=true vs no_agent=false

| Pattern | `no_agent` | When |
|---------|-----------|------|
| Script produces exact output for delivery | `true` | Watchdog alerts, data collection, fixed-format reports |
| Output needs interpretation/reasoning | `false` | Summarize feeds, draft briefings, conditional responses |
| Script is silent-on-OK | `true` | Avoids burning tokens on "everything is fine" |
| Need to check multiple sources and decide | `false` | Cross-referencing, multi-step investigation |

For monitoring/watchdog jobs, `no_agent=true` with `--alert-only` is almost
always the right choice — no tokens wasted on OK runs, alerts delivered directly.

## Retry patterns in bash pipeline scripts

For multi-step pipeline cron jobs (data download → processing → logging):

```bash
# Per-step error handling — don't kill the whole pipeline on one failure
MAX_RETRIES=3
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_RETRIES ]; do
    ATTEMPT=$((ATTEMPT + 1))
    if python step1.py 2>&1; then
        echo "[OK] step1 (attempt $ATTEMPT)"
        break
    else
        echo "[FAIL] step1 attempt $ATTEMPT"
        if [ $ATTEMPT -ge $MAX_RETRIES ]; then
            FAILED_STEPS=$((FAILED_STEPS + 1))
        fi
        sleep 5
    fi
done
```

**Design rules:**
- Remove `set -e` — handle errors per-step
- Each step gets its own try/retry block
- Track `FAILED_STEPS` for the final exit code
- Add `[OK]`/`[FAIL]` markers for machine parsing
- Always run the watchdog/report step last, even if earlier steps failed
