---
name: free-model-catalog-hygiene
description: "Keep Hermes provider model catalogs cleaned, free-first, and up to date. Use when the user wants to refresh free models, remove stale/paid models from /model pickers, rebuild provider lists, fix /model default confusion, set up weekly automatic refresh, or audit provider config for surprise-charge risks."
version: 1.0.0
author: Kevin McEuen
metadata:
  hermes:
    tags: [hermes, models, free, openrouter, nvidia, groq, dashscope, gemini, automation, provider-hygiene]
---

# Free Model Catalog Hygiene

Keep Hermes configured so `/model` shows useful free options, default stays free-first, and paid providers are only reachable manually.

## Trigger Phrases

- "refresh free models" / "update model lists" / "rebuild providers"
- "only the free ones" / "remove paid ones"
- "make this a weekly automation to rebuild free models"
- "/model defaults to older / wrong models"
- "fallback system" / "free fallback"
- "what models from grok are free"
- "free model picker" / "remove stale or old or paid ones"

## Core Problems This Skill Solves

1. `/model` defaults to wrong/older/paid models because `model.provider` and `model.base_url` are mismatched
2. `/model` picker shows stale or paid models
3. Users incur surprise charges because paid providers are in auto-fallback
4. NVIDIA NIM returns ~100+ free models, flooding `/model`
5. Groq / DashScope free tiers 403 during refresh; scripts must degrade gracefully
6. No ongoing mechanism to keep lists fresh

## Provider Ordering (Free-First)

`openrouter(free)` → `nvidia(free NIM)` → `groq(free)` → `dashscope(free tier)` → `gemini(free tier)` → `nous(portal credits)` → `deepseek(paid direct API)`

Primary should be `openrouter/free` unless the user explicitly wants DeepSeek as primary. Paid providers must be excluded from `fallback_providers` unless the user opts in.

## Live-API Rules By Provider

### OpenRouter
- Free if model id ends in `:free` OR `prompt == completion == 0`.
- All `grok-*` variants are paid — no free Grok on OpenRouter.
- Exclude non-chat/non-useful: `lyria-*`, `content-safety`, `nano-12b-v2-vl`, `prompt-guard`, `safeguard`.
- Keep only `:free` models in the Hermes OpenRouter picker.

### NVIDIA NIM
- Free tier charge covers many models: Llama, Qwen, DeepSeek V4 Pro/Flash, Gemma, Yi, DBRX, etc.
- Do **not** dump all 100+ free models into Hermes. Use a curated shortlist (prefer chat/instruct).
- If the curated list returns no matches at refresh time, fall back to a full free scan.

### Groq
- Commonly rate-limited to 403 on refresh.
- Keep a static known-free fallback list:
  - `llama-3.3-70b-versatile`
  - `llama-3.1-8b-instant`
  - `qwen/qwen2.5-32b`
  - `groq/compound`
  - `groq/compound-mini`
- Filter out: `whisper`, `guard`, `safeguard`, `orpheus`, `prompt-guard`.

### DashScope
- Free tier is rate-limited; live API may return 401/403.
- Keep a static known-free fallback list when API fails:
  - `qwen3-coder-plus`, `qwen3-max`, `qwen3-plus`, `qwen3-turbo`, `qwen3-coder`
  - `qwen2.5-coder-32b-instruct`
  - `qwen-turbo`, `qwen-plus`

### Gemini
- Free tier is rate-limited.
- Filter to chat models only; exclude TTS, image, robotics previews.
- Prefer: `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite`, `gemini-3.5-flash`, `gemini-3-pro-preview`, `gemini-3-flash-preview`.

### Nous Portal
- Uses OAuth portal credits — not charge-guaranteed.
- Keep out of free-first fallback; manual selection only if user wants Nous models.

### DeepSeek
- Direct API is paid. Keep configurable via `/model` for manual use.
- **Exception**: NVIDIA NIM exposes `deepseek-ai/deepseek-v4-pro` and `deepseek-ai/deepseek-v4-flash` as free. When the DeepSeek direct API key is invalid or expired, NVIDIA NIM is the free path to V4 Pro/Flash.

## Common Config Smells

| Symptom | Root Cause | Fix |
|---|---|---|
| `/model` shows old/paid defaults | `model.base_url` set to a provider X endpoint while `model.provider` is provider Y | Remove `model.base_url`; let each provider use its own default endpoint |
| `/model` picker has 100+ NVIDIA entries | Full free scan dumped into Hermes config | Use curated picker list instead of full scan |
| Surprise charges on Grok or Codex | Paid provider in `fallback_providers` | Remove paid providers from fallback; keep manual-only |
| DashScope/Groq 403 on refresh | Free-tier quota exceeded | Script must degrade to known static list instead of failing empty |
| DeepSeek key invalid | Old key expired / rotated | Re-auth or switch to NVIDIA NIM free endpoint |

## Weekly Refresh Automation

Use the canonical script:

`C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\scripts\refresh_free_models.py`

Synced copy:

`C:\Users\kevin\.hermes\scripts\refresh_free_models.py`

Log:

`C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\scripts\refresh_free_models.log`

Cron job `weekly-free-models-refresh` runs Sunday 17:00 local. Output is local-only by default.

## Integration

- Invoke standalone: `refresh-free-models` skill
- For Hermes provider auth issues: pair with `hermes-provider-debugging` (devops)
- For OmniRoute / external gateway free-model pooling: pair with `free-llm-gateway-stack` (mlops)
