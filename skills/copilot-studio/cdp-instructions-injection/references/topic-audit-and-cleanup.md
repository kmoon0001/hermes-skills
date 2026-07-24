# Topic Audit & Cleanup via Dataverse API

Full methodology for auditing and cleaning up Copilot Studio agent topics. Validated on QM Coach V2 (62→30 topics, 71%→95% eval).

## Step 1: Get All Topics with Content

```javascript
await page.goto('https://ORG.crm.dynamics.com', { waitUntil: 'domcontentloaded', timeout: 60000 });
await sleep(8000);

const botId = 'YOUR-BOT-ID';
const topics = await page.evaluate(async (botId) => {
    const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
    const url = `https://ORG.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name,botcomponentid,content,description&$filter=${encodeURIComponent(filter)}&$top=100`;
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } });
    const data = await resp.json();
    return data.value.map(v => ({ name: v.name, id: v.botcomponentid, content: v.content || '', description: v.description || '' }));
}, botId);
```

## Step 2: Categorize Topics

```javascript
const empty = [];    // 0 chars
const stubs = [];    // <300 chars, "under development"
const broken = [];   // Missing AdaptiveDialog, wrong componentName
const short = [];    // <300 chars, not stubs
const clean = [];    // Everything else

for (const topic of topics) {
    const c = topic.content;
    if (c.length === 0) empty.push(topic);
    else if (c.length < 300 && (c.includes('under development') || c.includes('stub') || c.includes('placeholder'))) stubs.push(topic);
    else if (c.length > 0 && !c.includes('AdaptiveDialog')) broken.push(topic);
    else if (c.length < 300) short.push(topic);
    else clean.push(topic);
}
```

## Step 3: Check for Cross-References to Deleted Topics

After identifying topics to delete, search remaining topics for references:

```javascript
const toDeleteNames = ['Topic A', 'Topic B'];
for (const topic of clean) {
    for (const name of toDeleteNames) {
        if (topic.content.includes(name)) {
            console.log(`${topic.name} references deleted: ${name}`);
        }
    }
}
```

## Step 4: Check for Corrupted Content

Look for topics with wrong componentName or wrong intent kind:

```javascript
for (const topic of topics) {
    const c = topic.content;
    // Check componentName matches topic name
    const componentMatch = c.match(/componentName:\s*(\S+)/);
    if (componentMatch) {
        const componentName = componentMatch[1];
        const topicNameClean = topic.name.replace(/[^A-Za-z0-9]/g, '');
        if (componentName !== topicNameClean && componentName !== topic.name) {
            console.log(`MISMATCH: ${topic.name} has componentName: ${componentName}`);
        }
    }
    // Check for wrong intent kind
    if (c.includes('OnUnknownIntent') && !topic.name.includes('Fallback')) {
        console.log(`WRONG INTENT: ${topic.name} has OnUnknownIntent (should be OnRecognizedIntent)`);
    }
}
```

## Step 5: Delete via Dataverse API

```javascript
for (const topic of toDelete) {
    const result = await page.evaluate(async (id) => {
        const resp = await fetch(`https://ORG.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, {
            method: 'DELETE', credentials: 'include',
            headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
        });
        return { status: resp.status, ok: resp.ok };
    }, topic.id);
    console.log(result.ok ? 'DELETED' : 'FAILED', topic.name);
    await sleep(300);
}
```

## Step 6: Republish

After deletions, navigate to Overview and click Publish. Check for:
- `published: true` in page text
- No "Something went wrong" crash
- No console `$kind` errors

## Step 7: Run Eval

Trigger single-response eval first (faster, more reliable). Then conversation eval if single-response passes.

## QM Coach V2 Results

| Metric | Before | After |
|--------|--------|-------|
| Topics | 62 | 30 |
| Single-response eval | 71% | 95% |
| Publish crash | Yes | No |
| Stubs | 18 | 0 |
| Empty topics | 1 | 0 |
| Broken refs | 3 | 0 |
| Interactive menus | 9 | 0 |

## Categories of Topics to Delete

1. **Empty** (0 chars) — corrupted during creation, usually from typos
2. **Stubs** (<300 chars, "under development") — placeholder topics that add no value
3. **Wrong componentName** — topic content belongs to a different topic (copy/paste error)
4. **Broken references** — topic references deleted topics in BeginDialog/menu
5. **Interactive menus** — topics that return cards/menus instead of text answers (hurt eval)
6. **Duplicates** — same topic created twice with different casing or naming

## Pitfalls

- Dataverse API PATCH on content field returns 400 — cannot update topic YAML via API
- Only DELETE works reliably via API for topic cleanup
- After deletions, MUST republish before running evals
- Conversation evals are more sensitive to topic deletions than single-response
- The `$kind` frontend error persists in console even after successful publish (harmless)
