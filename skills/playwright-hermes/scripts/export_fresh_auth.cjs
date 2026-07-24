const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Resolve output path from USERPROFILE
const homeDir = process.env.USERPROFILE.replace(/\\/g, '/');
const outPath = homeDir + '/AppData/Local/hermes/profiles/coding-profile/home/fresh_auth.json';

http.get('http://127.0.0.1:9223/json', (res) => {
  let data = '';
  res.on('data', c => data += c);
  res.on('end', () => {
    const pages = JSON.parse(data);
    // Prefer the first non-about:blank page, fall back to first page
    const page = pages.find(p => p.url !== 'about:blank') || pages[0];
    if (!page) { console.error('No CDP page found'); process.exit(1); }

    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let callId = 0;
    const pending = {};

    ws.on('message', raw => {
      const r = JSON.parse(raw);
      if (r.id && pending[r.id]) { pending[r.id](r); delete pending[r.id]; }
    });

    function send(method, params) {
      return new Promise(resolve => {
        const id = ++callId;
        pending[id] = resolve;
        ws.send(JSON.stringify({id, method, params}));
      });
    }

    ws.on('open', async () => {
      // Navigate to Copilot Studio so MSAL tokens populate localStorage
      await send('Page.navigate', {url: 'https://copilotstudio.microsoft.com'});
      await new Promise(r => setTimeout(r, 15000));

      // Extract cookies
      const cookiesResp = await send('Network.getAllCookies', {});
      const cookies = cookiesResp.result.cookies;

      // Extract localStorage
      const lsResp = await send('Runtime.evaluate', {
        expression: 'JSON.stringify(Array.from(Object.entries(localStorage)))'
      });
      const ls = JSON.parse(lsResp.result.result.value || '[]');

      // Convert to Playwright storageState format
      const pwCookies = cookies.map(c => ({
        name: c.name, value: c.value, domain: c.domain,
        path: c.path || '/', expires: c.expires || -1,
        httpOnly: c.httpOnly || false, secure: c.secure || false,
        sameSite: c.sameSite || 'Lax'
      }));

      const storageState = {
        cookies: pwCookies,
        origins: [{
          origin: 'https://copilotstudio.microsoft.com',
          localStorage: ls.map(([name, value]) => ({name, value}))
        }]
      };

      const dir = path.dirname(outPath);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, {recursive: true});
      fs.writeFileSync(outPath, JSON.stringify(storageState, null, 2));
      console.log('Auth exported to ' + outPath);
      console.log('Cookies: ' + cookies.length + ', localStorage items: ' + ls.length);
      ws.close();
      process.exit(0);
    });
  });
});
