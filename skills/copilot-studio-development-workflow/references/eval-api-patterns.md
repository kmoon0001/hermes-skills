# Evaluation API Patterns

## Bearer Token Capture

The Eval REST API requires a Bearer token. Capture it from Chrome CDP:

```javascript
// 1. Enable network monitoring on a CS tab
await cdpSend(ws, 'Network.enable', {});

// 2. Navigate to any CS API endpoint to trigger auth
await cdpSend(ws, 'Page.navigate', {
  url: 'https://api.powerva.microsoft.com/api/evaluation/v1.0/environments/' + env + '/bots/' + bot + '/evaluationruns?$top=1'
});

// 3. Listen for requestWillBeSent events
ws.on('message', (data) => {
  const msg = JSON.parse(data);
  if (msg.method === 'Network.requestWillBeSent') {
    const auth = msg.params.request.headers['Authorization'];
    if (auth?.startsWith('Bearer ')) {
      token = auth.replace('Bearer ', '');
    }
  }
});
```

## Fetching Evaluation Runs

```
GET https://api.powerva.microsoft.com/api/evaluation/v1.0/environments/{envId}/bots/{botId}/evaluationruns?$top=5&$orderby=createdon desc
Headers: Authorization: Bearer {token}
```

Response includes: `name`, `testcasecount`, `datatype` (single-response / conversation),
`status` (Running/Completed), `generationqualityscore`.

## Evaluation Page Limitations

Scores on the Copilot Studio evaluation page are rendered in `<canvas>` charts
and interactive widgets — NOT in accessible DOM text. `body.innerText` will
show "General quality" as a label but NOT the numeric percentage.

**Reliable approaches:**
1. Use the Eval REST API (requires Bearer token)
2. Read the "Recent results" list which shows scores in plain text after completion
3. Use `vision_analyze` on a screenshot

## Score History Pattern

Recent results list format (from page text):
```
Evaluate OT_Specialist 260610_2147
20 test cases • Data type: conversation
Evaluate
Evaluate OT_Specialist
MK
Moon, Kevin
9:47 PM today
General quality
End of interactive chart.
70%
```

Parse by matching `General quality\nEnd of interactive chart.\n{score}%\n`.
