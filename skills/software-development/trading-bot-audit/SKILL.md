---
name: trading-bot-audit
description: "Systematic 3-tier codebase audit for trading bots: production pipeline, backtest engine, data/scripts. Proactively discover hidden bugs (cost handling, position sizing, dead code, labeling, cron gaps) before they cause losses. Covers the full audit-and-fix lifecycle with parallel subagent dispatch."
category: software-development
version: 1.0.1
---

# Trading Bot Codebase Audit

## When This Skill Applies

- You've found several bugs in a bot and suspect more are hiding
- It's been months since the codebase had a systematic review
- A strategy's live metrics don't align with backtest expectations
- A new developer or AI agent inherits the bot codebase
- The user proactively asks "should we double check the rest of the bot?"

## The 3-Tier Audit Methodology

Decompose the audit into three independent tiers, run in parallel via `delegate_task`:

### Tier 1: Production Pipeline

**Scope:** Files that control what the bot actually trades — execute_trades.py, generate_signals.py, strategies/, monitor_status.py, check_alerts.py, trade_logger.py.

**Checklist:**
- **Position sizing** — Does it use real equity (from signals/wallet) or a hardcoded value (e.g., `$1000 dry_run_wallet`)?
- **Cost accounting** — Is P&L gross or net of trading costs? The research backtest includes 20bps; the live pipeline often omits it entirely.
- **STOPLOSS dead code** — Is the stoploss constant defined but never checked in any execution path? Wire it up or remove it.
- **Error handling** — What happens if yfinance download fails, JSON is corrupt, feather file is missing? Silent skip (good) or hard crash (bad)?
- **Signal alignment** — Does the live signal computation match the validated backtest? (Same SMA windows, vote threshold, Parkinson vol window, vol_target?)
- **Strategy-research alignment** — Does the live Freqtrade strategy match the research methodology? Check: trailing stops (should be OFF if research uses signal-only exits), ROI timers (should be loose enough that signal exits fire first), stoploss (should match research), and execution model (market vs limit orders). Common gap: Freqtrade strategies often have trailing_stop=True and tight minimal_roi that were never part of the research backtest — this silently diverges live behavior from validated results.
- **Position reconciliation** — Does the execution pipeline know which positions are already open? Without reconciliation, every daily run would re-buy already-held pairs. Check: a `_get_open_positions()` function reading trade_history.json, and the position-determination loop branching on `already_held`.
- **Direction consistency** — Long-only as designed, or does any path accidentally allow shorts?
- **Datetime format** — Standardized to ISO 8601 T-separated across all JSON outputs? Or mixed formats?
- **Signal wiring trace** — For every field consumed by a downstream script via `sig.get("field", default)`, trace back to confirm the UPSTREAM script actually writes that field. Common bug: `execute_trades.py` reads `sig.get("strength", 1.0)` but `generate_signals.py` never sets a `strength` field, so strength-based sizing silently degrades to always-1.0.

### Tier 2: Backtest Engine

**Scope:** cycle*_backtest.py, experiment runners, walkforward_validation.py, expanding_window.py. See `backtest-debugging` for the full 5-category audit framework (Cost, NaN, Methodology, Architecture, Data Integrity).

**Key checks that surface most frequently:**
- **Cost handling** — Charged on full notional every day (wrong) or only on target allocation changes (correct)?
- **Sign convention** — Is `max_drawdown` written as negative across ALL result JSONs? Positive values are ambiguous and propagate silently.
- **NaN fill policy** — `fillna(0)` vs `fillna(1)` vs `fillna(False)` — each choice biases the result differently.
| **Feature backtest NAV mismatch** — The feature backtest harness (`backtest_features.py`) may use `result[\"nav\"]` (which includes all 5 sleeves) while the experiment runner uses `result[\"sleeve_b\"] / SLEEVE_WEIGHT` (B-only, normalized). This makes feature comparisons invalid — the baseline CAGR can differ by 10+pp between the two systems. Fix: align the feature harness NAV aggregation with the experiment runner's. See backtest-debugging Pitfall 16.

### Tier 3: Data + Scripts + Automation

**Scope:** All result JSONs, shell scripts, cron jobs, Windows Scheduled Tasks, file paths.

