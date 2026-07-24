# Conversational Boosting YAML Patterns

## Popup Blockers

- **What's New popups** fire on page load and block navigation. Dismiss with Escape x5 + click "Got it"/"Skip"/"Close" buttons.
- **CB topic editor popup** fires after clicking "Open code editor" in CB topic. Dismiss with Escape x3 before reading/writing YAML.

## Fallback Activity Rules

```yaml
# The fallback message IS the response when no knowledge is found.
# It MUST contain real compliance information, not just "I can help with X."
# BAD:
activity: I can help with OT documentation compliance. Could you provide more detail?

# GOOD:
activity: I can help with OT documentation compliance. Key Medicare requirements include skilled service justification per CMS Ch. 15 Section 220, functional outcomes with measurable progress, and medical necessity documentation. Which document type would you like me to help with?
```

## additionalInstructions Rules

```yaml
# NEVER demand citations per response — backfires on test cases without clinical text.
# BAD (causes regression):
additionalInstructions: |-
  1. Provide specific CMS Ch. 15, AOTA, or 42 CFR references for EVERY compliance question.

# GOOD (cite when natural):
additionalInstructions: |-
  1. Provide the best available answer using knowledge sources. Cite regulatory references when they naturally apply — do not force a citation where none exists.
  2. When asked to audit without document text: describe the key compliance elements for that document type then ask for the content.
  3. Keep responses under 800 characters.
  4. Never refuse to help. If knowledge sources are insufficient, provide general guidance.
```

## Validated Structure

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  priority: -1
  actions:
    - kind: SearchAndSummarizeContent
      id: search-content
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        # ≤4 bullets, cite when natural, never refuse
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-conditions
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: EndDialog
              id: end-topic
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: fallback-message
          activity: # Real compliance info, not "I can help"
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
```
