# Stale BeginDialog References After Topic Reorganization

## The Problem

When Copilot Studio topics are reorganized (renamed, merged, deleted), the Document Upload Intake topic and Conversation Start topic may still reference old topic names via `BeginDialog` + `dialog:` fields. These BeginDialog calls silently fail — the bot doesn't error visibly but falls through to the Fallback (OnUnknownIntent) topic, producing generic responses instead of the expected document review flow.

## Detection

Query Dataverse for the old topic names referenced in BeginDialog:

```
GET /botcomponents?$filter=_parentbotid_value eq '<botId>' and name eq '<OldTopicName>'
```

If no results, the target topic doesn't exist.

## Fix

Replace the BeginDialog block with a SendActivity asking for document upload + EndDialog. This lets the user's natural language trigger phrases route subsequent turns to the correct topic.

### Before (broken):
```yaml
- id: condition_evaluation_poc
  condition: =Topic.DocumentTypeSelection = '...'
  actions:
    - kind: BeginDialog
      id: beginDialog_evaluation_poc
      dialog: cr917_CopyTherapyDocuementationFeedbackAg.topic.EvaluationAssessmentandPlanofCare
```

### After (working):
```yaml
- id: condition_evaluation_poc
  condition: =Topic.DocumentTypeSelection = '...'
  actions:
    - kind: SendActivity
      id: sendActivity_upload_evaluation
      activity: Please upload the Evaluation and POC document for compliance review processing.
    - kind: EndDialog
      id: endDialog_evaluation
```

## Root Cause

The bot topics were reorganized from a hub-and-spoke model (one ConvStart menu → routes to 6 child review topics) to a flat NLU-intent model (each review query matches directly to its own topic via trigger phrases). The old child topics were deleted but the Document Upload Intake topic's routing was not updated.
