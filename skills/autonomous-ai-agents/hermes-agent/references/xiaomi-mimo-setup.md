# Xiaomi MiMo Provider Setup

## Correct Configuration

```bash
# 1. Set API key in .env
echo "XIAOMI_API_KEY=<your-key>" >> ~/.hermes/.env

# 2. Configure provider (models MUST include provider prefix)
hermes config set model.provider xiaomi
hermes config set model.default "xiaomi/mimo-v2.5-pro"
hermes config set providers.xiaomi.models.0 "xiaomi/mimo-v2.5-pro"
hermes config set providers.xiaomi.models.1 "xiaomi/mimo-v2.5"

# 3. Clear base_url if switching from another provider (e.g., OpenRouter)
hermes config set model.base_url ""
```

## Common Pitfall: Missing Provider Prefix

Model names MUST include the `xiaomi/` prefix. Bare names like `mimo-v2.5-pro` will fail with:
```
✗ Model `mimo-v2.5-pro` was not found in this provider's model listing.
  Similar models: `xiaomi/mimo-v2.5-pro`, `xiaomi/mimo-v2.5`
```

## Common Pitfall: Stale base_url

If switching from OpenRouter to Xiaomi, the `model.base_url` may still be `https://openrouter.ai/api/v1`. 
Clear it with `hermes config set model.base_url ""` — Hermes auto-detects the endpoint for built-in providers.
