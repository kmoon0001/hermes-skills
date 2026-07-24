---
name: standalone-project-delivery
description: "Package any Hermes-built project for delivery to someone who doesn't use Hermes. Replace Hermes cron with native OS schedulers, bundle dependencies, build one-shot installers, add uninstall scripts. Covers Windows Task Scheduler, NSSM services, hardening patterns, and the 'who is this for?' preflight check."
version: 1.0.0
---

# Standalone Project Delivery

Use this skill when the user says any of:
- "I want to give this to my brother" / "this is for someone else"
- "they don't use Hermes" / "no agent dependency"
- "make it standalone" / "one-shot install" / "double-click to run"
- "how would someone else set this up?"
- You're about to wire up orchestration (cron, scheduling) and haven't asked who the end user is

## The Cardinal Rules

### Rule 1: Ask "Who is this for?" BEFORE building orchestration

**Pitfall:** Building everything on Hermes cron, Hermes paths, and Hermes delivery
without checking whether the recipient uses Hermes. This wastes hours — every cron
job, wrapper script, and delivery target must be rebuilt.

**Fix:** Before writing any cron/scheduling/orchestration code, ask:
- "Is this just for you, or for someone else?"
- "Does the recipient use Hermes?"

If the answer is "someone else" or "no Hermes," switch to standalone mode immediately.

### Rule 2: Before calling a project "done," ask "What's NOT connected?"

**Pitfall:** Delivering a project with independent subsystems that don't talk to
each other (e.g., crypto bot + stock bot sharing a repo but no portfolio layer).
The subsystems work in isolation but the user expects them to be integrated.

**Fix:** After every major feature, run this checklist before saying "done":
- What subsystems exist? Do they share data? Should they?
- Is there a unified view (dashboard, watchdog, report) that shows everything?
- Are there cross-asset risks (correlation, concentration) that nobody monitors?
- Would a real user be surprised by something that's missing?

**Kevin's rule:** "Present all options even when I don't ask. If there's a better
way to do things, bring it up. Omission is breaking the rule." — Active
gap-finding is part of the job, not optional.

## Delivery Checklist

Every standalone project needs these files:

| File | Purpose |
|------|---------|
| `install.bat` (or `install.sh`) | One double-click does everything: Python check, venv, pip install, scheduler setup |
| `START-*.bat` / `START-*.ps1` | **One-shot launcher** — menu-driven entry point for ALL daily operations (crypto, stocks, pipeline, watchdog, status) |
| `setup.bat` | Lighter version — just scheduler setup if venv already exists |
| `uninstall.bat` | Removes all scheduled tasks, services, and offers to keep data |
| `requirements.txt` | Pinned dependencies with `>=` (not `==`) for portability across Python versions |
| README rewrite | No mention of Hermes. Written for someone who just cloned a repo. |

## Windows Task Scheduler (replaces Hermes cron)

Use `schtasks /create` with no `/ru SYSTEM` (avoids admin requirement):

```bat
schtasks /create ^
    /tn "Project Name - Task" ^
    /tr "cmd /c path\to\script.bat" ^
    /sc daily ^
    /st 10:00 ^
    /f
```

Key patterns:
- `/sc hourly` / `daily` / `weekly` — schedule
- `/st HH:MM` — start time (24h)
- `/f` — force overwrite existing task
- Do NOT use `/ru SYSTEM` — requires admin, and tasks don't need it
- Use absolute paths in `/tr` — Task Scheduler's working directory is `C:\Windows\System32`
- For Python scripts: `/tr "C:\path\.venv\Scripts\python.exe C:\path\script.py --flags"`
- `.bat` wrappers are fragile in Task Scheduler — prefer calling Python directly

## NSSM Windows Service (auto-start + auto-restart)

NSSM (Non-Sucking Service Manager) is public domain. Bundle `nssm.exe` (64-bit, ~370KB) in `scripts/`.

