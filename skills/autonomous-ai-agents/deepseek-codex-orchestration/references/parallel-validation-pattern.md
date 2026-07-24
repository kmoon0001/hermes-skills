# Parallel Subagent + Codex Hybrid Validation Pattern

Use this pattern when you need to run multiple independent validation tests in parallel while also having Codex available for standalone analysis tasks.

## Architecture

```
Orchestrator (deepseek-reasoner)
├── Subagent A: Walk-forward validation      (delegate_task)
├── Subagent B: Symbol dropout test           (delegate_task)
├── Subagent C: Expanding-window backtest     (delegate_task)
├── Codex: Standalone code analysis           (codex exec)
└── Direct terminal: Final optimization run   (terminal background)
```

## When to Use

- Phase-based research (validate → improve → production)
- Parallel independent tests (walk-forward, dropout, rolling windows)
- Analysis tasks that benefit from separate reasoning (Codex reading/finding)
- Final verification runs (terminal background for reliability)

## Subagent Timeout Warning

**`delegate_task` subagents have an effective ~600s timeout.** This is the API-call budget, not wall-clock time. For long-running tasks:

- Each experiment run takes 3-5 minutes
- 6 runs × 3 min = 18 minutes = ~1080 seconds
- Subagents will **time out** before completing all runs

**Solution: Run directly in terminal background instead.**

```python
# This WILL time out for >600s total:
task = delegate_task(goal="Run 6 backtests")

# This works for long jobs:
terminal(command="python -B research/symbol_dropout.py", background=true, timeout=3600)
```

## Context Sharing

Subagents start with ZERO knowledge of your conversation. Pass everything they need in the `context` parameter:

```python
delegate_task(
    context="Project at C:\\path\\to\\repo. Code structure: ... Current constants: ...",
    goal="Run validation test: ...",
)
```

Do not rely on shared memory (MCP `shared_memory`) for cross-agent context — it's unstable. Use Hermes persistent memory as fallback.

## Phase Handoff

Subagents report results as async messages that re-enter your conversation. The orchestrator reviews and decides next phase. Don't wait/poll — just continue working. The results arrive when ready.

## Terminal Background vs Subagent

| Factor | terminal(background=true) | delegate_task |
|--------|--------------------------|---------------|
| Timeout | Unlimited (set timeout=3600) | ~600s effective |
| Parallelism | One process | Up to 3 tasks |
| State isolation | Separate shell | Isolated agent |
| Works for | Long-running batch jobs | Parallel independent research |

## Windows Experiment Runner Quirk

On Windows, Python subprocess calls that import heavy data (pandas, feather files) can **hang silently**. The experiment runner works reliably when run **directly** but may hang when spawned via `subprocess.run([sys.executable, "-c", code])` or inside a Python `-c` one-liner.

**Workarounds:**
1. **Direct execution** — run `python -B research/run_cycle6_experiment.py` directly, not inside a `-c` wrapper
2. **importlib.reload** — to reset module state between runs in the same process:
   ```python
   import importlib, research.run_cycle6_experiment as r6
   setattr(r6, 'BOOTSTRAP_REPLICATES', 0)
   setattr(r6, 'PAIRS', new_pairs)
   importlib.reload(r6)
   from research.run_cycle6_experiment import main as run_c6
   result = run_c6()
   ```
3. **Short experiments** — avoid bootstrap (BOOTSTRAP_REPLICATES=0) to cut runtime from ~5min to ~3min

**Root cause:** Unconfirmed — likely a Python initialization race on Windows when importing numpy/pandas/pyarrow from a subprocess that shares the parent's module cache.

## Research → Production Bridge

When moving research signals to a live trading bot, DO NOT replicate the signal computation inside the bot's strategy. Instead:

### Production Pipeline Architecture

```
Research Code (Python, pandas, numpy)
        ↓
generate_signals.py  ←  runs daily via cron (e.g. 10:00 PT)
  - Fetches latest OHLCV from exchange via Freqtrade download-data
  - Computes TS MOM, Parkinson vol, vol scaling using EXACT same code as research
  - Writes signals.json (target_b per pair, trend status, entry/exit flags)
        ↓
signals.json  ←  shared state file
        ↓
execute_trades.py  ←  runs immediately after signal generation
  - Reads signals.json
  - Sizes positions proportionally to target (cap at 1.0)
  - Dry-run: logs what would be traded
  - Live: executes via CCXT (exchange API)
```

### Why Not a Native Bot Strategy

Freqtrade's backtester and the research pipeline simulate differently:
- Research: portfolio-level NAV, continuous sleeve allocation
- Freqtrade: individual trade open/close with slippage, order book depth
- Result: -22.9% in Freqtrade vs +33.5% in research for the SAME 2024 period

The research code IS the strategy. The bot just executes its outputs.

### Concentration Cap (Single Best Optimization)

Implement in the portfolio aggregation step, not per-symbol computation:

```python
MAX_CONCENTRATION = 0.40
def _cap(df):
    d = df.ffill().bfill().fillna(1.0)
    t = d.sum(axis=1)
    w = d.div(t, axis=0).clip(upper=MAX_CONCENTRATION)
    w = w.div(w.sum(axis=1), axis=0)
    return (d * w).sum(axis=1)

combined_nav = _cap(nav_df)
```

This cut SOL concentration from 73% of returns to under 40%, improving CAGR by +46pp.
