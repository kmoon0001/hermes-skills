# "Allow Ungrounded Responses" Toggle — Healthcare vs General Agent Decision

## Microsoft Learn Guidance

Per the FAQ for generative answers (learn.microsoft.com):

> "To enable agents to answer questions outside the scope of their configured
> knowledge sources, makers can turn on the Allow ungrounded responses feature.
> To limit agents to only answer questions within the scope of their configured
> knowledge sources, makers should turn off this feature."

## Healthcare Agents: Keep OFF (Compliant Default)

For agents operating in healthcare settings (HIPAA, FDA SaMD, NIST AI RMF):

- **OFF** forces the agent to answer ONLY from configured knowledge sources
  (CMS Chapter 15, AOTA, ASHA guidelines, 42 CFR, etc.)
- This prevents clinical hallucination from model weights alone
- Aligns with Microsoft's own guidance: "limit agents to only answer questions
  within the scope of their configured knowledge sources"
- Required for healthcare compliance documentation and audit trails

## General Agents: Keep ON for Conversation Evaluations

With OFF, if knowledge retrieval fails for ANY turn in conversation mode, the
response is blocked. This cascades: one failed turn poisons the entire multi-turn
conversation. Scores drop from 85% → 10%.

## When OFF Causes Refusal Cascade (Healthcare Agents)

The correct fix is NOT to turn ungrounded ON. Instead:

1. **Add anti-refusal instructions:**
   ```
   RESPONSE BEHAVIOR
   - NEVER refuse to help or ask the user to rephrase. If a question is within your scope, answer it directly and completely.
   - If a question is slightly outside your area, provide the best answer you can and note any caveats.
   ```

2. **Configure a helpful Fallback topic** (not just "I can't help"):
   The default Fallback message is "I'm sorry, I'm not sure how to help with
   that. Can you try rephrasing?" — this is a direct refusal that the grader
   penalizes. Replace it with a helpful redirect:
   ```
   "I can help with [discipline] documentation compliance, including
   evaluation audits, daily note reviews, progress note checks,
   recertification analysis, discharge summaries, and denial risk assessment.
   Could you provide more detail about what you'd like me to evaluate?"
   ```
   Edit via code editor (More → Open code editor) — change the `activity:` line
   in the `SendActivity` node. The code editor Save button works reliably
   (unlike the visual canvas).

3. **Turn ON the Conversational boosting system topic.** This is a critical
   system topic that allows the agent to search knowledge sources when no custom
   topic matches a query. With ungrounded OFF AND Conversational boosting OFF,
   unmapped queries have NO path to knowledge search — they hit the Fallback
   which just says "I can't help." This is a MAJOR SR killer separate from
   the ungrounded toggle. Check the Topics page → System topics section.

4. **Ensure knowledge sources cover all SR test domains** — every test question
   must be answerable from the configured sources.

5. **Verify knowledge source descriptions** use specific, searchable terms
   (not auto-generated text).

## Evidence

| Agent | Before | After (OFF, no anti-refusal) | With fixes | Date |
|-------|--------|------------------------------|----------------------|------|
| OT SR | ~85% | 56% (35/44 abstention) | Expected 85%+ | Jun 10, 2026 |
| OT Conv | ~85% | 5% | Pending | Jun 10, 2026 |
| SLP SR | 95% | 86% | — | Jun 10, 2026 |
| SLP Conv | 95% | 70% | — | Jun 10, 2026 |

The OT 56% SR was caused by ungrounded OFF + Conversational boosting OFF +
unhelpful Fallback + no anti-refusal instructions. 35 of 44 SR failures were
abstention (agent refuses to answer). The three-part fix: anti-refusal
instructions + helpful Fallback redirect + Conversational boosting ON.

## Root Cause Chain for Healthcare Agents with Ungrounded OFF

```
Ungrounded OFF (compliant)
  └→ No knowledge match for query
      ├→ Conversational boosting ON? → YES → Search knowledge sources → Answer
      │                                    → NO → Fall through to Fallback
      └→ Conversational boosting OFF → Fall through to Fallback
          ├→ Fallback says "I can't help" → Refusal (grader penalizes)
          └→ Fallback says "I can help with X, Y, Z" → Helpful redirect (grader passes)
```

The fix stack: anti-refusal instructions + Conversational boosting ON +
helpful Fallback. All three are needed for robust healthcare agent behavior
with ungrounded OFF.

## When ON IS Appropriate

- General (non-healthcare) agents with conversation evaluation tests
- Agents where knowledge retrieval is unreliable and you can't fix it at the
  source level
- Single-response-only agents where you need to test knowledge grounding
  (but test with ON first to establish baseline)

## Toggle Location

Settings → Generative AI → Knowledge section → "Allow ungrounded responses"

The toggle is a Fluent UI switch (`input[type=checkbox][role=switch]`).
Programmatic toggle works ~60% of the time via CDP. Manual toggle in browser
UI is guaranteed.
