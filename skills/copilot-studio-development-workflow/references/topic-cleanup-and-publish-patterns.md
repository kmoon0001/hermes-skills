# Topic Cleanup & Publish Crash Patterns

Session: June 19, 2026 — QM Coach V2 (a944fdf0, bot ea52ad9c)
Agent went from 62 → 30 topics, eval 71% → 95%.

## Publish Crash Root Cause

**Symptom:** Clicking Publish crashes silently — no error dialog, page may show "Something went wrong" or just hang.

**Root cause:** Empty or malformed topics (0 chars, missing `kind: AdaptiveDialog`).

**Detection:** Open browser console (CDP `page.on('console')`) and look for:
```
TypeError: Cannot read properties of undefined (reading '$kind')
  at makerx/static/js/module/607.e0254530.chunk.js
```

**Fix:** Delete the corrupted topic via Dataverse API:
```javascript
await fetch(`https://org.crm.dynamics.com/api/data/v9.2/botcomponents(${topicId})`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
});
```

**Common causes:**
- CDP Monaco injection corruption (writes to accessibility textarea, not editor model)
- Partial topic creation (user started creating but didn't finish)
- Typo-named duplicates (e.g., "HIPPA Guardrail" vs "HIPAA Guardrail")

## Stub Topic Detection

**Pattern:** Topics with ~229 chars that contain:
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent: {}
  actions:
    - kind: SendActivity
      id: sendActivity_stub
      activity: This workflow is under development.
```

**How to detect via Dataverse API:**
```javascript
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
const url = `https://org.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name,botcomponentid,content&$filter=${encodeURIComponent(filter)}&$top=100`;
```
Then check: `content.length < 300 && content.includes('under development')`

**Action:** Delete all stubs. They add no value, cause eval failures, and may interfere with publishing.

## Interactive Menu Topics Hurt Eval

**Pattern:** Topics that return card-based menus, wizards, or interactive prompts instead of text answers.

**Symptom:** Single-response eval shows "Fail" with the agent response being a menu/card instead of a text answer.

**Examples from QM Coach V2:**
- Email Generator (returned email template menu)
- Escalation Matrix (returned severity selection card)
- Workflow Menu (returned interactive workflow picker)
- Severity Classifier (returned classification menu)

**Fix options:**
1. **Delete the topic** — agent answers from general knowledge (often better)
2. **Restructure** — add text answer first, interactive follow-up as optional

**Impact:** Removing 20 interactive menu topics was the primary factor in the 71% → 95% eval improvement.

## Topic Overlap Analysis

**Method:** Query all topics via Dataverse API, group by functional area:
1. Escalation/HITL
2. HIPAA/Compliance
3. QM Drivers/Analysis
4. Resident Submission/Intake
5. Documentation
6. Power BI/Dashboards
7. Workflow/Menu
8. Conversation Management

**Duplicate signals:**
- Same topic with different casing ("Power BI - Run a query" vs "Power BI - Run a Query")
- Same topic with different prefixes ("QM - HITL Approval" vs "HITL APPROVAL")
- Topic A references Topic B in its content, but Topic B was deleted

## Bulk Topic Deletion via Dataverse API

**Approach:** Use Playwright CDP to connect to the Dataverse org page, then call the API directly:

```javascript
// Navigate to org to establish auth
await page.goto('https://org.crm.dynamics.com', { waitUntil: 'domcontentloaded' });
await sleep(8000);

// Delete topic
const result = await page.evaluate(async (id) => {
    const resp = await fetch(`https://org.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
    });
    return { status: resp.status, ok: resp.ok };
}, topicId);
```

**Status codes:**
- 204 = success
- 404 = already deleted or wrong GUID
- 400 = invalid request

**After deletion:** Must republish the agent for changes to take effect.

## Key Metric: Topic Count vs Eval Score

| Agent | Topics | SR Eval | Notes |
|-------|--------|---------|-------|
| QM Coach V2 (before) | 62 | 71% | 18 stubs, 10 duplicates, interactive menus |
| QM Coach V2 (after) | 30 | 95% | Clean topics only |

**Lesson:** Fewer, cleaner topics beat more topics with stubs/duplicates/menus.
