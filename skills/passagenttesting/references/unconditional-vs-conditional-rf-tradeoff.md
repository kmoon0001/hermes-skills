# Unconditional vs Conditional RESPONSE FORMAT — The SR/Conv Trade-off

## The Pattern

Agent instructions that say **"RESPONSE FORMAT (use for ALL audit requests)"** create a tension:
- **SR benefits:** The grader rewards the structured format (Classification, Score X/100, Risk Levels) — expects it on EVERY audit question
- **Conv suffers:** In multi-turn conversations, forcing the full 6-section format on every turn (including follow-ups and general clinical questions) produces unnatural responses that the grader penalizes

## Evidence (June 2026)

| Agent | RF Strategy | SR | Conv | 
|-------|-------------|-----|------|
| OT v7 | Unconditional "use for ALL audit requests" | **98%** ✅ | **85%** ❌ |
| OT v4/v8 | Conditional/full conversation continuity | 84%→98% | 100%→85%→? |
| SLP | Conditional "Use for full document audits only" | **100%** ✅ | 90% ⚠️ |
| PT v4 | Unconditional (was working) | 90% | 80%→100% (after topic fix) |

## Root Cause

The unconditional format breaks conversation in two ways:
1. **Follow-up redundancy:** When a user asks a follow-up like "What about Section GG?", the agent re-outputs the entire Classification → Score → Advisory structure instead of giving a direct response
2. **General question format mismatch:** When a user asks "Can you give me general guidance on SLP documentation?" the agent forces an audit structure on what should be a natural clinical answer

## The Fix (v8 pattern)

Two instruction changes:

```yaml
# Change this:
RESPONSE FORMAT (use for ALL audit requests):

# To this:
RESPONSE FORMAT — Use for full document audits only
(evaluation, daily note, progress note, recertification, discharge):

For general clinical questions or specific element checks:
give a focused natural answer without the numbered format.
```

Plus add conversation continuity rules:

```yaml
For follow-up questions in a conversation:
  - Provide additional detail on the same document without re-stating the full prior response
  - Adapt your output format to the question
  - First audit response uses full RESPONSE FORMAT
  - Follow-up responses use natural focused answers that reference the prior context
```

## Verification Checklist

After changing RF strategy:

- [ ] SR score did not drop (should stay same or improve)
- [ ] Conv score improved (should see +5-10% gain)
- [ ] Failing cases shifted from "format mismatch" to real content errors
- [ ] Run 2-3 evaluations to confirm non-deterministic variance (<5% spread is normal per MS Learn)
