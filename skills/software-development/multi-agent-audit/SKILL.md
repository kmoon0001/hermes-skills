---
name: multi-agent-audit
description: "Systematic multi-agent codebase audit using parallel subagents with different review lenses. Audit → consolidate findings → fix in parallel → verify. Prevents single-perspective blind spots."
version: 1.0.0
author: Hermes Agent
---

# Multi-Agent Codebase Audit

Use when a user asks for a code review, audit, bug hunt, security review, or "find everything wrong with X." The core insight: **one agent has one blind spot. Run parallel agents with different lenses to cover gaps.**

## Workflow

### Phase 1: Design the Lenses

Before dispatching, decide on 2-4 independent review perspectives. Each must be substantially different from the others:

| Lens | What it catches |
|------|-----------------|
| **Methodology** | Are the algorithms right? Off-by-one, wrong formula, wrong assumptions |
| **Security** | Hardcoded creds, injection, unsafe patterns, path traversal |
| **Numerical** | CAGR formula, Sharpe formula, volatility calc, sign conventions |
| **Error propagation** | What breaks when each component fails? Corrupt JSON, missing data |
| **Data integrity** | Labeling accuracy, metric sanity, format consistency |
| **Performance** | Unnecessary work, no caching, N+1 queries |
| **Type/mutable** | Python mutable defaults, type conflicts, int/float/None mixing |
| **Race/concurrency** | File collisions, atomic writes, shared state |

Never re-use a lens the same way twice. If a previous audit used a "methodology" lens, the next one should be "security + numerical + error propagation" — explicitly different.

### Proven Lens Configurations

For backtest engine / trading bot codebases, this 3-lens parallel configuration has proven most effective (July 2026 freqtrade audit — found 2 MAJOR + 5 MINOR bugs in one dispatch):

| Subagent | Lens | What it covers |
|----------|------|----------------|
| **Lens 1: Numerical + Methodology** | Pass F (formula audit) + Pass E (sign conventions) + Pass C (methodology pitfalls) | CAGR/Sharpe/MaxDD formulas, annualization, sign convention consistency, duplicated compute_metrics, documented pitfalls 0-17 |
| **Lens 2: Security + Error + Type** | Pass G (security) + Pass H (error propagation) + Pass I (type safety) | Failure chain tracing, atomic writes, JSON read wrappers, hardcoded secrets, eval/exec, subprocess injection, mutable defaults, or-traps, bare excepts |
| **Lens 3: Engine + State** | Pass A (cost) + Pass B (NaN) + Pass D (state management) | Cost handling (full notional vs turnover), NaN fill policies, setattr state mutation, RNG determinism, timezone consistency, index validation |

Each lens self-validates by running small Python verification scripts (not just reading code). The numerical agent verifies formulas with known inputs; the engine agent runs cost=0 sanity checks; the security agent traces failure chains end-to-end.

### Phase 2: Dispatch Subagents

Each subagent gets:
1. **Repo path** and file list
2. **Lens-specific checklist** — what to look for
3. **Known issues list** — what was ALREADY found by prior lenses (so they don't waste time rediscovering)
4. **Deliverable** — write findings to a file, not just the summary (so results persist)
5. **Goal** — self-contained, specific

**Parallel parent sweeps:** While subagents run, the parent agent should immediately run its own targeted grep sweeps for the most actionable patterns — duplicated functions, sign conventions, setattr mutations, mutable defaults, hardcoded secrets. This catches findings subagents might miss and produces results before the subagent reports arrive. Use these commands:
```bash
grep -rn "def.*compute_metrics\|def.*_compute_metrics" --include="*.py" production/ research/ stocks/
grep -rn "float.*np.min\|float.*np\.min" --include="*.py" research/
grep -rn "setattr(" --include="*.py" research/
grep -rn "r\[\"nav\"\]" --include="*.py" research/  # NAV aggregation pattern
grep -rn "api_key\|api_secret\|jwt_secret\|ws_token" --include="*.json" user_data/
```

```python
from hermes_tools import delegate_task

delegate_task(tasks=[
    {"goal": "...", "context": "...", "role": "leaf"},
    {"goal": "...", "context": "...", "role": "leaf"},
    {"goal": "...", "context": "...", "role": "leaf"},
])
```

### Phase 3: Consolidate Findings

When all subagents return, read their reports and categorize:
- **Critical** — wrong numbers, data loss, security hole, pipeline not running
- **Major** — dead code, missing error handling, silent failures
- **Minor** — labeling, formatting, documentation
- **Info** — optimization opportunities, technical debt

### Phase 4: Fix in Parallel

Group fixes by domain (production/, research/, stocks/) and dispatch fix subagents. Each one should:
- Make surgical changes (not rewrites)
- Verify the file compiles after each change
- Log the fix in a shared changes document

### Phase 5: Final Verification

After all fix agents return:
- Verify all modified files compile (python3 -c "import ast" check)
- Confirm runtime JSONs (signals.json, positions.json, etc.) are NOT committed
- Run the pipeline once if possible
- Commit + push

## Common Pitfalls

### Re-finding known issues
Always provide a "known issues" list to each new audit subagent so they don't re-discover yesterday's bug. Add it to their context explicitly.

### Overlapping audit scopes
If two subagents read the same file with different lenses, they may flag the same line differently. That's fine — the lenses are different. Document the overlap in the consolidated report.

### Fix agents stepping on each other
If two fix agents modify the same file, their changes must be in different functions or the later patch will fail. Group fixes by file, not by type, to avoid conflicts.

### No verification step
Always syntax-check (or compile-check) every modified file. The Python mutable-defaults trap and bash escaping errors are the most common silent failures.

### Subagent timeouts from file discovery
When subagents are given a repo path but no file list, they spend 30-60% of their time budget on `search_files` and `terminal find` calls just to locate the files they need to read. On Windows, `search_files` with backslash paths is unreliable — it often returns 0 results for patterns that exist. **Always provide an explicit file list** in the subagent context: include the exact paths of the 5-10 files each lens needs to examine. This cuts dispatch-to-results time from 10+ minutes to 2-4 minutes, and prevents interrupted subagents that time out before producing results.

## Example: Three-Audit Pass (as used in Cycle 6)

**Pass 1 — Standard audit:** 3 subagents (production pipeline, backtest engine, data/scripts)
**Pass 2 — Fresh lens:** 1 subagent (security + numerical accuracy + error propagation + mutable defaults)
**Pass 3 — All fixes:** 3 fix batches (production safety, Sharpe + research cleanup, automation + scripts)

Each pass was explicitly told NOT to report what the prior pass found. The fresh-lens pass caught the Sharpe log-return formula that the methodology pass missed.

## Related

- `systematic-debugging` — for single-bug root cause analysis (complementary; this skill is for full-codebase sweeps)
- `github-code-review` — for PR-level review (this skill is deeper, for auditing entire repos)
