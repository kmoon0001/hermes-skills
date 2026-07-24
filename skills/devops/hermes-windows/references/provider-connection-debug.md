# Provider Connection Debug Workflow

Full diagnostic workflow for "model switch breaks connections" issues
in Hermes Agent. Use when a provider that should work returns auth errors.

## Real error log examples

### OpenRouter API key dead (401)
```
2026-05-29 02:24:13,887 INFO run_agent:
  Streaming failed before delivery: Error code: 401 -
  {'error': {'message': 'User not found.', 'code': 401}}
2026-05-29 02:24:13,893 INFO agent.credential_pool:
  credential pool: marking OPENROUTER_API_KEY exhausted (status=401), rotating
2026-05-29 02:24:13,912 INFO agent.credential_pool:
  credential pool: no available entries (all exhausted or empty)
```
→ The key was revoked/expired. Get a new key from openrouter.ai/keys.

### Nous upstream capacity (503)
```
2026-05-29 01:40:11,813 WARNING run_agent:
  API call failed provider=nous model=google/gemini-3.1-flash-lite-preview
  summary=HTTP 503: The requested model is temporarily unavailable
  due to upstream capacity limits.
```
→ Transient. Retry. If persistent, check model availability.

### Rate limiting (429)
```
2026-05-13 03:13:24,670 WARNING run_agent:
  API call failed provider=minimax-oauth model=MiniMax-M2.7
  summary=HTTP 429: The Token Plan is designed for individual,
  interactive developer workflows. Traffic is currently high
```
→ Rate limited. Wait and retry, or upgrade plan.

## Step-by-step workflow

### 1. Check what's actually configured
```bash
hermes config check
```
Shows which env vars are set (✓) vs missing (○). Focus on the
providers you care about: OPENROUTER_API_KEY, GOOGLE_API_KEY,
GEMINI_API_KEY, DEEPSEEK_API_KEY, etc.

### 2. Check credential pool state
```bash
hermes auth list
```
Each provider shows its credentials. `←` marks the active one.
Rate-limited/exhausted creds show `(ready to retry)`.

### 3. Find the root cause in logs
```bash
# Quick scan for auth errors
grep -i "401\|403\|429\|exhaust\|credential.*pool" \
  ~/AppData/Local/hermes/logs/errors.log | tail -20

# Deeper scan including retry/fail patterns
grep -i "API call failed\|auth.*fail\|provider.*fail\|marking.*exhausted" \
  ~/AppData/Local/hermes/logs/agent.log | tail -30
```

### 4. Reset exhaustion if needed
```bash
hermes auth reset <provider>
```
Only do this after fixing the underlying key issue.

### 5. Check for OpenRouter proxy cascade
If OpenRouter is dead but Google/Anthropic have valid direct keys,
check if you're routing through OpenRouter:
```bash
grep "openrouter/" ~/AppData/Local/hermes/profiles/*/config.yaml
```
Models prefixed `openrouter/` go through the OpenRouter key even if
the target provider has its own valid credentials.

### 6. Verify which .env the session reads
```bash
hermes config env-path
```
Profile sessions may read a different .env than the base one.

### 7. Test provider directly
```bash
# OpenRouter
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Google Gemini
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY" \
  | python -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'models' in d else d)"
```

## Common patterns

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| All models fail, only DeepSeek works | OpenRouter key dead, cascading | Fix OpenRouter key or use direct providers |
| One provider works, another doesn't | Missing/invalid key for that provider | Check .env for that specific key |
| `hermes auth list` shows cred but calls fail | Credential exhausted | Check logs → `hermes auth reset` |
| OAuth provider (nous) stopped working | Token expired | `hermes auth add nous` |
| Profile session can't see keys | Profile .env is an island | Copy keys from base .env to profile .env |
