---
name: ai-codebase-audit
description: Systematic multi-pass codebase audit using AI coding agents — Flash for speed, Pro for deep analysis, Hermes for surgical fixes. Proven on Python trading bot codebase.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, code-review, multi-pass, opencode, deepseek, quality]
    related_skills: [opencode, claude-code, systematic-debugging]
---

# AI Codebase Audit

Systematic multi-pass audit workflow for Python codebases. Uses a tiered approach: speed model for broad sweeps, reasoning model for deep analysis, and Hermes for surgical fixes.

## When to Use

- User asks for a comprehensive codebase audit/review
- After completing a feature, verify the whole codebase for regressions
- Before a production deployment
- When inheriting or onboarding to a codebase
- "Find everything wrong with this code" type requests

## Kevin's Cardinal Rule: Analysis First, Fix Second

**NEVER mix analysis and fixes in one pass.** The user explicitly wants analysis-only sweeps first, then fixes. This prevents the agent from fixing symptoms while missing root causes, and gives the user visibility into what was found before changes happen.

Wrong: `"Audit and fix all issues"`
Right:
1. `"ANALYSIS ONLY — audit the codebase. Report findings. Do NOT edit files."`
2. Read the report, then fix findings yourself with Hermes tools.

## Three-Tier Audit Workflow

### Tier 1: Speed Pass (Fast Model)

Use a fast model (DeepSeek V4 Flash, Gemini Flash) for broad coverage:

```bash
opencode run "Audit the codebase for bugs, safety issues, code quality, dead code.
Focus on: production/ and research/ directories.
Report findings with file:line, severity (HIGH/MED/LOW), description.
ANALYSIS ONLY — DO NOT EDIT FILES." \
  --model deepseek/deepseek-v4-flash
```

**What Flash catches best:**
- Python anti-patterns (mutable defaults, bare excepts)
- Dead code, unused imports, duplicated logic
- Type safety issues
- Error handling gaps
- Missing tests

**Flash limitations:** May miss cross-file logic errors, numerical edge cases, config drift, and race conditions. That's what Tier 2 is for.

### Tier 2: Deep Analysis (Reasoning Model)

Use a reasoning model (DeepSeek V4 Pro) for areas Flash misses:

```bash
opencode run "ANALYSIS ONLY — DO NOT EDIT ANY FILES. Read-only audit.

Deep-dive analysis. Focus on what prior sweeps missed:
1. CROSS-FILE LOGIC — trace data flow, check for format mismatches
2. EDGE CASES — market holidays, missing data, corrupt files, empty DataFrames
3. CONFIG DRIFT — compare config defaults against what code expects
4. NUMERICAL STABILITY — division by zero, log(0), overflow, NaN propagation
5. STATE CORRUPTION — can state files become inconsistent?
6. API SURFACE — broken imports, circular deps

Report findings with file:line, severity, description. DO NOT make changes." \
  --model deepseek/deepseek-v4-pro
```

**V4 Pro timeout pitfall:** DeepSeek V4 Pro can time out on large tasks (>300s). If it does:
- Break the task into smaller focused checks
- Use V4 Flash for the same query (faster, nearly as thorough for structured questions)
- Don't use sub-agents in the prompt — keep it direct

### Tier 3: Surgical Fixes (Hermes)

After both analysis passes, fix findings yourself:

1. Read the analysis report
2. Create a todo list of fixes by severity
3. Fix HIGH items first, one commit per batch
4. Run tests after each batch
5. Commit with descriptive messages

**Fix pattern:**
```
# Fix HIGH severity items → commit → test
# Fix MEDIUM severity items → commit → test
# Fix LOW severity items → commit → test
# Final sweep to catch anything missed → commit → push
```

## Model Selection

| Model | Tier | Speed | Best For | Pitfall |
|-------|------|-------|----------|---------|
| `deepseek/deepseek-v4-flash` | 1 | Fast | Broad sweeps, implementation | May miss deep logic errors |
| `deepseek/deepseek-v4-pro` | 2 | Slow | Deep analysis, edge cases | Times out >300s; use read-only |
| `google/gemini-2.5-flash` | 1 (fallback) | Fast | Simple checks, verification | Via OpenRouter |
| Hermes (current model) | 3 | N/A | Surgical fixes, commits | Use patch/write_file tools |

