# Stale BeginDialog IDs

## Symptom
User selects a document type in the intake/routing topic (Document_Upload_Intake or Conversation_Start). The agent errors instead of routing to the correct audit topic. The error fires On_Error, not Fallback.

## Root Cause
The `dialog:` field in a `BeginDialog` action node stores a fixed Dataverse component ID:

```yaml
dialog: cr917_CopyTherapyDocuementationFeedbackAg.topic.RecertificationUPOTReview
```

If the target topic was renamed, re-imported, or the solution was migrated, the component ID changes. The stored ID becomes stale.

## How to Identify
1. Open the intake topic (Document_Upload_Intake or Conversation_Start) in Copilot Studio UI
2. Look at the **Go to another topic** action nodes
3. If one shows "Unknown" or a stale-looking topic name, the ID is stale
4. Alternatively, cross-reference the `dialog:` value against the actual topic list in the same agent

## Fix (UI Only — Cannot be done in YAML)
1. Open the intake/routing topic
2. Find the failing **Go to another topic** action node
3. Click the topic picker dropdown
4. Re-select the correct target topic from the list
5. Save the topic
6. Publish

## Prevention Checklist
- After any solution import: verify all BeginDialog references
- After renaming a topic: verify all BeginDialog references
- After cloning an agent: verify all BeginDialog references
- When a user reports "I said X but got an error": check Document_Upload_Intake and Conversation_Start first

## Related Topics Affected
All document-type routing branches in:
- `Document_Upload_Intake.yml` (ClosedListEntity with 7 items + BeginDialog routes)
- `Conversation_Start.yml` (ClosedListEntity with 6 items + BeginDialog routes)

Each branch uses a hard-coded Dataverse topic ID. Any of them may go stale independently.
