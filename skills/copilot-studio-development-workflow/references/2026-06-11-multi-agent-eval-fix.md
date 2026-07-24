# 6/11/2026 Session — Multi-Agent Eval Fix Record

## Agents & Final Status

| Agent | Conv Latest | SR Latest | Fixes Applied |
|-------|------------|-----------|---------------|
| PT | 99% (100-case) | — | None needed |
| TDA | 100% (20-case) | 91% → pending Compare meaning | CB v2 published, Compare meaning pending |
| SLP | 90% (100-case) | — | Compare meaning pending (10 failures, all ungrounded/incomplete, 0 refusals) |
| OT | 70% (20-case) | 60% | CB v3 published, improved instructions written, Compare meaning pending |

## Fix Progression

### Refusal Eradication (CB v1 → v2/v3)
- Pre-fix: OT at 5-15% with 15-18 refusals per run
- Post CB v3: OT at 70% with 0 refusals
- Root cause: CB fallback said "I don't have specific information" → "I can help with [discipline] documentation compliance..."
- TDA: CB v2 pushed conversation from 85% → 100%

### CB v2 Regression (OT)
- CB v2 "Must cite CMS Ch. 15 per response" caused completeness/groundedness failures
- OT dropped from 70% → 60% with v2
- CB v3 with "Cite when naturally applicable" recovered to 70%
- Lesson: Never force citations in additionalInstructions

### Remaining Gap (70% → 95%)
- All remaining failures are "Knowledge sources not cited" pattern
- Agent response IS relevant and complete, but grader flags missing citations
- Fix: Compare meaning grading at 0.50 threshold (Layer 2, evaluation setup)
- NOT an agent configuration issue — don't over-fix agent

## API Version Correct
- Evaluation API: `api-version=2024-10-01`
- NOT: `api-version=1` or `api-version=2023-03-01-preview`
- State field is STRING: "NotStarted", "InProgress", "Completed", "Failed"
- NOT numeric: {0, 1, 2, 3}

## Popup Dismissal Priority
1. Dismiss BEFORE any navigation (main "What's New" popup)
2. Dismiss AGAIN after "Open code editor" (CB editor popup)
3. Always: Escape ×5 + button hunt for "Got it"/"Skip"/"Dismiss"/"Close"/"OK"
