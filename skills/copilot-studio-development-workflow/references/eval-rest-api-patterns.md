# Eval REST API — Programmatic Score Checks

## Token Setup

Capture a fresh Bearer token via CDP Network.enable before every eval session:

```javascript
const cdp = await page.context().newCDPSession(page);
await cdp.send('Network.enable');
cdp.on('Network.requestWillBeSent', (params) => {
  const h = params.request.headers;
  if (h.Authorization?.startsWith('Bearer ') && params.request.url.includes('api.powerplatform')) {
    const token = h.Authorization.replace('Bearer ', '');
    // Save and use immediately — token is valid ~1 hour
  }
});
```

## API Calls

Base URL: `api.powerplatform.com`
API version: `2024-10-01`

### Get latest runs
```
GET /copilotstudio/environments/{envId}/bots/{botId}/api/makerevaluation/testruns?$orderby=startTime desc&$top=5&api-version=2024-10-01
```

### Get run score with test case results
```
GET /copilotstudio/environments/{envId}/bots/{botId}/api/makerevaluation/testruns/{runId}?$expand=testCasesResults&api-version=2024-10-01
```

Response includes `testCasesResults[]` with per-case:
- `metricsResults[0].result.status` — "Pass" / "Fail" / "Error"
- `metricsResults[0].result.data` — `{abstention, relevance, groundedness, completeness}`
- `metricsResults[0].result.aiResultReason` — grader explanation (conversation only, null for SR)

### State field
`state` is a STRING (not numeric): "InProgress", "Completed", "Failed", "NotStarted"

## Token Limitations
- Read-only for evaluation data (GET only, no POST/PATCH)
- Cannot use for botcomponents API (different scope)
- Scoped to `api.powerplatform.com` only
- Does NOT work for Dataverse (`org*.crm.dynamics.com` — returns 401)

## Score Calculation
```javascript
let pass = 0, fail = 0;
for (const tc of d.testCasesResults) {
  tc.metricsResults?.[0]?.result?.status === 'Pass' ? pass++ : fail++;
}
const rate = Math.round(pass / (pass + fail) * 100);
```
