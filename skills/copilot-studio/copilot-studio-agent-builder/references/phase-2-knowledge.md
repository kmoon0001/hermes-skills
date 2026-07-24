# Phase 2 — Knowledge Sources

## The Hard Stop: File Uploads Are UI-ONLY

**API CANNOT upload binary files (.md, .pdf, .docx, .xlsx) to knowledge sources.** Only two source types exist via API:
- **PublicSiteSearchSource** (type 16) — web-crawl URLs (GitHub repos, public sites)
- **SharePoint** sources

For file uploads: Copilot Studio UI → Knowledge → Add knowledge → Upload files. There is no workaround.

## Create a PublicSiteSearchSource (Type 16)

```python
import subprocess, json, urllib.request

org = "https://orgbd048f00.crm.dynamics.com"
bot = "7667e9b4-cb86-f111-ab0f-70a8a5ae56f8"
prefix = "cr917_CompetencyCheckGamerAgent"  # From schemaname

# Auth
az = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
r = subprocess.run([az, 'account', 'get-access-token', '--resource', org + '/'],
                   capture_output=True, text=True, timeout=15)
TOKEN = json.loads(r.stdout)['accessToken']

# YAML — MUST use \r\n line endings
yaml_data = (
    "kind: KnowledgeSourceConfiguration\r\n"
    "displayName: My Knowledge Source\r\n"
    "description: What it covers and why it's authoritative.\r\n"
    "isOfficialDataSource: true\r\n"
    "source:\r\n"
    "  kind: PublicSiteSearchSource\r\n"
    "  site: https://github.com/user/repo\r\n"
)

body = {
    "name": "My Knowledge Source",
    "schemaname": f"{prefix}.knowledge.{unique_suffix}",
    "componenttype": 16,
    "parentbotid@odata.bind": f"/bots({bot})",
    "data": yaml_data,
}

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0', 'OData-Version': '4.0',
}

req = urllib.request.Request(f"{org}/api/data/v9.2/botcomponents",
    data=json.dumps(body).encode(), method='POST', headers=headers)
with urllib.request.urlopen(req, timeout=30) as resp:
    cid = resp.headers.get('OData-EntityId', '').split('(')[-1].split(')')[0]
    print(f"Created: {cid}")
```

## PITFALLS

1. **Line endings**: YAML `data` field MUST use `\r\n` (CRLF). `\n` alone causes double-CR artifacts.
2. **Token scope**: Must end with `/` — `--resource 'https://orgbd048f00.crm.dynamics.com/'`
3. **Python 3.11+ urllib**: `_validate_path` rejects spaces. Use `az rest` for complex queries.
4. **schemaname prefix**: Must be the agent's customization prefix (e.g. `cr917_AgentName`). Find via: `GET botcomponents?$filter=_parentbotid_value eq '{bot}' and componenttype eq 9&$select=schemaname&$top=1`
5. **Empty PATCH body not allowed**: MUST send `{}` with publishv2 API

## KS Best Practices

- **displayName**: Descriptive, not file name. "CMS Chapter 15 — Therapy Coverage" not "bp102c15.pdf"
- **description**: 1-2 sentences on what it covers, why authoritative
- **isOfficialDataSource: true**: For compliance/regulatory sources
- **No duplicates**: Same content in multiple KBs = retrieval confusion
- **Under 5MB**: For file uploads per MS Learn

## Uploaded Files vs Web-Crawl

| Approach | Reliability | Speed | Use When |
|----------|------------|-------|----------|
| Web-crawl (API) | Depends on Bing indexing | Fast deploy | Content on public URLs |
| Uploaded files (UI) | Deterministic | Manual | PDFs, proprietary docs |

## Set displayName/description via PATCH

```python
current_data = comp.get('data', '')
new_data = current_data.replace(
    'kind: FileAttachmentComponentMetadata',
    'kind: FileAttachmentComponentMetadata\ndisplayName: CMS Chapter 15\ndescription: Official CMS therapy coverage manual.\nisOfficialDataSource: true'
)
# PATCH botcomponents({id}) with {"data": new_data}
```
