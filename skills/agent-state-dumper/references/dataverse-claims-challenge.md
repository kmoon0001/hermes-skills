# Dataverse Claims Challenge (`insufficient_claims`)

## Symptoms

- `az account get-access-token` returns a valid JWT (decodes correctly, not expired, audience matches)
- Every Dataverse API call returns **HTTP 401** with empty body
- `WWW-Authenticate` header contains `error="insufficient_claims"` and a `claims="eyJhY2...19fQ=="` value

## Root Cause

Dataverse (and other Entra ID-protected APIs with conditional access) requires certain claims in the token that `az account get-access-token` doesn't include by default. The most common missing claim is `xms_rp_ipaddr` (client IP address).

The API issues a **claims challenge** — a base64-encoded JSON blob in the `WWW-Authenticate` header — that the client must pass back to Entra ID when requesting a new token. Entra ID then issues a token with the required claims.

## Detection

```python
import json, base64, urllib.request

req = urllib.request.Request("https://org3353a370.crm.dynamics.com/api/data/v9.2/WhoAmI")
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Accept', 'application/json')

try:
    with urllib.request.urlopen(req) as resp:
        print("Token OK — no claims challenge")
except urllib.error.HTTPError as e:
    if e.code == 401:
        www_auth = e.headers.get('WWW-Authenticate', '')
        if 'claims=' in www_auth:
            claims_b64 = www_auth.split('claims="')[1].split('"')[0]
            padded = claims_b64 + '=' * (4 - len(claims_b64) % 4)
            claims = json.loads(base64.urlsafe_b64decode(padded))
            print("Claims challenge:", json.dumps(claims, indent=2))
            # Save claims_b64 for re-auth
            return claims_b64
```

Typical decoded challenge:
```json
{
  "access_token": {
    "nbf": {"essential": true, "value": "1783159296"},
    "xms_rp_ipaddr": {"value": "68.5.29.89"}
  }
}
```

## Why `az` CLI Can't Fix It

`az account get-access-token` (tested through v2.84.0) does **not** expose a `--claims` parameter. The token it returns always lacks the `xms_rp_ipaddr` claim, so Dataverse always rejects it when conditional access is active.

## Workaround: MSAL Python with Claims Challenge

```python
import msal, json, base64, urllib.request

TENANT = "03cc92c3-986c-4cf4-ae27-1478cf99d17f"
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
RESOURCE = "https://org3353a370.crm.dynamics.com"
SCOPE = [f"{RESOURCE}/.default"]

app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT}"
)

# Step 1: Get initial token via device code
flow = app.initiate_device_flow(scopes=SCOPE)
print(f"Go to: {flow['verification_uri']}")
print(f"Code:  {flow['user_code']}")

result = app.acquire_token_by_device_flow(flow)
token = result["access_token"]

# Step 2: Test — will fail with claims challenge
claims_challenge = detect_claims_challenge(token)  # use detection code above

# Step 3: Re-acquire with claims
result2 = app.acquire_token_silent(
    SCOPE,
    account=result["account"],
    claims_challenge=claims_challenge
)
token2 = result2["access_token"]
# token2 now has xms_rp_ipaddr and should work

# Step 4: Verify
detect_claims_challenge(token2)  # should print "Token OK"
```

## Alternative: `az rest` (untested)

Once logged in, `az rest` might handle claims challenges internally:
```bash
az rest --method get \
  --url "https://org3353a370.crm.dynamics.com/api/data/v9.2/WhoAmI" \
  --resource "https://org3353a370.crm.dynamics.com"
```

## Relevance to `dump_agent_full.cjs`

The dump script at `D:/my agents copilot studio/pipeline/scripts/dump_agent_full.cjs` uses `execSync('az account get-access-token ...')` — same token path that triggers the claims challenge. If the script gets HTTP 401 on the botcomponents query, this is the cause. The fix would be to add MSAL-based token acquisition with claims challenge handling to the script.
