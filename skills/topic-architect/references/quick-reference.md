# Topic Architect — Quick Reference Card

## Input Questionnaire (ask agent builder)

1. What is the agent's single-sentence purpose?
2. What domains/subdomains does it cover? (list all)
3. What knowledge sources will it use? (exact schemanames from Dataverse)
4. What document types will it audit/process? (evaluation, daily note, etc.)
5. Which model? (Sonnet46 or GPT5Chat)
6. Is this for SR eval, Conv eval, or both?

## Output: Minimal Topic Set

### Always Required

| # | Topic | Kind | Node | Purpose |
|---|-------|------|------|---------|
| 1 | Conversational boosting | AdaptiveDialog | SearchAndSummarizeContent | Catch-all for all unmatched queries |
| 2 | Greeting | AdaptiveDialog | SendActivity | Agent introduction (deactivate if has Question node) |

### Conditionally Added

Add domain-specific topics ONLY when the catch-all can't differentiate knowledge sources or needs different additionalInstructions.

Maximum: 1-3 domain topics.

## Topic Template (copy-paste ready)

```yaml
kind: AdaptiveDialog
modelDescription: <one-line purpose statement>
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: <PascalCase Topic Name>
    triggerQueries:
      - <unique trigger phrase 1>
      - <unique trigger phrase 2>
      - <unique trigger phrase 3>
  actions:
    - kind: SearchAndSummarizeContent
      id: search
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Provide specific requirements with inline citations
        - Use knowledge sources to ground all claims
        - Never fabricate or invent data
        - Be thorough and complete
      knowledgeSources:
        - schemaname: <exact_dataverse_schemaname>
      applyModelKnowledgeSetting: true
    - kind: EndDialog
      id: done
      clearTopicQueue: true
```

## Instruction Template (paired output)

The instructions block must include these 6 sections for >95% SR eval:

1. CLINICAL ROLE — who the agent is
2. SCOPE — domains, out-of-scope clarification
3. NO-CAVEAT STANDARDS CHECK — never ask for documents
4. RESPONSE FORMAT — 6 numbered sections
5. RESPONSE BEHAVIOR — "never defer, never ask, just audit"
6. SCORING STRICTNESS — domain-specific deductions

See `copilot-studio-instructions-v9` skill for full template.
