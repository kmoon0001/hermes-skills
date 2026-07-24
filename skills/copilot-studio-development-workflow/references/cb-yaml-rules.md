# Conversational Boosting (CB) Topic Rules

## YAML Format Rules (Copilot Studio code editor)

These rules are enforced by the Copilot Studio YAML parser in the code editor.
Violating any of them causes save/publish errors.

### Must:
1. **SearchAndSummarizeContent** action kind — NOT CreateGenerativeAnswers
2. **One-line activity** — the fallback message must be a single line (no line breaks in the activity string)
3. **No commas** in the `activity:` string — they break YAML list parsing
4. **No question marks** (`?`) in the activity string
5. **No contractions** — `you'd` → `you would`, `can't` → `cannot`
6. **`applyModelKnowledgeSetting: true`** on SearchAndSummarizeContent node (or omit)
7. **`EndDialog` with `clearTopicQueue: true`** — prevents topic stacking
8. **`allowLatencyMessage: false`** — suppresses "Searching..." messages

### Valid CB YAML Template:

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
        1. [Instruction one]
        2. [Instruction two]
        3. Keep responses under 800 characters
        4. Never refuse to help
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
          activity: [One-line help message with no commas or question marks]
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
```

## CB additionalInstructions — The Citation Trap

**PITFALL**: Demanding "cite CMS Ch. 15 per response" or "include at least one regulatory citation" will backfire. When knowledge sources are insufficient or the query is a record_id lookup (no clinical text), the model cannot produce a citation and the response gets marked "incomplete" and "ungrounded."

**FIX**: Use permissive citation language:
```yaml
additionalInstructions: |-
  1. Provide the best available answer using knowledge sources. Cite regulatory references when they naturally apply — do not force a citation where none exists.
  2. When asked to audit without document text: describe the key Medicare compliance elements then ask for content.
  3. Keep responses under 800 characters.
  4. Never refuse to help. If knowledge sources are insufficient, provide general compliance guidance.
```

**DO NOT** use:
```
additionalInstructions: |-
  For every response, include at least one CMS Ch. 15 citation.  ← TOO AGGRESSIVE
  Always cite authoritative sources.                            ← BACKFIRES
```

This was validated 6/11/2026: OT CB v2 (with aggressive citation mandate) caused conversation eval to drop from 70% to 60%. CB v3 (permissive language) is the correct pattern.

## Fallback Message

The `elseActions` SendActivity should provide useful information, not just "I can help with...". Bad pattern:

```
activity: I can help with OT documentation compliance audits. Could you provide more detail?  ← TOO VAGUE
```

Good pattern — includes real compliance framework:
```
activity: I can help with OT documentation compliance. Key Medicare requirements include skilled service justification per CMS Ch 15 Section 220 functional outcomes with measurable progress and medical necessity documentation. Which document type would you like me to help with?
```

## Agent-Specific CB Rules

| Agent | CB Status | Architecture |
|-------|-----------|-------------|
| OT | ON | CB + guard topics. Can disable if guard topics cover all prompts. |
| PT | OFF | Guard topics only. CB not needed. |
| SLP | ON (REQUIRED) | CB is PRIMARY router. Disabling = 0% conversation eval. |
| TDA | ON | CB + guard topics. CB handles multi-discipline queries. |
