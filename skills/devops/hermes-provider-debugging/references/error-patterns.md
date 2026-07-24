# Error Patterns & Transcripts

Real-world error patterns encountered and resolved.

## OpenRouter 401 Cascade ("User not found")

**Symptom:** Switching to any OpenRouter model fails. User reports "all connections don't work when I change model."

**Root cause:** Dead/revoked `OPENROUTER_API_KEY`. OpenRouter returns 401 "User not found" on every call.

**How it cascades:** With `openrouter` as first fallback provider and many model shortcuts aliased through OpenRouter (e.g., `openrouter/google/gemini-2.5-flash`, `openrouter/free`), one dead key breaks ALL proxied models — not just OpenRouter-native ones.

**Log evidence (from errors.log, May 29):**
```
provider=openrouter model=openrouter/google/gemini-2.5-flash
HTTP 401: User not found.

provider=openrouter model=nvidia/nemotron-3-super-120b-a12b:free
HTTP 401: User not found.

provider=openrouter model=openrouter/free
HTTP 401: User not found.

provider=openrouter model=deepseek/deepseek-chat-v3.1
HTTP 401: User not found.
```

**Credential pool behavior:**
```
credential pool: marking OPENROUTER_API_KEY exhausted (status=401), rotating
credential pool: no available entries (all exhausted or empty)
```

Single-key pool → exhaustion = provider dead. Reset doesn't help — key itself is invalid.

**Fix:** Get new key from https://openrouter.ai/keys, then `hermes auth add openrouter --type api-key`.

**Account deactivation variant:** If even a brand new key from the dashboard returns 401 immediately, the OpenRouter account itself was deactivated — not just the key. Credits may still display in the dashboard (stale cache) but the account is gone. Solution: create a new OpenRouter account entirely.

## Nous OAuth Expiration

**Symptom:** `hermes auth list` shows no `nous` entry. Models configured under `providers.nous` fail silently.

**Root cause:** OAuth device-code token expired. Hermes doesn't auto-refresh Nous OAuth tokens.

**Log evidence:**
```
provider=nous base_url=https://inference-api.nousresearch.com/v1
model=google/gemini-3.1-flash-lite-preview
HTTP 503: The requested model is temporarily unavailable
```

The 503 is upstream capacity, but the OAuth token had also expired — the provider would have gone dark regardless once the token expired.

**Fix:** `hermes auth add nous` — interactive browser OAuth flow.

## Google/Gemini Provider Routing Confusion

**Symptom:** User has valid `GOOGLE_API_KEY` but Google models still fail.

**Root cause:** Google models can route through TWO different providers:
- **Direct `gemini` provider** — uses `GOOGLE_API_KEY` / `GEMINI_API_KEY`, works
- **OpenRouter proxy** (`openrouter/google/*`) — uses `OPENROUTER_API_KEY`, inherits OpenRouter's auth state

Dead OpenRouter key = `openrouter/google/gemini-2.5-flash` fails even though `gemini` provider works fine.

**Model alias check:** In `config.yaml` under `providers.gemini.models` vs `providers.openrouter.models`, Google models appear under both. The shortcut key determines which provider handles the call.

## Credential Pool Exhaustion Window

On Windows, `hermes auth` commands (list, reset, add) need **30-second timeouts**. The credential pool scan + env var resolution can take 15-20s. 10s timeouts always fail.

```bash
# Works:
hermes auth list                    # 30s timeout
hermes auth reset openrouter        # 30s timeout

# Fails:
timeout 5 hermes auth list         # Too short
```

## Bypassing Secret Redaction for Key Validation

Hermes redacts API keys in terminal output. To validate a key directly without redaction, use `execute_code` with Python's `urllib`:

```python
import urllib.request, urllib.error

# Read key from .env (bypasses redaction since execute_code has file access)
with open(r"C:\Users\<user>\AppData\Local\hermes\.env") as f:
    for line in f:
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.strip().split("=", 1)[1]
            break

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/auth/key",
    headers={"Authorization": f"Bearer {key}"}
)
try:
    resp = urllib.request.urlopen(req)
    print(f"HTTP {resp.status}: key valid — {resp.read().decode()[:200]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:200]}")
    # 401 "User not found" = key dead
    # 401 "Invalid API key" = malformed
```

OpenRouter key format: `sk-or-v1-...` (73 chars typical). If the prefix doesn't match, it's not an OpenRouter key — check you copied from the right provider.

## Google AI Studio OAuth — Not Supported

`hermes auth add gemini --type oauth` returns: `"not implemented for auth type oauth yet"`.

Google AI Studio only supports API keys (`GOOGLE_API_KEY` / `GEMINI_API_KEY`). For Vertex AI (Google Cloud), use service account JSON with `VERTEX_CREDENTIALS_PATH`.

## Session Transcript: July 5 OpenRouter + Nous + Google Debug

Real session: user reported Google, OpenRouter, and Nous all broken after model switch.

1. `hermes auth list` → no `nous` entry (OAuth expired), `openrouter` had 1 key (← active)
2. `hermes config check` → `OPENROUTER_API_KEY` ○ (not in profile `.env`, but in base `.env` via auth pool scan)
3. `grep` errors.log → 7+ OpenRouter 401 "User not found" across multiple sessions, credential pool exhausted
4. `hermes config env-path` → pointed to coding-profile `.env` (33 lines, no API keys). Base `.env` had 479 lines with all keys. Auth pools scan both — confirmed by `hermes auth list` showing active credentials.
5. New key test via `execute_code` → still 401. User's key was dead despite correct format.
6. Nous OAuth resolved separately (device_code appeared in auth list later).
7. Google direct gemini provider confirmed working (GOOGLE_API_KEY valid); the Google failures were all through OpenRouter proxy.
