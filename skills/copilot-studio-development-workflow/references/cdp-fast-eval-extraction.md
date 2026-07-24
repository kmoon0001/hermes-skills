# CDP Fast Evaluation Score Extraction

## Pattern

Read Copilot Studio evaluation scores from already-open Kiro Chrome tabs via CDP
in ~5 seconds, vs 3-7 minutes with playwright-cli auth cycles.

## Prerequisites

- Kiro Chrome running with CDP on port 9223
- Evaluation pages open in tabs for each agent (SLP, PT, OT, TDA)
- Node.js with `ws` module

## Usage

```javascript
const WebSocket = require('ws');
const http = require('http');

// Find the agent's evaluation tab
http.get('http://127.0.0.1:9223/json', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const targets = JSON.parse(data);
    const agent = targets.find(t => t.title.includes('OT_Specialist'));
    const ws = new WebSocket(agent.webSocketDebuggerUrl);
    
    ws.on('open', () => {
      ws.send(JSON.stringify({
        id: 1,
        method: 'Runtime.evaluate',
        params: {
          expression: 'document.body.innerText',
          returnByValue: true
        }
      }));
    });
    
    ws.on('message', (msg) => {
      const text = JSON.parse(msg).result.result.value;
      // Parse scores from text: "General quality\nEnd of interactive chart.\n85%"
      const matches = text.match(/General quality[\s\S]*?(\d+)%/g);
      console.log(matches);
      ws.close();
    });
  });
});
```

## Bot IDs

All in environment `Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f` (Ensign Services default):

| Agent | Bot ID |
|-------|--------|
| OT_Specialist | 73b45e98-af7a-443a-aa12-6d8a05118530 |
| SLP_Specialist | 6e437a77-a5dc-4984-90eb-4924eab10006 |
| PT_Specialist | 593407f3-539b-490f-84ac-d74e13216c81 |
| TDA | 4d0ed0d3-30f6-f011-8406-000d3a37eba2 |

## Also Works For

- Overview page (instructions, settings, knowledge sources)
- Topics page (ON/OFF status, topic names)
- Knowledge page (source names, types, statuses)

The pattern is always the same: find the tab's WebSocket URL from `/json`, connect,
evaluate `document.body.innerText`, parse the text.
