---
name: copilot-studio-add-adaptive-card
description: Add AdaptiveCardPrompt node to Copilot Studio topics for display, input forms, and confirmation flows.
category: copilot-studio
---

# Add Adaptive Card

Add AdaptiveCardPrompt node to Copilot Studio topics. Use for all card scenarios: display-only, input forms, confirmation flows.

## AdaptiveCardPrompt Structure
```yaml
- kind: AdaptiveCardPrompt
  id: adaptiveCardPrompt_m9Kp2x
  card: |
    {
      "type": "AdaptiveCard",
      "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
      "version": "1.5",
      "body": [...],
      "actions": [...]
    }
  output:
    binding:
      fieldId: Topic.MyVariable
  outputType:
    properties:
      fieldId:
        type: String
```

## Rules
- card: | or card: |- literal block scalar is mandatory (not card: >)
- $schema and version required inside card JSON
- output.binding maps card input id to Topic.VarName (no = prefix)
- outputType.properties must declare type for every bound field (shorthand `fieldId: String` is valid)
- Every AdaptiveCardPrompt MUST have output, outputType, and Action.Submit button
- For info cards with no inputs, add dummy acknowledgement (Topic.CardAcknowledged, type String)
- **Every `isRequired: true` input MUST include `errorMessage`** — missing → publish `AdaptiveCardInputIsRequiredMissingErrorMessage` (validated PCR deep-dive 2026-07-16)
- Action.Submit should carry unique `data.actionSubmitId` when multiple cards may appear in a conversation

## Field Validation
Use regex for validation (not style: Email/Tel which only change keyboard):
```json
{"type": "Input.Text", "id": "email", "isRequired": true, "regex": "^[a-zA-Z0-9._%+\\\\-]+@...", "errorMessage": "Enter valid email"}
```
Every Input.ChoiceSet must have `label`. Required ChoiceSets also need `errorMessage`:
```json
{"type": "Input.ChoiceSet", "id": "selectedDiscipline", "label": "Discipline focus", "isRequired": true, "errorMessage": "Choose a discipline or Not now.", "choices": [...]}
```

## Output Binding
Card input id values must exactly match output.binding keys.
Topic variable references: Topic.VariableName (no = prefix).
Declare every bound field in outputType.properties.

## Dynamic Text Around Cards
Card JSON is static — no Power Fx or {} inside card body. Use SendActivity before/after for dynamic content.

## Card Types
| Type | Has inputs | Has output | Template |
| form | Yes | Yes | Form Card |
| info | No (dummy) | Yes (always) | Info Card |
| confirmation | Yes (ChoiceSet) | Yes | Confirmation Card |

## Card → Generate → Audit Pattern (Post-Session Documentation)

For agents that collect structured data via AdaptiveCard and generate clinical notes, append this block AFTER the AdaptiveCardPrompt:

```yaml
    # After AdaptiveCardPrompt outputType...
    - kind: SearchAndSummarizeContent
      id: gen_discipline_noteType
      userInput: "=Concatenate(\\"Generate a skilled DISCIPLINE NOTE_TYPE. SECTIONS - 1. Header 2. Diagnosis 3. Subjective 4. Objective 5. Assessment with skilled justification 6. Plan 7. Signature. Use only provided data. Clean plain text. VAR1 \\", Text(Topic.var1), \\" VAR2 \\", Text(Topic.var2), \\".\\")"

    - kind: SendActivity
      id: draft_discipline_noteType
      activity: |-
        DRAFT - CLINICAL REVIEW REQUIRED

        {Topic.Answer}

        Review before EHR entry.

    - kind: BeginDialog
      id: audit_discipline_noteType
      input:
        binding:
          incomingDiscipline: ="DISCIPLINE"
          incomingDocumentType: ="NOTE_TYPE"
      dialog: pcca_theradocworkbench.topic.AuditExistingNote

    - kind: EndDialog
      id: end_discipline_noteType
      clearTopicQueue: true
```

**YAML Quoting Pitfall:** SearchAndSummarizeContent `userInput` with `Concatenate()` containing colons or braces MUST use double-quoted string with escaped inner quotes:
```yaml
userInput: "=Concatenate(\\\\\"text with colons: item 1\\\\\", Text(Topic.var), \\\\\"more text\\\\\")"
```
NOT unquoted — colons and braces break YAML parsing.

**When to use this pattern:**
- Post-session documentation (therapist clicks buttons → AI generates note)
- Any AdaptiveCard collecting structured data that needs AI processing
- Clinical note generation from structured inputs

**When NOT to use:**
- Knowledge-grounded Q&A alone without needing structured pickers (use SearchAndSummarizeContent with knowledgeSources instead)
- Conversational flows (use AnswerQuestionWithAI instead)
- **SR eval catch-all paths (Fallback / Conversational boosting)** — AdaptiveCardPrompt returns interactive content → grader Abstention. Put cards in a dedicated topic; advertise trigger phrases from Fallback instead.

## Post-report menu → knowledge-grounded deep dive (clinical agents)

Pattern for "after first report, offer PT/OT/SLP buttons for deeper clinical interpretation":

1. **Dedicated topic** with AdaptiveCardPrompt (discipline picker) → SASC (files + KBs) → SendActivity → EndDialog.
2. After report topics: SendActivity(report) → gate (long paste / keywords) → BeginDialog(dedicated topic); else text hint with phrases.
3. Fallback: text hint only — **no card** on catch-all.
4. SASC `userInput` Concatenate of card fields: prefer bare `Topic.SelectedDiscipline` + `System.Activity.Text`. Avoid `Text(...)` wrappers that fail publish on some types; avoid stuffing FullResponse records into Concatenate.

Full validated recipe (PCR Reviewing Agent): skill `case-history-agent-fix` → `references/discipline-clinical-deep-dive.md`.

Verified: TheraDoc Workbench (PT/OT/SLP Daily, Evaluation, Progress, Recert, Discharge Cards — Jun 30 2026); PCR Discipline Clinical Deep Dive (Jul 16 2026)

Schema lookup: node "D:/my agents copilot studio/pipeline/scripts/schema-lookup.bundle.js" summary AdaptiveCardPrompt
Adaptive Card element schema (v1.6): node "D:/my agents copilot studio/pipeline/scripts/schema-lookup.bundle.js" ac-summary TextBlock
