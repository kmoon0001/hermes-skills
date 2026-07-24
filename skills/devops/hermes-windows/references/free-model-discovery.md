# Free Model Discovery — OpenRouter & Gemini

Query available free models programmatically. Useful when choosing a
default model or helping the user pick cost-effective options.

## OpenRouter free models

OpenRouter marks free models with `pricing.prompt == "0"` and
`pricing.completion == "0"`.

```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | python -c "
import sys, json
d = json.load(sys.stdin)
free = [m for m in d.get('data', [])
        if float(m.get('pricing',{}).get('prompt','1') or '1') == 0
        and float(m.get('pricing',{}).get('completion','1') or '1') == 0]
print(f'{len(free)} free models')
for m in sorted(free, key=lambda x: x['id']):
    ctx = m.get('context_length', '?')
    print(f'  {m[\"id\"]:55s}  ctx: {ctx}')
"
```

### Notable free OpenRouter models (as of Jun 2026)

| Model | Context | Notes |
|-------|---------|-------|
| nousresearch/hermes-3-llama-3.1-405b:free | 131K | Nous Hermes |
| nvidia/nemotron-3-super-120b-a12b:free | 1M | Very large |
| nvidia/nemotron-3-ultra-550b-a55b:free | 1M | Largest free |
| qwen/qwen3-coder:free | 1M | Code-focused |
| openai/gpt-oss-120b:free | 131K | OpenAI open model |
| meta-llama/llama-3.3-70b-instruct:free | 131K | Meta |
| google/gemma-4-31b-it:free | 262K | Google open model |

## Gemini free tier

All Gemini models are free via Google AI Studio (rate-limited, no charge).
Use `GOOGLE_API_KEY` or `GEMINI_API_KEY`.

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY" \
  | python -c "
import sys, json
d = json.load(sys.stdin)
models = [m for m in d.get('models', [])
          if 'generateContent' in m.get('supportedGenerationMethods', [])]
print(f'{len(models)} Gemini models (all free with rate limits)')
for m in sorted(models, key=lambda x: x['name']):
    print(f'  {m[\"name\"].replace(\"models/\",\"\"):45s}  {m.get(\"displayName\",\"\")}')
"
```

### Recommended free defaults

- **gemini-2.5-flash** — fast, smart, free via Google API directly
- **openrouter/openai/gpt-oss-120b:free** — large, free via OpenRouter
- **openrouter/nousresearch/hermes-3-llama-3.1-405b:free** — Nous, free via OpenRouter

## Setting a free model as default

```bash
# Via Gemini directly
hermes config set model.provider gemini
hermes config set model.default gemini-2.5-flash

# Via OpenRouter (access to many free models)
hermes config set model.provider openrouter
hermes config set model.default openrouter/openai/gpt-oss-120b:free
```

## Pitfalls

- Free models on OpenRouter have rate limits. Heavy use may hit 429.
- Gemini free tier has per-minute and per-day quotas. Check console.
- `:free` suffix is required for free OpenRouter models — omitting it
  routes to the paid version.
- Some free models have lower quality than paid alternatives. Test before
  committing as a default for important workflows.
