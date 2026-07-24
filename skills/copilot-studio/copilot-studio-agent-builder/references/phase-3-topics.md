# Phase 3 — Topics

## Topic Template (Standard Pattern)

```yaml
kind: AdaptiveDialog
modelDescription: What this topic handles — helps AI routing select the correct topic.
beginDialog:
  kind: OnRecognizedIntent
  intent:
    displayName: Topic Display Name
    triggerQueries:
      - Natural language trigger phrase 1
      - Natural language trigger phrase 2
      - (5-10 phrases recommended)
  actions:
    - kind: SearchAndSummarizeContent
      id: search_default
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Specific instruction for this topic
        - Another instruction
      allowLatencyMessage: false
      responseCaptureType: FullResponse   # CRITICAL — missing = incomplete eval responses
      fileSearchDataSource:
        searchFilesMode:
          kind: SearchAllFiles
      knowledgeSources:
        kind: SearchAllKnowledgeSources
    - kind: SendActivity
      id: send_answer
      activity: =Topic.Answer
    - kind: EndDialog
      id: end_topic
      clearTopicQueue: true
```

## Critical Topic Rules

| Rule | Why |
|------|-----|
| `EndDialog` + `clearTopicQueue: true` on EVERY topic | Prevents context bleed between topics |
| NO `Question` nodes in audit/answer topics | Kills SR eval — grader sees question, not answer |
| `responseCaptureType: FullResponse` on every SASC | Missing = truncated eval responses |
| `allowLatencyMessage: false` | Prevents "searching..." from being counted as answer |
| `modelDescription` present + unique on every topic | Helps AI routing select correct topic |
| 5-10 trigger phrases per topic | Natural language, no robot phrases, no overlaps |
| Topic names under 50 chars | Truncated in UI if longer |

## Knowledge Source Binding (SASC Fix)

When a topic has `SearchAndSummarizeContent`, ensure it's bound to knowledge sources:

```yaml
# ✅ CORRECT — searches all files + all knowledge sources
fileSearchDataSource:
  searchFilesMode:
    kind: SearchAllFiles
knowledgeSources:
  kind: SearchAllKnowledgeSources

# ❌ WRONG — restricts to specific files, blocks all others
fileSearchDataSource:
  searchFilesMode:
    kind: SearchSpecificFiles
    fileNames: [file1.pdf, file2.pdf]

# ❌ WRONG — leans on model memory, ignores KBs
applyModelKnowledgeSetting: true   # (without the above blocks)
```

## Model Description Rules

| Rule | ✅ Good | ❌ Bad |
|------|---------|--------|
| What the topic DOES | Reviews therapy progress notes for Medicare compliance | Contains SASC node with EndDialog |
| Unique across all topics | Each topic has distinct description | Two topics say "Handles document review" |
| 1-3 sentences | Scope, purpose, outcome | One word or entire paragraph |
| No implementation details | Don't mention SASC, BeginDialog, variables | "Uses SearchAndSummarizeContent to search" |

## Create a New Topic via API (POST)

```python
body = {
    "name": "Progress Report Review",
    "schemaname": f"{prefix}.ProgressReportReview",
    "componenttype": 9,
    "_parentbotid_value@odata.bind": f"/bots({botId})",
    "data": topic_yaml,  # Full YAML per template above
}
# POST to /api/data/v9.2/botcomponents
# Response: 204, ID in OData-EntityId header
```

**CRITICAL**: `_parentbotid_value@odata.bind` format, NOT `_parentbotid_value` as GUID.

## Edit Existing Topic (PATCH)

```python
# Pull current data
GET /botcomponents({id})?$select=data

# Modify YAML
new_data = current_data.replace(old_string, new_string)

# PATCH
PATCH /botcomponents({id}) with {"data": new_data}
```

**System topics**: PATCHing system topic data (OnError, OnConversationStart, etc.) returns 204 but BREAKS publish. Use UI code editor for system topics only.

## Conversational Boosting / Fallback

This is the `OnUnknownIntent` catch-all (priority -1, schema `{prefix}.topic.Search`). Must have:

```yaml
- kind: SearchAndSummarizeContent
  id: search
  userInput: =System.Activity.Text
  additionalInstructions: |-
    Provide specific requirements with inline citations. Never fabricate.
  allowLatencyMessage: false
  responseCaptureType: FullResponse
  fileSearchDataSource:
    searchFilesMode:
      kind: SearchAllFiles
  knowledgeSources:
    kind: SearchAllKnowledgeSources
- kind: ConditionGroup
  conditions:
    - condition: =Not(IsBlank(Topic.Answer))
      actions:
        - kind: SendActivity
          activity: =Topic.Answer
        - kind: EndDialog
  elseActions:
    - kind: SendActivity
      activity: I can help with [capabilities]. Describe what you need.
    - kind: EndDialog
```

NEVER leave SASC→EndDialog without SendActivity (silent failure for unmatched queries).
