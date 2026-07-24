#!/usr/bin/env node
// Usage: node get_scores.cjs <PAGE_ID> <LABEL> <TIMEOUT_SEC>
// Extracts SR and Conv scores from a Copilot Studio evaluation page via CDP.
// PAGE_ID = Chrome DevTools Protocol page ID (from /json endpoint)
// LABEL = printed label for output (e.g., "OT", "SLP")
// TIMEOUT_SEC = seconds to wait for the page to render (default 15)
//
// Output: Recent results section showing pass % for each evaluation run

const WebSocket = require("ws");
const PAGE_ID = process.argv[2];
const LABEL = process.argv[3] || "SCORES";
const TIMEOUT_SEC = parseInt(process.argv[4] || "15");

if (!PAGE_ID) {
  console.error("Usage: node get_scores.cjs <PAGE_ID> [LABEL] [TIMEOUT_SEC]");
  process.exit(1);
}

const ws = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${PAGE_ID}`);
let id = 0;
function send(m, p = {}) { id++; ws.send(JSON.stringify({ id, method: m, params: p })); }

let answered = false;

ws.on("open", () => {
  send("Runtime.evaluate", {
    expression: `(function(){
      var t = document.body?.innerText || "";
      var i = t.indexOf("Recent results");
      var result = i < 0
        ? t.substring(0, 800)
        : t.substring(Math.max(0, i - 300), Math.min(t.length, i + 1800));
      return JSON.stringify({found: i >= 0, text: result});
    })()`
  });
});

ws.on("message", (data) => {
  try {
    const msg = JSON.parse(data.toString());
    if (msg.id === 1) {
      const r = JSON.parse(msg.result?.result?.value || '{}');
      console.log(`=== ${LABEL} ===`);
      console.log(`Found: ${r.found}`);
      console.log(r.text?.substring(0, 2500) || "N/A");
      answered = true;
      process.exit(0);
    }
  } catch (e) {}
});

ws.on("error", (err) => { console.error(`WS Error: ${err.message}`); process.exit(1); });
setTimeout(() => { if (!answered) { console.error(`TIMEOUT after ${TIMEOUT_SEC}s`); process.exit(1); } }, TIMEOUT_SEC * 1000);
