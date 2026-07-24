# Topic Cleanup Pattern — Removing Question-Phrase Duplicates

## The Problem

Copilot Studio agents accumulate question-phrase topics over time — each evaluation test question gets converted into a topic with an exact-match trigger phrase. This creates:

- **200+ active topics** all competing for routing
- Non-deterministic behavior (random topic fires each run)
- Topic queue overflow (no `EndDialog` on most topics)
- "Refuses to help" on conversation turns 2-3

## Microsoft Learn Guidance

> "Fewer, well-designed topics outperform many narrow topics. Generative orchestration handles variations naturally."

## Cleanup Protocol

1. **Query all topics via pac:**
   ```bash
   pac org fetch --xml "<fetch><entity name='botcomponent'><attribute name='name'/><attribute name='componentstate'/><filter><condition attribute='parentbotid' operator='eq' value='<botId>'/><condition attribute='componenttype' operator='eq' value='9'/></filter></entity></fetch>"
   ```

2. **Categorize topics:**
   - **KEEP:** Named audit topics (Analyze OT Daily Note, Analyze SLP Evaluation Report, etc.)
   - **KEEP:** System topics (Fallback, Escalate, Conversation Start, etc.)
   - **KEEP:** Intentional prompt topics (Insurance Denial Risk Prompt, OT Caregiver Competency Prompt)
   - **DELETE/OFF:** Question-phrase topics that match evaluation test questions ("How do I document FIM scores...", "Can you analyze...", etc.)

3. **For guard topics:** Assess whether they have hardcoded record_ids that break evaluation. If yes, delete them. If they work correctly (like PT's guard topics at 95%+), keep them.

## Evidence (Jun 10, 2026)

**OT_Specialist:** Had 200+ question-phrase topics. After removing them (keeping 12 named + system topics), the agent's routing chaos was eliminated. The remaining issue was `CancelAllDialogs` in 2 remaining topics, which was fixed separately.

**PT_Specialist:** Has 14 guard topics ON but achieves 95-100% conversation with them. These guard topics work correctly — no hardcoded record_ids causing failures. Keep them.

## Decision Framework

| Condition | Action |
|-----------|--------|
| Guard topics ON, Conv 90%+ | Keep them |
| Guard topics ON, Conv below 50% with "refuses to help" | Delete or fix EndDialog |
| 200+ question-phrase topics | Delete all, keep named only |
| Named topics with `CancelAllDialogs` | Fix to `EndDialog` + `clearTopicQueue: true` |
