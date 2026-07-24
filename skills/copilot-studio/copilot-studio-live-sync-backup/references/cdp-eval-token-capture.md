# PPAPI Eval Token Capture via CDP Chrome

Capturing a PPAPI evaluation token from an authenticated Copilot Studio browser session.

## Setup

1. Kill existing Chrome: `mcp_cua_driver_kill_app(pid=...)`
2. Launch with CDP: `mcp_cua_driver_launch_app(path='chrome.exe', additional_arguments=['--remote-debugging-port=9223'])`
3. Verify CDP: `curl -s http://127.0.0.1:9223/json/version`
4. Navigate to eval page via raw CDP WebSocket:

```javascript
const WebSocket = require('ws');
const http = require('http');
http.get('http://127.0.0.1:9223/json/list', res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    const pages = JSON.parse(d);
    const target = pages.find(p => p.url.includes('newtab') || p.url === 'about:blank');
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    ws.on('open', () => {
      ws.send(JSON.stringify({id:1, method:'Page.navigate',
        params:{url:'https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/evaluation'}}));
    });
  });
});
```

5. Run `cdp_capture_token.cjs` to extract PPAPI Bearer token from network traffic
6. Token saved to `~/.copilot-studio-cli/test-agent-token.txt`

## Token Usage

PPAPI base URL: `https://api.powerplatform.com/copilotstudio/environments/{envId}/bots/{agentId}/api/makerevaluation`

### List test sets
`GET /testsets?api-version=2024-10-01`

### Start run
`POST /testsets/{testSetId}/run?api-version=2024-10-01`
Body: `{"runOnPublishedBot": false}` (tests draft, no publish needed)

### Poll run
`GET /testruns/{runId}?api-version=2024-10-01`

## Known Pitfalls

- **cua-driver `execute_javascript` does NOT work for CDP Chrome on Windows.** It tries the bookmark-URL UIA bypass and fails. Use raw CDP WebSocket instead.
- **PPAPI token expiry is ~15 minutes** in practice (not 1 hour). Re-capture via CDP.
- **Test-set detail endpoint may return 404** (`RouteNotFound`) — list endpoint works, detail is broken in some regions. Fall back to SPA score extraction.
- **The manage-agent MSAL cache scope (`api://96ff4394-...`) cannot get PPAPI tokens.** The refresh token was issued for the PowerVA gateway app, not PPAPI. The `eval-api.bundle.js` with `--client-id 96ff4394-...` requires interactive login which may fail with `AADSTS50011` (redirect URI mismatch).
- **Direct Line token endpoint** (`/api/makerevaluation/directline/token`) returns 404 from PPAPI — Direct Line testing needs a separate auth path.
