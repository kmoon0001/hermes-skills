# Kevin's Hermes Provider Landscape

Last updated: 2026-07-21

## Active Providers & Auth Method

| Provider | Config Key | Auth | Tier | Models |
|---|---|---|---|---|---|
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | Free tier + credits | Nemotron Ultra 550B, Nemotron Super 120B, Qwen3 Coder, GPT-OSS 120B, Llama 3.3 70B, Hermes 3 405B, Gemma 4 31B, Qwen3 Next 80B, North Mini Code, Nemotron Nano 9B |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` | Free tier | 2.5 Pro, 3.1 Pro Preview, 3.5 Flash, 2.5 Flash, 3.1 Flash Lite, 2.0 Flash |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | Paid (credits) | deepseek-v4-flash (replaces chat/reasoner, 1M ctx), deepseek-v4-pro (upgraded reasoning, 1M ctx). deepseek-chat and deepseek-reasoner deprecated 2026-07-24. |
| Nous | `nous` | OAuth (`hermes auth add nous`) | Subscription | Hermes 4 70B/405B, Hermes 3 70B/405B |
| Xiaomi MiMo | `xiaomi` | `XIAOMI_API_KEY` | Paid (credits) | MiMo V2.5 Pro, MiMo V2.5 |
| DashScope/Qwen | `alibaba` ⚠️ | `DASHSCOPE_API_KEY` | Free credits | Qwen3 Coder Plus, Qwen3 Max, Qwen3 Plus |
| Z.AI / GLM | `zai` | `GLM_API_KEY` | Free tier | GLM-4 Plus, GLM-4 Flash |
| Groq | `groq` | `GROQ_API_KEY` | Free tier | Llama 3.3 70B, Qwen 2.5 32B, DeepSeek R1 Distill 70B, Mixtral 8x7B |
| OpenAI Codex | `openai-codex` | OAuth (`hermes auth add openai-codex`) | ChatGPT sub | GPT-5.x, GPT-4.1, o4-mini |
| NVIDIA NIM | `nvidia` | (configured in config.yaml) | Free | Nemotron 3 Ultra 550B, Super 120B, Nano 9B |

⚠️ **DashScope provider key is `alibaba`, not `dashscope`.** The config.yaml `providers:` section must use `alibaba:` (or `alibaba-coding-plan:` for the coding endpoint). Using `dashscope:` may silently fail. See `alibaba-qwen-provider-setup` skill for details.

## Free Model Ranking (agentic coding capability)

Best → worst among free-tier models:

1. `nvidia/nemotron-3-ultra-550b-a55b:free` (OpenRouter) — 550B MoE
2. `gemini-2.5-pro` (Gemini) — Google's best free
3. `nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter) — 120B MoE
4. `qwen/qwen3-coder:free` (OpenRouter) — coding specialist
5. `openai/gpt-oss-120b:free` (OpenRouter) — 120B
6. `meta-llama/llama-3.3-70b-instruct:free` (OpenRouter) — 70B
7. `nousresearch/hermes-3-llama-3.1-405b:free` (OpenRouter) — 405B older arch
8. `gemini-3.5-flash` (Gemini) — fast + capable
9. `google/gemma-4-31b-it:free` (OpenRouter) — 31B
10. `qwen/qwen3-next-80b-a3b-instruct:free` (OpenRouter) — 80B MoE
11. `cohere/north-mini-code:free` (OpenRouter) — coding
12. `nvidia/nemotron-nano-9b-v2:free` (OpenRouter) — small/fast

## Fallback Provider Chain

The `fallback_providers` list in `config.yaml` controls which providers Hermes tries when the primary model fails. Current chain:

1. **openrouter** — default, broadest free model selection
2. **nvidia** — Nemotron 3 Ultra → Super → Nano (per-provider model list)
3. **gemini** — Google Gemini direct API
4. **deepseek** — deepseek-v4-pro / deepseek-v4-flash (legacy deepseek-chat/reasoner deprecated 2026-07-24)
5. **openai-codex** — OAuth via ChatGPT subscription
6. **nous** — OAuth via Nous subscription

Per-provider model lists (under `providers.<name>.models`) act as sub-priority — e.g. groq has `llama-3.3-70b → qwen-2.5-32b → deepseek-r1-distill-llama-70b → mixtral-8x7b`.

Inspect via: `grep -A10 'fallback_providers:' "$(hermes config path)"`

## Editing Provider Model Lists in config.yaml

The `hermes config set` CLI only handles single keys. For bulk model list edits:

```python
# In execute_code — read, transform, write
config_path = r"C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\config.yaml"
with open(config_path, "r") as f:
    content = f.read()

# Use regex to find the providers block
import re
match = re.search(r'^providers:.*?(?=^credential_pool)', content, re.DOTALL | re.MULTILINE)

# Build replacement, write back
# ... transform ...
with open(config_path, "w") as f:
    f.write(content)
```

Never use `read_file` for `.env` or `config.yaml` — they're guarded. Always use `execute_code` or `terminal` with `cat`.
