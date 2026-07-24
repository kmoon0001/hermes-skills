# Freqtrade Standalone Production Deployment

Reference implementation of a complete standalone Windows production system
for a Freqtrade trading bot. Built July 2026 to replace Hermes cron dependencies
with native Windows Task Scheduler.

## Architecture

```
Windows Task Scheduler (schtasks, no admin, current-user context)
├── Freqtrade Daily Pipeline   → daily 10:00 AM
│   └── python production/run_cycle6_full.sh (hardened bash script)
├── Freqtrade Watchdog         → hourly
│   └── python production/watchdog.py --alert-only --restart --notify
├── Freqtrade Stock Paper Trade → Saturdays 9:00 AM
│   └── python stocks/paper_trade.py
└── Freqtrade Log Cleanup       → Sundays 3:00 AM
    └── python production/log_rotation.py

NSSM Windows Service (optional)
└── FreqtradeBot → auto-start on boot, auto-restart on crash
    └── python -m freqtrade trade --config config.json --strategy Cycle6Strategy
```

## Key Files

| File | Purpose |
|------|---------|
| `setup.bat` | One-click Task Scheduler creation |
| `production/watchdog.py` | 5 health checks, auto-restart, Windows toasts, heartbeat |
| `production/run_cycle6_full.sh` | Hardened pipeline with retry + per-step error handling |
| `production/log_rotation.py` | Log cleanup + dead man's switch |
| `scripts/install_service.bat` | NSSM service installation |

## Watchdog Checks

1. **Bot health** — HTTP ping to `localhost:8080/api/v1/ping`
2. **Data freshness** — signals.json age (<36h), feather file age (<48h)
3. **Disk space** — free GB (<10GB warn, <5GB critical), data dir size
4. **Pipeline status** — parse latest log for RESULT: PASS/PARTIAL/FAIL
5. **Equity** — current equity, drawdown %, P&L

Exit codes: 0=OK, 1=WARNING, 2=CRITICAL.
Modes: `--verbose`, `--json`, `--alert-only` (silent when OK), `--restart`, `--notify`.

## Critical Pattern: `sys.path.insert` Ordering

When writing standalone scripts that import sibling modules:

```python
# WRONG — import fails because 'production' isn't on sys.path yet
from production.util import atomic_write
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# RIGHT — path insert BEFORE the import
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from production.util import atomic_write
```

All production scripts (`generate_signals.py`, `execute_trades.py`, `trade_logger.py`, `check_alerts.py`) needed this fix to run standalone. Tests passed because test files set up the path first — the bug only manifested when running scripts directly.

## Task Scheduler Lessons Learned

1. **Call Python directly in `/tr`**, not through .bat wrappers. Avoid `cmd /c` redirects — they get mangled.
2. **Omit `/ru SYSTEM`** unless admin rights are guaranteed. Default (current user) works without elevation.
3. **Always use absolute paths** in task commands. Task Scheduler's working directory is unpredictable.
4. **Test with a bare `echo >> file` task first** to verify the scheduler works, then add complexity.
5. **Use `schtasks /run` to trigger on demand** for testing without waiting for the schedule.

## Deployment Checklist for Brother (Non-Technical)

1. Copy the `freqtrade/` folder to his machine
2. Install Python 3.11+ if not present
3. Open terminal in the folder, run:
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
4. Double-click `setup.bat`
5. Start the bot (manual or NSSM service)
6. Everything runs automatically from then on

## Files Not Needed (Hermes Cleanup)

Removed from the project:
- Hermes cron jobs (`cycle6-daily-run`, `Freqtrade Watchdog (Hourly)`)
- `production/watchdog_cron.sh` (Hermes cron wrapper)
