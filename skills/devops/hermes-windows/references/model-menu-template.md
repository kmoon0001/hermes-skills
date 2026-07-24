# Comprehensive Model Menu Template

Ready-to-paste model menu for `config.yaml` providers section. Organized
by category with free models first. Customize model IDs as needed.

## Full template (OpenRouter + Gemini + Nous)

```yaml
fallback_providers:
  - openrouter
  - gemini
  - nous

providers:
  openrouter:
    models:
      # === FREE ===
      '00': nousresearch/hermes-3-llama-3.1-405b:free
      '01': qwen/qwen3-coder:free
      '02': nvidia/nemotron-3-ultra-550b-a55b:free
      '03': nvidia/nemotron-3-super-120b-a12b:free
      '04': openai/gpt-oss-120b:free
      '05': meta-llama/llama-3.3-70b-instruct:free
      '06': google/gemma-4-31b-it:free
      '07': cohere/north-mini-code:free
      '08': qwen/qwen3-next-80b-a3b-instruct:free
      '09': nvidia/nemotron-nano-9b-v2:free
      '10': openrouter/free
      # === NOUS (paid) ===
      '20': nousresearch/hermes-4-70b
      '21': nousresearch/hermes-4-405b
      '22': nousresearch/hermes-3-llama-3.1-70b
      '23': nousresearch/hermes-3-llama-3.1-405b
      # === OPENAI (paid) ===
      '30': openai/gpt-5.5
      '31': openai/gpt-5.5-pro
      '32': openai/gpt-5.4
      '33': openai/gpt-5.4-mini
      '34': openai/gpt-4.1
      '35': openai/gpt-4.1-mini
      '36': openai/o4-mini
      # === ANTHROPIC (paid) ===
      '40': anthropic/claude-sonnet-4
      '41': anthropic/claude-opus-4
      '42': anthropic/claude-haiku-4.5
      '43': anthropic/claude-3-haiku
      # === GOOGLE (paid via OpenRouter) ===
      '50': google/gemini-2.5-flash
      '51': google/gemini-2.5-pro
      '52': google/gemini-2.5-flash-lite
      '53': google/gemini-3.1-flash-lite
      '54': google/gemini-3.1-pro-preview
      # === DEEPSEEK (paid) ===
      '60': deepseek/deepseek-chat
      '61': deepseek/deepseek-r1
      '62': deepseek/deepseek-chat-v3.1
      # === XAI/GROK (paid) ===
      '70': x-ai/grok-4.20
      '71': x-ai/grok-4.3
      # === MISTRAL (paid) ===
      '80': mistralai/codestral-2508
      '81': mistralai/devstral-2512
      '82': mistralai/mistral-large
      # === XIAOMI (paid) ===
      '90': xiaomi/mimo-v2.5
      '91': xiaomi/mimo-v2.5-pro
      # === KIMI (paid) ===
      '95': moonshotai/kimi-k2.6
      '96': moonshotai/kimi-k2.5
      # === AUTO ===
      '99': openrouter/auto
  gemini:
    models:
      '0': gemini-2.5-flash
      '1': gemini-2.5-pro
      '2': gemini-3.1-flash-lite
      '3': gemini-3.1-pro-preview
      '4': gemini-3.5-flash
      '5': gemini-2.0-flash
  nous:
    models:
      '0': hermes-4-70b
      '1': hermes-4-405b
      '2': hermes-3-llama-3.1-70b
      '3': hermes-3-llama-3.1-405b
```

## How to set default

```yaml
model:
  default: openrouter/nousresearch/hermes-3-llama-3.1-405b:free
  provider: openrouter
```

## Key naming convention

Use two-digit strings (`'00'`, `'01'`, ...) grouped by category:
- `00-19`: Free models
- `20-29`: Nous
- `30-39`: OpenAI
- `40-49`: Anthropic
- `50-59`: Google
- `60-69`: DeepSeek
- `70-79`: xAI/Grok
- `80-89`: Mistral
- `90-99`: Other (Xiaomi, Kimi, auto)

## Pitfalls

- YAML treats unquoted `00` as integer `0`. Always quote model keys: `'00'`.
- `:free` suffix is required for free OpenRouter models — omitting it
  routes to the paid version.
- Profile .env must have the API key, not just main .env.
- `python -m py_compile` won't catch YAML issues — validate with a
  quick `grep` or load test after editing config.yaml.
