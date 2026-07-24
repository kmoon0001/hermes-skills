---
name: coding-agent-setup
description: Setup, auth, and provider compatibility for autonomous coding agents (Claude Code, Codex CLI, OpenCode). Use before delegating to any coding agent to avoid known compatibility traps.
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [Coding-Agent, Setup, Auth, Provider, Compatibility]
related_skills: [claude-code, codex, opencode]
---

# Coding Agent Setup & Provider Compatibility

Before delegating a task to any coding agent, run through this skill to pick the right agent + provider combo. Each agent has specific API requirements — guessing wastes tokens.

## Quick Compatibility Matrix

| Agent | Anthropic API | OpenAI API | OpenRouter | DeepSeek API | ChatGPT Auth |
|-------|:---:|:---:|:---:|:---:|:---:|
| **Claude Code** | ✅ | ❌ | ❌ (404s) | ❌ | ❌ |
| **Codex CLI** | ❌ | ✅ | ❌ (Responses API) | ❌ | ✅ (rate-limited) |
| **OpenCode** | ✅ | ✅ | ✅ | ✅ | ❌ |

## Agent-Specific Setup

### Claude Code

**Requires:** Real Anthropic API key (NOT OpenRouter). Bedrock also works.

1. Ensure `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` is set to a real Anthropic key (`sk-ant-...`)
2. Check `~/.claude/settings.json` — if it has `CLAUDE_CODE_USE_BEDROCK: "1"`, either:
   - Fix the Bedrock config (AWS_REGION, AWS_PROFILE), or
   - Remove all Bedrock entries and set Anthropic base URL
3. Smoke test: `claude -p "Say: OK" --max-turns 1 --output-format json --model claude-haiku-4-5`
4. If 404 on model: settings.json env vars are overriding your CLI env vars — edit the file

**OpenRouter pitfall:** Claude Code's SDK queries Anthropic-specific model metadata endpoints that OpenRouter doesn't emulate. Curl to `/api/v1/messages` works, but Claude Code fails with 404. Do NOT use OpenRouter as `ANTHROPIC_BASE_URL`.

**Bedrock pitfall:** When `CLAUDE_CODE_USE_BEDROCK=1` is in settings.json, CLI env var overrides may not take effect. Edit the file directly.

### Codex CLI

**Requires:** OpenAI API key (NOT OpenRouter), or ChatGPT auth with available credits.

1. Check auth mode: `codex doctor` — look for `auth mode: chatgpt` vs API key
2. If ChatGPT: check usage limit at chatgpt.com/codex/settings/usage
3. If API key: set `OPENAI_API_KEY` and configure `~/.codex/config.toml`:
   ```toml
   model = "gpt-4.1"
   model_provider = "openai"
   ```
4. Smoke test: `codex exec "Say: CODEX_OK"` (requires PTY)

**OpenRouter pitfall:** Codex uses OpenAI's Responses API (`/v1/responses`), NOT Chat Completions. OpenRouter doesn't support this endpoint — returns 404 "No endpoints found." The `[model_providers.openrouter]` config section exists but only works for the desktop app, not CLI exec mode.

**ChatGPT rate limit:** If ChatGPT auth shows "usage limit" with a reset date, wait until that date or switch to API key auth via `codex login --with-api-key`.

### OpenCode

**Requires:** Any OpenAI-compatible API. Works with OpenRouter, Anthropic, DeepSeek, Google, etc.

1. Auth: set provider env var (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, etc.)
2. Smoke test: `opencode run "Say: OPENCODE_OK" --model <model>`
3. Model format: `provider/model` (e.g., `openrouter/google/gemini-2.5-flash`, `deepseek/deepseek-v4-flash`)

**OpenRouter `:free` models:** All 13 free models on OpenRouter are listed but non-functional in practice — they return provider errors or don't support tool use. Use a paid model or a direct provider.

**DeepSeek direct:** Works with `DEEPSEEK_API_KEY` env var pointing to DeepSeek's API. Available models: `deepseek-v4-flash` (fast), `deepseek-v4-pro` (powerful). DeepSeek key on Windows may be stored as a user environment variable, not exported in git-bash — extract with:
```bash
DEEPSEEK_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')" | tr -d '\r\n')
export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
```

## Common Pitfalls Across All Agents

1. **API key not in env but stored in Hermes:** Hermes manages credentials internally for its own model calls. These are NOT exported as shell env vars. For external tools (claude, codex, opencode), you must either:
   - Set the env var manually from the stored key
   - Extract from Windows env vars via PowerShell (see OpenCode > DeepSeek above)
   - Extract from Hermes auth.json credential_pool

2. **OpenRouter is NOT a universal proxy:** Each agent uses different API surface (Anthropic Messages, OpenAI Responses, OpenAI Chat Completions). OpenRouter only reliably supports Chat Completions. Claude Code and Codex CLI fail through OpenRouter.

3. **Always smoke-test before delegating real work:** A 5-second "Say: OK" test catches auth, model, and provider issues before wasting tokens on a complex task.

4. **Free models are unreliable:** Across providers, free-tier models frequently return provider errors, timeout, or lack tool-use support. Budget ~$0.10-0.50 for any non-trivial coding task.

## References

- `references/provider-smoke-test-log.md` — Session-specific test results and error transcripts for each agent/provider combo
