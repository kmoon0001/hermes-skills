# Eval Failure Triage Methodology

When an eval returns below target (typically <95% SR), categorize failures BEFORE making changes.

## Failure Categories

| Category | Symptom | Count Pattern | Fix Strategy |
|----------|---------|---------------|--------------|
| A - System Errors | "I hit a system error" | 5-10 failures | Fix action nodes, add fallback text |
| B - Misroutes | Welcome/generic response for domain Qs | 2-5 failures | Add trigger phrases to correct topic |
| C - Prompt Injection | cite:1, template vars, metadata in output | 1-3 failures | Sanitize output templates |
| D - Interactive Menus | Cards/menus instead of text answers | 15-25 failures | Text-first pattern (see below) |
| E - Grader Mismatch | Topic answers correctly but eval fails | 5-15 failures | Adjust response to match grader expectations |

## Category D — Text-First Pattern

The biggest failure category. Topics designed as interactive wizards return cards/menus
instead of text answers. Evals test single-response quality; real users want guided workflows.

**Fix: Add SendActivity with direct text answer BEFORE any interactive nodes.**

```yaml
nodes:
  - id: text_answer
    kind: SendActivity
    properties:
      activity: |
        <comprehensive text answer about the topic>

        Would you like me to walk you through the full workflow step by step?
    next:
      id: end_dialog

  - id: end_dialog
    kind: EndDialog
```

The interactive menu nodes stay in the topic but only fire when the user asks
for the guided workflow as a follow-up.

## Category B — Trigger Phrase Matching

Eval questions are phrased naturally. Topic trigger phrases must match.

Common gaps:
- "ensure HIPAA compliance" → topic only has "hipaa guardrail"
- "QM processes are HIPAA compliant" → topic has "is this hipaa compliant" (close but not exact)
- "workflow menu" → topic has "Choose a QM workflow" (different phrasing)

Fix: Add the exact eval question phrasing as trigger phrases.

## Category A — System Error Debugging

Topics throw system errors when:
1. Connected agent ID is invalid or unpublished
2. Connector auth expired
3. Action node input variables are null/empty
4. External API endpoint is down

Check order:
1. Verify connected agents are published (Overview → Agents section)
2. Check connector status (Tools section)
3. Review action node inputs in topic YAML
4. Add fallback text response after action node

## Post-Fix Verification

After fixing topics:
1. Publish the agent
2. Run eval (single-response, 100 cases)
3. Compare failure count and categories
4. If new failures appear, categorize them
5. Loop until target score reached

Per MS Learn evaluation framework: "The grader evaluates general quality —
accuracy, completeness, relevance, and helpfulness."

## Reference

- Eval results via UI: Copilot Studio → Evaluation → click result → Fail tab
- Topic GUIDs via Dataverse API: `botcomponents?$filter=_parentbotid_value eq '{botId}' and componenttype eq 9`
- Topic direct URL: `/environments/{envId}/bots/{botId}/adaptive/{topicGuid}`
