# Production Security Audit — Recurring Patterns

Documented from the freqtrade audit (2026-07-21). These are patterns agents should check for
when running Pass G/H/I against any production pipeline codebase.

## Pattern 1: The "Append-Overwrite" Anti-Pattern (JSON State Files)

**Symptom:** A helper function like `append_alert()` or `log_event()` writes a JSON file with only
its own key (`{"alerts": [...]}`), but the same file is also used by another component to store
state under a different key (`"last_state"`). Each append wipes the other component's data.

**Detection:** Grep for all writes to a shared JSON file. Count the keys written by each call site.
If any caller writes a subset of the file's known keys, you have this bug.

**Example (freqtrade C3):**
```python
# append_alert() writes ONLY "alerts" key
def append_alert(level, msg):
    alerts = load_alert_log()          # reads {"alerts": [...], "last_state": {...}}
    alerts.append({"level": level, "message": msg})
    atomic_write(ALERT_LOG, {"alerts": alerts})  # ← "last_state" LOST

# Later, check_signal_changes() reads last_state → always empty {}
def check_signal_changes():
    log_data = json.loads(ALERT_LOG.read_text())
    last_state = log_data.get("last_state", {})  # ← empty because append_alert wiped it
```

**Fix:** Every writer must read the full file, preserve all existing keys, update only its own key,
then atomically write back.

```python
def append_alert(level, msg):
    existing = {}
    if ALERT_LOG.exists():
        try:
            existing = json.loads(ALERT_LOG.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    alerts = existing.get("alerts", [])
    alerts.append({"level": level, "message": msg})
    existing["alerts"] = alerts[-MAX_ALERTS:]
    atomic_write(ALERT_LOG, existing)  # preserves existing["last_state"]
```

**Alternative:** Split into separate files — one per component — if there is no read-after-write
dependency that requires both components to see the same atomic snapshot.

---

## Pattern 2: Pipeline-Exit Crash After Write

**Symptom:** A pipeline script does all the expensive work (data download, signal computation,
output write), then crashes on the LAST step (config read, notification) with an unhandled exception.
The output file exists but the operator sees a traceback and assumes the whole pipeline failed.

**Detection:**
```bash
grep -n "json.loads" pipeline_script.py | while read line; do
    # Check if this loads call is inside a try/except
done
```

Any `json.loads()` at the end of a pipeline that isn't wrapped is a potential crash-after-write.

**Example (freqtrade C2):**
```python
# Steps 1-3: download data, compute signals, write signals.json (all succeed)
# Step 4: read config → CRASH
config = json.loads(config_path.read_text())  # ← no try/except
```

The operator sees a traceback. But `signals.json` was already written by Step 3. Next cron run
may pick up the stale file and double-process.

**Fix:** Either:
1. Wrap in try/except (consistent with all other reads in the same file)
2. Move the config read to the TOP of main(), before any work is done
3. Both

---

## Pattern 3: Hardcoded Secrets Beyond API Keys

**Symptom:** When grepping for secrets, most agents check for `api_key`, `secret`, `password`.
But config files often have additional credential-like fields: `jwt_secret_key`, `ws_token`,
`telegram.token`, `chat_id`, `db_url` (with embedded credentials).

**Detection:**
```bash
grep -nE '(secret|token|password|key|jwt|credential|auth)' config.json
```

Any non-empty value is a finding. Even empty strings (`"secret": ""`) should be flagged if the
field name suggests a credential that could be populated later.

**Fix:** Environment variable interpolation. The config loader should support `${VAR_NAME}` syntax
so secrets never touch disk.

---

## Pattern 4: XSS via Unsanitized HTML Dashboard Generation

**Symptom:** A monitoring script generates an HTML dashboard by embedding data (trade pairs,
prices, reasons) directly into HTML/JS via f-strings without `html.escape()`.

**Risk:** Any field that originates from an external source (exchange pair names, trade reasons
that include user-provided text) can inject HTML/JS if it contains metacharacters like `<`, `>`,
`"`, `&`, or `</script>`.

**Detection:**
```bash
grep -rn "f\"<" *.py | grep -v "html.escape\|escape("
```

**Fix:** 
```python
import html
f"<td>{html.escape(str(value))}</td>"
```

For JavaScript blocks, never embed JSON via string concatenation. Use `json.dumps()` which
properly escapes special characters:
```python
# WRONG
html += f"const data = " + json_string + ";"

# RIGHT
html += f"<script>const data = {json.dumps(data)};</script>"
```

---

## Pattern 5: Code Injection via Subprocess with String-Formatted Code

**Symptom:** Research scripts construct Python code strings using `%` formatting and pass them
to `subprocess.run([sys.executable, "-B", "-c", code])`. The formatted values include user or
file-derived data.

**Detection:**
```bash
grep -rn "subprocess.run.*-c" *.py
grep -rn 'SWEEP_SCRIPT\|runner_code\|%(' *.py
```

Even with `%r` (repr) escaping, this pattern is fragile. A value containing a quote char
could break the repr and inject code.

**Fix:** Pass parameters via environment variables or a temp JSON file:
```python
import tempfile, json
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump({"root": str(ROOT), "params": overrides}, f)
    tmp = f.name
proc = subprocess.run(
    [sys.executable, "-B", script_path, tmp],
    ...
)
```
And in the subprocess script, read `json.load(open(sys.argv[1]))`.

---

## Pattern 6: Non-Atomic HTML/Dashboard Writes

**Symptom:** A monitoring script writes an HTML dashboard file directly (`path.write_text(html)`)
instead of using the same atomic_write utility used for JSON state files.

**Risk:** If the process crashes mid-write (OOM, disk full, SIGKILL), a partial HTML file is left.
If served via a web server, it displays as broken/malformed. Lower severity than JSON state files
(dashboard is informational only), but same fix applies.

**Fix:** Use the same atomic_write pattern, or write to `.tmp` then rename.

---

## Quick Audit Checklist (Add to Pass G/H)

When running a production pipeline audit, add these checks:

- [ ] **Pass G+: Config secrets:** `grep -nE '(secret|token|password|key|jwt|credential)' config.*` — flag non-empty values AND empty-but-named credential fields
- [ ] **Pass G+: HTML sanitization:** `grep -rn "f\"<" *.py | grep -v "html.escape"` — any unchecked HTML generation?
- [ ] **Pass G+: Subprocess injection:** `grep -rn "subprocess.run.*-c" *.py` — any code-as-string patterns?
- [ ] **Pass H+: JSON append-overwrite:** For each JSON file, list all writers and the keys they write. If any writer writes a subset of keys, flag it.
- [ ] **Pass H+: Pipeline crash-after-write:** Check every `json.loads()` at the end of a pipeline (after data writes). Must be wrapped.
- [ ] **Pass H+: Non-atomic writes:** Check for any `.write_text()` calls on files that could be read concurrently. Should use atomic_write.
