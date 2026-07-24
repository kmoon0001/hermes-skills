# Phase 4 — Agent Instructions

## Overview

The instructions component (type 15) is the highest-leverage single component. It defines role, scope, routing rules, output contracts, and guardrails. Stored as `GptComponentMetadata` YAML in the `data` field.

## View Current Instructions

```bash
TOKEN=$(az account get-access-token --resource "https://{org}.crm.dynamics.com/" --query accessToken -o tsv)
curl -s "https://{org}.crm.dynamics.com/api/data/v9.2/botcomponents?\$filter=_parentbotid_value%20eq%20{botId}%20and%20componenttype%20eq%2015&\$select=data,name" \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/json"
```

## Inject Description (Overview Page)

The description shown on the Copilot Studio overview page is the `description:` field in the type 15 YAML:

```yaml
kind: GptComponentMetadata
displayName: My Agent Name
description: Routes users to discipline-specific clinical scenarios and competency tracking based on user intent.
instructions: |-
  # SCOPE
  You are the ...
```

**Patch:**
```python
new_data = current_data.replace(
    'description: <old text>',
    'description: <new text>'
)
# PATCH botcomponents({id}) with {"data": new_data}
```

**Component ID for Competency Check Gamer**: `7af0c709-eda9-4aa9-9af1-c9249e9cdc23`

## Instructions Template (Proven Pattern)

```yaml
kind: GptComponentMetadata
displayName: Agent Name
description: One-line description shown on overview page.
instructions: |-
  # SCOPE
  [What agent DOES and DOES NOT do — one paragraph]

  # ROLE
  [Agent persona and expertise — one paragraph]

  # ROUTING RULES
  - Route A — Document Review: [when user provides document]
  - Route B — General Question: [no document, conceptual Q]
  - Route C — Missing Document: [user asks for review but no doc]
  - Route D — Procedural: [how to use the agent]

  # ROUTE B OUTPUT CONTRACT
  Answer directly from approved sources. Plain text, max 3 bullets or 4 sentences.

  # ROUTE D OUTPUT CONTRACT
  Answer the workflow question directly. 2-4 sentences.

  # EVALUATION CONTEXT — DIRECT ANSWER REQUIRED
  ## DATA-SPARSE PROMPTS
  When prompt asks without providing text: answer directly. Do NOT refuse or hedge.
  ## DATA-RICH PROMPTS
  When user provides detailed data: follow normal workflow, complete analysis.

  # GUARDRAILS
  G1. Source Grounding: Use only approved sources
  G2. Review Scope: Only content in current conversation
  G3. No Hallucination: Report only what is present/missing/required
  G4. Citation: Every finding includes inline citation
  G5. Advisory: Educational output; requires independent clinical review
  G6. AI Transparency: Disclose AI-generated status
  G7. PHI Handling: Ignore and never repeat patient identifiers

responseInstructions: Respond concisely. Use formatting when it improves clarity.
aISettings:
  model:
    modelNameHint: GPT5Chat
```

## Key Rules from Eval Analysis

| Rule | Why |
|------|-----|
| 2000-6000 chars max | >8000 chars causes eval slowdown |
| No contradictory caps | "Under 800 chars" + "prioritize completeness" = Conv drops 20pp |
| No "No headers or markdown" | Blocks structured formatting; +10-15pts removing it |
| EVALUATION CONTEXT block at top | Prevents abstention on sparse queries; +5-15pts |
| Route D expansion early in doc | Buried rules don't reach catch-all path |
| Conditional response format | Structured for audits, plain for general Q&A |
| responseInstructions must not contradict | Settings box overrides main instructions |

## Settings (in `configuration` field on bot)

```json
{
  "aISettings": {
    "useModelKnowledge": true,
    "isFileAnalysisEnabled": true,
    "isSemanticSearchEnabled": true,
    "contentModeration": "High",
    "optInUseLatestModels": false
  }
}
```

PATCH via `bots({id})` with `{"configuration": "<json>"}`.

**Critical**: `authenticationMode: 0` (None) prevents auth gate from blocking general questions. 40-67% of SR failures are caused by auth gate.

## Fix Empty Conversation Starters

Empty starter `conversationStarters: [{}]` blocks publishing. Fix:

```python
old = "conversationStarters:\r\n  - {}"
new = "conversationStarters:\r\n  - title: Get Started\r\n    text: How can I test my clinical competency?"
fixed_data = data.replace(old, new)
# PATCH component
```
