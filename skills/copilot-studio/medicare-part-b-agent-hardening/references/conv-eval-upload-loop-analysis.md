# Conv Eval Upload-Loop Analysis (Jul 10 2026)

## Environment
- Bot: Medicare Part B Compliance Agent (b0346795)
- Environment: a944fdf0-0d2e-e14d-8a73-0f5ffae23315 (Therapy AI Agents Dev)
- Gateway: powervamg.us-il106.gateway.prod.island.powerapps.com
- Conv test set: 21b54c2b-a977-4b8a-a70c-168746d07464 (20 cases)

## Discovery Process

### Step 1: Check Recent Runs
```javascript
// Via gateway API with MSAL cache auth
const base = `${GW}/api/botmanagement/v2/environments/${ENV}/bots/${BOT_ID}/makerevaluations`;
const runs = await fetch(base + '?count=10', { headers: authHeaders() });
```

Ran scores:
- SR eval: 85%, 95% — acceptable
- Conv eval: 20%, 25%, 35% — consistently failing

### Step 2: Get Case Details
```javascript
const details = await fetch(`${base}/${runId}/details`, { headers: authHeaders() });
const cases = details.details.testCases;
```

### Step 3: Identify Pattern
Every case had consecutive turns where the agent returned the EXACT same message:
- "Please upload the X document for compliance audit processing"
- "What type of therapy document did you want reviewed?"

The user's follow-up turns provided document descriptions ("Here is the discharge summary...", "I've attached the report...") but the agent ignored them and re-asked for the file upload.

### Root Cause Confirmation
1. Question node with `entity: FilePrebuiltEntity` never completes without a file
2. Any ConditionGroup below the Question never executes
3. The GotoAction in elseActions just re-routes back to the same Question
4. This creates an infinite loop until the test times out or the user gives up

### Fix Applied
Changed all 6 doc topics from FilePrebuiltEntity to StringPrebuiltEntity + First(System.Activity.Attachments) check + .Content suffix on AI Builder binding.
See Fix #9 in medicare-part-b-agent-hardening skill.

### Iterative Debugging (Publish Error Chain)
When applying the fix, expect these errors in order if misapplied:
1. `MissingRequiredProperty: Entity` — entity was removed entirely instead of changed
2. `IncorrectTypeAssignment: expected String, got Record(Content:File...)` — SetVariable assigned First(System.Activity.Attachments) to String-typed Topic variable
3. `IncorrectTypeAssignment: expected File, got Record` — `.Content` suffix missing on AI Builder binding
4. YAML parse errors — caused by removing lines by index from split lists

**Correct path:** StringPrebuiltEntity + `=First(System.Activity.Attachments).Content` in the AI Builder input binding directly. No SetVariable needed. Edit via targeted string replace, never line-index removal.

## Gateway API Auth Pattern (Working)
```javascript
const { PublicClientApplication } = require('@azure/msal-node');
const { PersistenceCreator, PersistenceCachePlugin, DataProtectionScope } = require('@azure/msal-node-extensions');

const TENANT = '03cc92c3-986c-4cf4-ae27-1478cf99d17f';
const CLIENT = '51f81489-12ee-4a9e-aaae-a2591f45987d';
const GW = 'https://powervamg.us-il106.gateway.prod.island.powerapps.com';
const ENV = 'a944fdf0-0d2e-e14d-8a73-0f5ffae23315';
const CACHE = path.join(os.homedir(), '.copilot-studio-cli', 'manage-agent.cache.json');

async function getToken() {
  const p = await PersistenceCreator.createPersistence({
    cachePath: CACHE, dataProtectionScope: DataProtectionScope.CurrentUser,
    serviceName: 'copilot-studio-cli', accountName: 'manage-agent', usePlaintextFileOnLinux: true
  });
  const app = new PublicClientApplication({
    auth: { clientId: CLIENT, authority: `https://login.microsoftonline.com/${TENANT}` },
    cache: { cachePlugin: new PersistenceCachePlugin(p) }
  });
  const accs = (await app.getTokenCache().getAllAccounts()).filter(a => a.tenantId === TENANT);
  const r = await app.acquireTokenSilent({
    scopes: ['api://96ff4394-9197-43aa-b393-6a41652e21f8/.default'],
    account: accs[0]
  });
  return r.accessToken;
}
```

## Key Headers for Gateway API
```javascript
function headers(bearer) {
  return {
    authorization: 'Bearer ' + bearer, accept: 'application/json', 'content-type': 'application/json',
    referer: 'https://copilotstudio.microsoft.com/',
    'x-ms-user-agent': 'PVA-Portal/1.0.0', 'x-cci-applicationsource': 'Web',
    'x-cci-tenantid': TENANT, 'x-cci-bapenvironmentid': ENV,
    'x-cci-organizationid': 'bd048f00-0d2e-e14d-8a73-0f5ffae23315',
    'x-ms-client-principal-id': '700a4462-830f-4df4-96f2-2627f16fbc86',
    'x-cci-cdsbotid': BOT_ID, 'x-cci-botid': BOT_ID,
    'x-ms-client-session-id': crypto.randomUUID(),
    'x-ms-client-request-id': crypto.randomUUID(),
  };
}
```

## Conv Eval Score Reporting
When analyzing Conv evals, the platform-reported score may differ from strict grading:
- Platform reports aggregated pass/fail per-test-case (some "pass" cases still have com=? and fail strict grading)
- For accurate reporting: count cases where EVERY turn has rel=Yes AND com=Yes AND abs=No
