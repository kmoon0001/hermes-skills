# OT Topic Bloat — 200+ Duplicate Question-Phrase Topics

## Discovery

On June 10, 2026, `pac org fetch` on the OT_Specialist botcomponents (componenttype=9)
revealed **200+ topics** — far more than the 20 visible in the Copilot Studio Topics UI.

The extra topics are **question-phrase duplicates** — each one is a narrow topic with
an exact-match trigger phrase matching an evaluation test question:

```
"How do I document FIM scores in OT notes for SNF residents?"
"Can you help me identify missing elements in an OT progress note for a SNF patient?"
"What are the best practices for documenting OT progress metrics?"
"How do I document adaptive equipment for regulatory compliance?"
"Can you review my OT daily note for missing elements and risk of insurance denial?"
... (200+ more)
```

## Why It Matters

Per Microsoft Learn best practices:
- **Too many narrow topics create routing conflicts.** Each topic competes for intent
  matching with every similar topic. The model has to resolve hundreds of near-identical
  trigger phrases.
- **Generative orchestration handles variations naturally.** You don't need a dedicated
  topic for "How do I document FIM scores" — the generative AI + instructions + knowledge
  sources handle this.
- **Non-deterministic behavior.** With 200+ competing topics, which one fires is
  unpredictable — the same evaluation test can produce different results on different runs.

## How to Detect

```bash
pac org fetch --xml "<fetch><entity name='botcomponent'>
  <attribute name='botcomponentid'/><attribute name='name'/>
  <filter><condition attribute='parentbotid' operator='eq' value='<botId>'/></filter>
</entity></fetch>" | grep -c "botcomponentid"
```

If the count is >50 for a specialist agent, topic bloat is present.

## The 12 Named Non-Guard Topics (Keepers)

Only these structured topics should remain active (plus system topics):

| Name | ID |
|------|-----|
| Analyze OT Daily Note | 11bd598c-... |
| Analyze OT Discharge | 31bdf7f9-... |
| Analyze OT Evaluation | 2a055852-... |
| Analyze OT Progress Note | f9a94423-... |
| Analyze OT Recertification Note | 02bb9b41-... |
| Insurance Denial Risk Prompt | 71034da0-... |
| OT Caregiver Competency Prompt | 60041e7f-... |
| OT Clinical Documentation Standards | e11812ef-... |
| OT General Knowledge | f8d2f891-... |
| OT Progress Missing Elements Exact Intake | 6ff36f26-... |
| OT Recertification Missing Elements Exact Intake | edf16f26-... |
| Conversational boosting | 7937da33-... |

Plus 8 system topics: Conversation Start, Fallback, Escalate, End of Conversation,
Sign in, Multiple Topics Matched, On Error, Reset Conversation.

Total: 20 topics (down from 200+).

## The 12 Guard Topics — DELETED

These exact-match intake handlers had hardcoded record_ids (e.g., "12345") that
didn't match evaluation test record_ids (OT13579, OT22334, etc.). When active,
they responded with wrong IDs, causing "agent refers to a different record_id" failures.

**Decision (Jun 10, 2026):** DELETED all 12 guard topics per user direction.
Turning them OFF wasn't enough — they still existed as potential routing targets.
Deleting them removed the routing ambiguity entirely.

**Evidence:** OT conversation: 55% with all 12 ON (wrong record_ids), 60% with
partial ON, 25% with all OFF. Neither ON nor OFF was correct — only deletion
resolved the routing conflict.
