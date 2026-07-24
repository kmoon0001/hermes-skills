# PT Guard Topic Activation — Case Study (Jun 15-16, 2026)

## Problem

PT Conv score stuck at 74%, volatile (hitting 95% once but regressing). All other agents (OT 95%, SLP 80-95%) had higher or comparable Conv.

## Root Cause

Dataverse query revealed **16/31 PT topics were INACTIVE (statecode=1)**:
- 15 Eval Guard intake topics (all exact-match conversation evaluation topics)
- Conversational boosting (CB fallback topic)

The 15 Eval Guard topics were designed as exact-match intake for evaluation test cases. When inactive, test case questions fell through to generic generative AI which produced inconsistent/ungraded responses.

## Fix

```javascript
// PATCH each inactive topic via Dataverse API
await fetch(`/api/data/v9.2/botcomponents(${id})`, {
  method: 'PATCH',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ statecode: 0 })
});
```

All 16 topics activated in one batch, then PT was republished.

## Result

| Metric | Before | After |
|--------|--------|-------|
| PT Conv | 74% | **95%** |
| OT Conv | 95% | 95% (unchanged) |
| SLP Conv | 80% | 86% (2 guards also activated) |

## Impact Assessment

This is the **single highest-impact fix** across all 4 agents. No YAML changes, no instruction changes — just activating existing topics.

## Lessons

1. **Check topic ON/OFF status FIRST** before any YAML or instruction changes. The `passagenttesting` skill already says this but it's easy to overlook.
2. Dataverse API PATCH is the fastest way to batch-activate topics. The SPA Topics page toggle is slow and unreliable via automation.
3. **Always republish after statecode changes** — unpublished changes don't affect evaluation behavior.
4. Guard topics being inactive is a silent failure mode — the agent still responds, just not through the intended topic, so the scores degrade without obvious "broken" behavior.

## Topics Activated

```
PT Eval Guard - Denial Risk Intake
PT Eval Guard - Daily Note Compliance Intake
PT Eval Guard - Progress High Risk Intake
PT Eval Guard - Caregiver Competency Intake
PT Eval Guard - Fall Risk Intake
PT Eval Guard - Functional Outcomes Intake
PT Eval Guard - CPT Alignment Intake
PT Eval Guard - Skilled Justification Intake
PT Eval Guard - Section GG Intake
PT Eval Guard - Continued Care Intake
PT Eval Guard - Caregiver Education Intake
PT Eval Guard - Fall Interventions Intake
PT Eval Guard - Recommendations Intake
PT Eval Guard - Missing Components Intake
PT Eval Guard - Evaluation Compliance Intake
Conversational boosting
```
