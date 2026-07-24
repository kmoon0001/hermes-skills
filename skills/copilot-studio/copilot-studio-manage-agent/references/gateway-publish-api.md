# Gateway publishv2-operations API

When `pac copilot publish` returns a cached failure timestamp or `PvaPublish` silently fails, use the Power Virtual Agents gateway API directly. This bypasses the CLI and MSAL flows entirely.

## Prerequisites
- Gateway URL from `.mcs/conn.json` (`AgentManagementEndpoint` field)
- Bot ID, environment ID, tenant ID
- `az` CLI authenticated in the target tenant

## Token
The gateway uses the PVA resource ID `96ff4394-9197-43aa-b393-6a41652e21f8`:
```python
import subprocess
result = subprocess.run(
    ["powershell", "-Command",
     "az account get-access-token --resource '96ff4394-9197-43aa-b393-6a41652e21f8' --query accessToken -o tsv"],
    capture_output=True, text=True, timeout=30)
pva_token = result.stdout.strip()
```

## Trigger publish (POST)

```python
GATEWAY = "https://powervamg.us-il106.gateway.prod.island.powerapps.com"
ENV_ID = "<environment-guid>"
BOT_ID = "<bot-guid>"
TENANT = "<tenant-guid>"

publish_url = f"{GATEWAY}/api/botmanagement/v1/environments/{ENV_ID}/bots/{BOT_ID}/publishv2-operations"

# Required headers
headers = {
    "Authorization": f"Bearer {pva_token}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-CCI-TenantId": TENANT,
    "x-cci-applicationsource": "Web",
    "x-ms-client-session-id": BOT_ID,   # helps routing
}

# POST to trigger a new publish operation — empty body
req = urllib.request.Request(publish_url, data=b"{}", method="POST")
for k, v in headers.items():
    req.add_header(k, v)

with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read().decode())
```

## Poll for completion (GET)

**IMPORTANT:** Poll by GET, NOT by repeated POST. Each POST creates a NEW operation. GET returns the status of the LATEST operation:

```python
import time
for i in range(60):
    time.sleep(5)
    req = urllib.request.Request(publish_url, method="GET")
    req.add_header("Authorization", f"Bearer {pva_token}")
    req.add_header("Accept", "application/json")
    req.add_header("X-CCI-TenantId", TENANT)
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        status = json.loads(resp.read().decode())
        is_final = status.get("isInFinalState", False)
        state = status.get("state", "")
        print(f"[{i+1}] state={state} final={is_final}")
        if is_final:
            break
```

If GET returns 404 with `StorageUnitNotAssigned`, no operation exists yet — POST first, then GET.

## Response fields

| Field | Meaning |
|-------|---------|
| `state` | `Queued` → `Started` → `Finished` or `FinishedWithUserErrors` |
| `isInFinalState` | `true` when the operation is complete |
| `executionState` | `0`=Queued, `1`=Started, `2`=FinishedWithErrors, `3`=Finished |
| `exceptionType` | Full exception type on failure (e.g. `ValidationFailedException`) |
| `exceptionMessage` | Human-readable error message |
| `impersonatedUserId` | Who triggered the publish |
| `lastUpdatedTimeStamp` | ISO 8601 timestamp of last state change |

## Error Codes

### 4002 / BadRouting ("The routing header value in request is incorrect")

The gateway rejects requests where the `X-CCI-TenantId` header doesn't match the expected tenant for the environment/bot combination. This happens when:

- Environment ID format mismatch: the gateway expects the **short GUID** (e.g. `a944fdf0`) but the full format (`Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f`) was used in the URL
- The bot belongs to a different environment than the one in the URL path
- The tenant GUID in `X-CCI-TenantId` doesn't correspond to the environment's owning tenant

**Resolution:** Always use the short environment GUID from `.mcs/conn.json` or by querying the `bots` table in Dataverse. The `Default-<tenant>-<guid>` format from the browser URL bar does NOT work with the gateway API.

### HTTP 404 with empty body or "StorageUnitNotAssigned"

No publish operation exists yet. `POST` first to create one, then `GET` to poll.

### Connection closed without response

Usually means the bot ID is wrong (the short prefix like `4d0ed0d3` is not a valid gateway bot ID). Use the full bot GUID from Copilot Studio URL (`4d0ed0d3-30f6-f011-8406-000d3a37eba2` format).

## Key ID Format Rules

| Parameter | Format | Source |
|-----------|--------|--------|
| Environment ID | Short GUID (`a944fdf0`) NOT `Default-<guid>` | `.mcs/conn.json` or Dataverse |
| Bot ID | Full GUID with dashes (`4d0ed0d3-30f6-...`) | Copilot Studio URL bar |
| Tenant ID | Short GUID (`03cc92c3`) NOT `Default-<guid>` | `az account show` or `.mcs/conn.json` |

**PITFALL:** The Copilot Studio SPA URL bar shows `environments/Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f/bots/4d0ed0d3-30f6-f011-8406-000d3a37eba2`. Do NOT use the `Default-<...>` prefix as the environment ID for the gateway API — it triggers `400 BadRouting`.

## Failure recovery

### FinishedWithUserErrors / ValidationFailedException
The API says validation failed but does NOT expose specific diagnostics. Options:
1. **Copilot Studio UI → Publish** — shows specific validation errors with source
2. **BotEntity diagnostics** (if hostname resolves) — `POST https://<envId>.environment.api.powerplatform.com/powervirtualagents/bots/<botId>/api/botcomponents?api-version=2022-03-01-preview` with body `{"Kind":["BotEntity"]}`, inspect `bot.synchronizationStatus.lastFinishedPublishOperation.diagnosticDetails`
3. **Common causes to check manually:**
   - Blank `text:` in conversation starters (check GPT metadata component, type=15)
   - Stale knowledge source references pointing to deleted topic/component IDs
   - `BeginDialog` referencing a non-existent topic
   - Duplicate YAML properties like `applyModelKnowledgeSetting`
   - Knowledge type-19 sources referencing deleted type-14 file sources

### Cached pac copilot publish failure
`pac copilot publish` returning the same timestamp every attempt is a Dataverse cache issue. The gateway API creates a fresh operation that bypasses this cache entirely. If the gateway also fails, fix validation errors and try again.

## Regional gateway URLs

| Region | Gateway URL |
|--------|-------------|
| US IL106 | `https://powervamg.us-il106.gateway.prod.island.powerapps.com` |
| US IL107 | `https://powervamg.us-il107.gateway.prod.island.powerapps.com` |

Determine your region from `.mcs/conn.json` `AgentManagementEndpoint` field.
