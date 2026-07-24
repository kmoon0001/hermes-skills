---
name: copilot-studio-knowledge-api
description: Programmatic knowledge source management for Copilot Studio via Dataverse and Gateway APIs — creating PublicSiteSearchSource entries, discovering org URLs from environment IDs, fixing publish-blocking conversation starters, and gateway publish workflows.
category: copilot-studio
---

> **For standard KS workflows, load `copilot-studio-agent-builder` first (Phase 2 + `references/phase-2-knowledge.md`).** This skill provides deep Python code and verified API examples for programmatic operations.

# Copilot Studio Knowledge Source API


Create and manage Copilot Studio knowledge sources programmatically via Dataverse REST API and Gateway publish API. Use this when you can't or don't want to use the Copilot Studio UI for knowledge source management.

## HARD STOP — Do NOT attempt file uploads via API

**The Dataverse API CANNOT upload binary files (.md, .pdf, .docx, .xlsx) to knowledge sources.** Only two source types are creatable programmatically:
- **PublicSiteSearchSource** (type 16) — web-crawl URLs like GitHub repos or public sites
- **SharePoint** sources

Actual file uploads require the Copilot Studio UI file picker. There is no Dataverse endpoint for uploading file content; the ingestion/vectorization pipeline is only accessible through the UI. Any attempt to create a `FileAttachmentComponentMetadata` (type 14) via API will fail.

**If you find yourself writing code to upload a file to a knowledge source, stop — it's impossible.** Use web-crawl references as a workaround, or tell the user to upload manually via the UI.

## Quick Reference

| Operation | API | Component Type |
|-----------|-----|---------------|
| Create web knowledge source | Dataverse POST | 16 (PublicSiteSearchSource) |
| Upload file (PDF/DOCX) | UI only | 14 (FileAttachmentComponentMetadata) |
| PATCH file KS metadata (name, description, isOfficialSource) | Dataverse PATCH | 14 — **JSON `data` field** |
| PATCH agent description | Dataverse PATCH | 15 — `description:` in GPT YAML |
| Publish agent | Gateway publishv2 | n/a |
| Find Dataverse org | Power Platform admin API | n/a |
| Fix empty conversation starters | Dataverse PATCH | 15 (instructions) |

## Reference Files

- `references/kiro-deployment-patterns.md` — Deployment patterns from Kiro's agent-builder power (single-token flow, JSON vs YAML, Playwright boundaries, fleet constraints).
- `references/verified-workflow-competency-check-gamer.md` — Step-by-step verified example.
- `references/cross-agent-alignment.md` — Systematic audit workflow for aligning Hermes with another agent's config (MCPs, skills, steering).

## Discovery: Find the Dataverse Org

Copilot Studio environments don't use the `{envId}.crm.dynamics.com` pattern. Get the real org URL from the Power Platform admin API:

```bash
TOKEN=$(az account get-access-token --resource 'https://service.powerapps.com/' --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.powerapps.com/providers/Microsoft.PowerApps/environments/{envId}?api-version=2023-06-01"
# → properties.linkedEnvironmentMetadata.instanceUrl
# → properties.linkedEnvironmentMetadata.domainName
```

Example: Copilot Studio URL shows `a944fdf0-0d2e-e14d-8a73-0f5ffae23315` → org is `orgbd048f00.crm.dynamics.com`.

## Discovery: Find the Bot

The Copilot Studio URL bot GUID is NOT the Dataverse `botid`. Query by name:

```python
filt = f"contains(name,'Agent Name')"
url = f"{org_url}/api/data/v9.2/bots?$filter={urllib.parse.quote(filt)}&$select=name,botid"
```

## Discovery: Find the Customization Prefix

New components need a `schemaname` starting with the agent's customization prefix:

```python
filt = f"_parentbotid_value eq '{bot_id}' and componenttype eq 9"
url = f"{org_url}/api/data/v9.2/botcomponents?$filter={urllib.parse.quote(filt)}&$select=schemaname&$top=1"
# prefix = '.'.join(schemaname.split('.')[:2])
# Example: "cr917_CompetencyCheckGamerAgent"
```

## Create PublicSiteSearchSource (Type 16)

Use this for web-crawlable content (GitHub repos, documentation sites, public web pages).

```python
import subprocess, json, urllib.request

org_url = "https://orgXXXXXXXX.crm.dynamics.com"
bot_id = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
prefix = "cr917_AgentName"

# Auth
az = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
result = subprocess.run([az, 'account', 'get-access-token', '--resource', org_url + '/'],
                       capture_output=True, text=True, timeout=15)
TOKEN = json.loads(result.stdout)['accessToken']

# YAML — CRITICAL: use \r\n (CRLF) line endings
yaml_data = (
    "kind: KnowledgeSourceConfiguration\r\n"
    "displayName: My Knowledge Source\r\n"
    "description: One sentence on what it covers, why authoritative, and retrieval terms.\r\n"
    "isOfficialDataSource: true\r\n"
    "source:\r\n"
    "  kind: PublicSiteSearchSource\r\n"
    "  site: https://github.com/user/repo\r\n"
)

body = {
    "name": "My Knowledge Source",
    "schemaname": f"{prefix}.knowledge.{unique_suffix}",
    "componenttype": 16,
    "parentbotid@odata.bind": f"/bots({bot_id})",
    "data": yaml_data,
}

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0',
}

req = urllib.request.Request(f"{org_url}/api/data/v9.2/botcomponents",
    data=json.dumps(body).encode(), method='POST', headers=headers)
with urllib.request.urlopen(req, timeout=30) as resp:
    new_id = resp.headers.get('OData-EntityId', '').split('(')[-1].split(')')[0]
    print(f"Created: {new_id} (HTTP {resp.status})")  # 204 = success
```

