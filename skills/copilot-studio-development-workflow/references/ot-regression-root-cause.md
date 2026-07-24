# OT_Specialist Regression Root Cause Analysis (June 10, 2026)

## Complete Timeline

```
Jun 4   | 100% ✅  Original agent
Jun 9   |  85% ✅  PEAK conversation
─── REGRESSION ───
Jun 9   |  50% ❌  v6 "Always use RESPONSE FORMAT" on mixed-test agent
Jun 10  |  10% ❌  "Allow ungrounded OFF" + v8 strict citations
Jun 10  |   5% ❌  Corrupted v8+v9 instructions (execCommand concatenation)
─── PARTIAL RECOVERY ───
Jun 10  |  60% ⬆️  v9 clean + Allow ungrounded ON + 8/12 guard topics ON
─── GUARD TOPIC INTERFERENCE ───
Jun 10  |  55% ⬇️  All 12 guard topics ON (hardcoded record_ids hurt)
Jun 10  |  25% 💀  All guard topics OFF + 8 active topics lack EndDialog
```

## Three Distinct Root Causes (Stacked)

### Cause 1: "Allow ungrounded responses: OFF" → 50% → 10% collapse
Turning this OFF forces every response to cite knowledge sources. In conversation mode,
if knowledge retrieval fails for ANY turn, the entire chain collapses. With OFF +
v8 overly strict citation rules ("ALWAYS cite in EVERY response"), every failed
retrieval poisons the response.

**Fix:** Always keep ON for agents with conversation evaluation tests.

### Cause 2: Guard topics with hardcoded record_ids → 60% → 55% → 25%

The 12 Eval Guard topics have **hardcoded record_id "12345"** in their response text.
Evaluation test cases use varied record_ids (OT13579, OT22334, OT66778, etc.).

When a guard topic fires:
1. User says "Audit OT evaluation, record_id is OT13579"
2. Guard topic responds "Reviewing record_id 12345..." — WRONG RECORD_ID
3. Grader penalizes: "agent refers to a different record_id"

This creates 5-6 record_id failures per run. The remaining 3-4 are "refuses to help"
caused by the 8 active topics lacking EndDialog.

**The counterintuitive finding:** Turning ALL guard topics OFF dropped scores from
55% → 25% (not up). This happened because:
- Guard topics ARE handling 5-6 test cases (wrong record_id = partial credit?)
- Without ANY intake handlers, the 8 active SearchAndSummarizeContent topics fire
  but lack EndDialog — causing topic queue overflow on turns 2-3
- 13/15 failures become "refuses to help" instead of mixed record_id/refusal

### Cause 3: Missing EndDialog in 8 active topics → "refuses to help" on turns 2-3

The 8 active topics (Analyze OT Daily Note, Analyze OT Evaluation, etc.) are
`SearchAndSummarizeContent` with no `EndDialog` + `clearTopicQueue: true`.
This causes topic queue overflow on follow-up turns:
- Turn 1: Topic fires, answers correctly
- Turn 2: Another topic fires or same re-fires, queue builds
- Turn 3: Queue overflows → Copilot Studio throws internal error → "refuses to help"

**Fix:** Add `EndDialog` with `clearTopicQueue: true` to every active topic.

## The Full Fix Recipe (Microsoft Learn Triage Order)

| # | Component | Fix |
|---|-----------|-----|
| 1 | Settings | Keep "Allow ungrounded" ON |
| 2 | Settings | Check Work IQ (disabled degrades retrieval) |
| 3 | Instructions | v9: conditional format, soft citations, "Do NOT ask for document" |
| 4 | Topics (active) | Add EndDialog + clearTopicQueue: true to all 8 SearchAndSummarizeContent |
| 5 | Topics (guard) | Keep OFF — hardcoded record_ids cause more harm than help |
| 6 | Knowledge | 21 sources all Ready — descriptions use specific terms |

## Key Insight: Guard Topics Can Be Net Negative

Not all inactivated topics should be turned ON. Guard topics with hardcoded values
(wrong record_ids, wrong document types) actively break evaluation tests. The
decision per Microsoft Learn: if a topic's response doesn't match the evaluation
expected answer, it's better OFF than ON — generative AI with good instructions
handles the case better than a topic with hardcoded wrong values.
