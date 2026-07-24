# Cross-Cutting Formula Fix — Implementation Guide

Use this when you need to fix a formula bug (e.g., log-return Sharpe → simple-return Sharpe) that appears across multiple files in a codebase. It bridges **cross-cutting-codebase-audit.md** (which finds the issues) and **production-pipeline-fix-implementation.md** (which patches them).

## Workflow

### Step 1: Discover all occurrences

Search for the buggy pattern across ALL project `.py` files, excluding virtual environments and caches:

```bash
find . -name "*.py" -not -path "*/.venv/*" -not -path "*/__pycache__/*" -not -path "*site-packages/*" | sort
```

Or use `search_files` with `output_mode='files_only'` to find every file that references the pattern.

### Step 2: Classify each file — defining vs. importing

For each file that matches the search:

1. **Read the file** — find the exact location of the pattern.
2. **Determine if this file DEFINES the function** (has `def metrics(...)` or `def compute_metrics(...)` or the relevant function signature) **or IMPORTS it** from another file (`from x import metrics`).
3. **Only patch the defining files.** Importers automatically inherit the fix — don't touch them.

### Step 3: Handle different implementation styles

The same formula can appear in different forms across files:

| Source Type | Pattern | Fix |
|---|---|---|
| **From pct_change** | `lr = np.log(1 + rets)` then `mean(lr)/std(lr)*sqrt(N)` | Change to `mean(rets)/std(rets)*sqrt(N)`. Keep `lr` for CAGR/vol if unchanged. |
| **From NAV array** | `log_r = np.diff(np.log(nav))` | Add `rets = np.diff(nav) / nav[:-1]` and use that for Sharpe. Keep `log_r` for CAGR. |
| **Bootstrap from log returns** | `boot_returns` are log-space resamples | Use `np.expm1(boot_returns)` to convert to simple returns for Sharpe. Keep CAGR on log returns. |
| **Raw equity list** | Manual pct calc in loop | Convert the loop's simple returns to simple-return Sharpe directly. |

### Step 4: Keep CAGR and MaxDD unchanged

These formulas are typically correct across all styles:

- **CAGR (geometric):** `exp(mean(log_returns) * annual_days) - 1` — only correct for log returns. Do NOT change.
- **Max Drawdown:** `min(nav / nav.cummax() - 1)` — already uses NAV directly. Do NOT change.
- **Sharpe (simple returns, industry standard):** `mean(rets) / std(rets, ddof=1) * sqrt(N)` — this IS what we're fixing.

### Step 5: Verify all modified files compile

```bash
python3 -m py_compile path/to/modified_file.py
```

Also compile **dependent importers** — files that import the patched function — to make sure signature changes didn't break them.

### Step 6: Cross-reference against downstream consumers

After patching defining files, check that files importing them (from Step 2 discovery) still compile and that their import syntax matches (same function name, same return type).

## Pitfalls

- **Don't patch importers.** Fix the source. If you patch both the defining file and an importer, you create a maintenance burden and confusion.
- **Watch for bootstrap loops.** Bootstrap resamples are often in log-return space. Converting log→simple for Sharpe inside the bootstrap loop requires `np.expm1()` or `np.exp(x) - 1`, not the standard `pct_change` approach.
- **`np.diff(np.log(nav))` vs `np.log(1 + rets)`.** Both give the same log returns, but the first computes from NAV directly and the second from pct_change series. Recognize both forms when searching.
- **Annualization factor differences.** Some inline bootstrap Sharpe calculations may be missing the `sqrt(N)` annualization factor (a pre-existing bug). Only change numerator/denominator from log→simple, not the annualization structure — that's a separate fix.
- **Escape hatch.** If the same formula exists in 10+ files with wildly different surrounding structure, consider whether extracting it to a shared utility is worth the refactoring cost. The trade-off: N micro-patches vs 1 extraction + N import rewrites.
