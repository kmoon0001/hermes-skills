const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');

// Export Copilot Studio auth from any Chrome with DevTools Protocol open on port 9223.
// Usage: node export-auth.cjs
// Output: fresh_auth.json in current directory (Playwright storageState format)
//
// Prerequisites: Chrome running with --remote-debugging-port=9223
// and at least one tab signed into copilotstudio.microsoft.com.

const CDP_PORT = process.env.CDP_PORT || 9223;

http.get(`http://127.0.0.1:${CDP_PORT}/json`, (res) => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    const pages = JSON.parse(d);
    const cs = pages.find(p => p.url && p.url.includes('copilotstudio'));
    if (!cs) {
      console.error('No Copilot Studio page found. Open one and retry.');
      process.exit(1);
    }
    console.error('Using page: ' + cs.title.substring(0, 60));

    const ws = new WebSocket(cs.webSocketDebuggerUrl);
    let cid = 0, calls = {};
    ws.on('message', msg => {
      const r = JSON.parse(msg);
      if (r.id && calls[r.id]) { calls[r.id](r); delete calls[r.id]; }
    });

    function send(m, p) {
      return new Promise((resolve) => {
        const id = ++cid;
        calls[id] = resolve;
        ws.send(JSON.stringify({ id, method: m, params: p || {} }));
      });
    }

    ws.on('open', async () => {
      try {
        // Get all cookies for copilotstudio.microsoft.com
        await send('Network.enable');
        const ck = await send('Network.getAllCookies');
        const cookies = ck.result.cookies.map(c => {
          const cc = { ...c };
          // Remove partitionKey objects (Playwright rejects them)
          if (typeof cc.partitionKey === 'object') delete cc.partitionKey;
          return cc;
        });

        // Get localStorage entries
        await send('DOMStorage.enable');
        const ls = await send('DOMStorage.getDOMStorageItems', {
          storageId: {
            securityOrigin: 'https://copilotstudio.microsoft.com',
            isLocalStorage: true,
          },
        });

        const auth = {
          cookies,
          origins: [{
            origin: 'https://copilotstudio.microsoft.com',
            localStorage: (ls.result?.entries || []).map(e => ({
              name: e[0],
              value: e[1],
            })),
          }],
        };

        const path = process.argv[2] || 'fresh_auth.json';
        fs.writeFileSync(path, JSON.stringify(auth));
        console.log('SAVED: ' + cookies.length + ' cookies, ' +
          (ls.result?.entries?.length || 0) + ' ls entries → ' + path);
        ws.close();
        process.exit(0);
      } catch (e) {
        console.error('Error:', e.message);
        process.exit(1);
      }
    });
  });
});
