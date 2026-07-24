# Freqtrade Audit Session (Jul 2026)

Repo: kmoon0001/freqtrade-cycle5-research (~20K LOC Python)
Agent: OpenCode + DeepSeek V4 Flash (via DEEPSEEK_API_KEY)

## Task 1: Code Review
Prompt: "Review production/strategies/strategy_tsmom.py for bugs, logic errors, missing edge cases..."
Results: 6 issues found (dead constants, NaN contract violation, duplicated SMA logic, missing validation, index leak, B-only side)

## Task 2: Bug Fix
Prompt: "Fix 3 most critical issues: remove dead constants, fix NaN target, remove duplicated SMA"
Results: 11 files changed (+217/-29), refactored compute_trend_mom to return tuple, updated 8 callers

## Task 3: Test Generation
Prompt: "Write unit tests for strategy_tsmom.py"
Results: 17 tests passing, covers uptrend/downtrend/flat/NaN/short history/multiple pairs/5 market regimes

## Task 4: Feature Build
Prompt: "Add 'strength' field scaled from mom_vote"
Results: 2 files changed, all 17 tests updated and passing

## Task 5: Full Audit (3 severity batches)
Prompts: "Audit codebase for issues..." then "Fix all high/medium/low"
Results: 54 issues found across 3 batches, 58 total fixed

## 58 Issues Summary

### High (13): Fixed
- 5x except BaseException -> except Exception
- 2x silent except Exception: pass -> logging
- 2x in-place source rewriting scripts neutralized
- Hardcoded path -> Path(__file__).parents[1]
- 2x stale "Vol target: 20%" -> 30%
- Dead main() restored
- Test stub documented
- setattr monkey-patching isolated (expanding_window, symbol_dropout)

### Medium (16): Fixed
- _atomic_write extracted to production/util.py (was in 4 files)
- subprocess.run returncode checked
- pandas import moved to module level
- Explicit target= param added
- df.iloc[-2] IndexError guard
- import-time json.loads try/except
- Bare except narrowed (2 places)
- None handling for _get_latest_close
- Mutable-default pattern fixed
- O(n) index() -> enumerate
- os.link cross-device fallback to os.replace
- Rolling max/min pre-computed outside loop
- HTTP status preserved in RuntimeError
- Timeout handling distinguishes failure types
- Relative imports moved to module top

### Low (25): Fixed
- Type hints narrowed (TypedDict, concrete types)
- Duplicated constant imported instead
- Bare excepts narrowed to specific types
- Redundant min() clamp removed
- df.set_index simplified
- Sharpe comment (365 vs 252)
- Performance notes on for-loops
- Dead-branch comments (regime_filter, funding_fade, OI_DIVERGENCE)
- Float-precision guard extracted into helper
- Brittle regex documented
- pragma: no cover markers verified
- Deprecated pct_change(fill_method=None) fixed
- Variable leak from genexpr fixed
- Discarded _ result documented
- TODO markers for shared utility extraction
- camelCase -> snake_case TODO

### Final Sweep: Fixed
- atomic_write str/Path type bug (introduced by util extraction)
- Path.rename -> os.replace for Windows compat

## Key Learnings
- DeepSeek V4 Flash handles 20-file refactors in a single run
- It reads callers/imports before editing (avoids breaking changes)
- It runs tests and self-corrects on failures
- Specific prompts work better than vague ones
- git add -A can grab venv files - use explicit file paths
- OpenRouter :free models are non-functional for tool-using agents
