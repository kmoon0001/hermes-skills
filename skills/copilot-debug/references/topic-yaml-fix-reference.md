# Topic YAML Fix Reference (June 2026)

## Root Cause Pattern

Agent Conv evaluation failures are caused by TOPIC `additionalInstructions`, not agent instructions. The 800-character limit in topic YAML truncates responses mid-sentence, causing grader to mark "incomplete."

## Affected Topics (June 14 2026)

| Agent | Topics with 800-char limit | Fixed? |
|-------|---------------------------|--------|
| OT | Daily, Progress, Evaluation, Recertification, Discharge | Not yet |
| PT | Daily, Progress, Evaluation, Recertification, Discharge | Yes (user applied) |
| SLP | Daily Therapy Note | Yes (user applied) |

## Topic YAML Template

Every audit topic must follow this structure:

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: [Topic Name]
    triggerQueries:
      - [trigger phrase 1]
      - [trigger phrase 2]

  actions:
    - kind: SearchAndSummarizeContent
      id: search_[TopicId]
      latencyMessageSettings:
        allowLatencyMessage: false

      userInput: =System.Activity.Text
      additionalInstructions: |-
        [Audit criteria specific to document type]
        Use risk levels (High/Moderate/Low).
        Cite CMS Chapter 15 and [discipline] guidelines by natural source name. Do not output cite:1 or metadata tags.
        Be concise but complete. Prioritize accuracy over strict length limits.
      applyModelKnowledgeSetting: true

    - kind: EndDialog
      id: end-topic
      clearTopicQueue: true

inputType: {}
outputType: {}
```

## Key Rules

1. First line MUST be `kind: AdaptiveDialog` -- omitting causes "Invalid kind" error
2. Remove ALL instances of "Keep response under 800 characters"
3. Add citation instruction: Cite CMS Chapter 15 and [discipline] guidelines by natural source name. Do not output cite:1 or metadata tags.
4. Add "Be concise but complete. Prioritize accuracy over strict length limits."
5. EndDialog + clearTopicQueue: true must be the LAST action
6. 2-space indentation (Monaco editor is strict)

## Results After Fix

| Agent | Metric | Before | After |
|-------|--------|--------|-------|
| OT SR | Single Response | 88% | 99% |
| OT Conv | Conversation | 85% | 90% |
| PT SR | Single Response | 89% | 96% |
| PT Conv | Conversation | 75% | Pending test |
| SLP SR | Single Response | 100% | 100% |
| SLP Conv | Conversation | 85% | Pending test |

## Extract Template Script

To check topic YAMLs offline without CDP:
```bash
pac copilot extract-template --bot "<botId>" --templateFileName "/path/to/output.yaml" --overwrite
```
Then search for `800` in the file to find affected topics.