**Checklist:**
- **Metric sanity** — CAGR, Sharpe, MaxDD, Calmar in plausible ranges? No NaN, no zero-DD holes?
- **Labeling accuracy** — Do JSON field names and values match what the generating code actually computed?
- **Sign conventions** — MaxDD negative everywhere? Calmar = CAGR / |MaxDD|?
- **Cron/automation verification** — Does a scheduled task or cron job ACTUALLY run the pipeline? Run `hermes cron list` or `schtasks /query`. Don't trust inline comments. **ALSO: is the automation Hermes-dependent?** If the user says "this is for someone else," check whether cron jobs are Hermes-only. Hermes cron breaks for non-Hermes users — flag for standalone delivery conversion (see `standalone-project-delivery` skill).
- **Script hardening gaps** — Check all production scripts for the hardening checklist: error handling on I/O, atomic writes (os.replace, not write_text), idempotency (same-date rerun protection), exit codes (0/1/2), standalone executability. Missing any of these is a P1 finding.
- **Watchdog missing** — Is there a watchdog monitoring bot health, data freshness, disk space, pipeline status, and equity? If not, flag as CRITICAL — ops risks > code risks.
- **Shell script correctness** — Absolute venv paths (brittle) vs relative `SCRIPT_DIR` pattern. Check for escaped-quote typos. Verify with `bash -n script.sh`.

## Running the Audit

### Step 0: Repo Discovery (Before Dispatching)

Before launching subagents, spend 2-3 minutes surveying the repo so each subagent gets an accurate file list, recent commit context, and known-issue set. This prevents subagents from wasting time rediscovering already-fixed bugs or auditing files that don't exist.

```
1. LOCATE the repo:
   find /c/Users/<user> -maxdepth 4 -name "freqtrade*" -type d   # or pattern-match the bot name
   find /c/Users/<user> -maxdepth 4 -name "cycle*_backtest*" -o -name "run_*_experiment*"

2. KEY FILES — list and count:
   ls research/*.py production/*.py production/*.sh user_data/strategies/*.py
   wc -l <key files>   # gives subagents a size budget for how much to read

3. RECENT HISTORY:
   git log --oneline -15                 # what fixes already landed
   git status --short                    # working tree state (uncommitted changes, untracked files)

4. SCAN RESULT JSONs:
   cat research/*results*.json | python3 -m json.tool | head -50   # quick metric sanity check
   # Look for: CAGR/Sharpe/MaxDD values, sign conventions, obvious red flags (NaN, zero, positive DD)

5. BUILD KNOWN-ISSUES LIST:
   # Cross-reference git log messages + memory entries for already-documented bugs.
   # Inject this list into each subagent's context so they skip already-found issues.
```

The output of this step is the **subagent dispatch brief** — a structured context block with: repo path, file list with line counts, recent git history, known issues, and the specific checklist for that tier.

### Step 1: Dispatch 3 parallel subagents

```python
subagent_tasks = [
    {"goal": "Audit production pipeline...", "context": "Repo: ... Files to check: ..."},
    {"goal": "Audit backtest engine...",    "context": "Repo: ... Files to check: ..."},
    {"goal": "Audit data/scripts/cron...",  "context": "Repo: ... Files to check: ..."},
]
```

Each subagent gets:
- The repo path, specific file list, the audit checklist (above)
- A list of KNOWN ISSUES so they don't waste time rediscovering already-documented bugs
- An output path for the report (e.g., `audit/<tier>_audit.md`)

### Step 2: Review consolidated findings

Classify by severity:
- **CRITICAL** — Live money issues (automation gap, position sizing wrong, cost missing). Fix immediately.
- **MAJOR** — Could degrade performance or cause future bugs. Fix soon.
- **MINOR** — Bookkeeping, labeling, code quality. Fix when convenient.

### Step 3: Dispatch fix subagents (parallel)

Group fixes into logical batches and dispatch `delegate_task` subagents to apply surgical patches. Each fix agent should:
- Change only what's broken — no rewrites
- Verify each file compiles/syntax-checks after changes (`python3 -c "import ast; ast.parse(open(path).read())"` for .py, `bash -n script.sh` for shell scripts)
- Append a before/after table to `audit/changes_made.md` documenting every file changed, what was wrong, and the fix
- Do NOT modify runtime state files (signals.json, positions.json, alert_log.json, trade_history.json — gitignored)

Typical fix batches:
1. Production pipeline (position sizing, cost, STOPLOSS, error handling, datetime)
2. Automation + scripts (cron job creation, shell script fixes, venv paths, alert log)
3. Backtest engine + data (MaxDD sign, simulate_sleeves cost bug, stale results)

**Important:** After all fix batches complete, verify syntax of EVERY modified file in one sweep. Also check that changes didn't conflict across fix agents that touched different sections of the same file.

### Step 4: Update long-term memory

