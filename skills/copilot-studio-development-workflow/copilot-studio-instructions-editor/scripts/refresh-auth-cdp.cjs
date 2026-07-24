// refresh-auth-cdp.cjs
// Extract fresh MSAL auth from Kiro Chrome CDP (port 9223).
// Saves to fresh_auth.json as Playwright storageState.
// Prerequisite: Kiro Chrome running with --remote-debugging-port=9223
//               with a logged-in Copilot Studio tab.

const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');

const OUTPUT = 'C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/home/fresh_auth.json';

http.get('http://127.0.0.1:9223/json', (res) => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    const pages = JSON.parse(d);
    const cs = pages.find(p => p.url && p.url.includes('copilotstudio'));
    if (!cs) { console.log('NO CS PAGE'); process.exit(1); }
    console.log('Using: ' + cs.title.substring(0, 60));
    
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
        ws.send(JSON.stringify({id, method: m, params: p || {}}));
      });
    }
    
    ws.on('open', async () => {
      await send('Network.enable');
      const ck = await send('Network.getAllCookies');
      const cookies = ck.result.cookies.map(c => {
        const cc = {...c};
        if (typeof cc.partitionKey === 'object') delete cc.partitionKey;
        return cc;
      });
      
      await send('DOMStorage.enable');
      const ls = await send('DOMStorage.getDOMStorageItems', {
        storageId: {
          securityOrigin: 'https://copilotstudio.microsoft.com',
          isLocalStorage: true
        }
      });
      
      const auth = {
        cookies,
        origins: [{
          origin: 'https://copilotstudio.microsoft.com',
          localStorage: (ls.result?.entries || []).map(e => ({name: e[0], value: e[1]}))
        }]
      };
      
      fs.writeFileSync(OUTPUT, JSON.stringify(auth));
      console.log('SAVED ' + cookies.length + ' cookies, ' + (ls.result?.entries?.length || 0) + ' ls entries');
      ws.close();
      process.exit(0);
    });
  });
});
