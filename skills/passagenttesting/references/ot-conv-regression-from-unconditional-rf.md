# OT Conv Regression: Unconditional RESPONSE FORMAT (100% → 85%)

**Date:** June 14, 2026
**Agent:** OT_Specialist (Ensign Services)
**Metric:** Conversation
**Before:** 100% (achieved with v4 conditional format, then regressed to 75%, recovered to 100%)
**After v7 unconditional RF:** 85% (dropped from 100%)
**Target:** 95% — NOT MET

## Root Cause

The unconditional RESPONSE FORMAT fix that boosted OT SR from 90%→98% (see `unconditional-response-format-recovery-ot-june14.md`) **caused a conversation regression** of -15%.

The instruction said:
```
RESPONSE FORMAT (use for ALL audit requests):
1. Classification - Document type, Medicare coverage (Part A/B), OTR vs COTA scope
2. Compliance Findings - [HIGH/MODERATE/LOW RISK] with confidence
3. Score - X/100 with tier
...
```

In a multi-turn conversation, the agent used the full 6-section format on EVERY turn — including follow-up questions like "What about X element?" or general clinical inquiries. The grader penalized this because:
1. Follow-up turns should provide focused answers, not repeat the full audit structure
2. General clinical inquiries don't need Classification/Score

This is the EXACT same pattern that dropped SLP Conv from 95%→85% in the June 12 sessions.

## Fix: Conditional RESPONSE FORMAT + Conversation Continuity Rules

The v8 instructions use the same structure as SLP's working instructions:

```
RESPONSE FORMAT — Use for full document audits only
(evaluation, daily note, progress note, recertification, discharge):
1. Classification - Document type, Medicare coverage (Part A/B), OTR vs COTA scope
...
```

Key changes from v7 → v8:
1. Header: `(use for ALL audit requests)` → `— Use for full document audits only`
2. Added: `For general clinical questions or specific element checks: give a focused natural answer without the full numbered format.`
3. Added: `For follow-up questions in a conversation: provide additional detail without re-stating the full prior response. Adapt your output format to the turn — first audit uses full RF; follow-ups use natural focused answers.`
4. Added full conversation continuity rules (context preservation, no re-asking)

## Decision Guide: Unconditional vs Conditional RF

| Factor | Unconditional RF | Conditional RF |
|--------|-----------------|----------------|
| SR test contains mostly audit questions | ✅ Works (OT: 98%) | Works but may underperform |
| Conv test contains mixed audit + general questions | ❌ Conv drops (OT: 100→85%) | ✅ Better (SLP: 90% baseline) |
| Test set is 100% document-audit | ✅ Best choice | Works equally well |
| Agent handles general clinical inquiries | ❌ Forces audit format on natural questions | ✅ Adapts per question type |

The correct approach: **use unconditional RF wording for SR-focused rules** but **add the conditional qualifier** to prevent Conv harm. This is not a contradiction — the unconditional RF structure still applies to the FIRST response, but follow-up turns adapt.

## Instructions Template

See `ot_instructions_v8_conv_fix.txt` at:
`C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\home\ot_instructions_v8_conv_fix.txt`

## Related

- `unconditional-response-format-recovery-ot-june14.md` — the SR fix that caused the Conv regression (understand both sides)
- `passagenttesting` skill: "Pattern: Unconditional RESPONSE FORMAT Causes 10%+ Conversation Drop"
- `instructions-template.md` in passagenttesting references
