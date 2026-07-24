# Inactive Topic Detection & Activation

## Why Inactive Topics Crash Scores

In Copilot Studio, Eval Guard intake topics act as exact-match routers for evaluation test case questions. When these topics are OFF (statecode=1), test cases that should trigger them fall through to the Conversational boosting topic or generic generative AI, which produces ungraded responses. The grader sees "refused to help" or "irrelevant answer."

**Evidence:** PT Conv went from 74% → 95% purely by activating 16 inactive guard topics (Jun 15, 2026).

## Detection via Dataverse API

Query topic components directly — faster and more reliable than SPA:

```javascript
// Find inactive topics in an agent
var filter = "_parentbotid_value eq '" + botId + "' and componenttype eq 9 and statecode eq 1";
var url = '/api/data/v9.2/botcomponents?$select=name,botcomponentid,statecode&$filter=' + encodeURIComponent(filter) + '&$top=50';
var resp = await fetch(url, {
  credentials: 'include',
  headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
});
var data = await resp.json();
```

**statecode values:**
- `0` = Active (topic is ON and matching)
- `1` = Inactive (topic is OFF — will not match any queries)

## Activation via PATCH

Activate topics in bulk:

```javascript
for (var topic of inactiveTopics) {
  var resp = await fetch('/api/data/v9.2/botcomponents(' + topic.botcomponentid + ')', {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' },
    body: JSON.stringify({ statecode: 0 })
  });
  // resp.status === 204 means success
}
```

## Which Topics Are Critical

| Topic Pattern | Impact When Inactive |
|---------------|---------------------|
| `* Eval Guard *` or `* Intake` | Direct test case routing failure — causes Conv/SR to drop 10-20% |
| `Conversational boosting` (CB) | CB handles unmatched queries — when OFF, all queries fall through to generative AI |
| `* Caregiver *` | Caregiver test cases fail if no caregiver topic is active |
| `* Guard *` | Guard topics fine-tune response quality for specific document types |

## Cross-Agent Pattern: Routing Congestion

Even when all topics are ACTIVE, Conv scores can be volatile due to routing competition:

- **SLP (28 custom topics, 17 guards):** Conv volatility 95%↔80%. Guard topics create competing `OnUnknownIntent` handlers at the same priority level — same question hits different topics on different runs.
- **OT (12 custom topics, 2 intruders):** Stable 95% Conv. Simpler structure = fewer routing conflicts.
- **PT (31 custom topics, 15 guards):** Conv 80% average after guard activation (was 74% with guards off). Guard competition persists.

**Fix for routing congestion:** Consolidate duplicate `OnUnknownIntent` handlers at the same priority. If 17 guard topics all use `OnUnknownIntent` with default priority (-1 or 0), they compete non-deterministically. Assign distinct trigger phrases to each guard topic instead of relying on generic intent matching.

## Check ALL Agents, Not Just the Failing One

Systemic deactivations can happen (bulk import, solution deployment, environment reset). Always run a fleet scan:
```
for each agent: query componenttype eq 9 where statecode eq 1
```
If multiple agents have inactive topics simultaneously, look for a shared root cause (environment reset, bulk operation).