When subagents find labeling errors or metric misstatements that have propagated into memory (e.g., "+8.73% CAGR mislabeled as SPY-only"), correct memory immediately. Wrong labels in memory infect every future session.

**Essential cron verification:** After a fix subagent creates or modifies cron jobs, ALWAYS run the job once with `cronjob action='run'` and confirm it reports status 'ok'. Also verify the schedule timezone — check `next_run_at` field. A schedule of `0 17 * * *` = 5 PM local time, not 10 AM. Verify with `hermes cron list`.

### Step 5: Fresh-lens review (orthogonal)

After the initial 3-tier audit is fixed, dispatch one more subagent with a completely different lens that explicitly excludes already-found issues. The goal is to catch what the tiered audit missed.

**Fresh-Lens Brief (copy-paste to the subagent context):**
```
Audit the codebase from a completely different lens than the previous review.
Do NOT re-check simulation methodology, cost handling, labeling, position sizing,
or production pipeline bugs — that was already done. Instead inspect for:

1. SECURITY: hardcoded API keys/tokens, command injection, path traversal,
   eval/exec/pickle usage, setattr on modules, hardcoded temp file paths.

2. NUMERICAL ACCURACY: Is Sharpe mean(simple_returns)/std(simple_returns) or
   mean(log_returns)/std(log_returns)? Is CAGR formula correct? Is max_drawdown
   global or rolling? Annualization consistent? Risk-free rate correct?
   Falsy-zero traps: `equity or default` masks equity=0.0.

3. ERROR PROPAGATION: Trace dependency chain. Try/except on every JSON read?
   Atomic writes (.tmp → rename) or direct (corrupt on interruption)?

4. MUTABLE DEFAULTS: Classic Python `def fn(items=[])` trap.
```

### Step 6: Clean up artifacts & commit

Clean up leftover subagent artifacts:
- `stocks/.venv/` — created by backtest-run subagents; not part of repo
- Validation scripts (`_verify_combine.py`) — one-off, remove after results confirmed
- Duplicate shell scripts — consolidate into canonical script, remove duplicate
- Orphaned parameter-override files (`tmpvgkcagf7.json`) and temp/research scripts flagged as security issues

Commit and push:
1. `git add` all modified source files (.py, .sh, research JSONs, audit/ docs)
2. `git rm` any deleted files
3. Stage ONLY source and result files — skip runtime state JSONs (gitignored)
4. Write a descriptive commit message with summary of each batch
5. `git push`

## Common Patterns Found

**Automation Gap** — The code says it runs daily, cron jobs exist for monitoring, but nothing actually runs the trading pipeline. Always verify with `hermes cron list`.

**Position Sizing Uses Fixed Wallet** — Hardcoded `dry_run_wallet: 1000`. Fix: generate_signals writes an `equity` field, execute_trades reads it with a fallback chain.

**Cost Accounting Absent in Live** — Research includes 20bps, production records only gross P&L. Fix: add `TRADING_COST_BPS` to trade_logger with `pnl_gross/cost/pnl_net`.

**STOPLOSS Dead Code** — Defined but never checked. Fix: `_check_stoploss()` called per-pair before sizing.

**MaxDD Sign Convention** — Research JSONs store as positive (double-negation), stock JSONs as negative. Fix: recursive JSON walker.

**No Atomic Writes** — `write_text()` directly; interrupted writes corrupt files. Fix: `_atomic_write(path, data)` helper (.tmp → rename) in every file.

**Sharpe Log-Return Formula** — `mean(log(1+r))/std(log(1+r))` instead of `mean(r)/std(r)`. Systematic downward bias for crypto. Fix: one line per metrics function. See backtest-debugging Pitfall 12.

## Pitfalls

### Never Trust Docstrings for Automation

Always verify with `hermes cron list` or `schtasks /query`. A cron job that was created but never tested is functionally the same as no cron job. After creating, run once with `cronjob action='run'`.

### Cron Deliver Mode

`deliver='origin'` only reaches the current chat session. When the session closes, delivery goes nowhere. Use `deliver='local'` for persistence. Use `origin` only for testing.

### Cron Job Prompt vs Script

- **Agent-driven** (default): LLM runs each step. Prompt must be self-contained. Use `enabled_toolsets=['terminal', 'file']` to limit tokens.
- **Script-only** (`no_agent=True`): scheduler runs a script directly. No LLM tokens. Use for simple runners like paper_trade.py.
For multi-step pipelines, prefer agent-driven mode with the consolidated shell script as a single command.

### The Backtest Bug That Makes You Underconfident

