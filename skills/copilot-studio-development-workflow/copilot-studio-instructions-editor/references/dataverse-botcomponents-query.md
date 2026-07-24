# Dataverse Bot Components Query Pattern

Query agent structure (topics, knowledge sources, instructions, test cases) via Dataverse REST API from the CRM domain. More reliable than the browser SPA for getting complete component lists.

## Endpoint

```
GET https://org{XXXX}.crm.dynamics.com/api/data/v9.2/botcomponents
  ?$filter=_parentbotid_value eq {bot-guid}
  &$select=name,componenttype,category,statecode,description
  &$top=200
```

**Must be called from the CRM domain** (`org{XXXX}.crm.dynamics.com`), NOT from `copilotstudio.microsoft.com` (CORS blocks it).

## Component Types

| Type | Category | What it is |
|------|----------|------------|
| 9 | (none) | Topics (AdaptiveDialog) |
| 11 | (none) | Connected agents |
| 14 | (none) | Knowledge sources (files, websites) |
| 15 | (none) | Agent instructions |
| 19 | Testing | Evaluation test cases |

## Key Property Names

- `_parentbotid_value` — the owning bot's GUID (NOT `_owningbot_value` which throws 400)
- `name` — component display name
- `componenttype` — integer type code (see table above)
- `category` — "Testing" for eval cases, null for other types
- `data` — YAML content for topics/eval cases
- `description` — component description

## UI vs Dataverse Count Discrepancy

The Copilot Studio UI "Custom (N)" count includes topics from connected child agents, not just the parent bot. The Dataverse query filtered by `_parentbotid_value` returns only the bot's OWN components.

**Example**: QM Coach V2 UI shows "Custom (48)" but Dataverse returns only 5 type-9 topics. The other 43 are from connected agents (Case Historian V2, Regulatory Hub V2, SNF Dashboard V2).

## Usage Pattern (from browser)

```javascript
const botId = 'ea52ad9c-8233-f111-88b3-6045bd09a824';
const result = await p.evaluate(async (id) => {
    const resp = await fetch(
        '/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq ' + id + 
        '&$select=name,componenttype,category,statecode&$top=200',
        { headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } }
    );
    return (await resp.json()).value || [];
}, botId);
```

## 200-Result Limit

The API returns max 200 results per page. Agents with 100+ eval test cases will hit this limit. Filter by componenttype to get specific categories:
- `&$filter=_parentbotid_value eq {id} and componenttype eq 9` — topics only
- `&$filter=_parentbotid_value eq {id} and componenttype eq 14` — knowledge sources only