## Provider Setup

### DeepSeek (Recommended Primary)
```bash
# Get key from Windows env var
DEEPSEEK_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')")
export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"

# Verify
opencode run "Say: OK" --model deepseek/deepseek-v4-flash
```

### OpenRouter (Fallback)
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
opencode run "Say: OK" --model openrouter/google/gemini-2.5-flash
```

## Provider Compatibility Matrix

OpenCode is the only coding agent that works reliably with non-native providers:

| Agent | OpenRouter | Direct API | Root Cause |
|-------|-----------|------------|------------|
| OpenCode | ✅ | ✅ | Standard chat completions |
| Claude Code | ❌ | ✅ (needs Anthropic key) | Uses proprietary model validation |
| Codex CLI | ❌ | ✅ (needs OpenAI key) | Uses Responses API, not Chat |

**OpenRouter `:free` models do NOT support tool use.** All 13 free models fail with OpenCode. Always use a paid model for coding tasks.

See `references/provider-compatibility.md` for detailed findings.

## Audit Dimensions

When designing audit prompts, cover these dimensions across tiers:

| Dimension | Tier 1 (Flash) | Tier 2 (Pro) |
|-----------|---------------|--------------|
| Dead code / unused imports | ✅ | — |
| Bare excepts / error handling | ✅ | ✅ (deeper patterns) |
| Type safety | ✅ | — |
| Duplicated logic | ✅ | — |
| Cross-file data flow | — | ✅ |
| Numerical stability | — | ✅ |
| Config drift | — | ✅ |
| State corruption | — | ✅ |
| Edge cases (empty data, holidays) | — | ✅ |
| API surface / imports | — | ✅ |

## Verification

After all fixes:
```bash
# Run full test suite
python -m pytest tests/ --ignore=tests/test_cycle2_mtf_strategies.py -q

# Check for pre-existing failures (flag them, don't fix unrelated tests)
# All modified files should be importable
python -c "import production.util; print('imports OK')"

# Commit each batch separately for clean git history
git add <fixed files> && git commit -m "fix: <severity> audit fixes — N issues resolved"
```

## Docstring Coverage Check

An automated quality gate that ensures every public function has a docstring.
Run it as part of any code-quality pass:

```bash
python scripts/check_missing_docstrings.py              # summary only
python scripts/check_missing_docstrings.py --fix .      # full list for batch fixing
```

### Mass-Fix Pattern (Parallel Dispatch)

When a scan reveals dozens/hundreds of missing docstrings, use parallel
delegate_task to add them efficiently:

1. **Scan** — run `check_missing_docstrings.py --fix` to get the full list
2. **Classify** — group by area: production/, research/stocks/, tests/
3. **Dispatch** — 3 parallel subagents, each given their file list + function
   descriptions (from reading the code, not guessing)
4. **Cleanup** — fix any remaining by hand (scan → dispatch misses a few)
5. **Verify** — run the full test suite; zero regressions is the bar

Each subagent receives: the exact file list, function names with line numbers,
and a brief description of what each function does (so the docstring is
accurate, not boilerplate). The subagent reads the code to verify before
adding the docstring.

**Example dispatch for ~185 missing docstrings:**
- Agent 1: production/ (13 files, ~30 functions)
- Agent 2: research/ + stocks/ + top-level (15 files, ~65 functions)
- Agent 3: tests/ (9 files, ~90 test methods)

This pattern generalizes to any "scan-and-fix-all" quality task: bare excepts,
type hints, dead imports, etc. The key insight is that parallel dispatch turns
an hours-long manual task into a ~10-minute background operation.

## Quality Gate Sweep (Loop-Back Pattern)

After the initial audit→fix passes, run a comprehensive quality gate sweep that
checks every dimension a senior engineer would flag. Kevin expects the
"fix it all then loop back and keep looping until nothing comes up" pattern.

**Dimensions to check (in order):**

1. **Bugs** — undefined names (F821), bare excepts (E722), import errors
2. **Docstrings** — every public function must have one (see Docstring Coverage section)
3. **Ruff lint** — auto-fix first (`ruff --fix`), then manual fixes for remaining
4. **Type annotations** — return types + parameter types on all public functions
5. **Deduplication** — scan for copy-pasted utilities (load_json, now_pt, etc.), centralize into shared modules
6. **CI/CD gates** — add ruff, dedup, and pytest to GitHub Actions (see `references/ci-cd-patterns.md`)

**Loop-back protocol:**

```
while true:
    run comprehensive scan (ruff + ast + dedup check + test suite)
    if all_clean:
        break
    fix everything the scan found
    re-run the scan
