# Topic Cleanup via Dataverse API

## Overview

Delete duplicate/overlapping topics directly via the Dataverse REST API. Faster and more reliable than UI-based deletion.

## Prerequisites

- Authenticated browser session on the Dataverse org (e.g., `orgbd048f00.crm.dynamics.com`)
- Bot ID known

## Step 1: Get All Topic GUIDs

```javascript
const botId = 'ea52ad9c-8233-f111-88b3-6045bd09a824';
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
const url = `https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name,botcomponentid,content&$filter=${encodeURIComponent(filter)}&$top=100`;

const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } });
const data = await resp.json();
// Returns: [{ name, botcomponentid, content }, ...]
```

**Key**: Property is `_parentbotid_value` NOT `botid`. `componenttype=9` for topics.

## Step 2: Analyze for Overlaps

Group topics by functional area based on name patterns:
- Escalation/HITL: "escalat", "hitl", "human review"
- HIPAA/Compliance: "hipaa", "compliance", "safety"
- QM Drivers/Analysis: "driver", "analysis", "trend"
- Resident/Submission: "resident", "intake", "submission"
- Documentation: "document", "classif", "validat"
- Workflow/Menu: "workflow", "menu", "orchestrat"

Look for:
- Exact duplicates (same topic, different casing) — e.g., "Power BI - Run a query" vs "Power BI - Run a Query"
- Functional duplicates (different names, same purpose) — e.g., "HITL APPROVAL" vs "QM - HITL Approval"
- Interactive menu topics causing eval failures — these should be merged or deleted

## Step 3: Delete via API

```javascript
const topicId = '94492644-9856-f111-bec6-7ced8d3b6116';
const resp = await fetch(`https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents(${topicId})`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
});
// Success: 204 No Content
```

## Step 4: Verify Deletion

```javascript
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9 and (contains(name,'HIPAA'))`;
// Or just count all remaining:
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
```

## Step 5: Publish

After deletions, MUST republish the agent. Navigate to overview → click Publish.

## Validated: QM Coach V2 (June 19, 2026)

- 10 duplicate topics deleted in one batch
- 62 → 52 topics
- All deletions returned 204 (success)
- Single-response eval improved from 71% → 95%

## Pitfalls

1. **Conversation eval breaks after topic deletion** — If deleted topics were referenced by conversation test cases, the conversation eval returns 0% with "Error" on all cases. The agent returns empty responses ("--") because it can't route to deleted topics. FIX: Republish after deletion (re-indexes topic list), then re-run conversation eval.

2. **"By agent" topics use AI routing, not trigger phrases** — Most custom topics in modern agents use "By agent" trigger type, which means the agent's AI picks the topic based on the topic's description, NOT keyword matching. Adding trigger phrases to "By agent" topics has no effect. The AI routes based on topic name + description.

3. **Must navigate to Dataverse ORG URL, not Copilot Studio URL** — The Dataverse API calls must go to `orgbd048f00.crm.dynamics.com`, NOT `copilotstudio.microsoft.com`. The Copilot Studio URL returns HTML (login page) for API calls.

4. **Chrome restart needed between large operations** — After querying topics + deleting + publishing, Chrome can become unresponsive (CDP timeouts). Restart Chrome with `taskkill //F //IM chrome.exe` then relaunch with `--remote-debugging-port=9223 --user-data-dir=C:\Users\kevin\AppData\Local\Google\Chrome\User Data`.

5. **Eval triggering path** — To trigger a NEW eval (not just view old results):
   - Navigate to evaluation page
   - Click the TEST SET ROW (e.g., "20 test cases • Conversation") — NOT the Evaluate button in the results list
   - This opens the test set config page with "Save" and "Evaluate" buttons at the bottom
   - Click "Evaluate" to start a new run
   - The "Evaluate" buttons in the results list only open OLD results
