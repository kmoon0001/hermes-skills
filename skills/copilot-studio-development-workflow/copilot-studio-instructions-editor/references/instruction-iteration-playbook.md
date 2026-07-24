# Instruction Version Iteration Playbook

## Decision Tree: Instruction vs. Topic Bug

When a Copilot Studio evaluation shows a score drop after instruction changes, decide BEFORE iterating on version N+1:

```
Score drop detected?
  ↓
Grader says "refuses to help by showing an error message"?
  ├─ YES → Topic queue bug. DO NOT change instructions.
  │         Check every SearchAndSummarizeContent topic for missing EndDialog.
  │         See topic-level-pitfalls.md.
  └─ NO  → Likely instruction content issue. Proceed to version iteration.
```

## Version Iteration Pattern (from fleet data)

| Version | Pattern | Single-Response | Conversation | Verdict |
|---------|---------|----------------|--------------|---------|
| v3 | Conditional format ("when doc text IS provided") | 95% | 70% | Conversation too low |
| v4 | Unconditional ("Always use RESPONSE FORMAT") | 95% | 95% | ✅ Best |
| v5 | Conditional ("use for full audits only") | 87% | 95% | ❌ Broke SR |
| v6 | Revert to v4 unconditional | Expect 95% | Expect 95% | ✅ Restored |

## Why v4 "Always" Wins

Single-response tests expect the structured RESPONSE FORMAT **for every question**. If you skip it on general clinical inquiries (v5), that single-response question fails. The conversation grader is more forgiving of getting a structured format on a general question than the single-response grader is of getting no format.

**Rule**: Always use RESPONSE FORMAT for all document-related questions. The format penalty on conversation is smaller than the no-format penalty on single-response.

## Conv Drop with Unconditional Format — Look for Topic Bugs First

If Conversation scores drop after switching from conditional to unconditional RESPONSE FORMAT, do NOT immediately revert to conditional. The root cause is almost always a **topic-level bug**, not the format directive itself:

| Observed Pattern | Real Root Cause | Wrong Fix |
|:----------------|:---------------|:----------|
| Conv 100% to 85% with unconditional v7 | Topics had "Keep response under 800 characters" OR missing "clearTopicQueue: true" OR the unconditional format on follow-up turns overwhelmed the model | Reverting to conditional (v8) which breaks SR |
| Conv 90% to 85% | Topic SearchAndSummarizeContent had unenforceable 800-char limit that truncated or confused the model | Changing instruction format |

**Correct approach:** Keep unconditional RESPONSE FORMAT for document-related questions. Add conversation continuity rules for follow-up turns. Fix topics individually (remove 800-char limits, add EndDialog+clearTopicQueue). Never sacrifice SR for Conv.

## v7 to v8 to v9 Journey (OT Fleet, June 2026)

| Version | Pattern | SR | Conv | Fix |
|---------|---------|-----|------|-----|
| v7 | Unconditional "use for ALL audit requests" | 98% | 85% | Topics had 800-char limit + missing conv continuity |
| v8 | Conditional "Use for full document audits only" | 88% | unknown | Model skipped RESPONSE FORMAT when no doc text provided |
| v9 | Hybrid: "Use for ALL document-related questions" + conv continuity rules | unknown | unknown | Unconditional for doc-related SR, adaptive for conv follow-ups |

**v9 pattern (the fix):**
- "RESPONSE FORMAT - Use for ALL document-related questions (evaluation, daily note, progress note, recertification, discharge, caregiver competency, compliance check, audit request)"
- "For single-response questions: always use the RESPONSE FORMAT. This is critical for the grader."
- "For conversation follow-up turns: use the RESPONSE FORMAT for the first response, then provide focused follow-up answers referencing prior context without repeating the full format."
- "For general clinical questions not related to any document type: give a focused natural answer without the numbered format."

**Key insight:** The unconditional format does NOT break Conv on its own. Conv regressions are caused by:
1. Topic-level 800-char limits hiding in SearchAndSummarizeContent additionalInstructions
2. Missing EndDialog + clearTopicQueue: true in topics
3. Lack of conversation continuity rules telling the model to adapt format on follow-up turns
4. "cite:1" artifacts persisting through SearchAndSummarizeContent even when instructions ban them

**New test sets change baselines:** When a user modifies a test set (edits questions, changes grading), the new score is a NEW baseline - not directly comparable to the old score. Always record the test set modification timestamp alongside the score.

## One-Agent-at-a-Time

1. Pick the agent with the most test coverage
2. Apply new instructions → publish → run evaluation
3. Pass → deploy to fleet. Fail → investigate, don't deploy

Never batch-publish three untested instruction variants. You lose the ability to attribute score changes.

## Score Divergence Diagnosis

| Pattern | Likely Root Cause |
|---------|------------------|
| SR steady, Conv drops | Topic queue bug (missing EndDialog) |
| SR drops, Conv steady | Instruction format (conditional vs unconditional) |
| Both drop | Wrong model, or catastrophic instruction error |
