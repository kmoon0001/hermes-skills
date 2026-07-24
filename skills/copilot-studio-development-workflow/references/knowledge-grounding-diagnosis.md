# Knowledge Grounding Diagnosis

## When to suspect knowledge grounding failure

Symptom: Agent scores ~50% on conversation evaluations regardless of instruction format changes. Both unconditional "Always use RESPONSE FORMAT" and conditional "for full audits only" produce nearly identical scores.

## Diagnostic signals from the grader

The Copilot Studio evaluation grader gives specific feedback per test case. When knowledge grounding is the root cause, look for:

- **"One or more answers didn't cite knowledge sources"** — definitive signal
- **"One or more answers seem incomplete"** — often paired with the above
- Agent generates plausible-looking but unsourced content
- No specific source names appear in responses (e.g., "CMS Chapter 15" missing)

## When it's NOT knowledge grounding — Topic Overload

If scores are flat at 10-60% AND the grader says "refuses to help" or "different record_id",
the root cause is likely **topic overload**, not knowledge grounding. Check:

1. **Count active topics** via `pac org fetch` with `componenttype eq 9`. If >25, topic overload.
2. **Look for question-phrase duplicates** — topics named after specific evaluation test questions
3. **Look for guard topics with hardcoded record_ids** — they cause "different record_id" failures

See `references/topic-audit-methodology.md` for the full audit workflow.

## OT_Specialist Trajectory (June 2026)

| Time | Score | Root Cause |
|------|-------|------------|
| 10:35 PM | 85% | Baseline — clean instructions, topics OK |
| 11:24 PM | 50% | v6 "Always use" applied — instruction format regression |
| 1:04 AM | 55% | Same range |
| 3:17 AM | 50% | v7 conditional — format irrelevant now |
| 4:04 AM | 10% | "Allow ungrounded: OFF" — catastrophic |
| 8:07 AM | 5% | Corrupted v8+v9 instructions + guard topics OFF |
| 9:29 AM | 60% | v9 clean + Allow ungrounded ON + partial guard toggle |
| 10:55 AM | 55% | All 12 guard topics ON — hardcoded IDs hurt |
| 11:41 AM | 25% | All guard OFF, 200+ question-phrase topics active — topic overload |

**Key insight:** The 25% at 11:41 AM was NOT knowledge grounding. It was 200+ competing
topics causing routing chaos + "refuses to help" on every turn. After topic cleanup (200→20),
the agent should recover toward 85%.

## Fix checklist

1. **Verify knowledge sources are attached**: Navigate to Knowledge page → check that all expected sources show "Ready" status
2. **Check settings**: `useModelKnowledge: true` in agent settings
3. **Check descriptions**: Knowledge source descriptions should use specific, searchable terms matching what the agent will query
4. **Re-publish**: After any knowledge change, publish the agent
5. **Add explicit instruction**: "Always cite specific knowledge sources by name (e.g., 'Per CMS Chapter 15...')." Even if already present, re-emphasize.
6. **Re-add knowledge sources**: If sources appear attached but don't work, remove and re-add them via the UI
7. **Test with authenticated connection**: Use `mcsConnectionId` in evaluation to ensure authenticated knowledge access
8. **Check for topic overload first**: Before debugging knowledge grounding, count active topics. 200+ topics can produce identical symptoms to knowledge grounding failure. See `references/topic-audit-methodology.md`.
