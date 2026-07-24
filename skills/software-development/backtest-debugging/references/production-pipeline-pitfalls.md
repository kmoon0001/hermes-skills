# Production Pipeline Pitfalls (Discovered July 2026)

These pitfalls were found during a multi-agent audit of a crypto trading bot's
production pipeline (generate_signals → execute_trades → trade_logger → check_alerts).
They are NOT covered by the existing simulation-engine pitfalls (0-20) because
they live in the production I/O layer rather than the backtest engine.

## Pitfall P1: Alert Append Wipes Shared State

**Symptom:** `check_alerts.py` always reports "no position changes" even when
positions clearly changed between runs. Signal change detection is permanently broken.

**Cause:** `append_alert()` writes only `{"alerts": alerts}` to the shared
`alert_log.json`, nuking the `last_state` key that `check_signal_changes()`
needs for diff detection. Every alert append destroys the state needed for the
next run's change detection.

```python
# BUG: writes only alerts, wipes last_state
def append_alert(level, message):
    alerts = load_alert_log()
    alerts.append({...})
    atomic_write(ALERT_LOG, {"alerts": alerts})  # last_state is GONE
```

**Detection:** Check whether `check_alerts.py` output ever shows position
changes or vote changes. If it's always silent on changes, the state is being
wiped.

**Fix:** Read the full JSON, preserve all keys, write back complete:
```python
def append_alert(level, message):
    data = json.loads(ALERT_LOG.read_text()) if ALERT_LOG.exists() else {}
    alerts = data.get("alerts", [])
    alerts.append({...})
    data["alerts"] = alerts
    atomic_write(ALERT_LOG, data)  # preserves last_state
```

**When this bites:** Any shared JSON file where multiple writers append
different sections. The first writer that doesn't preserve existing keys
silently corrupts downstream readers.

## Pitfall P2: Bare json.loads After Stateful Writes

**Symptom:** Pipeline crashes AFTER writing output files, leaving stale
signals.json or positions.json that downstream steps consume as fresh data.

**Cause:** The pipeline writes its output (signals.json, positions.json) BEFORE
reading config for the final "dry run vs live" check. If config.json is
corrupt at that point, the crash leaves the stale output in place but the
pipeline exits non-zero. The next cron run sees a valid signals.json from
the failed run and proceeds with stale data.

```python
# signals.json ALREADY WRITTEN at this point
atomic_write(SIGNALS_PATH, output)

# This crashes → stale signals.json remains, pipeline exits
config = json.loads(config_path.read_text())  # NO try/except
```

**Detection:** Check the order of writes vs reads in each pipeline step.
If any non-critical read happens AFTER the critical write, it's a risk.

**Fix:** Wrap late-stage reads in try/except with safe defaults:
```python
try:
    config = json.loads(config_path.read_text())
except (json.JSONDecodeError, OSError) as e:
    print(f"WARNING: {e} — assuming dry run")
    config = {"dry_run": True}
```

Or reorder: read config FIRST, write output LAST.

## Pitfall P3: Sibling Sleeve Cash-Holding Asymmetry

**Symptom:** Two inactive sleeves (both with target=0) contribute different
amounts to total NAV — one holds cash (SLEEVE_WEIGHT), the other zeroes out.
This creates phantom capital in the NAV and dilutes metrics differently
depending on which sleeves are used.

**Cause:** P-sleeve loop holds cash flat when target_p=0:
```python
passive[t] = passive[t-1]  # = SLEEVE_WEIGHT, cash flat
```

But PV-sleeve zeroes out when target_pv=0:
```python
passive_vol[t] = SLEEVE_WEIGHT * target_pv  # = 0.0, ZEROED
```

**Detection:** When P and PV sleeves show different NAVs despite both having
target=0. Also: when `r["nav"]` includes phantom idle cash that dilutes
active-strategy metrics.

**Fix:** Make both sleeves consistent. Hold cash flat is preferred (preserves
capital realism):
```python
# PV-sleeve: hold cash when inactive, like P-sleeve
passive_vol[0] = SLEEVE_WEIGHT  # not SLEEVE_WEIGHT * 0
passive_vol[t] = passive_vol[t-1]  # not SLEEVE_WEIGHT * 0
```

## Pitfall P4: Full-Timestamp Idempotency Check

**Symptom:** Cron reruns within the same day pass through the idempotency
guard and create duplicate equity history entries.

**Cause:** Idempotency check compares full ISO timestamps with seconds
precision. Two runs at 12:00:00 and 12:05:00 produce different strings,
so the check never triggers for same-day reruns.

```python
today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")  # "2026-07-21T12:00:00Z"
last_entry = history["equity_history"][-1]["date"]       # "2026-07-21T12:00:00Z"
if last_entry == today:  # Only matches if exact same second!
    return  # idempotent skip
```

**Fix:** Compare date portion only:
```python
if last_entry[:10] == today[:10]:  # Compare YYYY-MM-DD
    return  # idempotent skip
```

**When this bites:** Any cron-based pipeline with sub-minute execution time.
The first run at :00 works, the second run at :01 bypasses the check.
