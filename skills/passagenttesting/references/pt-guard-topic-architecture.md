# PT Guard Topic Architecture — Why Unconditional RF Fails

## PT Guard Topic Structure

PT has 15 Eval Guard intake topics (activated June 15, 2026):
- PT Eval Guard - CPT Alignment Intake
- PT Eval Guard - Caregiver Competency Intake
- PT Eval Guard - Caregiver Education Intake
- PT Eval Guard - Continued Care Intake
- PT Eval Guard - Daily Note Compliance Intake
- PT Eval Guard - Denial Risk Intake
- PT Eval Guard - Evaluation Compliance Intake
- PT Eval Guard - Fall Interventions Intake
- PT Eval Guard - Fall Risk Intake
- PT Eval Guard - Functional Outcomes Intake
- PT Eval Guard - Missing Components Intake
- PT Eval Guard - Progress High Risk Intake
- PT Eval Guard - Recommendations Intake
- PT Eval Guard - Section GG Intake
- PT Eval Guard - Skilled Justification Intake

## Why They Conflict with Unconditional RESPONSE FORMAT

These are **intake topics** — they match specific compliance patterns and produce targeted element checks. Their `additionalInstructions` use short, focused prompts (not the full RESPONSE FORMAT).

When RESPONSE FORMAT is unconditional, the model tries to apply the 6-section audit format (Classification, Score X/100, Risk Level, Missing Elements, Recommendations, Advisory) to EVERY response — including intake topic responses. This creates:

1. **Format conflict**: Intake topics want focused element answers, not full audits
2. **Routing confusion**: Model can't decide if it's answering an intake question or an audit
3. **Response quality drop**: Neither the intake format nor the audit format is produced well

## Comparison with SLP Guards

SLP has 17 Conv Guard topics — but these are **conversation guards**, not intake guards. They check for specific conversation patterns (discharge followup, daily metrics, etc.) and produce element-level responses that align with the RESPONSE FORMAT.

The key difference:
- **PT guards**: Intake pattern (ask follow-up questions) → conflicts with unconditional RF
- **SLP guards**: Element check pattern (produce audit-quality responses) → benefits from unconditional RF

## Recommendation

For agents with intake-pattern guard topics:
- Keep RESPONSE FORMAT conditional ("Use for full document audits only")
- Add per-guard-topic `additionalInstructions` that reference the RESPONSE FORMAT for intake results
- Or: convert intake topics to element-check topics that produce structured output

For agents with conversation/element-check guard topics:
- Unconditional RESPONSE FORMAT works well
- All topics produce consistent structured output
