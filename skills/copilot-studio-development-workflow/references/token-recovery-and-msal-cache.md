# Token Recovery & MSAL Cache Management

When the `manage-agent.cache.json` (at `~/.copilot-studio-cli/manage-agent.cache.json`) is deleted, corrupted, or contains stale tokens, all MSAL-based auth paths fail silently. Here's the recovery hierarchy.

## Recovery Paths (try in order)

### 1. Capture token from browser Network traffic (fastest recovery)

If Chrome is running with CDP (port 9223) and Copilot Studio is signed in:

```python
import json, urllib.request, asyncio, websockets

async def capture_ppapi_token():
    r = urllib.request.urlopen("http://127.0.0.1:9223/json/list")
    pages = json.loads(r.read())
    target = [p for p in pages if 'copilotstudio' in p.get('url', '')][0]
    ws_url = target['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        await asyncio.sleep(0.5)
        # drain
        try:
            while True: await asyncio.wait_for(ws.recv(), timeout=0.3)
        except: pass
        
        await ws.send(json.dumps({"id": 2, "method": "Page.reload"}))
        
        for _ in range(300):
            msg = json.loads(await ws.recv())
            if msg.get('method') == 'Network.requestWillBeSent':
                req = msg['params']['request']
                headers = req.get('headers', {})
                auth = headers.get('Authorization', headers.get('authorization', ''))
                if auth and 'Bearer' in auth and len(auth) > 200 and 'powervamg' in req.get('url', ''):
                    token = auth.replace('Bearer ', '')
                    # Save as PPAPI token
                    import os
                    path = os.path.expandvars(r'%USERPROFILE%\.copilot-studio-cli\test-agent-token.txt')
                    open(path, 'w').write(token)
                    print(f"Saved PPAPI token ({len(token)} chars)")
                    return
            await asyncio.sleep(0.01)

asyncio.run(capture_ppapi_token())
```

This captures a PPAPI-scoped token valid for the gateway API (`powervamg.us-*.gateway.prod.island.powerapps.com`). Use it for eval operations.

### 2. Use the manage-agent MsalCache to get both PPAPI and DV tokens (clean cache)

If the cache is intact, MSAL Node can acquire tokens silently for both scopes:

```javascript
const { PublicClientApplication } = require('@azure/msal-node');
const { PersistenceCreator, PersistenceCachePlugin, DataProtectionScope } = require('@azure/msal-node-extensions');

const pers = await PersistenceCreator.createPersistence({
  cachePath: path.join(os.homedir(), '.copilot-studio-cli', 'manage-agent.cache.json'),
  dataProtectionScope: DataProtectionScope.CurrentUser,
  serviceName: 'copilot-studio-cli',
  accountName: 'manage-agent',
  usePlaintextFileOnLinux: true
});

const app = new PublicClientApplication({
  auth: { clientId: '51f81489-12ee-4a9e-aaae-a2591f45987d',
          authority: 'https://login.microsoftonline.com/<tenant-id>' },
  cache: { cachePlugin: new PersistenceCachePlugin(pers) }
});

const accounts = await app.getTokenCache().getAllAccounts();
const acct = accounts.find(a => a.tenantId === '<tenant-id>');

// PPAPI token (for gateway API)
const ppResp = await app.acquireTokenSilent({
  scopes: ['api://96ff4394-9197-43aa-b393-6a41652e21f8/.default'],
  account: acct
});

// Dataverse token (for botcomponent PATCH operations)
const dvResp = await app.acquireTokenSilent({
  scopes: ['https://<org>.crm.dynamics.com/.default'],
  account: acct
});
```

### 3. Restore corrupted cache from browser localStorage (DANGEROUS)

The browser's Copilot Studio session stores MSAL tokens in `localStorage` with keys starting with `msal.2|`. These are **DPAPI-encrypted** at the browser-process level. Writing this raw data to `manage-agent.cache.json` and expecting MSAL Node's `PersistenceCreator` to read it **will fail** because the browser uses a different DPAPI context than the Node.js process.

**Do NOT** do this:
```javascript
// BROKEN — browser data is DPAPI-encrypted in a different context
const browserData = JSON.parse(localStorage.getItem('msal.2|...'));
fs.writeFileSync('manage-agent.cache.json', JSON.stringify(browserData)); // ❌
```

The `PersistenceCreator` will fail with `Encryption/Decryption failed. Error code: 13` or `no_account_in_silent_request`.

**The ONLY reliable MSAL Node cache** is one that was created by MSAL Node's own `PersistenceCreator` — i.e., originally created by the pac CLI or VS Code Copilot Studio extension running in the same Windows user context.

### 4. Load MSAL Browser library from CDN into the SPA (unreliable)

In environments where CDN scripts are blocked (common in enterprise/corporate environments), loading MSAL Browser from CDNs (`alcdn.msauth.net`, `unpkg.com`, `cdn.jsdelivr.net`) will fail. Test with:

```javascript
['https://alcdn.msauth.net/browser/3.29.0/js/msal-browser.min.js',
 'https://unpkg.com/@azure/msal-browser@3.29.0/lib/msal-browser.min.js',
 'https://cdn.jsdelivr.net/npm/@azure/msal-browser@3.29.0/lib/msal-browser.min.js']
```

If all fail, fall back to method 1 (capture from network traffic).

### 5. TokenFactoryIframe postMessage (unreliable)

The `TokenFactoryIframe` at `webshell.suite.office.com/iframe/TokenFactoryIframe` can issue tokens but may not be loaded on the current page. It exposes `O365MSALTokenFactoryIframe.TokenFactoryInsideIframe` but the API contract is undocumented and may not respond to cross-origin postMessage requests.

## Scope Reference

**Trailing-slash gotcha for `az.cmd`:** `az account get-access-token --resource https://org.crm.dynamics.com/` (WITH trailing slash) works. Without it, Dataverse returns 401 even though the token decodes with the correct audience. The trailing slash was required for this tenant/org combination.\n\n| Token Scope | API Audience | Used For |
|------------|-------------|----------|
| `api://96ff4394-9197-43aa-b393-6a41652e21f8/.default` | `96ff4394-9197-43aa-b393-6a41652e21f8` (PVA app) | Gateway API (evals, runs) |
| `https://<org>.crm.dynamics.com/.default` | `<org>.crm.dynamics.com` | Dataverse API (botcomponents CRUD) |
| `https://api.powerplatform.com/.default` | `api.powerplatform.com` | PPAPI (publish, agent config) |
| `https://management.azure.com.int` | `management.azure.com.int` | BAP API (environment info) |

The PPAPI audience token **cannot** be used against the Dataverse API (returns 401). Each needs its own scope-specific token from MSAL.

## Publish Failure Cache (pac CLI)

`pac copilot publish --bot <id>` caches the last failure timestamp permanently. After a failed publish, every retry returns the same `Failed [timestamp]`. The cache survives `pac auth clear`.

**Workarounds:**
1. Verify true publish state with Dataverse: `GET /bots({id})?$select=publishedon`
2. Use the Copilot Studio SPA Publish button (force-click via CDP if disabled)
3. Use `manage-agent.bundle.js publish`
4. Publish via the PvaPublish action API
