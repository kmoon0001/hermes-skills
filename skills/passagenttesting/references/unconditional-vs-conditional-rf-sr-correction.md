# Unconditional vs Conditional RESPONSE FORMAT — SR Correction

## The Problem

The `passagenttesting` skill previously documented this as the "correct resolution" for the RESPONSE FORMAT:

> "For full document audits (evaluation, daily note, progress note, recertification, discharge): use RESPONSE FORMAT. For general clinical questions or specific element checks: give a focused natural answer without the numbered format."

**This approach has a critical edge case that breaks SINGLE-RESPONSE evaluations.**

## Root Cause

When SR test questions ask about a document type **without providing document text** (e.g., *"Can you audit my OT evaluation for Medicare compliance?"*, *"What are the key elements required in an OT daily note?"*, *"How do I justify skilled OT services for ADL training?"*), the conditional wording makes the model decide:

1. *"No document text was provided"* → *"This is not a full document audit"* → *"Skip the RESPONSE FORMAT"* → *"Give a general checklist answer"*

The grader then penalizes because the expected answer includes Classification, Score X/100, Compliance Findings — the RESPONSE FORMAT structure. The agent's generic checklist response fails Relevance, Completeness, or Groundedness.

## Evidence

| Agent | Version | RF Wording | SR Score | Conv Score |
|-------|---------|------------|----------|------------|
| OT | v7 | "RESPONSE FORMAT (use for ALL audit requests)" | 98% | 85% |
| OT | v8 | "RESPONSE FORMAT — Use for full document audits only" | 88% (dropped 10%) | Not yet tested |
| SLP | v4 | "RESPONSE FORMAT (use for ALL audit requests)" | 95% | 80% |
| SLP | v5 | "RESPONSE FORMAT — Use for full document audits only" | 87% (dropped 8%) | 90% (improved) |

The pattern: **Moving from unconditional to conditional RF improves Conv but hurts SR.** The conditional format causes the model to skip RF for questions that reference document types without providing text.

## Correct Fix (Jun 14, 2026)

**Combine unconditional RF scope with conversation continuity rules:**

```
RESPONSE FORMAT — Use for ALL document-related questions
(evaluation, daily note, progress note, recertification, discharge,
caregiver competency, compliance check, audit request)
```

Then add behavioral rules for conversation flow:

```
- For single-response questions: always use the RESPONSE FORMAT.
- For conversation follow-up turns: first response uses full RF;
  follow-up responses use focused natural answers without repeating
  the full format, referencing prior context.
- For general clinical questions not related to any document type:
  give a focused natural answer without the numbered format.
- When a document type or record_id is mentioned: use the RESPONSE FORMAT.
  Do NOT ask for the document.
```

This preserves SR scoring (unconditional RF for all document-related questions) while preventing Conv regression (conversation continuity rules for follow-up turns).

## How to Implement

1. Change the RF header to "Use for ALL document-related questions" with an explicit list
2. Add the "For single-response questions: always use RF" rule
3. Add the "For conversation follow-ups: first response RF, follow-ups natural" rule
4. Keep the "For general clinical questions: natural answer without RF" rule
5. Keep all other RESPONSE BEHAVIOR sections (conversation continuity, citation rules, no-refuse rules)

## Agents Affected

Apply to OT, SLP, and PT. TDA (routing agent) doesn't use RF.

## See Also

- `references/instruction-anti-patterns.md` — general instruction-level diagnostics
- `references/unconditional-response-format-recovery-ot-june14.md` — OT SR 90%→98% fix
- `references/cdp-score-extraction-and-fix-loop.md` — how to extract scores and trigger evaluations
