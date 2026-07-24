# Cross-Agent Score Tracking (June 17, 2026)

## Current Status

| Agent | SR | Conv | Status | Fix Applied |
|-------|-----|------|--------|-------------|
| OT | 99% | 100% | ✅ DONE | Conciseness + hedging removal |
| SLP | 95% | 100% | ✅ DONE | Hedging + citation + conciseness + balanced SR |
| TDA | 96% | 100% | ✅ DONE | Conciseness |
| PT | 97% | 90% | 🔧 IN PROGRESS | Soft citation requirement (baseline preserved) |

## PT Failure Analysis (June 17, 2026)

**Conv 90% = 18/20 pass, 2/20 fail:**
1. "assess caregiver competency documentation" → FAIL (grader: didn't cite knowledge sources)
2. "review caregiver education documentation" → FAIL (grader: didn't cite knowledge sources)

**Key finding:** OT has dedicated caregiver topics. PT does not. Topic-based remediation recommended (see references/pt-caregiver-topic-gap-2026-06.md).

## PT Fix Timeline

| Time | Score | Fix Applied | Result |
|------|-------|-------------|--------|
| Original | 90% Conv, 97% SR | Baseline | Stable |
| 1:24 AM | 85% Conv | CRITICAL citation ban | REGRESSION |
| 2:54 AM | 80% Conv | Stacked aggressive fixes | REGRESSION |
| 7:32 AM | 90% Conv | Reverted to baseline + soft citation req | Restored |

## Lesson Learned

NEVER apply fixes from one agent to another without per-agent root cause analysis. SLP's hedging fix worked for SLP but regressed PT when applied blindly.

## Next Step for PT

Create a dedicated caregiver competency topic (copy from OT). This is the MS Learn-recommended approach for specific failure patterns.
