---
name: coding-agent-orchestration
description: Set up, compare, and orchestrate autonomous coding agents (OpenCode, Claude Code, Codex) through Hermes — provider compatibility, model selection, and proven workflows.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agent, opencode, claude-code, codex, deepseek, openrouter]
---

# Coding Agent Orchestration

Set up and run autonomous coding agents (OpenCode, Claude Code, Codex CLI) through
Hermes. Covers provider compatibility, model selection, API key discovery, and
proven task patterns.

## Quick Decision: Which Agent With Which Provider?

| Agent | Anthropic Key | OpenAI Key | OpenRouter | DeepSeek | Bedrock |
|-------|:------------:|:----------:|:----------:|:--------:|:-------:|
| **OpenCode** | ✅ | ✅ | ✅ | ✅ | — |
| **Claude Code** | ✅ | — | ❌ | — | ✅ |
| **Codex CLI** | — | ✅ | ❌ | — | — |

**OpenCode** is the most flexible — it works with any OpenAI-compatible API. Use it
as the default when provider keys are mixed or uncertain.

**Claude Code** requires a real Anthropic API key or Amazon Bedrock. OpenRouter's
Anthropic-compatible endpoint (`/api/v1/messages`) is NOT sufficient — Claude Code
hits additional metadata/model-validation endpoints that return 404.

**Codex CLI** uses OpenAI's `/v1/responses` API which OpenRouter does not support.
It works only with a real OpenAI API key or ChatGPT token auth.

## OpenCode + DeepSeek (Proven Workflow)

DeepSeek V4 Flash/Pro are top-tier coding models with OpenAI-compatible APIs.
On Windows the key is often stored as a user-level environment variable, not in
the shell environment. Extract and use it:

```bash
# Extract DeepSeek key from Windows env
DEEPSEEK_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')" 2>/dev/null | tr -d '\r\n')
export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"

# Verify
curl -s "https://api.deepseek.com/v1/models" -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

Then run tasks:

```bash
# Fast tasks
opencode run "review auth.py for bugs" --model deepseek/deepseek-v4-flash

# Complex reasoning
opencode run "refactor the database layer" --model deepseek/deepseek-v4-pro
```

Available models: `deepseek-v4-flash` (fast, cheap) and `deepseek-v4-pro` (reasoning).

No pty needed for `opencode run`. Timeout 120-180s for multi-file tasks.

## OpenCode + OpenRouter

For providers without a direct key, use OpenRouter:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
opencode run "task" --model openrouter/google/gemini-2.5-flash
```

**PITFALL:** OpenRouter `:free` models (gemma, nemotron, gpt-oss, cohere — 13 total) are listed in `/models` but fail with "UnknownError" or "No endpoints available" — they lack tool/function calling support. Always use a paid model. Cheapest working: `google/gemini-2.5-flash` (~$0.15/M tokens) or `deepseek/deepseek-chat` (~$0.14/M).

## Smoke-Test Protocol

Always smoke-test an agent before delegating real work. One-liner per agent:

```bash
# OpenCode — fast, no pty needed
opencode run "Say: OK" --model <model-id>

# Claude Code — 20s is enough for one-turn smoke
ANTHROPIC_AUTH_TOKEN="$KEY" claude -p "Say: OK" --max-turns 1 --output-format json

# Codex CLI — needs pty
codex exec "Say: OK"
```

Expectation: agent returns the single word in <15s. Failure modes to check:
- 404 on model → wrong model ID format for provider
- "Server tool request failed" → provider doesn't support tool calls (free models)
- Timeout >20s → provider unreachable or model overloaded
- "No endpoints found for /v1/responses" → Codex using Responses API through OpenRouter

For real tasks, set generous timeouts: 120-180s for single-file, 180-300s for multi-file refactors.

## Codex CLI Provider Switching

