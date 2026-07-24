# Production Pipeline Fix Implementation

Systematic approach for applying surgical fixes to a production trading/research pipeline after audit findings have been identified. Complements `production-pipeline-audit.md` (which covers the FINDING phase) by covering the FIXING phase.

---

## When to Use

- You've completed an audit (using `production-pipeline-audit.md` or ad-hoc review) and now need to fix the issues
- User asks "fix all the issues" or "surgical fixes only" — no refactoring, no scope creep
- You're fixing a multi-file pipeline where changes in one file affect downstream consumers

---

## Core Principles

| Principle | Why |
|-----------|-----|
| **Read everything first** | You can't plan surgical fixes without seeing the full data flow |
| **Read the DATA files too** | What the code *intends* to write and what *actually exists* often differ. Check signals.json, positions.json, trade_history.json |
| **Plan all fixes before writing any** | Avoids "fix one thing → breaks downstream → fix that → cascading changes" |
| **Surgical patches only** | No refactoring, no "while I'm here" improvements. Change ONLY what's broken |
| **Backward compatibility** | Renaming fields? Add fallback: `.get("new_field", .get("old_field", default))` |
| **Verify syntax per-file** | `python -m py_compile file.py` after each file — catch mistakes immediately |
| **Update all consumers** | A data-format change (e.g. renaming `pnl` → `pnl_net`) requires updating every reader |
| **Document before/after** | Write an audit file so the user knows exactly what changed and why |

---

## Workflow

### Phase 1: Map the Surface

Read EVERY file in the pipeline directory. Do not skip any. Also read the pipeline runner script (`.sh`, `.ps1`, `.bat`) to understand execution order.

For each file, note:
- **Data read** — filenames, paths, expected format
- **Data written** — filenames, paths, output format
- **Constants/parameters** — literal values, hardcodes that should be dynamic
- **Assumptions** — what must exist for the code to work
- **Dead code** — defined but never used (STOPLOSS, config keys, imports)
- **Stubs** — `print("WOULD...")` paths with no real action

### Phase 2: Read the Actual Data Files

Production data files (JSON, feather, CSV) often have a different shape than what the code claims. Read:

- `signals.json` — field names, value types, datetime format
- `positions.json` — structure, stake values (are they real or hardcoded?)
- `trade_history.json` — field names, P&L fields, datetime format

This is the single most commonly skipped step and the single biggest source of failed fixes.

### Phase 3: Catalogue Every Issue

Group issues by type:

| Issue Type | Examples from this session |
|------------|---------------------------|
| **Missing data** | No equity field in signals.json → downstream sizing uses $1000 hardcode |
| **Dead code** | `STOPLOSS = -0.06` defined but never checked |
| **Missing feature** | P&L has no cost deduction (20bps) |
| **Format inconsistency** | Space-separated datetime instead of ISO 8601 T-separated |
| **No error handling** | `pd.read_feather(path)` crashes on corrupt file |
| **Consumer rot** | monitor_status.py references old field name |

### Phase 4: Plan the Fix Order

Fix in dependency order — downstream before upstream? Or fix upstream first and propagate? The right order depends on the change type:

- **Data format changes** (datetime, new fields): fix the WRITER first (upstream), then READERS (downstream)
- **Logic bug fixes**: can be done independently per file
- **Field renames**: write the new field in addition to (not instead of) the old one, then update readers, then remove the old field later

For this session's order:
1. `generate_signals.py` — adds equity field, fixes datetime, adds error handling
2. `execute_trades.py` — reads equity from signals, wires up STOPLOSS, error handling
3. `trade_logger.py` — cost accounting, error handling, datetime standardization
4. `monitor_status.py` — backward-compatible field name update
5. Audit file

### Phase 5: Apply Fixes

Use `patch` for surgical edits, not `write_file` (which replaces the entire file and can lose unrelated changes).

**Patch strategy for surgical fixes:**
- Match unique context (2-5 lines around the change point)
- Include docstring/comments marking the fix so the user can find it
- One logical change per patch call
- After each file, run syntax check

### Phase 6: Backward Compatibility

When renaming or restructuring data fields:

```python
# Bad — breaks all readers immediately
"pnl": round(pnl, 2)

# Good — old field still works (new code writes both)
"pnl_gross": round(pnl_gross, 2),
"pnl_net": round(pnl_net, 2),

# Reader side — safe fallback chain
t.get("pnl_net", t.get("pnl", 0))
```

This pattern lets the pipeline continue working before/after the deploy window without a simultaneous update of all files.

### Phase 7: Update All Consumers

Use `search_files` to find every reference to the old field/pattern across the entire production directory:
```bash
search_files('\.get\("pnl"|\["pnl"\]', path="production/")
```

Each consumer gets the backward-compatible `.get("new", .get("old"))` pattern. This is where most sessions fail — they fix the writer but miss the dashboard, alert monitor, or slack notifier.

### Phase 8: Document

Write to `audit/changes_made.md` (or `audit/changes_made_YYYY-MM-DD.md`):

```
# Production Pipeline Fixes — YYYY-MM-DD

## Files Modified

### 1. `path/to/file.py`
| Fix | Before | After |
|-----|--------|-------|
| **Title** | What it was | What it is now |

...

```

Use a table per file so the user can scan changes rapidly. Include before/after code behavior, not just "fixed X."

---

## Common Pitfalls

- **Skipping data file reads.** The code says it writes `"equity"` but the actual JSON has no such field. Always verify reality against intent.
- **Cascading breakage.** Renaming a field? `search_files` for every reader. Missed consumers silently produce wrong output.
- **Non-surgical scope creep.** "While I'm here" is the enemy. Fix ONLY the listed issues. Everything else is a separate PR.
- **Same fix, different files.** When the same pattern (e.g., try/except wrapping) needs to go in multiple files, apply it consistently each time — no one-off variations.
- **Upstream-first vs downstream-first confusion.** When adding a field that didn't exist: write it first (upstream generates it), then read it (downstream consumes it). Write-then-read, never read-then-hope.
- **Missing idempotency consideration.** A fix that causes the trade logger to skip a day because a timestamp format changed downstream is a regression. Test with existing data files.
- **Mixed date formats in dedup keys.** If you change `entry_date` from `YYYY-MM-DD` to `YYYY-MM-DDTHH:MM:SSZ`, any dedup/comparison logic that was string-matching will break. Always normalize to date-only for comparisons.

---

## Verification Checklist

- [ ] Every modified file passes `py_compile`
- [ ] Every modified file imports successfully (`python -c "import..."` if standalone)
- [ ] All consumers of renamed fields have backward-compatible fallbacks
- [ ] New data format is compatible with existing on-disk data (backward compat path)
- [ ] Audit document written with before/after per fix
- [ ] Pipeline runner script (`.sh`/`.ps1`) doesn't need changes