```bat
nssm install ServiceName "C:\path\.venv\Scripts\python.exe" "-m module args"
nssm set ServiceName AppDirectory "C:\path"
nssm set ServiceName Start SERVICE_AUTO_START
nssm set ServiceName AppExit Default Restart
nssm set ServiceName AppNoConsole 1
nssm set ServiceName AppStdout "C:\path\logs\stdout.log"
nssm set ServiceName AppStderr "C:\path\logs\stderr.log"
nssm set ServiceName AppRotateFiles 1
nssm start ServiceName
```

Download from: `https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip`
Extract: `win64/nssm.exe`

## Script Hardening Pattern

Every production script must pass these gates before delivery:

1. **Error handling** — try/except around all external I/O. One failure must not crash the pipeline.
2. **Atomic writes** — `os.replace(tmp, path)` for JSON. Never `write_text()` on the real file.
3. **Idempotency** — same-day rerun must not duplicate data. Check date and skip/replace.
4. **Exit codes** — 0=OK, 1=warning, 2=critical. Scheduler and watchdog depend on these.
5. **Standalone execution** — must work via `python path/to/script.py` without test harness.
6. **Config-driven paths** — use `Path(__file__).resolve().parents[1]`, never hardcode usernames.

## Watchdog Pattern

A watchdog script that the scheduler runs frequently (hourly) to check:

- Bot/service is running (API ping)
- Data is fresh (file timestamps, generation dates)
- Disk space (warn below 10GB, critical below 5GB)
- Pipeline status (last log file, PASS/FAIL markers)
- Current equity and drawdown
- Position concentration (optional)
- Any sub-project portfolios (stocks, etc.)

Output modes:
- `--verbose` — full report for manual inspection
- `--alert-only` — silent when OK, prints only on WARNING/CRITICAL (for cron)
- `--json` — machine-readable for dashboards
- `--restart` — auto-restart crashed services
- `--notify` — Windows toast notifications on problems

Heartbeat file: touch `.watchdog_heartbeat` on every run. A separate log rotation
script checks if the heartbeat is stale (>2h) — dead man's switch.

### Windows Toast Notifications

```python
def send_windows_toast(title: str, message: str) -> bool:
    """Send Windows 10/11 toast via PowerShell. Call on WARNING/CRITICAL only."""
    ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
    [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
$textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("App Name").Show($toast)
'''
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script],
                           capture_output=True, timeout=10)
    return result.returncode == 0
```

### Position Concentration Check

