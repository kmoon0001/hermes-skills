# Phase 5 — Publish

## Two Publishing Methods

### Method 1: Gateway publishv2 (Recommended — Freshest)

Bypasses `PvaPublish` stale cache. Works even when `pac copilot publish` returns old timestamps.

```bash
# Auth — DIFFERENT scope than Dataverse
TOKEN=$(az account get-access-token \
  --resource '96ff4394-9197-43aa-b393-6a41652e21f8' \
  --query accessToken -o tsv)
TENANT="03cc92c3-986c-4cf4-ae27-1478cf99d17f"
ENV="a944fdf0-0d2e-e14d-8a73-0f5ffae23315"
BOT="7667e9b4-cb86-f111-ab0f-70a8a5ae56f8"

# Try regions (us-il106 works for Therapy AI Dev)
for REGION in us-il106 us-il107 us-il108; do
  GATEWAY="https://powervamg.${REGION}.gateway.prod.island.powerapps.com"
  
  # Start publish
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "${GATEWAY}/api/botmanagement/v1/environments/${ENV}/bots/${BOT}/publishv2-operations" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-CCI-TenantId: $TENANT" \
    -H "x-cci-applicationsource: Web" \
    -H "Content-Type: application/json" \
    -d '{}')
  echo "$REGION: HTTP $HTTP"
  [ "$HTTP" != "404" ] && break
done

# Poll until final (10-30s typical)
for i in $(seq 1 12); do
  sleep 5
  RESULT=$(curl -s "${GATEWAY}/api/botmanagement/v1/environments/${ENV}/bots/${BOT}/publishv2-operations" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-CCI-TenantId: $TENANT" \
    -H "x-cci-applicationsource: Web")
  STATE=$(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('state','?'),'| final:',d.get('isInFinalState',False))")
  echo "  Poll $i: $STATE"
  if echo "$STATE" | grep -q "True"; then
    echo "FINAL: $(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('state')); e=d.get('exceptionType',''); m=d.get('exceptionMessage',''); print(f'{e}: {m}' if e else '')")"
    break
  fi
done
```

### Method 2: PAC CLI

```bash
pac copilot publish --bot {botId}
```

**Cache quirk**: May show old "Failed [timestamp]" — check `publishedon` in Dataverse for real timestamp.

## Verify Publish

```bash
az rest --resource "https://orgbd048f00.crm.dynamics.com/" --method GET \
  --url "https://orgbd048f00.crm.dynamics.com/api/data/v9.2/bots({botId})?\$select=publishedon,synchronizationstatus" -o json
```

```python
# Parse synchronizationstatus
j = json.loads(bot['synchronizationstatus'])
op = j.get('lastFinishedPublishOperation', {})
print(f"Status: {op.get('status')}")  # Succeeded / Failed
print(f"Published: {bot.get('publishedon')}")  # UTC timestamp
```

## Failure Diagnostics

| Symptom | Check |
|---------|-------|
| `MissingRequiredProperty: Title/Text` | Empty conversation starter — fix type 15 instructions |
| `SynchronizationSystemError` | System topic data was PATCHed via API — revert + use UI |
| `IncorrectTypeError` | Topic condition returns wrong type (e.g. string instead of Boolean) |
| `ExpressionError` | Power Fx expression invalid in topic YAML |
| `BadRoutingHeaderValue` / `4002` | X-CCI-TenantId wrong — must be FULL tenant GUID |

## PITFALLS

1. **X-CCI-TenantId**: Must be FULL GUID from `az account show`. Short prefix = 4002 error.
2. **Gateway 404**: Wrong region. Try us-il106 through us-il110.
3. **Empty body**: MUST send `{}` with publish POST — cannot send empty body.
4. **Token scope**: Gateway needs `96ff4394-...` resource, NOT the CRM resource.
5. **Publish staleness**: Gateway API always returns freshest result; PAC CLI may show cached.
