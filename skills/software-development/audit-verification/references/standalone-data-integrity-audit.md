# Standalone Data Integrity Audit

Use this reference when the user asks you to audit data files, run scripts, cron/job configurations, or Python modules for correctness and consistency — with **no pre-existing claims document** to verify against.

This covers five audit dimensions:
1. Labeling Accuracy (field names, descriptions, annotations)
2. Metric Sanity (numerical plausibility and sign conventions)
3. Argument Consistency (shell script parameters, quoting, missing steps)
4. File Path Correctness (every referenced path resolves to a real file)
5. Cron / Scheduled Task Integrity (actual automation that matches the docs)

---

## Workflow

### Step 0: Inventory the Audit Scope

Before reading anything, identify the full set of files to audit:
- Query the user or `find` the repo for: `*.json`, `*.sh`, `*.yaml`, `*.yml`, `*.py`, `cron*`, `*config*`
- Exclude: `.venv/`, `node_modules/`, `__pycache__/`, `.git/`, `site-packages/`
- Organize into categories: **data files** (JSON/CSV), **run scripts** (sh/bat/ps1), **Python modules**, **cron/scheduled tasks**

### Step 1: Read All Data Files

Batch-read every JSON and flat data file in the scope. For each file, note:
- Schema (top-level keys, array structure)
- Field naming conventions (camelCase vs snake_case, consistency across files)
- Datetime formats (ISO 8601 with T vs space-separated, timezone handling)
- Sign conventions (are losses negative? are drawdowns positive or negative?)
- Units (percentage as decimal 0.05 vs 5.0, currency as float vs string)

### Step 2: Cross-Reference Values Between Files

Systematically compare the same semantic fields across all files that should agree:

| Cross-Reference Pair | What to Check |
|---|---|
| `positions.json` ↔ `signals.json` | Position lists match; target values correspond |
| `positions.json` ↔ `trade_history.json` | Stake/size values for same pairs |
| `signals.json` ↔ `alert_log.json` / `last_state` | Target values, trend flags, generated_at timestamps |
| `trade_history.json` ↔ `positions.json` | Current open positions are consistent |
| Research result JSON ↔ Production result JSON | CAGR/Sharpe/MaxDD for overlapping periods |
| `results.json` ↔ `multiasset_*_results.json` | Same-named comparison figures (e.g. "+8.73%") |

Common findings:
- **Stale state**: alert_log's last_state has older target values than current signals.json
- **Stake mismatch**: positions.json stake differs from trade_history.json stake for same pair
- **Datetime drift**: generated_at is newer but last_state wasn't updated
- **Schema drift**: same field stored in different types across files

### Step 3: Cross-Reference Labels Against Actual Values

For each "name" or "description" field in a data file:
- Does the label accurately describe what the value actually represents?
- Look for **aggregation misattribution** (e.g. "SPY-only" label on an 8-ETF aggregate result)
- Look for **missing caveats** (e.g. "beats B&H" when the comparison is to a multi-asset portfolio, not SPY alone)

### Step 4: Check Metric Sign Convention ⚠️

This is the most common silent data defect. Check every `max_drawdown` field:

| Convention | Expected | Risk |
|---|---|---|
| Standard (negative-is-bad) | `-0.275` | ✅ Safe |
| Absolute (positive-is-loss) | `0.275` | ❌ Easily misread as gains |

Check ALL files for sign inconsistency. When different files use different conventions for the same metric, flag it as HIGH severity.

