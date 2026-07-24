# Gateway API Eval Flow (Medicare Part B Agent)

## Test Sets
Current Conv test set: `21b54c2b-a977-4b8a-a70c-168746d07464` (20 cases)
Environment ID: `a944fdf0-0d2e-e14d-8a73-0f5ffae23315`
Bot ID: `b0346795-4876-f111-ab0e-70a8a5b1b8cc`

## Auth: MSAL Cache (no interactive login)
```javascript
const { PublicClientApplication } = require('@azure/msal-node');
const { PersistenceCreator, PersistenceCachePlugin } = require('@azure/msal-node-extensions');
const cachePath = path.join(os.homedir(), '.copilot-studio-cli', 'msal_cache.json');
const persistence = await PersistenceCreator.createPersistence({ filePath: cachePath });
const pca = new PublicClientApplication({
  auth: { clientId: '6ab5df65-f845-4711-97ee-e2900c71289e', authority: 'https://login.microsoftonline.com/03cc92c3-986c-4cf4-ae27-1478cf99d17f' },
  cache: { cachePlugin: new PersistenceCachePlugin(persistence) }
});
const accounts = await pca.getTokenCache().getAllAccounts();
const result = await pca.acquireTokenSilent({ scopes: ['https://powervamg.us-il106.gateway.prod.island.powerapps.com/.default'], account: accounts[0] });
```

## List Recent Eval Runs
```javascript
const env = 'a944fdf0-0d2e-e14d-8a73-0f5ffae23315';
const res = await fetch(`https://powervamg.us-il106.gateway.prod.island.powerapps.com/evalapi/copilotStudio/${env}/testRunsHistory?botid=b0346795-4876-f111-ab0e-70a8a5b1b8cc`, {
  headers: { Authorization: `Bearer ${token}` }
});
```

## Get Eval Run Details (incl. per-test-case queries/answers)
```javascript
const runId = 'bfe90f49-...';
const res = await fetch(`https://powervamg.us-il106.gateway.prod.island.powerapps.com/evalapi/copilotStudio/${env}/testRuns/${runId}/details?botid=b0346795-4876-f111-ab0e-70a8a5b1b8cc`, {
  headers: { Authorization: `Bearer ${token}` }
});
```

Each test case has:
- `queries[]` — per-turn conversation turns
- `queries[].query` — user input
- `queries[].answer` — agent response
- `queries[].executionState` — "Evaluated" or "Failed"
- `queries[].metrics.queryResponseMetrics[].properties` — relevance, completeness, abstention

## Launch New Conv Eval
```javascript
const res = await fetch(`https://powervamg.us-il106.gateway.prod.island.powerapps.com/evalapi/copilotStudio/${env}/testRuns?botid=${botId}`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ testSetId: '21b54c2b-a977-4b8a-a70c-168746d07464', testType: 1 })
});
```

## Poll Eval Completion
```javascript
const res = await fetch(`https://powervamg.us-il106.gateway.prod.island.powerapps.com/evalapi/copilotStudio/${env}/testRuns/${runId}/status?botid=${botId}`, {
  headers: { Authorization: `Bearer ${token}` }
});
// status: 0=Queued, 1=Running, 2=Completed, 3=Failed
```

## Known Issues
- Environment ID must be the raw GUID (`a944fdf0-...`), NOT the `Default-tenantId` format
- `stdin is not a tty` error when running in background mode — pipe `echo "" |` to workaround
- Do NOT publish while an eval is running — 422 error "another test run is in progress for this bot component"
