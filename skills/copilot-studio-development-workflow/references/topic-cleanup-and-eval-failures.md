# Topic Cleanup and Eval Failure Patterns

## Conversation Eval Failures After Topic Deletion (Jun 19, 2026)

When conversation evals return 0% with "Something went wrong while evaluating this test case" and agent response "--", the cause is usually **broken topic routing from deleted topics**, NOT a platform error. Single-response evals may still work (95%) because they don't require multi-turn routing.

**Diagnosis:** Check if recently deleted topics were referenced by remaining topics via BeginDialog/Redirect. The eval system tries to route through the conversation flow and hits dead references.

**Fix:** Remove broken references from remaining topics (menu options + condition blocks), then republish. If CDP injection fails to save, delete the broken topic via Dataverse API and recreate it manually.

## Topic Cleanup Workflow

When consolidating duplicate topics:
1. Query Dataverse API for all topics: `GET /botcomponents?$filter=componenttype eq 9`
2. Group by functional area (escalation, HIPAA, drivers, etc.)
3. Identify duplicates by name similarity and content overlap
4. Before deleting, search ALL remaining topics for references to each candidate
5. Delete via Dataverse API: `DELETE /botcomponents({id})` → 204 success
6. Fix any remaining topics that referenced deleted ones (manual code editor paste)
7. Republish to re-index topic routing
8. Run both single-response AND conversation evals to verify

## BeginDialog Reference Format

Topics reference other topics via:
```yaml
- kind: BeginDialog
  id: beginDialog_TopicName
  dialog: cr917_agentu92bPc.topic.InternalTopicName
```

The `InternalTopicName` is NOT the display name. It's the `componentName` from the topic's `mcs.metadata` block. To find the correct internal name, query the topic's content via Dataverse API and extract the `componentName` field.

## "By Agent" Topics Use AI Routing

Topics triggered "By agent" use AI-based routing based on the topic's description and name, NOT trigger queries. Adding trigger phrases to a "By agent" topic has NO effect on routing. The agent's LLM matches user questions to topics based on semantic similarity.

After deleting topics, always republish to force the agent to re-index its topic routing.
