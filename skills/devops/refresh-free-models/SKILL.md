---
name: refresh-free-models
description: "On-demand weekly free-model list refresher for Hermes. Rebuilds provider model lists with only verified free models. Use when the user asks to refresh free models, update model lists, rebuild provider lists, or run the free-model refresh."
version: 1.0.0
author: Kevin McEuen
metadata:
  hermes:
    tags: [hermes, models, free, openrouter, nvidia, groq, dashscope, gemini, automation]
---

# Refresh Free Models Skill

On-demand free-model list refresher for Hermes config. Rebuilds provider model lists with only verified free models.

## Trigger Phrases

- "refresh free models"
- "update model lists"
- "rebuild providers"
- "run free-model refresh"
- "refresh free models skill"
- "weekly free models"

## What It Does

1. Reads API keys from the Hermes profile `.env`
2. Live-queries each provider's model API
3. Filters to free-only / free-tier models
4. Curates lists (removes stale/paid/broken entries)
5. Writes updated `config.yaml`
6. Appends results to `scripts/refresh_free_models.log`

## Providers Covered

| Provider | Source | Free Status |
|---|---|---|
| OpenRouter | Live API | Only `:free` tagged models |
| NVIDIA NIM | Live API + curated fallback | Free tier only |
| Groq | Live API + fallback list | Free tier |
| DashScope | Live API + fallback list | Free tier (rate-limited) |
| Gemini | Live API | Free tier |
| Nous Portal | Static list | Portal credits (not guaranteed free) |
| DeepSeek | Static list | **PAID** — kept out of auto-fallback |

## How to Invoke

### Via Skill Name
```
/skill refresh-free-models
```
or
```
hermes -s refresh-free-models -q "Refresh free models now"
```

### Via Cron (weekly auto)
Already configured as cron job `weekly-free-models-refresh` (Sundays 5pm).

### Manual Script Run
```bash
python "$HOME/AppData/Local/hermes/profiles/coding-profile/scripts/refresh_free_models.py"
```

## Output

After running, report:
- Models added/removed per provider
- Any providers that failed or were skipped
- Confirmation that config was updated
- Path to log file for details

## Script Paths

- Profile-local: `C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\scripts\refresh_free_models.py`
- Global: `C:\Users\kevin\.hermes\scripts\refresh_free_models.py`
- Log: `...scripts/refresh_free_models.log`

## Prerequisites

- Hermes profile at `C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile`
- `.env` file with valid API keys for each provider
- Python 3.11+ with `pyyaml` installed

## Maintenance

To add new providers: edit `build_config()` in the script.
To adjust free-model filters: edit the `_nim_candidates()`, `get_groq_free()`, etc.
To change schedule: `hermes cron edit weekly-free-models-refresh`
