# Auth Refresh via Kiro Chrome CDP

When the playwright-cli session redirects to `login.microsoftonline.com`, the MSAL session has expired.

## Fastest Refresh Path

Kiro Chrome on port 9223 maintains an SSO session via the `ESTSAUTHPERSISTENT` cookie (~90 day lifetime).

### Steps

1. Connect to Kiro Chrome CDP on port 9223
2. Navigate to a Copilot Studio page (agent overview, e.g. `/bots/.../overview`)
3. Wait 15-20s for SPA load
4. If login page appears, the ESTSAUTHPERSISTENT cookie may still enable silent redirect — try navigating again
5. Export cookies + localStorage
6. Save as Playwright storageState format
7. Load into playwright-cli session

### CDP Export Script

```javascript
const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');

http.get('http://127.0.0.1:9223/json', (res) => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    const pages = JSON.parse(d);
    const page = pages.find(p => p.url && p.url.includes('copilotstudio')) || pages[0];
    if (!page) { console.log('no page'); process.exit(1); }

    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let cid = 0, calls = {};
    ws.on('message', msg => {
      const r = JSON.parse(msg);
      if (r.id && calls[r.id]) { calls[r.id](r); delete calls[r.id]; }
    });

    function send(m, p) {
      return new Promise((resolve, reject) => {
        const id = ++cid;
        calls[id] = resolve;
        ws.send(JSON.stringify({id, method: m, params: p}), e => e && reject(e));
        setTimeout(() => { if (calls[id]) { delete calls[id]; resolve(null); } }, 15000);
      });
    }

    ws.on('open', async () => {
      await send('Page.navigate', {
        url: 'https://copilotstudio.microsoft.com/environments/Default-.../bots/.../overview'
      });
      await new Promise(r => setTimeout(r, 15000));

      await send('Network.enable', {});
      const cookiesResp = await send('Network.getAllCookies', {});
      let cookies = cookiesResp?.result?.cookies || [];

      await send('DOMStorage.enable', {});
      const storageResp = await send('DOMStorage.getDOMStorageItems', {
        storageId: { securityOrigin: 'https://copilotstudio.microsoft.com', isLocalStorage: true }
      });
      const localStorage = storageResp?.result?.entries?.map(e => ({name: e[0], value: e[1]})) || [];

      cookies = cookies.map(c => {
        if (c.partitionKey && typeof c.partitionKey === 'object') delete c.partitionKey;
        return c;
      });

      const pwAuth = { cookies, origins: [{origin: 'https://copilotstudio.microsoft.com', localStorage}] };
      fs.writeFileSync('fresh_auth.json', JSON.stringify(pwAuth, null, 2));
      console.log(`Exported: ${cookies.length} cookies, ${localStorage.length} storage items`);
      ws.close();
    });
  });
});
```

### Load into playwright-cli

```bash
npx playwright-cli --session cs state-load /path/to/fresh_auth.json
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/..."
```
