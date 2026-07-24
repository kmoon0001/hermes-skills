# Dataverse API Topic Creation for Copilot Studio

## Overview

Topics can be created and updated entirely via the Dataverse REST API at
`{ORG}/api/data/v9.2/botcomponents`. This bypasses Monaco, CDP, and the
Copilot Studio UI entirely.

Validated June 2026 on QM Coach V2 (ea52ad9c-8233-f111-88b3-6045bd09a824).

## Critical: The `data` Field

API-created topics are **INVISIBLE in the Copilot Studio UI** unless BOTH
`content` AND `data` fields are set. The UI reads from `data`; the runtime
reads from `content`. Working topics (created via UI) have both populated.

When creating via API POST, set `data` to the **empty shell template** (NOT the full content YAML).

## Create Topic (POST)

```javascript
const ORG = 'https://orgbd048f00.crm.dynamics.com';
const BOT_ID = 'ea52ad9c-8233-f111-88b3-6045bd09a824';
const yaml = fs.readFileSync('topic.yaml', 'utf8').replace(/\r\n/g, '\n');

const payload = {
  name: 'My Topic Name',
  componenttype: 9,
  content: yaml,
  data: shellYaml,                                      // EMPTY SHELL, NOT full content (causes eval regression)
  statecode: 0,                                         // Active
  statuscode: 1,                                        // Active
  schemaname: 'cr917_agent.topic.MyTopicName',          // REQUIRED field
  'parentbotid@odata.bind': `/bots(${BOT_ID})`         // OData nav property
};

const resp = await fetch(`${ORG}/api/data/v9.2/botcomponents`, {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
});
```

## Shell YAML Template (for `data` field)

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent: {}

inputType: {}
outputType: {}
```

When stringified for JSON payload, use `\r\n` line endings:
```javascript
const shellYaml = 'kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnRecognizedIntent\r\n  id: main\r\n  intent: {}\r\n\r\ninputType: {}\r\noutputType: {}';
```

## Update Existing Topic (PATCH)

```javascript
const topicId = 'fe61c0cf-7b6c-f111-ab0c-70a8a5b0f082';

const resp = await fetch(`${ORG}/api/data/v9.2/botcomponents(${topicId})`, {
  method: 'PATCH',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json', ... },
  body: JSON.stringify({
    name: 'Updated Name',
    content: newYaml
    // Do NOT set data to full content — use empty shell if data needs updating
  })
});
```

## List All Topics

```javascript
const filter = `_parentbotid_value eq '${BOT_ID}' and componenttype eq 9`;
const url = `${ORG}/api/data/v9.2/botcomponents?$select=name,botcomponentid,content,data,modifiedon&$filter=${encodeURIComponent(filter)}&$top=200&$orderby=name`;
const resp = await fetch(url, { credentials: 'include', headers: {...} });
const data = await resp.json();
// data.value = array of topic objects
```

## Pitfalls

1. **`_parentbotid_value` in POST body → 400 error**
   "CRM do not support direct update of Entity Reference properties"
   Fix: Use `'parentbotid@odata.bind': '/bots(BOT_ID)'` instead.

2. **Missing `schemaname` → 400 error**
   "Attribute 'schemaname' cannot be NULL"
   Fix: Always include `schemaname` in POST payload.

3. **`schemaname` is immutable** — Cannot be changed after creation via PATCH.
   Set it correctly on POST.

4. **`data` field null → invisible topics; full content → eval regression**
   Topics created via API show in Dataverse but NOT in Copilot Studio UI without `data`.
   BUT setting `data` to full YAML (1818 chars) instead of empty shell (121 chars) caused
   single-response eval to drop from 95% → 12%. The `data` field is the "draft" version
   used for routing; full content confuses the engine.
   Fix: Set `data` to empty shell template: `'kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnRecognizedIntent\r\n  id: main\r\n  intent: {}\r\n\r\ninputType: {}\r\noutputType: {}'`

5. **CORS blocks cross-domain fetch**
   Page must be on Dataverse org domain, not copilotstudio.microsoft.com.
   Navigate to `https://orgbd048f00.crm.dynamics.com` first.

6. **PAC CLI has no topic CRUD**
   `pac copilot` only supports list/status/publish/extract-template.
   Use raw Dataverse REST API for topic operations.

7. **Publish required after changes**
   `pac copilot publish --bot BOT_ID --environment ENV_ID`

8. **Working topic schema format**
   UI-created topics use: `cr917_agent.topic.TopicName`
   API-created topics use whatever schemaname you set.
   The format doesn't affect functionality, only naming convention.

## Verification Script

```javascript
// After creating topics, verify they have both fields
const topics = await page.evaluate(async ({BOT_ID, ORG}) => {
  const filter = `_parentbotid_value eq '${BOT_ID}' and componenttype eq 9`;
  const url = `${ORG}/api/data/v9.2/botcomponents?$select=name,content,data&$filter=${encodeURIComponent(filter)}&$top=200`;
  const resp = await fetch(url, { credentials: 'include', headers: {...} });
  const result = await resp.json();
  return result.value.map(v => ({
    name: v.name,
    contentLen: (v.content || '').length,
    hasData: v.data !== null && v.data !== undefined && v.data !== '',
    dataLen: (v.data || '').length,
    match: (v.content || '').length === (v.data || '').length
  }));
}, {BOT_ID, ORG});

for (const t of topics) {
  console.log(`${t.match ? '✓' : '✗'} ${t.name}: content=${t.contentLen} data=${t.dataLen}`);
}
```

## Chrome Launch for CDP (Windows)

```bash
# Kill all Chrome first
taskkill //F //IM chrome.exe //T 2>&1
sleep 3

# Launch with temp profile (NOT default profile — causes "Opening in existing browser session")
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9223 \
  --user-data-dir="$TEMP/chrome-cdp-profile" \
  --no-first-run \
  "https://orgbd048f00.crm.dynamics.com"
```

- Default user data dir causes Chrome to detect existing session and bypass CDP
- Always use `terminal(background=true)` to launch Chrome
- Wait 8-10 seconds before checking `curl -s http://127.0.0.1:9223/json/version`
- Close extra tabs via `curl http://127.0.0.1:9223/json/close/{TARGET_ID}` before Playwright connect
