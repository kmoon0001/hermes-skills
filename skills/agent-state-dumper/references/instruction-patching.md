# Instruction Patching via Dataverse API

## Template (Node.js)

```js
const https = require('https');
const { execSync } = require('child_process');

function patchDV(org, entity, id, body, token) {
  const url = `https://${org}.crm.dynamics.com/api/data/v9.2/${entity}(${id})`;
  return new Promise((resolve, reject) => {
    const d = JSON.stringify(body);
    const req = https.request(url, {
      method: 'PATCH',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(d),
        'Accept': 'application/json',
        'If-Match': '*'
      }
    }, resp => {
      let b = '';
      resp.on('data', c => b += c);
      resp.on('end', () => resolve({ status: resp.statusCode, body: b }));
    });
    req.on('error', reject);
    req.write(d);
    req.end();
  });
}

async function main() {
  const token = execSync(
    'az account get-access-token --resource "https://org3353a370.crm.dynamics.com" --query accessToken -o tsv',
    { encoding: 'utf8' }
  ).trim();
  
  const org = 'org3353a370';
  const compId = '<component-id>';
  const newData = '<new-instructions-yaml>';
  
  const result = await patchDV(org, 'botcomponents', compId, { data: newData }, token);
  console.log(`PATCH: ${result.status}`); // 204 = success
}

main().catch(e => { console.error(e); process.exitCode = 1; });
```

## Key patterns

- **Token source:** `az account get-access-token --resource "https://org3353a370.crm.dynamics.com/"`
- **Entity:** `botcomponents`
- **Body:** `{ data: "<YAML string>" }` — only the `data` field needs updating for instructions (componenttype 15)
- **Success code:** HTTP 204 (No Content)
- **No CDP needed:** Works without a running browser. Faster than Playwright-based scripts.
- **Token lifetime:** ~1 hour — regenerate if stale

## When to use API vs Playwright/CDP

| Operation | API | CDP/Playwright |
|-----------|-----|----------------|
| Read instructions | ✅ GET botcomponents | ✅ page.evaluate |
| Patch instructions | ✅ PATCH botcomponents | ✅ page.evaluate fetch |
| Read topics YAML | ✅ GET botcomponents | — |
| Patch topics YAML | ✅ PATCH botcomponents | — |
| Start evaluations | — | ✅ (needs eval API auth) |
| Navigate Copilot Studio UI | — | ✅ |
| Publish agent | ⚠️ pac copilot | ✅ |
