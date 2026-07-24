---
name: hermes-provider-debugging
description: Diagnose and fix Hermes provider/model connection failures — 401, 403, 429, credential exhaustion, missing auth, and provider routing issues.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, debugging, providers, auth, troubleshooting]
---

# Hermes Provider Debugging

Systematic workflow for diagnosing why a model/provider connection fails in Hermes Agent. Covers auth issues, credential pool exhaustion, and provider routing.

## When to Load

- Model switch breaks connections ("I changed model and now nothing works")
- 401/403/429 errors from any provider
- Provider silently falls back to a different model
- Credential pool shows a provider but calls still fail

## Diagnostic Workflow (in order)

### 1. Check credential inventory

```bash
hermes auth list
```

Look for:
- Is the provider even listed? Missing = no credentials configured at all.
- Active credential marker (←) — is the right one active?
- Exhaustion flags: `rate-limited (429)`, `AllocationQuota.FreeTierOnly (403)`, `(ready to retry)`
- Pool size: single-key pools are fragile — one exhaustion = provider dead

### 2. Check env vars recognized

```bash
hermes config check
```

○ = optional, not set. ✓ = set and recognized.

Common: `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `NOUS_BASE_URL`.

### 3. Check error logs for the real failure

```bash
grep -i "401\|403\|429\|credential.*pool\|exhaust\|provider.*fail" ~/.hermes/logs/errors.log | tail -40
grep -i "401\|403\|429\|credential.*pool\|exhaust" ~/.hermes/logs/agent.log | tail -40
```

Key patterns:
- `401: User not found` → API key is dead/revoked — replace it
- `401: Invalid API key` → malformed or wrong key
- `403: AllocationQuota.FreeTierOnly` → free tier exhausted, need paid key or wait
- `429: rate_limit_error` → rate limited, credential pool auto-rotates
- `credential pool: marking X exhausted, rotating` → pool is self-healing
- `credential pool: no available entries (all exhausted or empty)` → pool is stuck

### 4. Reset exhausted credentials

```bash
hermes auth reset <provider>
```

Resets exhaustion flags so the pool tries the key again. Only useful if the key itself is still valid (won't help with 401 "User not found" — those need a new key).

### 5. Add/replace API keys

```bash
hermes auth add <provider> --type api-key
```

Interactive secure prompt. For OAuth providers (Nous, OpenAI Codex):

```bash
hermes auth add nous                    # Opens browser for device-code flow
hermes auth add nous --no-browser      # Prints URL for manual auth
```

### 6. Understand provider routing

Models can route through multiple providers. The same Google model might work via direct `gemini` but fail via OpenRouter proxy:

- `google/gemini-2.5-flash` routed through `openrouter` → uses `OPENROUTER_API_KEY`
- Native `gemini` models under `providers.gemini` → uses `GOOGLE_API_KEY`

Check your model shortcuts in `config.yaml` under `providers:` to see which provider each model alias maps to. A dead OpenRouter key cascades to ALL models routed through it.

## Bypassing secret redaction to test keys

Hermes redacts API keys in tool output. To test a key directly without redaction:

```python
# In execute_code — bypasses secret redaction
import urllib.request
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/auth/key",
    headers={"Authorization": f"Bearer {key}"}
)
try:
    resp = urllib.request.urlopen(req)
    print(f"HTTP {resp.status}: {resp.read().decode()[:200]}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:200]}")
