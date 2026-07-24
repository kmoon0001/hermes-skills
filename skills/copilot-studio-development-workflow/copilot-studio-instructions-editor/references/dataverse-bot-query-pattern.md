# Dataverse API for Bot Component Queries

Use this to audit agent structure without pac CLI (which crashes on 60+ component agents).

## Prerequisites

Navigate to the CRM domain first (NOT copilotstudio.microsoft.com — CORS blocks API calls from there):

```javascript
await p.goto('https://orgXXXXX.crm.dynamics.com/main.aspx', { waitUntil: 'domcontentloaded', timeout: 30000 });
await sleep(15000); // Wait for auth
```

## Query All Bots

```javascript
const bots = await p.evaluate(async () => {
    const resp = await fetch('/api/data/v9.2/bots?$select=name,botid,statecode&$top=20', {
        headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
    });
    return await resp.json();
});
```

## Query Bot Components

The property is `_parentbotid_value` (NOT `_owningbot_value` which returns 400):

```javascript
const botId = 'ea52ad9c-...';
const components = await p.evaluate(async (id) => {
    const resp = await fetch(
        '/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq ' + id + '&$select=name,componenttype,category,statecode&$top=200',
        { headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } }
    );
    if (!resp.ok) return { status: resp.status, error: await resp.text() };
    return (await resp.json()).value || [];
}, botId);
```

## Component Types

| Type | Meaning |
|------|---------|
| 9 | Topics (actual authored topics) |
| 11 | Connected agents |
| 14 | Knowledge sources (files, websites) |
| 15 | Agent instructions |
| 19 | Evaluation test cases |

## Pitfall: UI Topic Count vs Actual Topics

The Copilot Studio UI shows "Custom (N)" on the Topics tab. This count includes topics from ALL connected agents in the fleet, NOT just the current agent. To find the actual agent's topics, query Dataverse for `componenttype=9`.

**Example:** QM Coach V2 showed "Custom (48)" in the UI but Dataverse returned only 5 type-9 topics. The other 43 were from connected agents (Case Historian V2, Regulatory Hub V2, SNF Dashboard V2) or evaluation test cases (type 19).

## Pitfall: 200 Result Limit

The Dataverse API returns max 200 results per query. Agents with 200+ components (like QM Coach V2 with 113 components + 181 test cases) need pagination or type-specific filtering:

```javascript
// Filter by component type to avoid hitting 200 limit
$filter=_parentbotid_value eq {botId} and componenttype eq 9
```

## Discovering Schema

If you don't know the entity schema, query with `$top=2` first:

```javascript
const schema = await p.evaluate(async () => {
    const resp = await fetch('/api/data/v9.2/botcomponents?$top=2', {
        headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
    });
    const data = await resp.json();
    return Object.keys(data.value[0]); // Returns all property names
});
```