```

Stop only when: ruff 0 errors, 100% docstrings, 100% type annotations, no
duplicated utilities, test suite fully green.

**Parallel dispatch for mass fixes:**

When the scan reveals dozens/hundreds of fixes needed (docstrings, types),
use `delegate_task` with parallel subagents. Dispatch 2-3 agents, each
responsible for a directory group. Each gets the exact file list and a brief
description of what each function does.

Example dispatch for ~185 docstrings:
- Agent 1: production/ (13 files)
- Agent 2: research/ + stocks/ + top-level (15 files)
- Agent 3: tests/ (9 files)

## CI/CD Hardening

After the code itself is clean, add enforcement so it stays clean. See
`references/ci-cd-patterns.md` for the complete GitHub Actions template and
CI-compatibility patterns.

Key CI gates:
- Ruff lint gate (hard fail, no `|| true`)
- Bare-except enforcement gate
- Undefined-name enforcement gate (F821)
- Deduplication check gate
- Pytest gate (all standalone tests)
- Type-check job (mypy, informational)

**CI compatibility — conditional imports:** Production code often imports
packages unavailable in CI (talib, freqtrade, ccxt). When tests import modules
that have hard dependencies at module level, they fail. Fix by making imports
conditional with fallback stubs:

```python
# Module-level import guards
try:
    import talib.abstract as ta
except ImportError:
    ta = None

try:
    from freqtrade.strategy import IStrategy
except ImportError:
    class IStrategy:
        def __init__(self, config: dict | None = None):
            self.config = config or {}

# Guard usage sites
if ta is not None:
    sma = ta.SMA(dataframe, timeperiod=w)
else:
    sma = dataframe["close"].rolling(w, min_periods=w).mean()
```

## Pitfalls

- **V4 Pro sub-agents cause timeouts.** When the Pro model spawns Explore/General agents, it can exceed 300s. Keep prompts direct — avoid "use sub-agents" or "explore first" language.
- **`git add -A` grabs venv files.** On Windows with `.venv/` in the repo, always stage specific files. Use `git add file1 file2`, never `-A`.
- **Pre-existing test failures are normal.** Flag them but don't fix unrelated tests. Skip with `-k "not test_name"` if they block the suite.
- **One commit per severity batch.** Don't squash all fixes into one commit. This makes reverts easy and bisects cleanly.
- **Don't trust `git commit` return code.** Git may commit before timing out on large diffs. Verify with `git log --oneline -1`.
- **CI imports break hard.** When a module-level import fails, the entire module is unimportable. Fix by making imports conditional with fallback stubs (see CI/CD Hardening above). Do NOT use `pytest.importorskip` at the test level — it skips too broadly and hides real regressions.
- **Variable renames must update ALL references.** When fixing N806 (uppercase→lowercase) or E741 (ambiguous names), every usage throughout the function body must be updated or F821 (undefined name) errors appear. Use regex-based batch replacement across the file, not line-by-line patching.
- **Ruff `--fix` handles ~60% of issues automatically.** Always run it first (`ruff check --fix`) before tackling the remaining issues manually. It handles F541 (f-strings without placeholders), E401 (multiple imports), UP031 (old % formatting→f-strings), UP035 (deprecated imports).

## Rules

1. Analysis sweeps are ALWAYS read-only. Explicitly say "DO NOT EDIT FILES" in the prompt.
2. Flash for speed/coverage, Pro for depth/edge-cases, Hermes for fixes.
3. One commit per severity batch — clean git history.
4. Verify every fix with tests before the next batch.
5. Report pre-existing test failures but don't fix them.
6. Stage files explicitly — never `git add -A` in venv-containing repos.
