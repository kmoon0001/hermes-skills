# Topic Audit & Cleanup via Dataverse API

Workflow for systematically auditing and cleaning up Copilot Studio topics using the Dataverse REST API. Validated on QM Coach V2 (ea52ad9c) in Therapy AI Agents Dev (a944fdf0, orgbd048f00).

## When to Use

- Agent has 40+ topics and eval scores are declining
- Publish is crashing silently
- Agent returns empty responses ("--") in conversation evals
- Suspecting duplicate, stub, or broken topics

## Step 1: Get All Topics via Dataverse API

```javascript
// From authenticated browser session on the org page
const botId = 'YOUR_BOT_ID';
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
const url = `https://ORG.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name,botcomponentid,content&$filter=${encodeURIComponent(filter)}&$top=100`;
const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } });
const data = await resp.json();
// Returns: [{ name, botcomponentid, content }, ...]
```

## Step 2: Classify Each Topic

| Category | Content Length | Detection | Action |
|----------|---------------|-----------|--------|
| Empty | 0 chars | `content.length < 50` | DELETE |
| Stub | ~229 chars | Contains "under development" or "stub" | DELETE |
| Short/Broken | < 300 chars | Missing AdaptiveDialog or actions | DELETE |
| Duplicate | Any | Same trigger queries or same purpose as another | DELETE the less-developed one |
| Interactive Menu | Any | Returns cards/menus instead of text answers | Consider DELETE (hurts eval) |
| Clean | > 500 chars | Has AdaptiveDialog, actions, EndDialog | KEEP |

## Step 3: Identify Duplicates by Functional Area

Group topics by functional area and look for overlaps:

- Escalation topics (Escalate, Escalate QM Concern, QM Escalation Rules)
- HITL topics (HITL APPROVAL, QM - HITL Approval, QM - Human Review Gate)
- Intake topics (QM Intake, SNF - Clinical Intake, SNF - Therapy AI Intake)
- Driver topics (QM DRIVERS, QM Driver Analysis, QM ANALYSIS)
- Start/Reset topics (Start Over, Reset Conversation)
- Power BI topics (duplicate with different casing)

For each overlap group, keep the most developed topic and delete the rest.

## Step 4: Check for Broken References

Search all remaining topics for references to deleted topic names:

```javascript
const deletedNames = ['WORKFLOW MENU', 'Start Over', 'HITL APPROVAL', 'QM DRIVERS', 'QM Intake'];
for (const topic of remainingTopics) {
    const refs = deletedNames.filter(name => topic.content.includes(name));
    if (refs.length > 0) console.log(`${topic.name} references deleted: ${refs.join(', ')}`);
}
```

## Step 5: Delete via API

```javascript
const result = await p.evaluate(async (id) => {
    const resp = await fetch(`https://ORG.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
    });
    return { status: resp.status, ok: resp.ok };
}, topicId);
// 204 = success, 404 = already deleted
```

## Step 6: Republish and Verify

After deleting, republish via the overview page. If publish crashes, there are still broken topics — repeat the audit.

## Pitfalls

1. **Stub topics cause publish crashes** — Empty or stub topics (< 300 chars) make the Publish button fail silently. Always delete stubs before publishing.

2. **Interactive menu topics hurt eval scores** — Topics that return cards, wizards, or menus instead of text answers cause single-response eval failures. The agent's general knowledge gives better answers. Deleting these topics improves eval scores.

3. **"By agent" routing doesn't use trigger phrases** — Most custom topics use AI-based routing (By agent), not trigger phrase matching. Adding trigger phrases to remaining topics won't help if the agent can't find the topic.

4. **Topic references use internal names** — `cr917_agentu92bPc.topic.FacilityQMAnalysis` is the internal Dataverse reference, not the display name. If the topic is deleted, other topics referencing it will show "Selected topic is no longer available" errors.

5. **Don't try to fix Monaco via CDP** — If a topic is corrupted (0 chars after CDP injection), delete it and recreate manually. CDP cannot reliably edit Monaco editors.

6. **Conversation eval "Something went wrong" with "--" response** — This means the agent returned empty, not that the eval system errored. Usually caused by broken topic routing (references to deleted topics) or platform rate limiting after multiple eval runs.

## Results from QM Coach V2 Session

| Metric | Before | After |
|--------|--------|-------|
| Topics | 62 | 31 |
| Stubs deleted | 18 | 0 |
| Duplicates deleted | 10 | 0 |
| Empty topics deleted | 1 | 0 |
| Broken refs fixed | 3 | 0 |
| Single-response eval | 71% | 95% |
| Publish crash | Yes | No |