```python
def check_position_concentration() -> tuple[str, str, dict]:
    """Warn if any single position exceeds 40% of equity."""
    # CRITICAL: include sanity guard for bad data
    if max_concentration > 500:
        return "info", "Position concentration data unavailable — entry data needs review", {}
    elif max_concentration > 50:
        return "critical", f"Position {pair} is {pct:.0f}% of equity", {}
    elif max_concentration > 40:
        return "warning", f"Position {pair} is {pct:.0f}% of equity", {}
    return "ok", f"Max concentration: {pair} at {pct:.0f}%", {}

## Non-Coder Config Switcher Pattern

When the project has a configurable setting that non-technical users need to change
(e.g., crypto exchange, data provider, model selection), provide a double-click
batch file that:

1. Shows the current value (read from the config file)
2. Lists numbered options with one-line descriptions
3. Lets the user pick by number (no typing, no errors)
4. Confirms the choice before applying
5. Writes the config atomically
6. Offers to trigger the downstream action (e.g., download fresh data)

**Pattern:** `SWITCH-EXCHANGE.bat` in the Freqtrade project. Double-click → pick
exchange by number → confirm → optional data download. Old data preserved so user
can switch back anytime.

Requirements:
- `setlocal enabledelayedexpansion` for variable expansion inside blocks
- `choice /c 1234560 /n /m "  Select [0-6]: "` for numbered menu
- `if errorlevel 7 goto :cancel` etc. — errorlevels are REVERSE order
- Call a Python config module for actual read/write: `"%PY%" exchange_config.py --set %EX%`
- Offer downstream action: `choice /c YN /m "    Download data now"`
- Show clear next steps after switch: what changed, how to verify, how to switch back

The underlying Python config module (`exchange_config.py`) should:
- Be a single source of truth imported by all production files
- Support `--set`, `--get`, `--list` CLI commands
- Validate the choice against a known-good list
- Create any needed directories automatically
- Report clear errors on invalid input

This pattern applies to any config that non-technical users might want to change:
model providers, data sources, alert targets, strategy parameters.

## Launcher Maintenance Rules & Drift Detection

**The most common delivery failure:** the launcher was built for v1 but v2 added
stocks, watchdog, portfolio manager, alerting, and trading ops — and nobody updated
the launcher. The user clicks it and only sees the old crypto menu, never discovering
the new subsystems.

**Detection signal — user asking "did you update the launcher?" means drift.** When
the user says "did you update the one select launcherlauncher, the ones that launch
her as well as anything of streaming downstream of the changes we made so that
everything is consistent" — this is NOT a feature request. It's a drift alarm.
Respond with a full audit: list every production script, compare against every menu
item in every launcher file, fix all gaps.

**Dual-launcher sync:** Both `.bat` and `.ps1` MUST stay in sync. When adding an
option to one, add it to the other. Verify: count menu items in both files, grep
for `--strategy` values, check all Python script paths match.

**Downstream wrappers:** Don't just update the main launcher. Check `pipeline.bat`,
`watchdog.bat`, `stocks.bat`, `CHECK-SETUP.bat` — all of them may reference stale
config, wrong strategy names, or bash dependencies that need native Windows replacement.

Full batch file patterns (menus, retry loops, timestamps) are in
`skill: trading-bot-production` reference `windows-bat-patterns.md`.

## .bat Wrapper Pitfalls

`.bat` wrappers called from Task Scheduler fail silently for several reasons:

1. **pushd/popd** — unreliable in scheduler context. Use absolute paths with `%~dp0`.
2. **Relative paths** — working directory is `C:\\Windows\\System32`. Always resolve paths.
3. **Pipe redirection** — `>> log.txt` in schtasks `/tr` is unreliable. Log from within the .bat instead, or call Python directly.
4. **Exit code propagation** — use `exit /b %ERRORLEVEL%` explicitly.

**Preferred pattern:** Call Python directly from schtasks, skip .bat wrappers entirely:

```bat
schtasks /create /tn "Watchdog" /sc hourly /f /tr "%PYTHON% %PROJECT%\\watchdog.py --alert-only --restart --notify"
```

This was discovered when .bat wrappers ran silently in Task Scheduler — direct Python
calls logged output correctly to redirected files while .bat wrappers produced nothing.

## Pitfall: Partial Implementation — Verify EVERY Reference

When changing a core parameter (strategy period, config key, credential), grep
EVERY file in the project for the old value. A config change that touches the
production script, backtest engine, watchdog, docstrings, comments, and
argparse defaults must be updated in ALL of them. Missing even one creates a
silent divergence.

**Detection:** `grep -rn "OLD_VALUE" . --include="*.py" --include="*.md" --include="*.sh"`
**Fix:** Update every reference. Verify with the same grep. Run tests afterward.
**Signal:** User says "did you implement it completely?" — you missed some.

## Uninstall Script

Must clean up EVERYTHING the install created:

1. All Task Scheduler jobs (`schtasks /delete /tn "..." /f`)
2. NSSM service (`nssm stop ...` + `nssm remove ... confirm`)
3. Offer to keep data files (trade history, logs)
4. Note the project folder can be deleted manually

## requirements.txt Hygiene

Generate with `>=` pins, not `==`:
```bash
.venv/Scripts/pip freeze | sed 's/==/>=/g' > requirements.txt
```

Then manually strip dev-only packages (pytest, ruff, mypy, black, build, etc.).
Keep only runtime dependencies. Test on a different Python patch version if possible.

## One-Shot install.bat

The `install.bat` should handle the ENTIRE setup in one double-click:

1. Check Python is on PATH (`python --version`)
2. Create `.venv` if missing (`python -m venv .venv`)
3. Install dependencies (`.venv\Scripts\pip install -r requirements.txt`)
4. Create Task Scheduler jobs (call setup.bat logic inline)
5. Offer to install NSSM service (`scripts\install_service.bat`)
6. Run a quick health check to show everything is green

The user should see success output after double-clicking — no terminal, no manual steps.
