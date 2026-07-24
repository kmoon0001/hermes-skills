# Verified API Workflow: Competency Check Gamer Agent (2026-07-23)

## Session Context
Created 7 knowledge sources via Dataverse API for the Pacific Coast Competency Check Gamer Agent in the Therapy AI Agents Dev environment.

## Environment Discovery

| Step | Method | Result |
|------|--------|--------|
| Copilot Studio URL | Browser address bar | `environments/a944fdf0-0d2e-e14d-8a73-0f5ffae23315/bots/7667e9b4-...` |
| Find Dataverse org | Power Platform admin API → `linkedEnvironmentMetadata.instanceUrl` | `orgbd048f00.crm.dynamics.com` |
| Find bot by name | `bots?$filter=contains(name,'Competency')` | `7667e9b4-cb86-f111-ab0f-70a8a5ae56f8` |
| Customization prefix | Query any existing topic `schemaname` | `cr917_CompetencyCheckGamerAgent` |

## Knowledge Sources Created

All 7 as componenttype 16 (PublicSiteSearchSource), pointing to `https://github.com/kmoon0001/competency-check-gamer`:

1. SNF Competency Matrix — APTA/AOTA/ASHA
2. Gamification Scoring Rules and Mechanics
3. PDPM Documentation and Classification Guide
4. PT Clinical Scenarios Bank — 35 Cases
5. OT Clinical Scenarios Bank — 35 Cases
6. SLP Clinical Scenarios Bank — 35 Cases
7. Culture and Teamwork Scenarios — 20 Cases

All with `isOfficialDataSource: true` and unique descriptions.

## Publishing

### Issue 1: Cached PvaPublish failure
- `PvaPublish` API returned `Failed` with old timestamp (cached)
- Gateway publishv2 API on `us-il106` succeeded
- Publish took ~15 seconds (Queued → Started → Finished)

### Issue 2: Empty conversation starter
- Instructions component had `conversationStarters:\r\n  - {}`
- Caused `MissingRequiredProperty: Title` / `MissingRequiredProperty: Text`
- Fixed by PATCHing to add `title: Get Started` / `text: How can I test my clinical competency?`

## Key Pitfalls Encountered

1. **Bot ID mismatch**: Copilot Studio URL GUID ≠ Dataverse botid. Always query by name.
2. **Org URL pattern**: `{envId}.crm.dynamics.com` doesn't resolve. Use Power Platform admin API.
3. **Line endings**: `data` field requires `\r\n` (CRLF), not `\n`.
4. **Python urllib OData**: Spaces in URL filters cause `InvalidURL` on Python 3.11+. Use `az rest` for queries.
5. **Token scopes**: Dataverse needs `{orgUrl}/`, Gateway needs `96ff4394-9197-43aa-b393-6a41652e21f8`, Power Platform admin needs `service.powerapps.com/`.
6. **Empty conversation starters**: `- {}` blocks publishing. Must have `title:` and `text:`.

## Bash Deployment Pattern (Hermes-optimized)

The Python urllib approach works but `az rest` is more reliable in Hermes' terminal:

```bash
ORG="https://orgbd048f00.crm.dynamics.com"
BOT="7667e9b4-cb86-f111-ab0f-70a8a5ae56f8"
PREFIX="cr917_CompetencyCheckGamerAgent"

# Build YAML with CRLF line endings (CRITICAL)
YAML=$(printf "kind: KnowledgeSourceConfiguration\r\ndisplayName: My Source\r\ndescription: What it covers and why authoritative.\r\nisOfficialDataSource: true\r\nsource:\r\n  kind: PublicSiteSearchSource\r\n  site: https://github.com/user/repo/blob/main/file.md")

# JSON-escape the YAML and POST
YAML_JSON=$(echo "$YAML" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')

az rest --resource "$ORG/" --method POST \
  --url "$ORG/api/data/v9.2/botcomponents" \
  --body "{
    \"name\": \"My Knowledge Source\",
    \"schemaname\": \"${PREFIX}.knowledge.uniquesuffix\",
    \"componenttype\": 16,
    \"parentbotid@odata.bind\": \"/bots($BOT)\",
    \"data\": $YAML_JSON
  }" \
  --headers "Content-Type=application/json" -o json
```

**Gateway publish — region discovery expanded to us-il110:**
```bash
TOKEN_GW=$(az account get-access-token --resource '96ff4394-9197-43aa-b393-6a41652e21f8' --query accessToken -o tsv)
TENANT=$(az account show --query tenantId -o tsv)
for REGION in us-il106 us-il107 us-il108 us-il109 us-il110; do
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "https://powervamg.${REGION}.gateway.prod.island.powerapps.com/api/botmanagement/v1/environments/a944fdf0-0d2e-e14d-8a73-0f5ffae23315/bots/${BOT}/publishv2-operations" \
    -H "Authorization: Bearer $TOKEN_GW" -H "X-CCI-TenantId: $TENANT" \
    -H "x-cci-applicationsource: Web" -d '{}')
  [ "$HTTP" != "404" ] && echo "Region: $REGION (HTTP $HTTP)" && break
done
```
