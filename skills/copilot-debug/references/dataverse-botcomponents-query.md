# Dataverse BotComponents Query Pattern

Query agent structure via the Dataverse REST API from the CRM domain (not copilotstudio.microsoft.com — CORS blocks it).

## Prerequisites

- Browser session authenticated to the CRM domain (e.g., `org3353a370.crm.dynamics.com`)
- Navigate to CRM domain first: `await p.goto('https://orgXXXXX.crm.dynamics.com/main.aspx')`
- Wait 15s for auth

## Entity Schema

Entity: `botcomponents`

Key fields:
- `_parentbotid_value` — GUID of the parent bot (NOT `_owningbot_value` — that field doesn't exist)
- `componenttype` — integer identifying component type
- `name` — component name
- `category` — category (e.g., "Testing" for eval cases)
- `statecode` — 0 = Active
- `data` — YAML content for topics, eval data, etc.
- `description` — component description
- `modifiedon` — last modified timestamp

## Component Types

| Type | Meaning |
|------|---------|
| 9 | Topics |
| 11 | Connected agents |
| 14 | Knowledge sources (files) |
| 15 | Agent instructions |
| 16 | Knowledge sources (websites) |
| 19 | Evaluation test cases |

## Query Examples

### List all topics for a bot
```javascript
const botId = 'ea52ad9c-8233-f111-88b3-6045bd09a824';
const resp = await fetch(
  `/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq ${botId} and componenttype eq 9&$select=name,componenttype,statecode&$top=100`,
  { headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } }
);
const data = await resp.json();
// data.value = [{ name: "DoR Summary", componenttype: 9, statecode: 0 }, ...]
```

### List all knowledge sources
```javascript
const resp = await fetch(
  `/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq ${botId} and (componenttype eq 14 or componenttype eq 16)&$select=name,componenttype,description&$top=100`,
  { headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } }
);
```

### List connected agents
```javascript
const resp = await fetch(
  `/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq ${botId} and componenttype eq 11&$select=name&$top=20`,
  { headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } }
);
```

### Get topic YAML content
```javascript
const resp = await fetch(
  `/api/data/v9.2/botcomponents(${topicGuid})?$select=name,data`,
  { headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } }
);
const topic = await resp.json();
// topic.data contains the YAML content
```

### Count all components by type
```javascript
const resp = await fetch(
  `/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq ${botId}&$select=componenttype&$top=200`,
  { headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } }
);
const data = await resp.json();
const byType = {};
data.value.forEach(c => {
  byType[c.componenttype] = (byType[c.componenttype] || 0) + 1;
});
// { 9: 5, 14: 12, 15: 1, 19: 181, 11: 1 }
```

## Pitfalls

- **Use `_parentbotid_value`, NOT `_owningbot_value`** — the latter doesn't exist on botcomponents
- **Query from CRM domain**, not copilotstudio.microsoft.com (CORS blocks it)
- **200 result limit** — use $top=200 and paginate if needed
- **Type 19 (eval cases) can be 100+** — filter by componenttype to avoid hitting the limit
- **pac copilot extract-template crashes on 60+ components** — use Dataverse API as fallback
