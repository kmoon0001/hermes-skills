---
name: coding-agent-comparison
description: Compare Claude Code, Codex CLI, and OpenCode — provider compatibility, setup, and performance for real coding tasks.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [coding-agent, comparison, claude-code, codex, opencode, deepseek, openrouter]
    related_skills: [claude-code, codex, opencode]
---

# Coding Agent Comparison

Side-by-side evaluation of coding agents for real-world Python tasks (freqtrade-cycle5-research, ~20K LOC).

## Quick Decision Matrix

| Task Type | Best Agent | Best Model | Why |
|-----------|-----------|------------|-----|
| Code review | OpenCode | deepseek-v4-flash | Fast, thorough, line citations |
| Multi-file refactor | OpenCode | deepseek-v4-flash | Updates all callers, runs tests |
| Bug fix (surgical) | OpenCode | deepseek-v4-flash | Reads codebase, makes minimal changes |
| Test generation | OpenCode | deepseek-v4-flash | Writes passing tests, covers edge cases |
| Feature build | OpenCode | deepseek-v4-flash | Adds feature, updates tests, verifies |
| Deep analysis | OpenCode | deepseek-v4-pro | Slower but catches more subtle issues |

## Provider Compatibility (tested Jul 2026, Windows)

### OpenCode — Works with everything

| Provider | Status | Setup |
|----------|--------|-------|
| DeepSeek API | ✅ Best | `export DEEPSEEK_API_KEY="sk-..."` → `opencode run --model deepseek/deepseek-v4-flash` |
| OpenRouter (paid) | ✅ Works | `export OPENROUTER_API_KEY="sk-or-v1-..."` → `opencode run --model openrouter/google/gemini-2.5-flash` |
| OpenRouter (free) | ❌ Broken | `:free` models listed but fail with provider errors / no tool support |

### Claude Code — Blocked via OpenRouter

OpenRouter doesn't fully emulate the Anthropic Messages API. Claude Code hits model-metadata endpoints that 404. `api_error_status: 404` on every model regardless of name format.

**Requires:** Real Anthropic API key (`ANTHROPIC_API_KEY`), or working Amazon Bedrock connection.

### Codex CLI — Blocked via OpenRouter

OpenRouter doesn't support OpenAI's `/v1/responses` API (only `/v1/chat/completions`). Codex uses the Responses API exclusively. Result: `No endpoints found, url: https://openrouter.ai/api/v1/responses`.

**Requires:** Real OpenAI API key, or ChatGPT auth (subject to rate limits, `gpt-5.6-terra`).

## Proven Workflow: OpenCode + DeepSeek V4 Flash

```bash
# One-shot task
export DEEPSEEK_API_KEY="sk-..."
opencode run "Review file.py for bugs" --model deepseek/deepseek-v4-flash

# Multi-step (it handles its own planning)
opencode run "Fix X, update all callers, add tests, verify" --model deepseek/deepseek-v4-flash
```

The agent reads the codebase, plans changes, executes across multiple files, runs tests, and self-corrects on failures — all in a single run. Works best with tasks under 20 files of scope.

### What it does well

- Reads project structure before editing (follows imports, finds callers)
- Makes surgical cross-file changes (modified 18 files in one run)
- Writes tests that pass on first attempt (17/17 in our test)
- Self-corrects when tests fail (found and fixed os.link→os.replace issue)
- Reports findings concisely with line citations

### Pitfalls

- Can time out on very large tasks (use `--model deepseek/deepseek-v4-flash` for speed)
- V4 Pro explores with sub-agents which is slower — use for analysis, not edits
- Sometimes over-engineers simple fixes (be specific in the prompt)
- `git add -A` in the prompt can grab venv files — use explicit file paths
- On Windows, `cd` needs quotes: `cd "C:/path/with spaces"`

## Evaluation Protocol

For fair comparison across agents, use these 5 task types on the same codebase:

1. **Code Review** — "Review X for bugs, logic errors, edge cases. Line citations."
2. **Bug Fix** — "Fix the top 3 issues found. Surgical changes, update all callers."
3. **Test Generation** — "Write unit tests for X. Cover edge cases. Match existing style."
4. **Feature Build** — "Add Y feature. Update tests. Verify."
5. **Refactoring** — "Clean up Z. Remove duplication, improve naming. Don't break tests."

Score on: issues found, correctness of fixes, test pass rate, cross-file awareness.