Codex stores its provider in `~/.codex/config.toml`. To switch from ChatGPT to
OpenRouter (note: doesn't fully work due to Responses API, but documents the config):

```toml
model = "google/gemini-2.5-flash"       # model ID without openrouter/ prefix
model_provider = "openrouter"           # matches [model_providers.openrouter]
```

The `[model_providers.openrouter]` section must exist with `base_url` and `env_key`.

## Claude Code Settings for OpenRouter (Does Not Work)

For reference — this config connects but all model names return 404:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1",
    "ANTHROPIC_AUTH_TOKEN": "<openrouter-key>"
  }
}
```

Remove `CLAUDE_CODE_USE_BEDROCK` and `AWS_REGION` to disable Bedrock.
Use a real Anthropic key or Bedrock instead.

## References

- `references/openrouter-incompatibility.md` — Detailed session findings on why Claude Code and Codex CLI fail with OpenRouter
- `references/deepseek-key-discovery.md` — Windows-specific recipe for extracting DeepSeek API keys

## Comparison Task Templates

When benchmarking agents, use these task types in order. Each builds on the last:

1. **Code Review** — Review a specific file for bugs, logic errors, edge cases. Expect line citations and severity ratings.
2. **Bug Fix** — Fix issues found in review. Verify across all callers, not just the target file.
3. **Test Generation** — Write unit tests for uncovered code. Match existing test patterns. Verify edge cases (NaN, empty, missing columns).
4. **Feature Build** — Add a small, well-scoped feature. Update existing tests.
5. **Refactoring** — Improve structure without changing behavior. Extract shared code, remove duplication.

For each task, verify: `git diff --stat`, run tests, commit if clean. Always commit before starting the next task so each is independently revertible.

## Multi-Pass Audit Workflow (Proven)

For large codebase audits (50+ issues), the most effective pattern uses
DeepSeek V4 Flash for speed and V4 Pro for depth:

### Phase 1: V4 Flash Sweep
Batch fixes by severity. Flash handles ~25 issues per run before timing out.
```bash
# Batch 1: High severity
opencode run "Fix all HIGH severity issues: safety, correctness, crashes."
    --model deepseek/deepseek-v4-flash
# Batch 2: Medium severity
opencode run "Fix all MEDIUM: duplication, error handling, config drift."
    --model deepseek/deepseek-v4-flash
# Batch 3: Low severity
opencode run "Fix all LOW: type hints, comments, deprecated APIs."
    --model deepseek/deepseek-v4-flash
```
**Commit between each batch** — git acts as undo for bad AI changes.

### Phase 2: V4 Pro Deep Analysis (Read-Only)
V4 Pro catches cross-file issues Flash misses. CRITICAL: add "ANALYSIS ONLY — DO NOT EDIT" or Pro will time out trying to implement.
```bash
opencode run "ANALYSIS ONLY — DO NOT EDIT ANY FILES.
Deep-dive: cross-file signal flow, config drift, numerical stability,
edge cases on empty/corrupt data, state corruption risks."
    --model deepseek/deepseek-v4-pro
```
Pro uses sub-agents ("Explore Agent") for broad codebase scanning — this is normal but adds latency. Budget 300s timeout.

### Phase 3: Hermes Surgical Fixes
Read Pro's analysis output and apply fixes with Hermes' own `patch`/`write_file` tools. This gives more control than delegating to Flash — you verify each change before committing.

### Session Results (freqtrade-cycle5-research, Jul 2026)
58 issues resolved across 4 audit passes + 1 final sweep:
- **V4 Flash High** (13): BaseException→Exception, silent excepts, dangerous scripts neutralized
- **V4 Flash Medium** (16): _atomic_write extracted to util, subprocess returncode checks, json.loads guards
- **V4 Flash Low** (25): Type hints, performance notes, dead-branch comments
- **V4 Pro Deep** (6): caught 3 things Flash missed — NameError crash (`_atomic_write`→`atomic_write`), VOL_TARGET 0.20→0.30 mismatch (33% under-sizing), Sharpe divide-by-zero
- **Hermes**: Applied Pro's 6 findings + built risk-management features (stoploss fallbacks, strength sizing, DD breaker, volume filter, HTML dashboard)
- **Initial sweep** (4): NaN contract violation, dead constants, duplicated SMA, signal strength field

**Key finding:** V4 Pro caught cross-file logic issues (import rename + vol target mismatch) that 3 Flash passes missed. The 3-phase pattern (Flash→Pro→Hermes) is worth the extra pass for production code.
- DeepSeek V4 Flash completed all 5 tasks correctly
- 58 issues found and fixed across 20+ files
- 3 clean commits, ~475 tests green
- Code review found real bugs (dead constants, NaN contract violation, duplicated logic)
- Bug fix propagated to 8 callers across the codebase
- Test generation produced 17 tests covering 5 market regimes + edge cases
