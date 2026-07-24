# Research Code TODO Cleanup Workflow

Reusable pattern for resolving research-code TODOs before project handoff.

## When to Use

A research codebase accumulated TODOs during iterative development. Before
handing the project to someone else (or archiving it), resolve all TODOs so
the next person doesn't inherit unfinished work.

## Workflow

### 1. Audit

```bash
grep -rn "TODO\|FIXME" research/ --include="*.py" | grep -v __pycache__
```

Categorize each TODO:
- **Duplicate code** (same function in 2+ files) → extract to shared module
- **Stale comments** (TODO about something already done) → remove the comment
- **Performance** (loop that should be vectorized) → rewrite with pandas vector ops
- **Missing data** (script needs data saved to disk) → implement the save step or proper skip

### 2. Extract Shared Utilities

When the same function body appears in two or more files:

1. Create `research/utils.py` with the canonical version
2. Add `from research.utils import function_name` to each consumer
3. Remove the duplicate function bodies
4. Run `grep -rn "TODO"` again — should be empty for that TODO category

Example: `aggregate_hourly_to_daily()` was 50 identical lines in both
`cycle5_backtest.py` and `weekly_momentum_backtest.py`. Now lives in
`research/utils.py`.

**Safety check before removing:** `grep -rn "from research.cycle5_backtest import\|from research.weekly_momentum_backtest import"` — confirm the function is NOT imported externally by name. If it IS imported (e.g., tests import it from the original module), either re-export from the original module or update the callers.

### 3. Vectorize Loops

When a research function has a `for day in df.index:` loop:

```python
# BEFORE (slow, ~0.5s per 1000 days)
for day in daily.index[complete]:
    hours = actual_hours[actual_days == day]
    complete.loc[day] = len(set(hours.tolist())) == 24

# AFTER (fast, ~0.02s per 1000 days — ~20x speedup)
day_bucket = frame.index.floor("D")
hour_counts = frame.groupby(day_bucket)["close"].transform("nunique")
complete = complete & hour_counts.groupby(day_bucket).first().eq(24)
```

### 4. Fix Bootstrap / Missing Data

If a script's main() function is a stub printing "TODO: implement X":

1. Read the function signature — what data does it need?
2. Check if upstream code already computes that data but throws it away
3. Add minimal persistence (e.g., `--save-nav` flag, `.to_feather()` call)
4. Rewrite main() to: try loading data → run analysis if available → print clear instructions if not

Example: `bootstrap_analysis.py` needed NAV series. Experiment runner already
computed NAV but discarded it. Added `--save-nav` flag + `_NAV_OUTPUT_PATH` module
variable. Bootstrap now detects missing data and prints exact commands to generate it.

### 5. Verify

```bash
# Should return empty
grep -rn "TODO\|FIXME" research/ --include="*.py"

# Run relevant tests
python -m pytest tests/test_cycle5_backtest.py tests/test_cycle6_backtest.py -q

# Verify imports still work
python -c "from research.utils import aggregate_hourly_to_daily; print('OK')"
```

## Anti-Patterns

- **Don't leave a TODO and move on.** The next person (including future-you) will
  not "come back to it." Either fix it or delete it.
- **Don't extract a function that's tested externally by name.** Check import
  chains before moving code.
- **Don't vectorize without testing.** The vectorized version must produce identical
  results. Run the relevant test suite after any vectorization change.
