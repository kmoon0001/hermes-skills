# Fleet-Wide Topic Replacement via Dataverse API (Python)

Use this approach when you need to replace topic YAML across multiple agents without the LSP-based manage-agent scripts. Validated on 4 agents simultaneously (OT, PT, SLP, TDA).

## Prerequisites
- `az` CLI authenticated to the target Dataverse org
- Bot IDs known (from `pac copilot list`)
- Component IDs of topics to replace (from Dataverse API query)

## Full Replacement Pattern

```python
import subprocess, json, urllib.request

# 1. Get token
r = subprocess.run(
    ["C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd",
     "account", "get-access-token",
     "--resource", "https://<org>.crm.dynamics.com/",
     "--query", "accessToken", "-o", "tsv"],
    capture_output=True, text=True
)
token = r.stdout.strip()

# 2. PATCH the botcomponent's data field
component_id = "..."  # from query
url = f"https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents({component_id})"
body = json.dumps({"data": new_yaml_string})  # full YAML content as string

req = urllib.request.Request(url, data=body.encode(), method="PATCH")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")
req.add_header("OData-MaxVersion", "4.0")

resp = urllib.request.urlopen(req, timeout=30)
# HTTP 204 = success
```

## Deactivation Pattern (delete without deleting)

```python
# Set componentstate=2 (Deactivated), statecode=1
body = json.dumps({"componentstate": 2, "statecode": 1})
req = urllib.request.Request(url, data=body.encode(), method="PATCH")
# ... same headers as above
resp = urllib.request.urlopen(req, timeout=30)
```

## URL Querying Pitfalls

Use `urllib.parse.urlencode` with `doseq=True` to avoid control-character errors from unencoded spaces in filter strings:

```python
params = urllib.parse.urlencode({
    '$filter': f"_parentbotid_value eq {bot_id} and componenttype eq 9",
    '$select': "botcomponentid,schemaname,componenttype,data",
    '$top': 100
}, doseq=True)
url = f"{base_url}/botcomponents?{params}"
```

## Key Points
- The `data` field stores raw YAML as a string — replace it completely with new YAML
- Always verify by re-querying after PATCH
- Retry pattern allowed multiple failures to resolve; use 30s timeouts
- `pac copilot publish` can fail with cached error — try API publish or UI as fallback
