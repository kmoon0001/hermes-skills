# CDP Script Reliability Patterns

## Problem

Inline `node -e` scripts with CDP WebSocket connections frequently fail with:
- `ReferenceError: m is not defined` inside `setTimeout` callbacks
- `Unexpected server response: 500` due to connection saturation
- Empty results from `document.body.innerText` when SPA hasn't hydrated
- Timeouts when the SPA doesn't load via `Page.navigate`

## Solution: File-Based Scripts with Read-Back Templates

### Pattern 1: read_full.cjs — Reliable SPA body reading

When Copilot Studio's SPA fails to render via `Page.navigate` (returns 0-200 chars), use this pattern to read the full body after CDP navigation:

```javascript
// read_full.cjs — Usage: node read_full.cjs <PAGE_ID> [keyword]
const WebSocket = require("ws");
const PAGE = process.argv[2];
const ws = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${PAGE}`);

ws.on("open", () => {
  ws.send(JSON.stringify({
    id: 1,
    method: "Runtime.evaluate",
    params: { expression: "document.body.innerText.substring(0, 8000)" }
  }));
});

ws.on("message", (data) => {
  try {
    const m = JSON.parse(data.toString());
    if (m.id === 1) {
      const v = m.result?.result?.value || "";
      console.log(v);
      process.exit(0);
    }
  } catch (e) {}
});

setTimeout(() => process.exit(1), 10000);
```

Key advantages over inline `node -e`:
- No shell escaping issues with quotes/expressions
- `let`/`const` declarations persist across async callbacks (no `m is not defined` scoping bug)
- Cleaner error output

### Pattern 2: get_scores.cjs — Evaluation score extraction

For reading evaluation scores from the CS evaluation page:

```javascript
// get_scores.cjs — Usage: node get_scores.cjs <PAGE_ID> <AGENT_NAME> <timeout_s>
const WebSocket = require("ws");
const PAGE = process.argv[2];
const TAG = process.argv[3] || "AGENT";
const ws = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${PAGE}`);

ws.on("open", () => {
  ws.send(JSON.stringify({
    id: 1, method: "Runtime.evaluate",
    params: { expression: `var t=document.body.innerText; t.includes("Recent results")||t.includes("Test sets")?"HAS_CONTENT":"NO_CONTENT:"+t.substring(400,800)` }
  }));
});

ws.on("message", (data) => {
  try {
    const m = JSON.parse(data.toString());
    if (m.id === 1) {
      const v = m.result?.result?.value || "";
      console.log(`=== ${TAG} ===`);
      console.log(`Found: ${v.includes("HAS_CONTENT")}`);
      if (v.includes("HAS_CONTENT")) {
        ws.send(JSON.stringify({
          id: 2, method: "Runtime.evaluate",
          params: { expression: "var t=document.body.innerText; var i=t.indexOf('Recent results'); return i<0?t.substring(400,1000):t.substring(i,Math.min(t.length,i+2000));" }
        }));
      } else {
        console.log(v.substring(0, 500));
        process.exit(0);
      }
    }
    if (m.id === 2) {
      console.log(m.result?.result?.value?.substring(0, 2000));
      process.exit(0);
    }
  } catch (e) {}
});
setTimeout(() => process.exit(1), 15000);
```

## Preventing CDP Connection Saturation

Opening 15+ CDP tabs to the same Chrome instance causes `Unexpected server response: 500` on new WebSocket connections.

### Symptoms

- Scripts that worked 10 minutes ago suddenly fail with WS 500 errors on the same page ID
- Fresh page IDs work for 1-2 calls then also fail
- `curl -s http://127.0.0.1:9223/json` shows 20+ pages

### Prevention

1. **Reuse existing tabs** instead of opening new `curl -X PUT /json/new` ones
2. **Close unused tabs**: `curl -s -X DELETE "http://127.0.0.1:9223/json/close/{pageId}"`
3. **Keep total under 15** by periodically cleaning up
4. **Batch reads**: Use one tab for multiple reads over time rather than creating a new tab per read

### Stale Node.js Process Cleanup

```bash
# Check for stale nodes (anything running since a prior day)
ps -W 2>/dev/null | grep "node.exe" | grep -v "codex\|extension-host"

# Kill stale ones (NOT Chrome)
taskkill //F //PID <pid>
```

## CDP Timing Heuristics

| Operation | Wait time | Notes |
|-----------|-----------|-------|
| SPA navigation (overview/eval/topics) | 25-30s | CS SPA is slow to hydrate |
| Tab creation to ready | 3-5s | curl returns immediately, SPA isn't loaded |
| Evaluation tab to Recent results visible | 25-35s | From fresh tab |
| Click nav tab to content visible | 8-15s | Tab click + SPA route + render |
| Monaco code editor to view-lines ready | 5-10s | After clicking Open code editor |
| Running eval to completion | 12-18 min | 100 SR cases; 20 Conv cases similar |