`simulate_sleeves()` charging cost on full notional daily inflates cost drag 6-30x on long backtests. This makes backtest METRICS CONSERVATIVE (CAGR is understated, not overstated). The strategy may be stronger than the numbers suggest. Fix the cost model, not the cost rate.

### Memory Contamination

When subagents discover labeling errors, update long-term memory immediately before the wrong labels propagate to future sessions.

### Subagent Rate-Limit Failure Recovery

When all parallel audit subagents fail with HTTP 429 (rate limiting) — common on free-model tiers — do NOT discard the work. Each subagent's live transcript (`cache/delegation/live/<id>/task-*.log`) contains every tool call and result that succeeded before the API failure. These partial transcripts often contain enough tool-output data (file reads, terminal output, grep results) to complete the audit without re-running the subagents. 

**Recovery procedure:**
1. Read all `task-*.log` files — they contain the full tool/assistant trace
2. Extract findings from the transcripts: tool results (read_file, terminal, search_files) contain the actual file contents and command outputs the subagent observed
3. The subagent's assistant text often includes inline analysis of what it found before the API call limit was reached
4. Combine partial findings with your own direct reads to complete the audit

**Prevention:** Prefer `no_agent=true` script-based cron jobs for pipelines that don't need LLM reasoning. For audits where subagents are essential, use a model with higher rate limits or accept that the transcripts are the real deliverable, not the final summary.

### Data Integrity: Shell Scripts

Absolute venv paths → `SCRIPT_DIR`-relative pattern. Check with `bash -n script.sh`. Stale `alert_log.json` `last_state` → clear to `{}`, self-heals on next run. Competing "daily" scripts → pick one, document, archive the other.

### Data Integrity: JSON Results

Metric sanity check every value. MaxDD negative everywhere. Calmar = CAGR / |MaxDD|. Datetime format ISO 8601 T-separated. No falsy-zero traps (`equity or default` masks 0.0).

### Production Package Import Failure

**Symptom:** `ModuleNotFoundError: No module named 'production'` when running production scripts directly (`python production/generate_signals.py`). The shell script (`run_cycle6_full.sh`) works because it `cd`'s into the project root first, but direct Python runs fail.

**Cause:** `production/` directory has no `__init__.py`. Python can't resolve `from production.util import atomic_write` without it. The scripts use `sys.path.insert(0, str(ROOT))` which adds the project root, but without `__init__.py`, the directory isn't recognized as a package.

**Fix:** Create an empty `production/__init__.py`. One-liner: `touch production/__init__.py`. All production scripts that import from `production.util` (execute_trades.py, generate_signals.py, etc.) will work when run directly.

**Detection:** `ls production/__init__.py` — if missing, create it. Also check: `grep -rn "from production" production/` to find all scripts that depend on the package import.

### CI Lint Failures — Ruff Fix Patterns

When CI runs `ruff check` on production/research files, three common failures surface:

1. **E401 Multiple imports on one line** — `import sys, os, json` → split to one per line: `import json\nimport os\nimport sys`
2. **F401 Unused import** — `import os` (never used) → remove it. Check: `grep "os\." file.py` to verify it's truly unused before removing.
3. **F841 Unused variable** — `n = len(decision_dates)` (never read) → remove the assignment line.

Fix with `ruff check --fix` for automatic fixes, or manually apply. Verify with `ruff check <files> --no-cache` after fixing. The CI typically only lints ~3 files (the ones in active production use), so focus fixes there first.

### Step 7: Post-Audit Mechanical Fixes

Some audit findings are mechanical — large numbers of identical changes across many
files that don't require per-case judgment. Docstrings, import sorting, type
annotation additions, and whitespace normalization all fall into this category.

**Don't fix these one at a time.** Instead:

1. **Scan** — Use `execute_code` with Python's `ast` module to enumerate every
   occurrence (e.g., every public function missing a docstring).
2. **Categorize** — Group by domain (production, research/stocks, tests).
3. **Delegate in parallel** — Dispatch one subagent per domain with the exact
   list of file:line:function tuples and what to add.

See `references/docstring-gap-fix.md` for the full two-phase workflow with the
reusable AST scanning script and delegation template.

## Cross-Reference

For detailed per-sleeve decomposition, cost interaction analysis, and the 5-category audit framework, see `backtest-debugging`. For packaging a bot for non-Hermes delivery, see `standalone-project-delivery`. For post-audit mechanical fixes like docstring gaps, see `references/docstring-gap-fix.md`. This skill covers the production + data tiers that backtest-debugging doesn't reach.
