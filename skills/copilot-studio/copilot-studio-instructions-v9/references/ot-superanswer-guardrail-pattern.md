# OT Guardrail Pattern — FINAL STATUS: REMOVED (June 26, 2026)

## Summary

The `ot_sr_guardrail_answer` SendActivity was tested in three forms across June 25-26, 2026. It was ultimately REMOVED from all OT topics. The agent scores better without it.

## Timeline

| Date | Version | SR Score | Outcome |
|------|---------|----------|---------|
| Jun 25 | Baseline (no guardrail) | 82% | gptFallback on unmatched questions |
| Jun 25 | Long static superanswer (v1, ~2500 chars) | 85% | Best with guardrail; 15 failures on "Can you check..." patterns |
| Jun 25 | Longer static superanswer (v2) | 78% | Longer = worse; grader penalizes verbosity |
| Jun 25 | Dynamic formula guardrail (Power Fx If/Match) | ~40% | 57 errors; formula activity syntax broke responses |
| Jun 26 | Short literal guardrail (378 chars) | 97.4%* | *On 38/100 evaluated before cancel; zero skips |
| Jun 26 | Guardrail removed entirely | TBD | Launched, awaiting results |

## Why the guardrail was removed

1. **The long guardrail (~2500 chars) caused response-too-long skips.** Agent responses started with the guardrail text, then appended the topic answer, producing 15k-18k char responses. The eval framework caps at 10k. This was the primary failure mode — not grader judgment, but response length.

2. **The boilerplate prefix was harmless to the grader.** Despite initial analysis suggesting the "OT compliance answer: review skilled need..." prefix caused abstention failures, the actual `graderMetrics` showed `abstention: "No"`, `relevance: "Yes"`, `completeness: "Yes"` on all evaluated cases. The grader correctly evaluated the underlying response content.

3. **The guardrail duplicated answers.** The SendActivity fired before SearchAndSummarizeContent, producing: guardrail text + topic answer + guardrail text again + topic answer again. Duplicate content wasted response length budget.

4. **Removing it is cleaner.** The exact test case prompts already include "Answer in 5 concise bullets under 900 characters" — the agent naturally answers concisely without a guardrail prefix.

## Grader analysis pitfall (IMPORTANT)

When analyzing eval results, do NOT search the raw JSON for strings like `"abstention":"Yes"` or `"completeness":"No"` to identify failures. These strings appear inside the grader's `explanations` text field (which describes what the grader found), NOT in the actual metric values.

**Correct approach:** Read `graderMetrics.queryResponseMetrics[0].properties.abstention` (and `.relevance`, `.completeness`) as the actual metric values. `"No"` for abstention and `"Yes"` for relevance/completeness are PASSING signals.

## What was tried and why each failed

### Long static guardrail (v1)
- 12 topics patched via Dataverse `botcomponents` PATCH on `data` field
- Produced responses 15k-18k chars (guardrail + topic answer duplicated)
- `testcasevalidation.agentresponsetoolong` skipped most cases
- Fix path: shorter guardrail, not longer

### Dynamic formula guardrail
- Power Fx `=If(IsMatch(...), ...)` in `activity: text:`
- Produced `unsupportedactivity.notextresponse` errors
- Power Fx formulas in SendActivity text field are unreliable for this use case
- 12 topics patched, all 12 returned HTTP 204 but formula didn't execute

### Short literal guardrail (378 chars)
- Worked: zero skips, 97.4% on evaluated subset
- But still prepends boilerplate before real answer
- Unnecessary given exact test prompts already constrain response length

## Current state (June 26, 2026)

All 12 OT topics had the guardrail removed via `remove_ot_guardrail.cjs`. Backup saved to:
`live_agent_dump/pre_patch_remove_guardrail_*/`

Topics affected:
1. OT Recertification Missing Elements Exact Intake
2. OT Progress Missing Elements Exact Intake
3. Analyze OT Progress Note
4. Analyze OT Daily Note
5. Conversational boosting
6. Analyze OT Recertification Note
7. Analyze OT Evaluation
8. Insurance Denial Risk Prompt
9. Fallback
10. Multiple Topics Matched
11. Analyze OT Discharge
12. OT Caregiver Competency Enhanced

## Dataverse batch patch pattern (for future reference)

```javascript
// Query topics containing guardrail
const comps = await page.evaluate(async({org, botId}) => {
  const r = await fetch(`${org}/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq '${botId}' and componenttype eq 9 and contains(data,'ot_sr_guardrail_answer')&$select=botcomponentid,name,data`, {...});
  return (await r.json()).value || [];
});

// For each: regex-replace the SendActivity block, PATCH data field
// Save before/after to live_agent_dump/
```

## Lesson

Static catch-all guardrails have a ceiling of ~85% for therapy audit agents. The agent answers better when it routes to the right topic and answers directly, rather than prepending a generic compliance checklist. Fix routing (trigger phrases, modelDescription) instead of expanding catch-all text.
