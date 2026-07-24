# SLP Official Source + Scoring Calibration Pattern (2026-06-30)

Use this reference when SLP_Specialist regresses after knowledge-source changes or when ASHA/CMS/IDDSI/NIDCD sources are being migrated from web sources to uploaded files.

## What was validated

Live Copilot Studio UI was the source of truth. Microsoft Learn confirmed uploaded files are agent-level knowledge sources and must reach `Ready` before retrieval is dependable. Marking a source as `Official source` in the UI displays an `Update agent instructions? (preview)` confirmation and updates the agent grounding instructions so that source is treated as authoritative.

Validated live source workflow:
1. Upload authoritative SLP PDFs through Copilot Studio UI.
2. Rename each uploaded file source to a clean official display name, not the raw filename.
3. Rewrite the description with retrieval terms: topic, assessment names, therapy/intervention terms, coding terms, and compliance use cases.
4. Toggle `Official source` ON.
5. Confirm the Microsoft official-source dialog.
6. Save.
7. Verify the detail page shows `Status: Ready`, `Official source` ON, and Save disabled.
8. Verify the list view shows all uploaded file sources with clean names and `Ready` status.

## Durable SLP source set from this session

The 10 uploaded file sources were:
- ASHA Adult Dysphagia Practice Portal
- ASHA Voice Disorders Practice Portal
- ASHA Reimbursement and CPT Coding for SLP
- CMS Medicare Learning Network Therapy
- ASHA Cognitive-Communication Disorders Practice Portal
- ASHA AAC Practice Portal
- ASHA Scope of Practice for SLP
- IDDSI Framework
- NIDCD Communication Disorders Health Information
- ASHA Aphasia Practice Portal

## Key pitfall

Do not treat retrieval fixes and scoring fixes as the same problem. File uploads + Official source reduce web-crawl/retrieval variance, but failing eval cases can still be scoring-calibration defects.

Old Public website sources may remain visible and Ready above the new files. If they stay active, they can still compete in retrieval. Prefer official uploaded files, and deactivate old PublicSiteSearchSource rows only after the file sources are verified stable.

## Failing-case pattern from the regression

The regression was three SLP scoring-calibration misses:

1. Recertification GOOD
   - Expected: LOW, 94-99
   - Actual: MODERATE, 83
   - Lesson: do not over-penalize minor SMART-goal specificity gaps when physician/NPP recertification, CCC-SLP signature, frequency/duration, objective progress, skilled need, and continuation/discharge plan are present.

2. Sparse initial evaluation MODERATE
   - Expected: MODERATE, 65-78
   - Actual: HIGH, 35
   - Lesson: a sparse but signed eval with SLP-relevant impairments, broad goals, frequency, and CCC-SLP signature should usually have a Moderate floor unless skilled need/plan/signature/therapy condition is absent.

3. Voice/motor speech GOOD
   - Expected: LOW, 88-95
   - Actual: LOW, 97
   - Lesson: excellent voice evals should cap at 95 when explicit prognosis, HEP/carryover, or discharge criteria are missing. Reserve 96-100 for fully complete notes.

## Recommended micro-patch if retest still fails

Add this as a narrow scoring-calibration block. Do not broad-rewrite SLP instructions or topics while testing this lever.

```text
SCORING CALIBRATION — SLP DOCUMENTATION AUDIT

Use exact output labels:
- Risk Level: LOW RISK / MODERATE RISK / HIGH RISK
- Score: NN/100

Do not over-penalize otherwise complete recertifications. A recertification with physician/NPP recertification, CCC-SLP signature, frequency/duration, objective progress from baseline, skilled need statement, and discharge/continuation plan is LOW RISK and should generally score 94-99. Minor SMART-goal specificity gaps are recommendations, not Moderate Risk, when the core recert elements are present.

For sparse but signed initial evaluations, use a Moderate floor when the note identifies SLP-relevant impairments, treatment frequency, broad goals, and CCC-SLP signature. Missing standardized scores, objective baselines, and SMART criteria should usually produce MODERATE RISK, 65-78, unless there is no skilled need, no plan of care, no signature, or no therapy-relevant condition.

Cap excellent voice/motor speech evaluations at 95 when any of these are missing: explicit prognosis statement, home exercise/carryover plan, or clear discharge criteria. Do not score 96-100 unless objective measures, standardized patient-reported outcome, functional impact, SMART goals, skilled rationale, prognosis, HEP/carryover, discharge criteria, physician certification, and CCC-SLP signature are all present.
```

## Sequence for future sessions

1. Verify live UI source state first.
2. If uploaded files are not Ready or not Official, fix knowledge first.
3. If knowledge is verified and the same scoring failures remain, apply only the micro calibration patch.
4. Retest the exact failing cases before running the full suite.
5. Avoid adding topics, re-enabling web browsing, or broad instruction rewrites unless the micro patch fails with evidence.
