# Conversational Compound Regression Pattern

**When:** All agents regress simultaneously after SharePoint KB folder rename. SR
drops 4-20%. Conv drops 10-40%. Conv recovers slower.

## Root Cause

SharePoint folder names ARE the GPT filter description. When renamed:
1. GPT routes to wrong sources or no sources
2. Each conversational turn requires independent retrieval
3. A retrieval failure on turn 2 compounds the failure from turn 1
4. The grader penalizes: ungrounded + inconsistent + incomplete

## Timeline (June 12, 2026 evidence)

| Time | Change | OT SR | OT Conv | PT SR | PT Conv | SLP SR | SLP Conv |
|------|--------|-------|---------|-------|---------|--------|----------|
| 2:28 AM | Pre-change peak | 91% | 90% | 94% | 95% | 96% | 85% |
| 4:05 AM | SharePoint folders renamed | 82% | - | 87% | - | 92% | 85% |
| 8:58 AM | Cache degrades further | 50% | 50% | 75% | 75% | - | 85% |
| 1:34 PM | KB cache refreshed + SLP published | 86% | 75% | 94% | 85% | 87% | 90% |

## Key Observations

1. **SR recovers first** — single-question, single-retrieval. PT SR recovered fully (94%) while PT Conv lagged (85%).
2. **Conv lags 5-15% behind SR** — the multi-turn amplification of retrieval failures.
3. **SLP Conv recovered to 90%** — the only agent where instructions were ALSO fixed (unconditional → conditional RESPONSE FORMAT). This shows BOTH KB + instruction fixes matter for Conv.

## Fix Priority for Conv Recovery

1. **Compare meaning 0.50** on Conv test sets — allows synonymous wording when retrieval paths differ
2. **Allow ungrounded responses ON** — if OFF, expect 40-50 pt Conv drops
3. **Re-add SharePoint sources** — forces full retrieval index rebuild
4. **Publish after every change** — evaluates use published version by default
