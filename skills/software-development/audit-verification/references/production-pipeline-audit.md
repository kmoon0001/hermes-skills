# Production Pipeline Audit Methodology

Audit a production trading/research pipeline for bugs, methodology mismatches vs validated research, and silent failure modes — when there is **no pre-existing report to verify**. The agent independently finds everything wrong.

---

## When to Use

- User asks "audit this production pipeline" or "find bugs in my trading system"
- User asks "does production match research?"
- You suspect production has diverged from validated research methodology
- You need a systematic baseline assessment of a pipeline's correctness

**Not for:** verifying claims in an existing audit/fix report (use the main `audit-verification` workflow + `references/statistical-backtest-audit.md` for that).

---

## Workflow

### Phase 1: Map the Production Surface

Read every file the user specified or that lives under the production directory. For each file, identify:

- **What it does** (signal gen, execution, logging, dashboard, alerting)
- **What data flows in** (files read, API calls, config)
- **What data flows out** (files written, prints, side effects)
- **Key constants and parameters** with their literal values
- **Assumptions** it makes about external state (files exist, columns present, balance known)

### Phase 2: Locate the Research Ground Truth

Find the validated research that the production code is supposed to implement. Look for:

- Backtest scripts (`cycle*_backtest.py`, `run_cycle*_experiment.py`)
- Result documents (`CYCLE*_RESULT.md`, `*_RECOMMENDATION.md`)
- Known-good signal functions (same function names used in experiments)
- Documented parameter values (vol_target, windows, stoploss, cost)

If the research is missing or the production code has no research reference, flag that as a methodology gap.

### Phase 3: Line-by-Line Comparison

For each production file, compare against the research reference on these axes:

| Axis | What to Check |
|------|---------------|
| **Signal math** | Do the signal functions produce identical outputs for identical inputs? Check formulas, rolling windows, fillna/clip/where behavior. |
| **Constants & parameters** | Every parameter used in production must match the validated research value. Watch for: vol_target, trend windows, vote threshold, Parkinson window, annualization days, stoploss. |
| **NaN/edge-case handling** | Research functions typically use `.where(np.isfinite(...)).fillna(0.0)` for vol, `fillna(False)` for trend. Production must handle the same cases: warm-up periods, missing data, division by zero, Inf values. |
| **Direction** | Research is long-only (target ∈ [0,1], side ∈ {"long", None}). Production must not introduce short positions. |
| **Cost** | Research applies one-way cost (`notional * cost`) on entry. Production must account for costs in P&L and equity. |
| **Position sizing** | Compare production's allocation formula against research's sleeve logic. They should produce similar allocations for identical signals. |
| **Sleeve compounding** | Research per-pair sleeves compound independently. Production should not use flat-equity-sharing without understanding the tracking difference. |
| **Execution delays** | Research uses T-close signal → T+1-open execution. Production must respect the same delay for causal validity. |

### Phase 4: Data Flow & State Audit

Trace the full pipeline data flow and identify broken links:

1. **Signal output → execution input**: Does the file format match? Are all fields expected by the executor present in the signal output?
2. **State feedback**: Does the pipeline know its own open positions? Does position sizing use current equity or a fixed initial value?
3. **Equity tracking**: Is equity updated with P&L, or does it rely on a config constant forever?
4. **Idempotency**: Can the pipeline safely run multiple times per day? Idempotency checks on the trade logger? Duplicate entry prevention?
5. **Exit logic**: How are positions closed? Is there a stoploss mechanism? What happens when a signal drops below threshold?

### Phase 5: Silent Failure Mode Search

The most dangerous bugs don't raise errors. Search for these specific patterns:

| Pattern | What to Look For |
|---------|------------------|
| **Silent skip** | `continue` on missing file or data — no log, no alert |
| **Dead code** | Constants defined but never read (e.g., `STOPLOSS = -0.06` with no stop-check function) |
| **Stub paths** | `if live: print("LIVE MODE — would execute trades")` with no actual exchange call |
| **Missing cost** | P&L computed as `stake * (exit/entry - 1)` with no cost deduction anywhere |
| **Fixed initial value** | Equity always reads from config initial wallet, never from actual account or trade history |
| **Redundant re-entry** | Every day re-"buys" the same pair because execution has no memory of current positions |
| **Calendar assumption** | `df.iloc[-2]` treated as "yesterday" when data may have gaps |
| **Unvalidated thresholds** | Hardcoded magic numbers (e.g., `0.15`) that differ from research thresholds |

### Phase 6: Dashboard & Alerting Audit

Even if execution is broken, the monitoring layer should detect it:

- Does the dashboard display correct parameter values or hardcoded ones?
- Are alert thresholds consistent with the strategy's risk profile?
- Does the alerting system test data freshness (staleness detection)?
- Would the dashboard show anything useful during a silent failure (e.g., empty signals)?

### Phase 7: Compile Report

Structure the findings as:

```
## Executive Summary
- Total issues found, with severity breakdown (Critical/Major/Minor/Info)
- Single-line summary of the biggest gap

## Critical Issues
### C1. Title
- **File:** path:line
- **What's wrong:** exact code quote and explanation
- **Why it matters:** business/risk impact
- **Fix needed:** actionable steps

... (repeat for each severity level)

## Passed Checks (No Issues Found)
Table of checks that passed with brief verification evidence.

## Verification Notes
How you verified the clean checks (which functions compared, which files read, which commands run).
```

---

## Pitfalls

- **The research may have bugs too.** The production code might match a buggy research artifact. If C-minus-B would be non-zero with neutral features (fade=1.0), flag the shared-NAV style bug first before auditing methodology.
- **Two implementations of the same signal.** If production has its own standalone copies of research functions, check they match **line-by-line**. Divergence is inevitable without shared imports.
- **Position sizing math can be algebraically different but numerically close.** Don't assume different formulas produce different results — compute both sides with sample values.
- **Display bugs matter.** A dashboard showing wrong parameters misleads operators about what the strategy is actually doing.
- **"LIVE mode" code paths often rot.** Examine what happens when `dry_run: false`. If the path is a stub, the system cannot go live regardless of configuration.
