# Conversational Boosting Topic — Citation Behavior

## Key Finding (June 14, 2026)

**The original CB topic config is correct. DO NOT modify it.**

The CB topic citation behavior (`[1]: cite:1`, URLs) is NOT responsible for
Single Response regression. The regression was caused by caregiver-authored
topics intercepting queries before the CB topic could route them through the
agent's instructions + knowledge sources.

## Proof

| State | SR Score | CB Config |
|-------|----------|-----------|
| Caregiver topics ON + original CB | 86% | 600 chars + Always cite |
| Caregiver topics DELETED + original CB | **92%** | 600 chars + Always cite |
| Caregiver topics deleted + modified CB (anti-citation) | **35%** | No limit + anti-citation |
| Caregiver topics deleted + **rolled back** to original CB | **95%** | 600 chars + Always cite |

## Why the Original Config Is Correct (Microsoft Learn-aligned)

1. **600-character limit** is a Microsoft Learn best practice for response
   quality — concise answers grade better on General Quality.
2. **"Always cite knowledge sources"** works WITH the platform's native
   citation rendering. The platform appends citations regardless of instructions.
3. **`applyModelKnowledgeSetting: true`** uses both KB + model knowledge.

## What Actually Happens

The CB topic's `SearchAndSummarizeContent` action:
- Searches all knowledge sources
- Generates a concise answer (<600 chars)
- The PLATFORM appends footnotes (`[1]: cite:1`, URLs) automatically after
  the answer — this is NOT controlled by `additionalInstructions`

The grader sees these footnotes but does NOT penalize for them (92-95% SR
scores prove this). The failures were from caregiver topics returning
INCOMPLETE template answers, not from citation formatting.

## DO NOT

- ❌ Remove the 600-character limit (causes 40+ min eval times, 35% SR)
- ❌ Add "NEVER include citations" instructions (no effect — platform appends
    citations, not LLM)
- ❌ Replace SearchAndSummarizeContent with AnswerQuestionWithAI (worse
    reliability, fewer features)

## Original YAML (preserved)

```yaml
additionalInstructions: |-
  Keep response under 600 characters. Give the most relevant 2-3 points only.
  - Always cite knowledge sources using [Source Name] format in every response
```