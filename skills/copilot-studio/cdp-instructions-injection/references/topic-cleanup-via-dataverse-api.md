# Topic Cleanup via Dataverse API

When topics are corrupted (Monaco shows 8 chars / NO LINES) or need bulk deletion, the Dataverse REST API is faster and more reliable than UI clicks.

## Delete a Single Topic

```javascript
// Navigate to Dataverse org first to establish auth cookies
await page.goto('https://orgbd048f00.crm.dynamics.com', { waitUntil: 'domcontentloaded', timeout: 60000 });
await sleep(8000);

const result = await page.evaluate(async (topicId) => {
    const resp = await fetch(`https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents(${topicId})`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
    });
    return { status: resp.status, ok: resp.ok };
}, topicGuid);
// 204 = success, 404 = already gone
```

## Bulk Delete Multiple Topics

```javascript
const toDelete = [
    { name: "Topic Name", id: "guid-here" },
    // ...
];
for (const topic of toDelete) {
    const result = await page.evaluate(async (id) => {
        const resp = await fetch(`https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, {
            method: 'DELETE', credentials: 'include',
            headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
        });
        return { status: resp.status, ok: resp.ok };
    }, topic.id);
    console.log(result.ok ? `✅ ${topic.name}` : `❌ ${topic.name}`);
    await sleep(500); // rate limit
}
```

## Verify Deletion

```javascript
const remaining = await page.evaluate(async () => {
    const botId = 'ea52ad9c-8233-f111-88b3-6045bd09a824';
    const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
    const url = `https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name&$filter=${encodeURIComponent(filter)}&$top=100`;
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } });
    const data = await resp.json();
    return data.value.length;
});
```

## Pitfalls

1. **Auth cookies required** — Must navigate to the Dataverse org URL first to establish MSAL cookies. The API returns HTML (login page) if called from the Copilot Studio domain.
2. **Connected agents have different componenttype** — Custom topics use `componenttype eq 9`. Connected agents, system topics, and knowledge sources use different types. The filter `_parentbotid_value eq '${botId}' and componenttype eq 9` returns only custom topics.
3. **Property name** — The filter property is `_parentbotid_value` (with underscore prefix), NOT `botid`.
4. **No undo** — API deletes are permanent. There's no recycle bin. Verify the topic GUID before deleting.
5. **Chrome timeout** — If Chrome is hung from heavy page loads (eval detail pages), restart Chrome before running API calls. The CDP connection hangs when Chrome has 30+ tabs or heavy pages.
