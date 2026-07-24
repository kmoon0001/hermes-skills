# M365 Declarative Agent → Copilot Studio Topic YAML Remix Guide

## The Mapping

| M365 Declarative Agent | Copilot Studio Equivalent |
|------------------------|--------------------------|
| `## Instructions` block | `instructions:` field in agent YAML (componenttype 15) |
| `## Conversation Starters` | `triggerQueries:` in topic YAML |
| `name:` frontmatter | `displayName:` in intent |
| `description:` frontmatter | `modelDescription:` |
| `## ROLE` | Agent-level instructions, ROLE section |
| `## WHAT YOU DO NOT DO` | Guardrails section in instructions |
| `## OUTPUT FORMAT` | SendActivity activity text pattern |
| Banned vocabulary list | G11 guardrail in instructions |
| Knowledge sources referenced | `knowledgeSources:` in SearchAndSummarizeContent |

## Remix Template

### Step 1: Extract the Instruction Block
From the M365 agent file, grab everything under `## Instructions` (between the ``` markers).

### Step 2: Paste into Copilot Studio Instructions
That entire block can go into:
**Settings → General → Instructions** field

No modification needed — the M365 instruction format is compatible with Copilot Studio's GPT instructions (componenttype 15).

### Step 3: Build Trigger Phrases
From `## Conversation Starters`, extract the natural language patterns:
```
- `Review this technical specification...` → "review document", "check document quality"
- `Check this proposal...` → "review proposal", "audit proposal"
```

### Step 4: Build the Topic YAML

```yaml
kind: AdaptiveDialog
modelDescription: "<from agent description>"
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: "<from agent name>"
    triggerQueries:
      - "<from conversation starters>"
      - "<adapted trigger phrase>"

  actions:
    - kind: Question
      id: question_input
      variable: Topic.user_input
      prompt: "<craft a prompt that asks for what the agent needs>"
      entity:
        kind: StringPrebuiltEntity

    - kind: SearchAndSummarizeContent
      id: search_generate
      variable: Topic.Result
      userInput: '=Concatenate("<agent role brief>: ", Topic.user_input)'
      additionalInstructions: |-
        <paste the agent's instructions here>
      applyModelKnowledgeSetting: <true if knowledge sources referenced>
      responseCaptureType: FullResponse

    - kind: SendActivity
      id: sendActivity_result
      activity: "{Topic.Result}"

    - kind: EndDialog
      id: endDialog_main
      clearTopicQueue: true
```

### Step 5: (Optional) Add Knowledge Sources
If the M365 agent requires knowledge (SharePoint, web), add them in:
**Settings → Knowledge** — add the same sources referenced in the agent's frontmatter.

## Example: Document Reviewer Remix

The `document-reviewer.md` agent (89 agents repo) instructs the AI to review documents across 6 criteria. To remix as a Copilot Studio topic:

1. **Instructions field**: Paste the full instructions block from the agent
2. **Topic**: Add condition groups for each of the 6 review criteria
3. **Output format**: Use the agent's output format template in a SendActivity

See the full worked example in `templates/document-reviewer-topic.yaml`
