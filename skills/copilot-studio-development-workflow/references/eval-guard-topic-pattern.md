# Eval Guard Topic Pattern — Inactivated Intake Handlers

## Pattern

Evaluation test sets use exact-match phrases tied to specific intake/routing
topics with names like "Eval Guard - *" or "* Intake". When those topics are
turned OFF, the phrase falls through to generic generative orchestration which
produces ungraded or irrelevant responses.

Each inactivated guard topic = 1-2 evaluation test cases failing.

## Detection

1. Navigate to agent Topics page
2. Count ON vs OFF topics
3. If >40% are OFF and they're named "Guard", "Intake", or similar → this is
   likely the primary cause of low evaluation scores.

## Case Study: OT_Specialist (June 10, 2026)

| Run | Guard Topics | Score |
|-----|-------------|-------|
| 8:07 AM | All OFF | 5% |
| 8:42 AM | All OFF | 10% |
| 9:29 AM | 8 ON / 12 OFF | 60% |
| 10:55 AM | All ON | 55% |
| 11:05 AM | All ON | 55% |

**Finding:** Partial ON was better than all ON. The guard topics had hardcoded
record_ids (e.g., "12345") in their response text. When the evaluation used
different record_ids (OT13579, OT22334), the guard topics responded with the
wrong IDs, causing grader failures ("agent refers to a different record_id").

**Resolution:** Guard topics should be OFF unless they match evaluation test
phrases AND use dynamic variables (not hardcoded values).

## Guard Topic Decision Tree

```
Does the evaluation test use EXACT trigger phrases matching the guard topic?
  → YES → Are the guard topic responses dynamic (variables, not hardcoded)?
    → YES → Turn ON
    → NO (hardcoded IDs/text) → Turn OFF, fix via instructions instead
  → NO → Turn OFF, let generative AI handle it
```

## When Guard Topics Help

- Exact phrase match with evaluation test triggers
- Structured intake flow (ask record_id → confirm setting → return audit)
- Responses use variables, not hardcoded data

## When Guard Topics Hurt

- Hardcoded record_ids or response text that doesn't match test variants
- Topic triggers that don't exactly match evaluation phrases
- Responses that reference wrong data (different record_id than test case)
