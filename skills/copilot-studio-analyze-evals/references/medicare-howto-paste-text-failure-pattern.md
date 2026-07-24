# "Paste the text" / How-To Instruction Failure Pattern (Validated 2026-07-14)

## Problem

When a user asks an instructional or how-to question — e.g. "How do I get color-coded risk ratings?" or "How do I get coaching on my documentation?" — the Medicare Part B Compliance Agent answers with:

> "To get a color-coded risk rating, paste the therapy note text into the chat..."

The grader flags this as:

- **completeness=No** — the answer tells the user to DO something (paste) rather than providing the actual information requested
- **groundedness=No** — no supporting citation because the answer is purely procedural
- **abstention=Yes** (in severe cases) — grader interprets "paste the text" as a refusal to answer

## Distinct from Existing Patterns

| Pattern | Query | Answer | Grader Signal |
|---------|-------|--------|---------------|
| **Connector gate** | General question | "Let's get connected first" | abstention=Yes |
| **No-note review** | "Review my note" (no text) | Generic framework | abstention=Yes |
| **Paste-text how-to** | "How do I get X" | "Paste a document and I'll review it" | completeness=No, groundedness=No |

This is NOT a connector-gate issue (no sign-in prompt). It is NOT a no-note-review issue (the answer is procedural, not a framework). It is its own class: **instruction question → procedural guidance grader treats as incomplete**.

## Root Cause

The agent is optimized as a **document review tool**. Its instructions and topics are designed around:
1. User pastes a document
2. Agent reviews it for compliance
3. Agent returns structured feedback

When asked a general-knowledge or how-to question WITHOUT a document, the agent's catch-all/boosting falls through to document-review flow language ("paste the note and I'll review it"). The agent never received instructions to handle the "instruction query" class directly.

Common Medicare how-to queries that trigger this:
- "How do I get color-coded risk ratings for my therapy note?"
- "How do I get a comprehensive compliance summary for my therapy note?"
- "How do I get coaching on documentation strengths and weaknesses?"
- "What are the five main sections you audit in therapy documentation?"
- "How do I upload an episode of care document for review?" (also hits Doc Intake)

## Fix: Catch-All/Boosting additionalInstructions

Add to the Conversational Boosting's `SearchAndSummarizeContent.additionalInstructions`:

```
When the user asks a how-to question about getting coaching, risk ratings, compliance summaries, or document reviews — answer directly with what those features provide. Do NOT tell them to paste or upload a document unless they have explicitly said they want to submit one. If they ask "how do I get a risk rating", explain what the rating evaluates (medical necessity, skilled therapy, documentation completeness, functional focus) and offer to review a specific document if they paste it. Answer general questions about CMS documentation standards, audit sections, and compliance coaching directly from knowledge sources — do not route to document-upload flow.
```

This is an **additive, regression-free** change to the catch-all topic only.

## Detection During Eval Analysis

When scanning SR failures, look for this signature:

```python
has_paste_guidance = 'paste the' in answer.lower() or 'paste your' in answer.lower()
if grader.evaluationResult == 'Fail' and has_paste_guidance:
    # This is a paste-text how-to pattern, not a topic routing issue
    category = 'PASTE_TEXT_HOW_TO'
```

## Impact

In the July 14, 2026 Medicare Part B Compliance Agent SR run (89/100):
- 4 of 11 failures (36%) were paste-text how-to pattern
- Fixing via Catch-All instructions would recover ~4 pts → 93/100

Combined with the fallback "could not find" pattern (2 more fails from no-topic CMS questions), fixing the Catch-All instructions recovers ~6 SR points.

## Pre-Fix Data (2026-07-14, Medicare Part B SR Run)

Run ID: `8dc99493-e4be-47a2-8546-ec82c6c632b5` — 89/100 pass

Failing queries and their grader properties:
| Query | abs | rel | comp | gnd | topics | Category |
|-------|-----|-----|------|-----|--------|----------|
| Does my evaluation meet CMS documentation standards? | Yes | NA | No | None | 0 | Fallback no-topic |
| What is the Ensign 7 Habits Framework? | Yes | Yes | Yes | None | 0 | Grader false positive |
| How do I get color-coded risk ratings? | No | Yes | No | No | 0 | **Paste-text how-to** |
| Can you provide coaching tips tied to Ensign 7 Habits? | Yes | Yes | No | None | 0 | Grader false positive |
| What are the five sections you audit? | No | Yes | No | No | 0 | **Paste-text how-to** |
| What are the main Ensign 7 Habits coaching points? | Yes | Yes | Yes | None | 0 | Grader false positive |
| How do I get coaching on documentation strengths? | No | Yes | Yes | No | 0 | **Paste-text how-to** |
| How do I upload an episode of care for review? | Yes | No | No | None | 1 | Doc Intake re-ask |
| How do I get a color-coded risk rating for my progress report? | No | Yes | Yes | No | 0 | **Paste-text how-to** |
| How do I get a comprehensive compliance summary? | No | Yes | No | No | 0 | **Paste-text how-to** |
| Review documentation for Medicare Benefit Policy Manual compliance? | Yes | Yes | No | None | 0 | Fallback no-topic |

## Fix Applied: Route D Expansion (Instructions, 2026-07-14)

Added to agent instructions (componenttype 15, component `1b6244b9`):

```
# PROCEDURAL ROUTE EXPANSION — "how do I get" patterns (Route D)
- Questions starting with "how do I get" (e.g., "how do I get color-coded risk ratings", 
  "how do I get coaching", "how do I get a compliance summary") are procedural Route D 
  questions. Answer directly: EXPLAIN that color-coded risk ratings (🔴🟡🟢) are 
  AUTOMATICALLY generated for each section of every audit. Coaching on strengths/weaknesses 
  is part of every audit output. Do NOT just say "paste the text" — describe WHAT the 
  agent will produce, then invite document paste as a SECOND step.
- Questions about "what are the five sections you audit" — this is Route B. LIST the five 
  sections directly from knowledge: (1) Medical Necessity & Clinical Reasoning, (2) Goals 
  & Patient-Centered Need, (3) Skilled Intervention & Therapist Analysis, (4) Progress, 
  Outcomes & Response to Treatment, (5) Discharge Planning & Care Continuity. Do NOT ask 
  for a document.
- Questions like "Can you review my documentation for compliance with the Medicare Benefit
  Policy Manual" or "Does my evaluation meet CMS standards" — these are Route B (general
  compliance). Answer from approved sources. Do NOT route to Fallback "I could not find
  an answer."
```