### PITFALL: Line Endings

The `data` field YAML MUST use `\r\n` (CRLF). Using `\n` alone causes double-CR artifacts (`\r\r\n`). In Python f-strings, use explicit `\r\n` escape sequences.

### PITFALL: Token Scope

The Azure CLI token must be scoped to the Dataverse org URL with trailing slash:
```bash
az account get-access-token --resource 'https://orgXXXXXXXX.crm.dynamics.com/'
```

### PITFALL: Python urllib OData Encoding

Python 3.11+ `urllib` has `_validate_path` that rejects spaces in URLs. Use `urllib.parse.quote()` on filter values. For complex queries, prefer `az rest`:
```bash
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/bots?\$select=name,botid&\$top=20" -o json
```

## Publish: Gateway publishv2 API

When `PvaPublish` returns cached/stale results, use the gateway API:

```bash
# Auth — different scope than Dataverse
TOKEN=$(az account get-access-token --resource '96ff4394-9197-43aa-b393-6a41652e21f8' --query accessToken -o tsv)
TENANT=$(az account show --query tenantId -o tsv)

# Find the right region (try us-il106 through us-il110)
for REGION in us-il106 us-il107 us-il108 us-il109 us-il110; do
  GATEWAY="https://powervamg.${REGION}.gateway.prod.island.powerapps.com"
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "${GATEWAY}/api/botmanagement/v1/environments/${ENV}/bots/${BOT}/publishv2-operations" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-CCI-TenantId: $TENANT" \
    -H "x-cci-applicationsource: Web" \
    -d '{}')
  [ "$HTTP" != "404" ] && break
done

# Poll until isInFinalState=true (typically 10-30s)
# state="Finished" = success
# state="FinishedWithUserErrors" = check exceptionType/exceptionMessage
```

### PITFALL: X-CCI-TenantId

Must be the FULL tenant GUID from `az account show --query tenantId -o tsv`. Using a shortened prefix returns `BadRoutingHeaderValue` / `ErrorCode 4002`.

## Fix: Empty Conversation Starters

If publish fails with `MissingRequiredProperty: Title` / `MissingRequiredProperty: Text`, the instructions component likely has an empty conversation starter object:

```yaml
conversationStarters:
  - {}   # ← THIS BLOCKS PUBLISHING
```

Fix via Dataverse PATCH:

```python
# GET current data
url = f"{org_url}/api/data/v9.2/botcomponents({instr_id})?$select=data"
# ... fetch data ...

# Replace empty starter with valid one
old = "conversationStarters:\r\n  - {}"
new = "conversationStarters:\r\n  - title: Get Started\r\n    text: How can I test my clinical competency?"
fixed_data = data.replace(old, new)

# PATCH back
patch_url = f"{org_url}/api/data/v9.2/botcomponents({instr_id})"
body = json.dumps({"data": fixed_data}).encode('utf-8')
# HTTP 204 = success
```

## PATCH File KS Metadata (Type 14) — JSON Format

Uploaded file knowledge sources (type 14) use **JSON** in their `data` field, NOT YAML. To set the description and official source flag:

```python
# PATCH botcomponents({id}) with:
body = json.dumps({
    "data": '{"description": "Contains CMS therapy coverage rules for SNF. Use for questions about skilled necessity, certification periods, and documentation requirements.", "isOfficialSource": true}'
}).encode('utf-8')

# HTTP 204 = success
```

The `name` field is a separate top-level property on the botcomponent, PATCH it directly:
```python
body = json.dumps({"name": "CMS Chapter 15 — Therapy Coverage"}).encode('utf-8')
```

## PITFALL: parentbotid@odata.bind for POST

When creating new botcomponents (POST), use the OData navigation property binding:
```json
"parentbotid@odata.bind": "/bots($botId)"
```
Do NOT use `"_parentbotid_value"` — it causes `0x80060888` (property not found).

## When to Use Uploaded Files Instead

| Approach | Use When |
|----------|----------|
| PublicSiteSearchSource (API) | Content is on a public web page/GitHub repo |
| Uploaded files (UI) | PDFs, DOCX, XLSX with content not crawlable via web |
| Both | PublicSiteSearchSource for quick deployment, uploaded files for reliable retrieval |

Uploaded files (componenttype 14) require the Copilot Studio UI — no API exists for uploading binary file content. Use the UI for PDFs of regulatory documents where retrieval reliability matters more than deployment speed.

## Verified Example (2026-07-23)

Pacific Coast Competency Check Gamer Agent:
- Org: `orgbd048f00.crm.dynamics.com` (discovered via Power Platform API)
- Bot: `7667e9b4-cb86-f111-ab0f-70a8a5ae56f8` (found by name query)
- Prefix: `cr917_CompetencyCheckGamerAgent`
- 7 knowledge sources created as PublicSiteSearchSource pointing to `github.com/kmoon0001/competency-check-gamer`
- Published via gateway `us-il106`
- Pre-existing empty conversation starter fixed before publish
