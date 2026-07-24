# Per-Agent RESPONSE FORMAT Decision Matrix (June 2026)

No universal rule. Choose format per-agent based on test set composition.

## Decision Flow

```
1. Check test set composition:
   - 100% audit/document questions → UNCONDITIONAL ("Always use RESPONSE FORMAT")
   - Mixed audit + general clinical questions → CONDITIONAL ("for full audits only")

2. If conditional format:
   - "RESPONSE FORMAT — Use for full document audits only (evaluation, daily note, progress note,
      recertification, discharge):"
   - "For general clinical questions or specific element checks: give a focused natural answer
      without the full numbered format."

3. If unconditional format:
   - "RESPONSE FORMAT (use for ALL audit requests):"
   - "Always use the RESPONSE FORMAT above for any document-related or audit question."

4. ALWAYS keep "Do NOT ask for the document" rule if tests use record_id pointers.
```

## Per-Agent Results

| Agent | Best Format | Single Response | Conversation | Notes |
|-------|------------|----------------|-------------|-------|
| **SLP** | Unconditional | 95% | 95% | Test set is 100% audit. Conditional drops SR to 67%. |
| **TDA** | Unconditional | 96% | N/A | Routing-only test set. |
| **PT** | Conditional | 89% | 100% | Unconditional drops conv to 90%. |
| **OT** | Conditional | 84% | 55%* | *OT conversation crash is knowledge grounding, not format. See below. |

## OT Conversation Crash Root Cause

OT dropped from 85% → 50% conversation. Format changes (both unconditional and conditional)
give ~50-55% — format is NOT the root cause. The grader flagged:
- "One or more answers seem incomplete"
- "One or more answers didn't cite knowledge sources"

**Root cause: "Allow ungrounded responses" was ON** in Generative AI settings.
This lets the agent generate responses from training data without citing knowledge sources.

**Fix:**
1. Turn OFF "Allow ungrounded responses" in Agent → Settings → Generative AI
2. Add to instructions: "ALWAYS cite specific knowledge sources by name in every response
   (e.g., 'Per CMS Chapter 15...', 'AOTA guidelines state...'). Every finding must trace to a source."
3. Add: "Never give incomplete or partial answers."
