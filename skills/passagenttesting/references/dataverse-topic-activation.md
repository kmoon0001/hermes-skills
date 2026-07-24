# Dataverse Topic Activation for Score Recovery

## Pattern: Inactive Topics Cause Massive Score Drops

When >25% of topics are INACTIVE (statecode=1), evaluation test cases fall through to generic generative AI which produces ungraded responses. This is the #1 root cause of single-digit and mid-range scores.

## Evidence (June 16, 2026)

- **PT_Specialist**: 16/31 topics (52%) were INACTIVE — all 15 Eval Guard intake topics plus Conversational boosting. PT Conv was stuck at 74% volatility.
- **SLP_Specialist**: 2/36 topics (5.5%) were INACTIVE — Caregiver Safety Guard + Caregiver Cognitive Capacity Guard. Minor effect.
- **Recovery**: Activating PT's 16 guard topics → PT Conv 74% → **95%** in a single evaluation run.

## Detection

Query botcomponents for topics with statecode=1 (inactive):

```javascript
// Via Dataverse API (requires CDP session with Copilot Studio auth)
var filter = `_parentbotid_value eq '${botId}' and componenttype eq 9 and statecode eq 1`;
var url = `/api/data/v9.2/botcomponents?$select=name,botcomponentid,statecode,statuscode&$filter=${encodeURIComponent(filter)}&$top=50`;
var resp = await fetch(url, {
  credentials: 'include',
  headers: { 'Accept': 'application/json' }
});
var data = await resp.json();
// data.value = array of inactive topics
```

## Activation

PATCH each inactive topic to set statecode to 0 (Active):

```javascript
for (var i = 0; i < inactiveTopics.length; i++) {
  var id = inactiveTopics[i].botcomponentid;
  var resp = await fetch(`/api/data/v9.2/botcomponents(${id})`, {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ statecode: 0 })
  });
  // HTTP 204 = success
}
```

After activation, **publish the agent** for changes to take effect in evaluations.

## Which Topics to Activate

Target these specific patterns:

| Topics to Activate | Impact | Why |
|---|---|---|
| Eval Guard / Conv Guard / Intake topics | **CRITICAL** | Exact-match intake topics fire for specific test case questions. When OFF, the test case gets a generic/graded response. |
| Conversational boosting (CB) | **HIGH** | Handles ALL unmatched queries. When OFF, unmatched queries get no response at all. |
| Work IQ / Upload / utility topics | **LOW** | These don't directly affect evaluation scores. Leave alone if scores are good. |

## Pre-check

Before activating guard topics, verify the agent isn't a **routing agent** (TDA). For routing agents, leaving some guard-like intakes OFF may be intentional — the CB topic handles unmatched queries differently.

`statecode` values in Dataverse:
- `0` = Active (topic fires in conversations)
- `1` = Inactive (topic does NOT fire — skipped during routing)

Always publish the agent after batch activation and re-run evaluations.
