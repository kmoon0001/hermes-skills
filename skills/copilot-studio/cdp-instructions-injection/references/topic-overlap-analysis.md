# Topic Overlap Analysis & Cleanup

## When to Run This

When an agent has 40+ custom topics, run overlap analysis before eval optimization. Duplicate topics cause routing confusion and inflate eval failures.

## Analysis Pattern

1. Get all topics via Dataverse API (`componenttype eq 9`, `$top=100`)
2. Group by functional area using name-based heuristics
3. Identify exact duplicates (case variants, prefix variants)
4. Identify functional overlaps (same trigger purpose)
5. For each overlap group, recommend KEEP (more mature) vs DELETE
6. Delete via Dataverse API (batch, 500ms pause between)
7. Check remaining topics for broken references to deleted topics
8. Fix broken references before publishing

## Common Duplicate Patterns

| Pattern | Example | Keep |
|---------|---------|------|
| Case variant | "Power BI - Run a query" vs "Power BI - Run a Query" | Newer |
| Prefix variant | "HITL APPROVAL" vs "QM - HITL Approval" | QM-prefixed (more specific) |
| Functional duplicate | "Start Over" vs "Reset Conversation" | Clearer name |
| Interactive menu vs orchestrator | "WORKFLOW MENU" vs "QM Orchestrator" | Orchestrator |
| Generic vs specific | "QM DRIVERS" vs "QM Driver Analysis" | More specific |

## Grouping Heuristics

Group topics by keyword matching:
- Escalation/HITL: `escalat`, `hitl`, `human review`, `approval`
- HIPAA/Compliance: `hipaa`, `compliance`, `safety`, `critical risk`
- QM Analysis: `driver`, `analysis`, `trend`, `facility qm`
- Resident/Intake: `resident`, `intake`, `submission`, `outlier`
- Documentation: `document`, `classif`, `validat`, `extract`, `normalize`
- Workflow/Menu: `workflow`, `menu`, `orchestrat`, `action plan`
- Conversation Mgmt: `start over`, `reset`, `thank`, `dor`, `publish`

## Broken Reference Detection

After deleting topics, search remaining topics for references to deleted names:

```javascript
const deletedNames = ['WORKFLOW MENU', 'Start Over', 'HITL APPROVAL'];
for (const topic of remainingTopics) {
    for (const name of deletedNames) {
        if (topic.content.includes(name)) {
            console.log(`${topic.name} -> references deleted: ${name}`);
        }
    }
}
```

Common reference types:
- Menu items in ClosedListEntity (orchestrator menus)
- BeginDialog calls (topic-to-topic routing)
- Condition blocks checking `Topic.routeChoice`

## Fix Sequence

1. Delete duplicates via Dataverse API
2. Search remaining topics for broken references
3. Fix references (remove menu items, condition blocks, BeginDialog calls)
4. Fix via Monaco code editor (manual paste — API PATCH returns 400 on content)
5. Republish
6. Run eval

## Results (QM Coach V2, Jun 19, 2026)

- Started: 62 topics, 71% eval
- Deleted: 10 duplicate/overlapping topics
- Result: 52 topics, 95% single-response eval (+24 points)
- Conversation eval hit 0% due to broken QM Orchestrator reference to deleted "QM Intake"
