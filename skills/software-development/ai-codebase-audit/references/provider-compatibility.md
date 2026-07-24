# Provider Compatibility Matrix

Findings from July 2026 testing of three autonomous coding agents (Claude Code 2.1.123, Codex CLI 0.144.5, OpenCode 1.18.4) against OpenRouter and direct API providers.

## Summary

| Agent | OpenRouter | Direct API | Root Cause |
|-------|-----------|------------|------------|
| **OpenCode** | ✅ Works | ✅ Works (DeepSeek) | Standard OpenAI-compatible `/v1/chat/completions` |
| **Claude Code** | ❌ 404 on models | ✅ (needs Anthropic key) | Uses Anthropic-specific model metadata endpoints |
| **Codex CLI** | ❌ 404 on `/v1/responses` | ✅ (needs OpenAI key/ChatGPT auth) | Uses OpenAI Responses API; OpenRouter only supports Chat Completions |

## OpenRouter Compatibility Details

### OpenCode + OpenRouter: ✅
- Tested model: `openrouter/google/gemini-2.5-flash`
- Uses standard `/v1/chat/completions` endpoint
- Works with any OpenRouter model that supports tool use
- Smoke test: `opencode run "Say: OK" --model openrouter/google/gemini-2.5-flash` → "OK"

### Claude Code + OpenRouter: ❌
- Claude Code v2.1.123 configured with `ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"`
- Requests hit 404 on model validation, even though `curl` confirms the model works on the same endpoint
- Error: `api_error_status: 404, "There's an issue with the selected model"`
- Claude Code likely queries model metadata endpoints that OpenRouter's Anthropic emulation doesn't support
- **Requires**: Real Anthropic API key + `ANTHROPIC_BASE_URL="https://api.anthropic.com"`

### Codex CLI + OpenRouter: ❌
- Codex v0.144.5 configured with `model_provider = "openrouter"`, `base_url = "https://openrouter.ai/api/v1"`
- Model routing works (model name accepted), but tool execution fails
- Error: `unexpected status 404 Not Found: No endpoints found for <model>, url: https://openrouter.ai/api/v1/responses`
- Codex uses OpenAI's Responses API (`/v1/responses`) for tool orchestration
- OpenRouter only supports Chat Completions (`/v1/chat/completions`)
- **Requires**: Real OpenAI API key or ChatGPT auth (rate-limited as of Jul 21, reset Jul 25)

## Free Model Limitations

All 13 OpenRouter `:free` models tested with OpenCode for coding tasks:

| Model | Error |
|-------|-------|
| `google/gemma-4-31b-it:free` | "Unexpected server error" |
| `nvidia/nemotron-3-super-120b-a12b:free` | "No endpoints available" |
| `openai/gpt-oss-20b:free` | "Unexpected server error" |
| `cohere/north-mini-code:free` | "Unexpected server error" |
| All others | Same class of error |

Root cause: free models don't support tool use (bash, file read/write) through OpenCode's tool orchestration. The models can complete simple chat but fail when OpenCode tries to use them as coding agents.

## Working Model Recommendations

### For Speed/Implementation
- `deepseek/deepseek-v4-flash` — ~$0.14/M tokens, fast, strong Python coder
- `google/gemini-2.5-flash` — ~$0.15/M tokens, reliable fallback

### For Deep Analysis
- `deepseek/deepseek-v4-pro` — ~$0.55/M tokens, thorough but slow (>300s timeout risk)

## Auth Setup

### DeepSeek (Windows)
```bash
# Key is in Windows User env vars, not Hermes credential pool
DEEPSEEK_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')")
export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
```

### OpenRouter
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

## Claude Code Auth Details

Claude Code auth modes tested:
- **Amazon Bedrock**: Configured but timed out (connectivity issues)
- **Anthropic API**: Requires `ANTHROPIC_API_KEY` env var (not set; Hermes lists it as available but env var is empty)
- **OpenRouter passthrough**: Fails (see above)

Claude Code settings at `~/.claude/settings.json`:
- `ANTHROPIC_BASE_URL` — base URL for API requests
- `ANTHROPIC_AUTH_TOKEN` — API key / auth token
- `CLAUDE_CODE_USE_BEDROCK` — set to "0" to use Anthropic API instead of Bedrock
- `model` — model alias (e.g., `claude-haiku-4-5`)

## Codex CLI Auth Details

Codex auth modes tested:
- **ChatGPT tokens**: Works but rate-limited (Jul 25 reset)
- **OpenAI API key**: Supports `codex login --with-api-key` but requires real OpenAI key
- **OpenRouter provider**: Configured in `~/.codex/config.toml` as `[model_providers.openrouter]` but unused because Codex routes through ChatGPT backend when ChatGPT-auth is active

Codex model_provider switching requires changing both the config's `model_provider` AND the auth mode. ChatGPT auth locks the provider to OpenAI.
