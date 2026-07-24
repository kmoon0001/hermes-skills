# Auth Refresh via CDP (Kiro Chrome → playwright-cli)

When a playwright-cli session's Copilot Studio auth expires, refresh it from Kiro Chrome's
existing SSO session. The ESTSAUTHPERSISTENT cookie usually enables silent SSO redirect.

## Prerequisites

- Kiro Chrome running with CDP on port 9223
- Copilot Studio logged in at least once in Kiro (creates MSAL token cache in localStorage)
- Node.js with `ws` module available

## Script: refresh_auth.cjs

```javascript
const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');

const targetUrl = 'https://copilotstudio.microsoft.com/environments/.../bots/.../overview';
const authPath = 'path/to/fresh_auth.json';

http.get('http://127.0.0.1:9223/json', (res) => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    const page = JSON.parse(d).find(p => p.url && p.url.includes('copilotstudio'));
    if (!page) process.exit(1);

    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let cid = 0, calls = {};
    ws.on('message', msg => { const r = JSON.parse(msg); if (r.id && calls[r.id]) { calls[r.id](r); } });
    function send(m, p) { return new Promise(resolve => { const id = ++cid; calls[id] = resolve; ws.send(JSON.stringify({id, method: m, params: p})); }); }

    ws.on('open', async () => {
      await send('Network.enable', {});
      await send('DOMStorage.enable', {});

      // 1. Navigate to CS URL
      await send('Page.navigate', {url: targetUrl});
      await new Promise(r => setTimeout(r, 18000));

      // 2. Check if redirected to login
      const loc = await send('Runtime.evaluate', {expression: 'window.location.href'});
      if (loc.result.result.value.includes('login.microsoft')) {
        // SSO didn't work — retry once
        await send('Page.navigate', {url: targetUrl});
        await new Promise(r => setTimeout(r, 20000));
        const loc2 = await send('Runtime.evaluate', {expression: 'window.location.href'});
        if (loc2.result.result.value.includes('login')) {
          console.log('SSO failed — user must log in manually in Kiro');
          process.exit(1);
        }
      }

      // 3. Export cookies
      const cResult = await send('Network.getAllCookies', {});
      let cookies = cResult.result.cookies;

      // 4. Remove partitionKey objects
      for (const c of cookies) {
        if (c.partitionKey && typeof c.partitionKey === 'object') delete c.partitionKey;
      }

      // 5. Export localStorage (MSAL token cache lives here)
      let localStorageEntries = [];
      for (const origin of ['https://copilotstudio.microsoft.com', 'https://login.microsoftonline.com']) {
        try {
          const ls = await send('DOMStorage.getDOMStorageItems', {
            storageId: {securityOrigin: origin, isLocalStorage: true}
          });
          if (ls.result && ls.result.entries) {
            localStorageEntries.push({origin, entries: ls.result.entries});
          }
        } catch (e) {}
      }

      // 6. Convert to Playwright storageState format
      const origins = localStorageEntries.map(ls => ({
        origin: ls.origin,
        localStorage: ls.entries.map(e => ({name: e[0], value: e[1]}))
      }));
      const authData = { cookies, origins };
      fs.writeFileSync(authPath, JSON.stringify(authData, null, 2));
      console.log(`Auth saved: ${cookies.length} cookies, ${origins.length} origins`);
      ws.close();
    });
  });
});
```

## Usage

```bash
# 1. Run the refresh script (connects to Kiro Chrome CDP on 9223)
NODE_PATH=$(npm root -g) node path/to/refresh_auth.cjs

# 2. Load into playwright-cli session
npx playwright-cli --session cs open https://example.com
npx playwright-cli --session cs state-load path/to/fresh_auth.json

# 3. Navigate to CS page (should land without login redirect)
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/..."
```

## How It Works

1. Kiro Chrome's ESTSAUTHPERSISTENT cookie (~90 day lifetime) enables silent SSO redirect
2. Navigating to CS triggers MSAL which reads the token cache from localStorage
3. MSAL uses the refresh token to silently acquire new access tokens
4. The page lands on the CS dashboard without user interaction
5. We export all cookies + localStorage in Playwright storageState format

## Why CDP Instead of playwright-cli auth reload?

- The exported auth.json can be reused across multiple playwright-cli sessions
- playwright-cli's `setStorageState` only rehydrates cookies + localStorage — it can't kick off
  MSAL token refresh. The tokens must be freshly minted by actually navigating to CS.
- CDP gives us control over both the navigation flow AND the export format.
