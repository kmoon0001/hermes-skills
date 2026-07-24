# Topic Deduplication via Dataverse API

## Methodology

### Step 1: Query All Topics
```javascript
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
const url = `https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name,botcomponentid,content&$filter=${encodeURIComponent(filter)}&$top=100`;
```

### Step 2: Group by Functional Area
Group topic names by keyword matching:
- Escalation: "escalat", "hitl", "human review"
- HIPAA: "hipaa", "compliance", "safety", "critical risk"
- Drivers: "driver", "analysis", "trend"
- Intake: "resident", "intake", "submission", "outlier"
- Documentation: "document", "classif", "validat", "extract"
- Workflow: "workflow", "menu", "orchestrat", "action plan"

### Step 3: Identify Duplicates
Types:
1. **Exact duplicates** — same name, different casing ("Power BI - Run a query" vs "Power BI - Run a Query")
2. **Semantic duplicates** — different names, same purpose ("HITL APPROVAL" vs "QM - HITL Approval" vs "QM - Human Review Gate")
3. **Subset duplicates** — one topic is a subset of another ("QM Intake" vs "SNF - Clinical Intake Handoff Router")

### Step 4: Keep/Delete Decision
- Keep the QM-specific version over generic ("QM - HITL Approval" > "HITL APPROVAL")
- Keep the more developed version (more actions, more trigger queries)
- Keep the newer version when both are equivalent
- Keep system topics and connected agents always

### Step 5: Cross-Reference Check
Before deleting, check remaining topics for references to topics being deleted:
```javascript
const deletedNames = ['WORKFLOW MENU', 'Start Over', 'QM Intake'];
for (const topic of remainingTopics) {
  for (const name of deletedNames) {
    if (topic.content?.includes(name)) {
      // This topic needs to be fixed before publishing
    }
  }
}
```

### Step 6: Batch Delete
```javascript
for (const topic of toDelete) {
  const result = await page.evaluate(async (id) => {
    const resp = await fetch(`https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, {
      method: 'DELETE',
      credentials: 'include',
      headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
    });
    return { status: resp.status, ok: resp.ok };
  }, topic.id);
}
```

### Step 7: Fix Cross-References
Open each referencing topic via direct GUID URL, open code editor, remove broken menu options and condition blocks, save.

### Step 8: Publish and Eval
Republish the agent, then run eval to verify improvement.

## Results: QM Coach V2
- Before: 62 topics, 71% eval (29 failures)
- After: 52 topics (10 deleted), 95% eval (5 failures)
- Improvement: +24 percentage points

## Key Insight: "By Agent" Routing
Most custom topics use AI-based routing (trigger type "By agent"), NOT trigger phrases. The agent selects topics based on topic descriptions and intent matching. This means:
- Adding trigger phrases to remaining topics won't help much
- The agent's topic list is what matters — removing duplicates reduces routing confusion
- After deletions, the agent naturally reroutes to the remaining topics