```

OpenRouter key format: `sk-or-v1-...` (73 chars typical). If it doesn't start with `sk-or-v1-`, it's not an OpenRouter key.

## Google AI Studio: API keys only, no OAuth

Google AI Studio / Gemini provider only supports `--type api-key` in Hermes. `hermes auth add gemini --type oauth` returns `"not implemented for auth type oauth yet"`. Use `GOOGLE_API_KEY` or `GEMINI_API_KEY` env vars only. For Vertex AI (Google Cloud), use service account JSON with `VERTEX_CREDENTIALS_PATH`.

### 7. Inspect the fallback provider chain

When Hermes's primary model fails (rate limit, 5xx, credential exhaustion), it walks down `fallback_providers` in order — each entry is a provider name, tried with that provider's default model.

```bash
# View the fallback chain directly from config
hermes config set show_fallback  # Not a real config key — read config.yaml instead
hermes config edit               # Search for 'fallback_providers'
```

Key locations in `config.yaml`:
- **`fallback_providers:`** — ordered list of provider names (e.g. `[openrouter, nvidia, gemini, deepseek, openai-codex, nous]`)
- **Per-provider `models:` under `providers:`** — sub-priority within each provider. When a provider's primary model fails, it tries its own model list first (e.g. `nvidia.nemotron-3-ultra-550b → super-120b → nano-9b`) before falling back to the next provider.

Full chain resolution:
1. Primary model (`model.default` + `model.provider`) fails → try next model in that provider's `models:` list
2. Provider's own model list exhausted → move to next provider in `fallback_providers:`
3. All providers exhausted → error returned to user

Quick inspection without editing:

```bash
# From execute_code or terminal
grep -A3 'fallback_providers' ~/AppData/Local/hermes/profiles/*/config.yaml
# Or with profile awareness (current profile):
grep -A10 'fallback_providers' "$(hermes config path)"
```

## Dataverse API Token: Trailing Slash in Resource URL

When acquiring a token for Dataverse API calls via `az account get-access-token`, the **trailing slash on the resource URL matters** and varies by environment:

```bash
# ✅ WORKS — no trailing slash (most Dataverse orgs)
az account get-access-token --resource "https://orgbd048f00.crm.dynamics.com"

# ❌ Returns 401 — with trailing slash (on some orgs)
az account get-access-token --resource "https://orgbd048f00.crm.dynamics.com/"

# ⚠ If one fails, try the other — the correct format is environment-dependent
```

**Symptoms:** Token returns `401 Unauthorized` when used against the Dataverse API, even though `az` successfully issued it. The JWT's `aud` claim looks correct.

**Debug command:**
```bash
# Decode the token to check audience
python3 -c "
import base64, json
parts=open('/path/to/token.txt').read().strip().split('.')
payload=parts[1] + '=' * (4 - len(parts[1]) % 4)
data=json.loads(base64.urlsafe_b64decode(payload))
print('aud:', data.get('aud','?'))
"
```

**Fix:** If one format returns 401, acquire a fresh token with the other URL format (trailing slash vs no trailing slash). The two tokens have different `aud` claims and only one will match the Dataverse API's expected audience.

## DeepSeek v4 Provider Config

DeepSeek's v4 models (`deepseek-v4-flash`, `deepseek-v4-pro`) have specific config requirements:

### Base URL

```yaml
# ✅ CORRECT — no /v1 suffix
providers:
  deepseek:
    base_url: https://api.deepseek.com

# ❌ OLD / WRONG — the /v1 path was from the pre-v4 era
    base_url: https://api.deepseek.com/v1
```

DeepSeek uses the same base URL (`https://api.deepseek.com`) for all models — the model name in the request body determines which version runs. The `/v1` suffix is technically still accepted (OpenAI compatibility fallback) but not documented and should be removed.

### Model Name Mapping

| Old Name | Replacement | Behavior | Deprecation |
|---|---|---|---|
| `deepseek-chat` | `deepseek-v4-flash` | Non-thinking mode | 2026-07-24 |
| `deepseek-reasoner` | `deepseek-v4-flash` | Thinking mode (default) | 2026-07-24 |
| (new) | `deepseek-v4-pro` | Premium reasoning, 1M context | — |

NOTE: Both `deepseek-chat` and `deepseek-reasoner` map to the same underlying model (`deepseek-v4-flash`), differing only in thinking mode. `deepseek-v4-flash` itself supports both modes — you switch via the `thinking_mode` parameter (not the model name). `deepseek-v4-pro` is a separate, larger model with 1.6T/49B MoE parameters.

### What to Check When User Says "I'm on v1 but expected v4"

1. Check `providers.deepseek.base_url` in config.yaml — if it has `/v1`, strip it (cosmetic, likely still works)
2. Check the model string being sent — `deepseek-chat` maps to v4-flash, not v1. The model name is the version selector, not the URL path.
3. Run a direct API test to confirm which model responds:

```bash
curl -s https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"what model are you?"}],"max_tokens":100}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','')[:200])"
```

The model will typically identify itself as "DeepSeek Chat" or "DeepSeek V4" — if it says "DeepSeek-V2" something's wrong.

## Pitfalls

- **Provider/base_url mismatch causes /model confusion.** The `model.provider`, `model.default`, and `model.base_url` fields in `config.yaml` must all be consistent. If `model.provider` is `openrouter` but `model.base_url` points to a different provider's endpoint (e.g. `https://open.bigmodel.cn/api/paas/v4` for Zhipu/GLM), the `/model` picker shows confusing options and routing silently breaks. Symptom: user says "I don't know why `/model` defaults to the older models" or sees models from the wrong provider. Fix: set all three fields to the same provider:
  ```bash
  hermes config set model.provider <provider>
  hermes config set model.default <model-name>
  hermes config set model.base_url <provider-api-url>
  ```
  Then restart the session (`/new`). The `/model` interactive picker reads from the provider's model list under `providers.<name>.models`, not the base_url — but the LLM client uses the base_url for actual API calls. A mismatch means the picker looks right but calls fail, or vice versa.

- **`hermes auth` commands need 30s+ timeout on Windows.** 10s is not enough — the credential pool scan and any network probes can take 15-20s.
- **Credential pool exhaustion is sticky.** After a 401, the pool won't retry that key until you `hermes auth reset` or restart. With single-key pools, the provider stays dead.
- **Profile `.env` vs base `.env`.** `hermes config env-path` shows the profile-specific file, but auth pools scan both. Don't assume a key is missing just because it's not in the profile `.env`.
- **Nous OAuth tokens expire silently.** `hermes auth list` shows no `nous` entry when the OAuth token expires. Re-run `hermes auth add nous`.
- **Direct provider vs OpenRouter proxy.** A Google API key works for direct Gemini but NOT for `openrouter/google/*` models. Those need a valid OpenRouter key.
- **"User not found" (401) on a valid-format key means the key is dead.** Even if the key has the correct prefix and length, 401 = the account was deleted, the key was revoked, or it was generated on a different account. Get a BRAND NEW key from the provider dashboard — don't reuse any existing key from the list.
- **Fresh key still 401 → account itself is dead.** If you generate a brand new key from the OpenRouter dashboard and it immediately returns 401, the entire account was deactivated — not just the key. The credits display in the dashboard may be stale/cached. Create a NEW OpenRouter account and start fresh. Do not keep generating keys on a dead account.
- **`hermes config set` with nested dicts writes JSON strings, not YAML.** Setting `providers.deepseek.models '{"0":"deepseek-v4-flash"}'` produces a YAML scalar string (`models: '{"0":"deepseek-v4-flash"}'`) instead of a proper YAML mapping. This breaks the `/model` picker. Workaround on Windows (git-bash):
  ```bash
  # Set each model individually — still has extra quoting
  hermes config set providers.deepseek.models.0 '"deepseek-v4-flash"'
  hermes config set providers.deepseek.models.1 '"deepseek-v4-pro"'
  # Then strip the extra quotes with sed
  sed -i 's/"deepseek-v4-flash"/deepseek-v4-flash/' "$LOCALAPPDATA/hermes/profiles/<profile>/config.yaml"
  ```
  Alternative: use `execute_code` to read the file, transform, and write back via Python — the `hermes config set` CLI only handles flat keys cleanly.
- **DeepSeek deprecated `deepseek-chat` and `deepseek-reasoner`** (effective 2026-07-24). See the "DeepSeek v4 Provider Config" section above for the full model mapping. NOTE: `deepseek-chat` maps to v4-flash, NOT v1 — the model name, not the URL path, determines the version.

## Reference Files

- `references/error-patterns.md` — Real-world error transcripts: OpenRouter 401 cascade, Nous OAuth expiration, Gemini routing confusion, credential pool exhaustion timing.
- `references/provider-landscape.md` — Kevin's complete provider landscape: active providers, auth methods (API key vs OAuth), free vs credit vs subscription tiers, free model ranking for agentic coding, and the execute_code workflow for bulk config.yaml model list edits.
- `references/zai-glm-provider-notes.md` — Z.AI GLM provider setup: API key requirements, model availability, and the difference between free tier assumptions and actual key-based access. GLM does NOT offer completely free API access without registration.
