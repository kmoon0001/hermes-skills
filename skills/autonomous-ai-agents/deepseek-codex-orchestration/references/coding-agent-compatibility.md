# Coding Agent Compatibility (verified 2026-07-21)

## OpenRouter Compatibility Matrix

| Coding Agent | Works with OpenRouter? | Why |
|-------------|----------------------|-----|
| **OpenCode** | ✅ Yes | Uses standard `/v1/chat/completions` — any OpenRouter model works |
| **Claude Code** | ❌ No | Hits Anthropic-specific model-metadata endpoints not emulated by OpenRouter. 404 on model discovery. Needs real Anthropic API key or Bedrock. |
| **Codex CLI** | ❌ No | Uses OpenAI's `/v1/responses` API. OpenRouter only supports `/v1/chat/completions`. 404 error: "No endpoints found." Needs real OpenAI key or ChatGPT OAuth. |

## Free Models on OpenRouter

All 13 `:free` models listed by OpenRouter fail with coding agents:

| Model | Failure |
|-------|---------|
| `google/gemma-4-31b-it:free` | Provider error |
| `nvidia/nemotron-3-super-120b-a12b:free` | No endpoints available (guardrail restrictions) |
| `openai/gpt-oss-20b:free` | Unknown server error |
| `cohere/north-mini-code:free` | Unknown server error |
| All others | Same — listed but can't serve requests |

**Conclusion:** `:free` models on OpenRouter are non-functional for coding agents. Use paid models only.

## Working Configurations

### OpenCode + DeepSeek (direct API)
```bash
export DEEPSEEK_API_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')")
opencode run "..." --model deepseek/deepseek-v4-flash   # fast, implementation
opencode run "..." --model deepseek/deepseek-v4-pro     # slow, deep analysis
```

### OpenCode + OpenRouter (paid models)
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
opencode run "..." --model openrouter/google/gemini-2.5-flash
opencode run "..." --model openrouter/anthropic/claude-haiku-4.5
```

### Claude Code (needs real Anthropic key)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
cd /project && claude -p "task" --max-turns 10 --output-format json
```

### Codex CLI (needs real OpenAI/ChatGPT auth)
The `codex exec` command works with ChatGPT OAuth tokens or `OPENAI_API_KEY`. OpenRouter config in `config.toml` will NOT work for `exec` — it's for the desktop app's model picker only.

## Provider Comparison for Coding Tasks

| Provider | Model | Coding Quality | Speed | Cost/M tokens |
|----------|-------|---------------|-------|---------------|
| DeepSeek (direct) | v4-flash | Excellent | Fast | ~$0.14 |
| DeepSeek (direct) | v4-pro | Excellent (deeper analysis) | Slow | ~$0.55 |
| OpenRouter | gemini-2.5-flash | Good | Fast | ~$0.15 |
| OpenRouter | claude-haiku-4.5 | Good | Fast | ~$0.25 |
