---
name: multi-agent-code-audit
description: "Parallel multi-agent code audit workflow: dispatch N subagents to audit different slices (production, backtest, data), consolidate findings, run a fresh-lens follow-up on a different axis (security, numerical accuracy, error propagation), then dispatch fix agents. One-shot pipeline for comprehensive codebase review."
version: 1.0.0
author: Hermes Agent
---

# Multi-Agent Code Audit Workflow

Systematic codebase audit using parallel subagents. Designed to catch what a single reviewer misses — different lenses find different bugs.

## When to Use

- First audit of a new or inherited codebase (especially one with live money)
- Bug pattern discovered — suspect more of the same exist
- "Let's find more issues" — systematic sweep rather than ad-hoc
- Before/after major refactor — verify nothing broke
- Pre-deployment security + correctness gate

## The Workflow (3 Phases)

### Phase 1: Parallel Discovery (3 subagents)

Dispatch 3 subagents simultaneously via `delegate_task(tasks=[...])`, each with a different slice:

| Task | What it audits | Example files |
|------|---------------|--------------|
| **Production pipeline** | Live/running code — execution, signal generation, logging, monitoring | execute_trades.py, generate_signals.py, strategies/, monitor_status.py, trade_logger.py |
| **Backtest / research engine** | Simulation logic, cost handling, NaN edge cases, formula correctness | backtest.py, cycle6_backtest.py, walkforward_validation.py |
| **Data + scripts** | JSON result files, shell scripts, cron configs, labeling accuracy | *.json, *.sh, cron jobs, config files |

Each subagent gets:
- The repo root and target files
- An audit checklist specific to its slice (see checklists below)
- A list of ALREADY-KNOWN issues so it doesn't waste time re-discovering them
- A deliverable: findings report with file:line, severity, and fix

**Checklist for Production pipeline subagent:**
  - Signal computation matches research? Off-by-one on rolling windows?
  - Cost handling present and correct?
  - Dead code (STOPLOSS defined but never checked)?
  - Edge-case handling (yfinance fails, prices stale, vol=0, corrupted JSON)?
  - Direction consistency (long-only as designed, no accidental shorts)?
  - Logging sufficient to reconstruct P&L?
  - Position sizing: hardcoded values vs real equity?

**Checklist for Backtest engine subagent:**
  - Cost on full notional every day or only on target changes? (The #1 bug)
  - Cost applied uniformly across all sleeves/variants?
  - Parkinson vol formula correct? Ann factor matches asset class?
  - SMA min_periods set correctly?
  - NaN fill values: conservative (0/bear) or optimistic (1/bull)?
  - Timezone handling consistent (all UTC)?
  - Intended trading frequency matches execution model?
  - SLEEVE_WEIGHT normalization? No double-compounding?

**Checklist for Data + scripts subagent:**
  - Labeling accuracy — do JSON field names match what the code computed?
  - Metric sanity — CAGR < 100%, Sharpe in [-1,2], MaxDD > -100%?
  - Sign conventions — MaxDD all negative? Consistent across files?
  - Script argument consistency — do shell scripts call the right Python files with the right params?
  - File paths — do scripts reference files that actually exist?
  - Cron job params — schedules, workdirs, model overrides correct?

### Phase 2: Consolidate + Fresh Lens

After Phase 1 returns, review findings. Then dispatch a **single fresh-lens subagent** with a completely DIFFERENT audit axis:

| Lens | What it checks | Example issues found |
|------|---------------|-------------------|
| **Security** | Hardcoded secrets, command injection, eval/exec, setattr from unvalidated files | Temp-file-based setattr, stale credentials |
| **Numerical accuracy** | CAGR formula, Sharpe formula (log vs simple returns), MaxDD (global vs rolling), annualization days | Sharpe using log returns biases crypto Sharpe downward |
| **Error propagation** | What breaks when each step in the pipeline fails — atomic writes, try/except on reads, stale state | JSON writes without atomic pattern, cascading crash on corrupt input |
| **Type safety + mutable defaults** | `def fn(items=[])`, `or` falsy traps, implicit type coercion | `equity = x.get("k") or default` masks $0 equity |

Give the fresh subagent:
- The Phase 1 findings (so it doesn't duplicate)
- A specific, different checklist
- The instruction: "Do NOT report already-found issues. Report ONLY new findings from this fresh lens."

### Phase 3: Fix

After all findings are collected, dispatch fix subagents. Each fix agent handles one group of related fixes (production pipeline fixes, data fixes, backtest engine fixes). Give them:
- The consolidated findings report
- Specific, surgical instructions per fix
- "Verify each file compiles after changes"

## Pitfalls

1. **Overlapping subagents** — Two subagents checking the same file for different things can conflict. Explicitly assign file ownership per subagent.
2. **Fabrication risk** — Subagents may claim "fixed" without actually changing anything. Require verifiable returns: file paths, line numbers, metric values. Spot-check compile status.
3. **Fix conflicts** — Two fix agents editing the same file can overwrite each other. Group fixes by file ownership, not by issue type. The production pipeline fixer and the backtest engine fixer should never touch the same file.
4. **Already-known issue dilution** — Without a "known issues" list, subagents waste time re-finding bugs from the last audit round. Always provide a DO-NOT-REPORT list.
5. **Fresh lens still finds stale issues** — The fresh-lens agent may still report something fixed in Phase 3 if Phase 3 hasn't run yet. Order matters: fresh lens runs BEFORE fixes, so its findings are new.
6. **Too many fix subagents** — Fixing 15 files across 5 subagents creates coordination overhead. Limit to 2-3 fix subagents, each owning a coherent slice (production/, research/ + stocks/, scripts/ + data/).

## Output Structure

```
audit/
├── production_audit.md       # Phase 1 — production pipeline
├── backtest_audit.md         # Phase 1 — backtest engine
├── data_audit.md             # Phase 1 — data files + scripts
├── security_and_accuracy.md  # Phase 2 — fresh lens findings
├── production_safety_fixes.md # Phase 3 — production fixes
├── sharpe_and_research_fixes.md # Phase 3 — research fixes
└── changes_made.md           # Consolidated before/after log
```

## Related

- `backtest-debugging` — deep methodology for backtest engine issues (extends Phase 1's backtest subagent checklist)
- `requesting-code-review` — pre-commit review (lighter weight, single-file focus, for before-merge gates)
