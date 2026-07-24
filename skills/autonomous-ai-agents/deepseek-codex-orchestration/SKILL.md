---
name: deepseek-codex-orchestration
description: "Orchestrate DeepSeek V4 models (via OpenCode CLI or Hermes) for multi-pass codebase audits and fixes. Analysis → implementation → verification pipeline."
version: 2.0.0
author: Hermes Agent
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [orchestration, multi-agent, opencode, deepseek, audit]
    related_skills: [opencode, claude-code, autonomous-ai-agents]
---

# DeepSeek + OpenCode Orchestration (v2 — 2026-07)

**Codex CLI + OpenRouter does NOT work.** Codex uses OpenAI's `/v1/responses` API which OpenRouter doesn't support. Use OpenCode CLI for implementation. Claude Code + OpenRouter also does not work (Anthropic-specific model-metadata endpoints aren't emulated). 

Use DeepSeek models (via OpenCode CLI) as the coding/analysis layer, orchestrated by Hermes.

## When to Use

- Multi-pass codebase audits (analysis → fix → verify → deeper analysis)
- Building features that need research + implementation
- Parameter optimization sweeps
- Debugging sessions (deep analysis traces root cause, then implementation fixes)
- Any task where splitting analysis from implementation reduces error rate

## Recommended Models (verified 2026-07)

| Phase | Model | Tool | Speed | Best For |
|-------|-------|------|-------|----------|
| Analysis | `deepseek-v4-pro` | `opencode run` (read-only) | Slow (~5min) | Deep cross-file logic, config drift, edge cases |
| Implementation | `deepseek-v4-flash` | `opencode run` | Fast (~2min) | Surgical fixes, refactoring, test generation |
| Final fix | V4 Pro analysis → Hermes fixes | Hybrid | Medium | Complex fixes needing human judgment |

**Do NOT use OpenRouter `:free` models** — all 13 listed free models return provider errors or lack tool support. Only paid models (`deepseek-v4-flash`, `google/gemini-2.5-flash`, etc.) work with OpenCode.

## Multi-Pass Audit Pattern (proven this session — 64 issues resolved)

```
Pass 1: V4 Flash → find bugs, fix them, commit  (initial sweep)
Pass 2: V4 Flash → high-severity fixes, commit  (safety, correctness)
Pass 3: V4 Flash → medium-severity fixes, commit (quality, duplication)
Pass 4: V4 Flash → low-severity fixes, commit   (docs, comments)
Pass 5: V4 Pro  → deep analysis ONLY (read-only, 'DO NOT EDIT ANY FILES')
Pass 6: Hermes reads V4 Pro findings, fixes with patch/write_file tools
```

**Why this layering works:** V4 Flash is fast and practical for 80% of issues. V4 Pro catches subtle cross-file logic errors Flash misses (NameError bugs from prior refactors, config drift between research and production, talib vs pandas SMA divergence). Hermes handles the final surgical fixes where model judgment matters.

## OpenCode + DeepSeek Setup

```bash
# On Windows, extract key from system env vars:
export DEEPSEEK_API_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')")

# Run implementation task:
cd /path/to/repo && opencode run "Fix all high-severity issues..." --model deepseek/deepseek-v4-flash

# Run analysis-only task:
cd /path/to/repo && opencode run "ANALYSIS ONLY — DO NOT EDIT. Audit for..." --model deepseek/deepseek-v4-pro
```

**Timeout warning:** V4 Pro analysis passes can exceed 300s on large codebases. Set terminal timeout to 600s. V4 Flash typically completes within 180s.

## Key Research Pattern: Direct Edit, Not setattr

When running parameter sweeps on a backtest engine:

```bash
# WRONG — setattr can cause hangs when constants propagate through
# existing module state (pandas rolling windows, cached computations)
setattr(module, 'CONSTANT', new_value)
result = experiment()

# RIGHT — edit the source file directly, run, then revert with git
patch(path, old_string, new_string)  # change the constant
terminal('python -B experiment.py')  # run
terminal('git checkout experiment.py')  # revert
```

The setattr approach silently breaks when the constant is read at module-import time (Python's mutable-default-arg pattern) or when changing it creates edge cases in cached computations that cause infinite loops or hangs.

## Research vs Production Backtest Discrepancy

**Research pipelines and trading backtesters simulate differently.** A research pipeline (portfolio-level sleeve simulation) will produce different results from a trade-level backtester (Freqtrade, Backtrader, etc.) because:

| Research Pipeline | Trade-Level Backtester |
|---|---|
| Portfolio NAV computed directly | Individual trades opened/closed |
| Continuous position sizing | Discrete entry/exit with slippage |
| No order book simulation | Order book depth + fill price |
| Fee applied to NAV | Fee per trade |

**Solution:** Use the research code as the signal source for production, not a replicated strategy in the trading platform. Run a daily signal generator that imports the research code and outputs positions. The trading platform executes those positions — it doesn't recompute signals.

```
Research Code → generate_signals.py → signals.json → execute_trades.py → OKX API
```

## Single Most Impactful Optimization: Concentration Cap

Adding a per-symbol concentration cap (max 40% of NAV per symbol) was the single most impactful optimization, improving CAGR from +64% to +110% and C-B from +0.17% to +0.55%. Implement it in the portfolio aggregation step, not in the per-signal computation.

## Workflow

### Phase 1: Analysis (V4 Pro via OpenCode, read-only)

```
opencode run "ANALYSIS ONLY — DO NOT EDIT. Audit for X, Y, Z..." --model deepseek-v4-pro
```

V4 Pro reads files, traces logic, reports findings. No edits. Timeout: 300-600s.

### Phase 2: Implementation (V4 Flash via OpenCode)

```
opencode run "Fix all N issues: 1) file:line — change X to Y..." --model deepseek-v4-flash
```

V4 Flash makes surgical edits, runs tests, reports results. Timeout: 180-600s.

### Phase 3: Review & Final Fix (Hermes)

Hermes reads the V4 Pro analysis, applies the most nuanced fixes with `patch`/`write_file`, verifies with `terminal`, commits.

### The Hybrid Pattern (most reliable for complex fixes)

1. V4 Pro analyzes (read-only) → produces findings
2. Hermes reads the findings, decides which need human judgment
3. Hermes fixes the high-judgment items (VOL_TARGET values, NameError bugs from refactors)
4. V4 Flash fixes the mechanical items (narrow bare excepts, extract duplicated code)
5. Hermes runs tests, commits

**When to use hybrid vs full-auto:**
- **Full-auto** (V4 Flash does everything): mechanical fixes, style changes, adding comments
- **Hybrid** (V4 Pro→Hermes→V4 Flash): config values, logic changes, cross-file refactors

### Example Session Flow (Backtest Audit)

### Phase 4: Iterate (back to Codex if needed)

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| OpenRouter `:free` models | Provider errors, no tool support | Use paid models only (`deepseek-v4-flash`, `gemini-2.5-flash`) |
| Codex + OpenRouter | 404 on `/v1/responses` | Codex requires Responses API — OpenRouter doesn't have it. Use OpenCode instead |
| Claude Code + OpenRouter | 404 on model discovery | Anthropic-specific metadata endpoints not emulated. Use real Anthropic key |
| V4 Pro timeout on large codebases | 300s timeout | Set terminal timeout to 600s |
| DeepSeek key not in shell | empty DEEPSEEK_API_KEY | Extract from Windows: `powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')"` |
| `git add -A` grabs venv | Thousands of venv files staged | Use explicit `git add file1 file2...` or `.gitignore` for venv |
| Atomic write cross-platform | `FileExistsError` on Windows | Use `os.replace()` not `Path.rename()` in shared utilities |
| Stale VOL_TARGET in Freqtrade strategy | Live bot under-sizing by 33% | Research and production must use same vol_target constant |

## Context Sharing

Write context to Hermes persistent memory before dispatching Codex:
```
memory(action='add', target='memory', content='Shared context for Codex: ...')
```

## Parallel Validation Pattern

When validating research, dispatch multiple `delegate_task` subagents in parallel (walk-forward, dropout, expanding-window tests) while using Codex for standalone analysis and terminal background for long runs.

See `references/parallel-validation-pattern.md` for the full architecture.
See `references/coding-agent-compatibility.md` for OpenRouter/provider compatibility matrix.