Also check:
- Sharpe: should be positive for alpha-generating strategies, typically -2 to +2 range
- CAGR: should be plausible for the asset class and period (e.g. 0-15% for bonds, 5-30% for equities, -50% to +200% for crypto)
- Bootstrap confidence intervals: wide CI (upper > 5× median) suggests insufficient data or overfitting
- `expected_shortfall`: should always be negative (it's a loss metric)

### Step 5: Audit Shell Scripts

For every `.sh`, `.bat`, or `.ps1` script:

| Check | Method |
|---|---|
| All referenced files exist | `search_files(files)` for each path mentioned |
| Python interpreter path | Does `.venv/Scripts/python` exist? Is it hardcoded? |
| Quoting consistency | Mismatched/escaped quotes across echo statements |
| Step ordering | Is the causal dependency order respected (generate → execute → log → alert)? |
| Missing steps | Compare full vs daily scripts — does the cron path miss vital checks? |
| Virtual environment | Is the venv activated or hard-coded? |
| Working directory | Does `cd` go to the project root before running scripts? |
| Logging | Does it have `set -euo pipefail`? Does it tee to a log file? |

Check each Python module that the script calls — verify all file imports and paths referenced in the code resolve.

### Step 6: Verify Cron / Scheduled Task Integrity

Check BOTH:
- Windows: `schtasks /query /v /fo CSV` and grep for project-specific entries
- Linux: `crontab -l` and `/etc/cron.d/`, `/etc/crontab`

For each found task:
- Does the schedule match what the code/documentation claims?
- Does the task command actually exist?
- Does the user context match (run as correct user)?
- Last result code (0 = success, non-zero = failure)

When no task exists despite code claiming "daily @ 10:00 PT" or similar, flag as HIGH — the pipeline is documented as automated but is not.

Also check for **competing scripts**: multiple shell scripts in the same repo that do similar things differently (different venv paths, different step ordering, different logging). Note the divergence and recommend consolidation.

### Step 7: Cross-Reference Code-Generated Data with Code Logic

- Does `generate_signals.py` actually compute the targets that `positions.json` shows?
- Does `execute_trades.py` apply the stated constraints (vol target, concentration cap, stoploss)? Verify by tracing the field values.
- Does `trade_logger.py` correctly seed positions with the right stake amounts?

Spot-check: pick one pair and trace its values through: signals.json → positions.json → trade_history.json to confirm the chain is unbroken.

### Step 8: Validate Schema Uniformity

- Do all research result JSONs share the same top-level keys?
- Do all production JSONs share a consistent schema?
- Are there files with stale schemas (missing fields that newer files have)?
- Is the same field name used for the same semantic meaning across files?

### Step 9: Compile the Report

Structure as:

```
# Data File Audit Report
**Audited:** [date]
**Scope:** [file list]

## 1. Labeling Accuracy
### Finding 1.N — [Title] (Severity: HIGH/MEDIUM/LOW)
- **File:** `path`
- **Issue:** description
- **Evidence:** exact values, line numbers
- **Verdict:** PASS/FAIL

## 2. Metric Sanity
...one subsection per finding, same format...

## 3. Argument Consistency — Shell Scripts
...

## 4. File Path Correctness
...

## 5. Cron / Scheduled Task Integrity
...

## Summary of Issues by Severity
### HIGH
- [list]

### MEDIUM
- [list]

### LOW
- [list]
```

---

## Pitfalls

- **Don't assume sign conventions are consistent** — always verify by reading multiple files. The research engine and the stock backtest engine may store MaxDD with opposite signs.
- **Don't assume labels are accurate** — a label like "sma_252_binary" can hide multi-asset aggregation. Read the companion files.
- **Don't assume cron exists** — verify independently with OS task tooling. "Daily @ 10:00 PT" in a print statement is a claim, not proof.
- **Batch independent reads** — read all JSON files, all scripts, and list scheduled tasks in the same turn. The cross-referencing comes after all raw data is collected.
- **Trace one value end-to-end** — pick one entry (e.g. BTC/USDT stake) and trace it through signals.json → positions.json → trade_history.json to catch silent drift.
- **Check for stale state** — `alert_log.json` may have a `last_state` that hasn't been updated since the last alert check ran.
- **Distinguish scripts from active jobs** — a `.sh` file on disk does not mean a cron/scheduled task exists to run it. Verify each independently.
- **Shell quoting bugs are surface noise** — they matter for professionalism but don't usually break execution. Focus first on HIGH severity (missing automation, unreproducible research, sign convention errors).
