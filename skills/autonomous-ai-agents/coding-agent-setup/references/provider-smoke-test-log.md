# Provider Smoke Test Log — 2026-07-21

Session: freqtrade-cycle5-research coding agent comparison setup.

## Environment

- Windows 10, git-bash
- Freqtrade repo: `~/Desktop/freqtrade`
- OpenRouter API key: `sk-or-v1-...` (73 chars)
- DeepSeek API key: stored in Windows user env vars (35 chars)

## Claude Code v2.1.123

### OpenRouter (Anthropic endpoint)
```
ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"
ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
```
**Result: 404 on every model.** Even models that work via curl to `/api/v1/messages`:
- `claude-haiku-4-5` → 404
- `anthropic/claude-haiku-4-5` → 404
- Changing ANTHROPIC_BASE_URL to `https://openrouter.ai/api` → 404
- Changing ANTHROPIC_BASE_URL to `https://openrouter.ai/api/v1/messages` → 404

**Root cause:** Claude Code's SDK queries Anthropic-specific model metadata/validation endpoints that OpenRouter doesn't emulate. The raw `/v1/messages` POST works via curl but Claude Code's internal model resolution step fails first.

**Curl confirmation (works fine):**
```bash
curl -s "https://openrouter.ai/api/v1/messages" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"anthropic/claude-haiku-4-5","max_tokens":20,"messages":[{"role":"user","content":"Say: OK"}]}'
# Returns: "OK" via anthropic/claude-haiku-4.5 (routed to Amazon Bedrock)
```

### Bedrock (original config)
Settings.json had `CLAUDE_CODE_USE_BEDROCK: "1"` with `AWS_REGION: us-east-1`.
**Result: Timeout.** Every attempt timed out after 20-30s.

### Settings.json override pitfall
The file `~/.claude/settings.json` contained:
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
    "ANTHROPIC_AUTH_TOKEN": "${OPENROUTER_API_KEY}",
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_REGION": "us-east-1",
    "AWS_PROFILE": "default"
  }
}
```
The `${OPENROUTER_API_KEY}` is NOT expanded by JSON — it's a literal string. And `CLAUDE_CODE_USE_BEDROCK=0` on CLI did NOT override the file setting. The file had to be rewritten to remove Bedrock entries entirely.

## Codex CLI v0.144.5

### ChatGPT auth (default)
Model: `gpt-5.6-terra`, Provider: `openai`
**Result: Rate limited until Jul 25.** "You've hit your usage limit. Upgrade to Pro..."

### OpenRouter provider
Config changed: `model_provider = "openrouter"`, `base_url = "https://openrouter.ai/api/v1"`
Models tried:
- `openrouter/openai/gpt-4.1` → "not supported when using Codex with a ChatGPT account" (ChatGPT auth still active)
- `google/gemini-2.5-flash` → "Server tool request failed" (model accepted, tools timeout)
- `openrouter/google/gemini-2.5-flash` → "not a valid model ID" (wrong prefix format)

**Root cause:** Codex uses OpenAI's Responses API (`/v1/responses`), not Chat Completions. OpenRouter returned:
```
ERROR: unexpected status 404 Not Found: No endpoints found for ..., url: https://openrouter.ai/api/v1/responses
```
The `[model_providers.openrouter]` config section exists in `~/.codex/config.toml` but only activates for the desktop app, not CLI `exec` mode. CLI mode uses ChatGPT auth which locks to ChatGPT's model list.

### Config file
`~/.codex/config.toml` has `model_provider = "openai"` at top level. `[model_providers.openrouter]` and `[model_providers.moonbridge]` sections exist but are unused by CLI.

## OpenCode v1.18.4

### OpenRouter (Gemini 2.5 Flash)
```bash
opencode run "Say: hello" --model openrouter/google/gemini-2.5-flash
```
**Result: ✅ Works.** Returns "hello" in ~11s.

### OpenRouter free models (ALL FAILED)
Models tested with `opencode run "Say: OK" --model <model>`:
- `google/gemma-4-31b-it:free` → "UnknownError" (provider error)
- `nvidia/nemotron-3-super-120b-a12b:free` → "UnknownError"
- `openai/gpt-oss-20b:free` → "UnknownError"
- `cohere/north-mini-code:free` → "UnknownError"

Curl confirmation: all `:free` models return "Provider returned error" or "No endpoints available matching your guardrail restrictions."

13 free models listed, 0 functional for tool-use tasks.

### DeepSeek direct
```bash
DEEPSEEK_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')" | tr -d '\r\n')
export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
opencode run "Say exactly: DEEPSEEK_OK" --model deepseek/deepseek-v4-flash
```
**Result: ✅ Works.** Returns "DEEPSEEK_OK". Models available: `deepseek-v4-flash`, `deepseek-v4-pro`.

### Default model pitfall
Without `--model` flag, OpenCode auto-selected `google/gemini-3-pro-image-preview` which returned:
```
Error: No endpoints found that support tool use. Try disabling "bash".
```
Always pass `--model` explicitly.

## Summary

| Agent + Provider | Works? | Key Issue |
|-----------------|--------|-----------|
| OpenCode + OpenRouter (paid) | ✅ | Gemini Flash confirmed |
| OpenCode + DeepSeek direct | ✅ | V4 Flash confirmed |
| OpenCode + OpenRouter (free) | ❌ | All 13 free models broken |
| Claude Code + OpenRouter | ❌ | 404 — Anthropic metadata endpoints not emulated |
| Claude Code + Bedrock | ❌ | Timeout — connectivity issue |
| Codex CLI + ChatGPT | ❌ | Rate limited until Jul 25 |
| Codex CLI + OpenRouter | ❌ | Uses /v1/responses, unsupported |
