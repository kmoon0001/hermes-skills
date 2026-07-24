# Z.AI GLM Provider Notes

## User Confusion: "I thought GLM had free use of 4.7 via API"

Users often assume GLM models (especially 4.7) are completely free without any registration. This is **incorrect**.

## Access Methods

### Direct Z.AI API (Requires Registration + API Key)

- **Provider name:** `zai` (not `glm`)
- **Environment variable:** `GLM_API_KEY`
- **Setup:** Get key from https://open.bigmodel.cn/
- **Commands:**
  ```bash
  hermes config set GLM_API_KEY=***
  # Or add to ~/.hermes/.env manually
  ```

- **Reality:** No completely free tier. You must register and get a key.

### NVIDIA NIM Hosting (Limited GLM Availability)

- **Provider name:** `nvidia`
- **Environment variable:** `NVIDIA_API_KEY`
- **Setup:** Get free key from https://build.nvidia.com/
- **GLM models on NVIDIA:** `z-ai/glm-5.2` (model '98' in NVIDIA config)
- **Reality:** NVIDIA's free tier includes credits, but model selection is limited. GLM-4.7 is NOT available on NVIDIA.

### OpenRouter Proxy (Pay-per-use)

- **Provider name:** `openrouter`
- **Environment variable:** `OPENROUTER_API_KEY`
- **GLM models available:** `z-ai/glm-5.2`, others
- **Reality:** Pay-per-token. No free tier, but you get access to all GLM models through one provider.

## Diagnostic Checklist

When a user says "I thought GLM was free" or "I don't have GLM API":

1. **Check current provider/model:**
   ```bash
   hermes config get providers | grep -i "zai\|z-ai\|glm"
   ```
   - Look for `zai` provider entry (NOT `glm`)
   - Look for GLM models under `nvidia` (only 5.2 typically)

2. **Check for API key:**
   ```bash
   env | grep -i GLM
   # Or
   hermes config check  # Look for GLM_API_KEY: ✓
   ```

3. **Explain the three paths:**
   - Direct Z.AI → requires GLM_API_KEY
   - NVIDIA → requires NVIDIA_API_KEY, limited GLM selection
   - OpenRouter → requires OPENROUTER_API_KEY, pay-per-use

4. **Clarify "free" vs "free tier":**
   - GLM has a free **tier** (with registration), not free **unlimited access**
   - NVIDIA has free credits, but not all GLM models
   - No truly free API access without some form of registration

## Key Misconceptions

- ❌ "GLM-4.7 is free and works without a key"
- ✅ GLM-4.7 requires `GLM_API_KEY` from https://open.bigmodel.cn/

- ❌ "NVIDIA hosts all GLM models for free"
- ✅ NVIDIA hosts GLM-5.2, not 4.7. Requires `NVIDIA_API_KEY`.

- ❌ "I can use GLM through any provider without setup"
- ✅ Must choose a path: direct Z.AI, NVIDIA, or OpenRouter, and set the corresponding API key.

## When This Shows Up

Symptom: User sees `zai/glm-4.7` in their config but gets auth errors.

Fix: Set `GLM_API_KEY` in `~/.hermes/.env` or `hermes config set GLM_API_KEY=***`.

## Related Skills

- `hermes-provider-debugging` — Full diagnostic workflow for provider failures.
- `free-model-catalog-hygiene` — For refreshing and maintaining free model lists.

## Last Updated

2026-07-21 — Based on conversation where user expected GLM-4.7 to work without API key.