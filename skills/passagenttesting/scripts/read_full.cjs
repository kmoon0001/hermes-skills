#!/usr/bin/env node
// Usage: node read_full.cjs <PAGE_ID> [KEYWORD]
// Reads a wide swath (first 8000 chars) of page body text via CDP.
// If KEYWORD is provided, searches around it. Useful for reading
// evaluation run details, failure lists, and page state.
//
// PAGE_ID = Chrome DevTools Protocol page ID
// KEYWORD = optional, search around this text in the output

const WebSocket = require("ws");
const PAGE = process.argv[2];
const KEYWORD = process.argv[3] || "";

if (!PAGE) {
  console.error("Usage: node read_full.cjs <PAGE_ID> [KEYWORD]");
  process.exit(1);
}

const ws = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${PAGE}`);
ws.on("open", () => {
  ws.send(JSON.stringify({ id: 1, method: "Runtime.evaluate", params: { expression: `document.body.innerText.substring(0, 8000)` } }));
});
ws.on("message", (d) => {
  try {
    const m = JSON.parse(d);
    if (m.id === 1) {
      const v = m.result?.result?.value || "";
      const i = KEYWORD ? v.indexOf(KEYWORD) : 0;
      const start = i < 0 ? 0 : Math.max(0, i - 200);
      console.log(v.substring(start, start + 3000));
      process.exit(0);
    }
  } catch (e) {}
});
setTimeout(() => process.exit(1), 10000);
