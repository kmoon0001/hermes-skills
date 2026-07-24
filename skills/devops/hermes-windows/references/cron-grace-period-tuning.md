# Cron Grace Period Tuning on Windows

## Why This Matters on Windows

Windows machines sleep/shutdown nightly. The cron scheduler's grace window
determines how long after a missed scheduled time the job will still fire
on next startup. The default MAX_GRACE is 7200 seconds (2 hours) — too
short for a machine that's off from 6 PM to 8 AM.

## The Constant

Location: `cron/jobs.py` → `_compute_grace_seconds()`

```python
MIN_GRACE = 120        # 2 minutes (one-shot jobs)
MAX_GRACE = 7200       # 2 hours (default)
```

The actual grace for a given job is `period_seconds // 2`, clamped between
MIN_GRACE and MAX_GRACE. For a weekly cron (`0 9 * * 1`), the period is
7 days = 604800s, so grace = min(302400, MAX_GRACE).

## Recommended Change for Windows

```python
MAX_GRACE = 86400  # 24 hours
```

This lets weekly/daily jobs catch up if the machine was off for up to 24
hours after the scheduled time.

## How to Apply

```bash
cd ~/AppData/Local/hermes/hermes-agent
# Edit the constant
sed -i 's/MAX_GRACE = 7200/MAX_GRACE = 86400/' cron/jobs.py
# Clear compiled cache
rm -f cron/__pycache__/jobs.cpython-*.pyc
# Restart gateway to pick up the change
hermes gateway restart
```

## Test Adaptation Pattern

Changing MAX_GRACE can break tests that assert on specific time gaps.
The pattern: if a test sets `now` to be N hours after a job's next_run_at,
and N was chosen to exceed the old grace but now falls within the new grace,
widen the gap so it still exceeds the new MAX_GRACE.

Example: `test_cron_offset_migration_does_not_repair_already_passed_wall_time`
had `now` 12 hours past the job's next_run_at. With MAX_GRACE=7200, 12h >
2h → past grace → fast-forward path. With MAX_GRACE=86400, 12h < 24h →
within grace → different code path → different next_run_at assertion.

Fix: bump `now` from May 19 to May 20 so the gap is ~36 hours, which
exceeds 24 hours and triggers the same code path.

```python
# Before (fails with MAX_GRACE=86400)
now = datetime(2026, 5, 19, 13, 2, 0, tzinfo=current_tz)  # 12h gap

# After (passes)
now = datetime(2026, 5, 20, 13, 2, 0, tzinfo=current_tz)  # 36h gap
```

## Verification

```bash
cd ~/AppData/Local/hermes/hermes-agent
export PYTHONPATH="$(pwd)"
./venv/Scripts/python.exe -m pytest tests/cron/test_jobs.py tests/cron/test_cron_script.py -v --tb=short -n 0
```

All tests should pass. The grace-specific tests are:
- `test_once_recent_past_within_grace_returns_time`
- `test_cron_offset_migration_does_not_repair_already_passed_wall_time`
