# OpenRouter Incompatibility Details (2026-07-21)

## Claude Code + OpenRouter

**Symptom:** All model names return 404 with `api_error_status: 404` and zero
input/output tokens. The error message says "It may not exist or you may not
have access to it."

**Root cause:** Claude Code hits Anthropic-specific endpoints beyond just
`/v1/messages`. It queries model metadata or validates the model ID against
endpoints that OpenRouter's Anthropic emulation doesn't support. Our curl
tests confirmed the same model name (`claude-haiku-4-5`, `anthropic/claude-haiku-4-5`)
works fine via direct curl to OpenRouter's `/api/v1/messages` but Claude Code
rejects it.

**Models tested and failed:** `claude-haiku-4-5`, `claude-haiku-4-5-20250505`,
`claude-sonnet-4-6`, `anthropic/claude-haiku-4-5`, `anthropic/claude-haiku-latest`.

**Resolution:** Use a real Anthropic API key or Amazon Bedrock. Do not attempt
OpenRouter as an Anthropic backend for Claude Code.

## Codex CLI + OpenRouter

**Symptom (initial):** `"The '<model>' model is not supported when using Codex
with a ChatGPT account"` — Codex routes through ChatGPT's backend which rejects
non-OpenAI model names.

**Fix for routing:** Change `model_provider` in `~/.codex/config.toml` from
`"openai"` to `"openrouter"`. This routes requests to OpenRouter's base URL.

**Symptom (after fix):** `"unexpected status 404 Not Found: No endpoints found
for <model>, url: https://openrouter.ai/api/v1/responses"` — Codex uses
OpenAI's Responses API (`/v1/responses`) which OpenRouter does not support.
OpenRouter only has `/v1/chat/completions`.

**Resolution:** Codex CLI requires a real OpenAI API key or ChatGPT token auth.
No OpenRouter workaround exists.

## OpenCode + OpenRouter Free Models

**Symptom:** All `:free` models return `"UnknownError"` / `"Unexpected server
error"` when used with `opencode run`. Direct curl tests show:
- `google/gemma-4-31b-it:free` → "Provider returned error" (400)
- `nvidia/nemotron-3-super-120b-a12b:free` → "No endpoints available matching guardrail restrictions"
- All 13 free models fail the same way.

**Resolution:** OpenRouter free models don't support tool use. Use a paid
model or a direct provider key (DeepSeek, Anthropic, Gemini).
