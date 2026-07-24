# Phase 1 — Create: Blank Agent & Environment Setup

## Create a Blank Agent

**Via Copilot Studio UI** (required — no API for agent creation):
1. Go to https://copilotstudio.microsoft.com → Agents → + New agent
2. Name it (e.g. "My Therapy Agent")
3. Choose **"Skip to create blank"** — do NOT use a template
4. Save — you now have a blank agent with only system topics

## Find the Bot ID

After creation, the URL shows a GUID that is NOT the Dataverse botid. Query Dataverse by name:

```bash
TOKEN=$(az account get-access-token --resource "https://{org}.crm.dynamics.com/" --query accessToken -o tsv)
curl -s "https://{org}.crm.dynamics.com/api/data/v9.2/bots?\$filter=contains(name,'Agent Name')&\$select=name,botid,schemaname" \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/json"
```

## Discover the Org URL from Environment ID

Copilot Studio environments don't use `{envId}.crm.dynamics.com`. Get the real org:

```bash
TOKEN=$(az account get-access-token --resource 'https://service.powerapps.com/' --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.powerapps.com/providers/Microsoft.PowerApps/environments/{envId}?api-version=2023-06-01"
# → properties.linkedEnvironmentMetadata.instanceUrl
```

## Working Environment

| Name | Env ID | Org URL |
|------|--------|---------|
| Therapy AI Agents Dev | `a944fdf0-0d2e-e14d-8a73-0f5ffae23315` | `orgbd048f00.crm.dynamics.com` |
| Tenant ID | `03cc92c3-986c-4cf4-ae27-1478cf99d17f` | — |

## Auth Setup (required before any API call)

```bash
# Dataverse PATCH/POST token
az account get-access-token --resource "https://orgbd048f00.crm.dynamics.com/" --query accessToken -o tsv

# Eval token
cd "D:/my agents copilot studio/pipeline"
node scripts/refresh_tda_eval_token.cjs
```

## Verify Blank State

After creation, confirm the agent has zero custom components:

```bash
az rest --resource "https://orgbd048f00.crm.dynamics.com/" --method GET \
  --url "https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents?\$filter=_parentbotid_value%20eq%20{botId}%20and%20componenttype%20in%20(9,14,15,16)&\$select=name,componenttype" -o json
# Should return 0 results for a truly blank agent
```

## Component Type Reference

| Type | Name | Creatable via API? | Published via |
|------|------|-------------------|---------------|
| 9 | Topic | ✅ POST | Dataverse PATCH |
| 12 | Trigger phrase | ✅ (part of topic YAML) | Dataverse |
| 14 | Uploaded file | ❌ UI only | UI upload |
| 15 | Instructions | ✅ PATCH (pre-existing) | Dataverse |
| 16 | Web knowledge source | ✅ POST | Dataverse |
| 18 | Settings | ✅ PATCH | Dataverse |
| 19 | Conversation starter | ✅ POST | Dataverse |
