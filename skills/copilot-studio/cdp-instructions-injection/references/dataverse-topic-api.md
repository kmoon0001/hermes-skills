# Dataverse API for Copilot Studio Topic CRUD

## Authentication

Use the browser's authenticated session (cookies) when calling from Playwright CDP.

**Critical**: Navigate to the Dataverse org URL first (e.g., `https://orgbd048f00.crm.dynamics.com`), NOT the Copilot Studio URL. The API endpoint lives on the org domain.

## Get All Topics for a Bot

```javascript
// Navigate to org first to get auth cookies
await page.goto('https://orgbd048f00.crm.dynamics.com', { waitUntil: 'domcontentloaded', timeout: 60000 });
await sleep(8000);

const botId = 'ea52ad9c-8233-f111-88b3-6045bd09a824';
const result = await page.evaluate(async (botId) => {
  const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
  const url = `https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name,botcomponentid&$filter=${encodeURIComponent(filter)}&$top=100`;
  const resp = await fetch(url, {
    credentials: 'include',
    headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
  });
  const data = await resp.json();
  return data.value.map(t => ({ name: t.name, id: t.botcomponentid }));
}, botId);
```

## Key Details

- **Property name**: `_parentbotid_value` (NOT `botid` — that returns 400 error)
- **Component types**: 9 = Topic, 16 = Knowledge Source, 19 = Suggested Prompt
- **Filter syntax**: OData `$filter` with `eq` operator
- **Top limit**: `$top=100` covers most agents (QM Coach V2 has 62 topics)
- **Auth**: Requires cookies from an authenticated Copilot Studio session
- **Org URL**: Must use the Dataverse org URL (e.g., `orgbd048f00.crm.dynamics.com`), not Copilot Studio URL. API calls to `copilotstudio.microsoft.com/api/data/...` return HTML login page.

## Delete a Topic

```javascript
// Delete corrupted topic via API — returns 204 on success
const topicId = '85492644-9856-f111-bec6-7ced8d3b6116';
const result = await page.evaluate(async (id) => {
  const resp = await fetch(`https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, {
    method: 'DELETE',
    credentials: 'include',
    headers: {
      'Accept': 'application/json',
      'OData-MaxVersion': '4.0',
      'OData-Version': '4.0'
    }
  });
  return { status: resp.status, ok: resp.ok };
}, topicId);
// Result: { status: 204, ok: true } = success
```

**Use cases for DELETE**:
- Corrupted Monaco topics (8 chars = empty after failed CDP injection)
- Topics that need to be recreated from scratch
- Cleaning up duplicate topics

## Filter by Name Pattern

```javascript
// Find topics matching a name pattern
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9 and (contains(name,'HIPAA'))`;
```

## Multiple Topics with Same Name

**Pitfall**: Copilot Studio allows multiple topics with identical display names. Example: QM Coach V2 had BOTH "HIPAA Guardrail" (85492644) AND "QM - HIPAA Guardrail" (5a8d5c91). Both were corrupted. Always check for duplicates when diagnosing routing issues — the agent might be routing to a different topic than expected.

**Detection**: Query by name substring and count results:
```javascript
const hipaaTopics = data.value.filter(t => t.name.toLowerCase().includes('hipaa'));
// If length > 1, there are duplicates — identify which one is active
```

## Response Format

```json
{
  "value": [
    { "name": "Analyze OT Daily Note", "id": "11bd598c-0da2-40b2-bbfd-137e1d6ad414" },
    { "name": "Conversational boosting", "id": "7937da33-1467-4f5c-8622-163b59231c1a" },
    ...
  ]
}
```

## Topic URL Pattern

Once you have the GUID, navigate directly to:
```
https://copilotstudio.microsoft.com/environments/{envId}/bots/{botId}/adaptive/{topicGuid}
```

This bypasses the SPA topics list entirely.
