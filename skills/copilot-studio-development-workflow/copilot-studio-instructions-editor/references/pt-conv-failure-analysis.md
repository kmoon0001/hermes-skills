# PT Conv Failure Analysis (June 17, 2026)

## PT Conv 90% Baseline (260616_1448)

**Pass: 18, Fail: 2, Error: 0**

### Failure 1: Section GG Compliance
- **Question**: "Can you assess the PT evaluation for Section GG compliance and highlight any deficiencies?"
- **Grader reason**: "One or more answers didn't cite knowledge sources"
- **Agent response**: Comprehensive Section GG audit with Classification, Compliance Findings, Score (82/100), Missing Elements, Recommendations — but NO citations to CMS Chapter 15 or any source
- **Fix**: Strengthened citation requirement ("EVERY response MUST include at least one citation when discussing compliance"). Result: PASS on next eval.

### Failure 2: Caregiver Education
- **Question**: "Can you check the PT evaluation for completeness of caregiver education and suggest enhancements?"
- **Grader reason**: Likely same ("didn't cite knowledge sources") or "incomplete"
- **Status**: UNFIXED as of June 17, 2026

## PT Conv 90% After Citation Fix (260617_0732)

**Pass: 18, Fail: 2**

### Failure 1: Caregiver Competency
- **Question**: "assess caregiver competency documentation in the PT evaluation for completeness and compliance"
- **Grader reason**: Unknown (need to click into detail)
- **Status**: UNFIXED

### Failure 2: Caregiver Education
- **Question**: "review caregiver education documentation in the PT evaluation for completeness and compliance"
- **Grader reason**: Unknown (need to click into detail)
- **Status**: UNFIXED

## Key Finding

**Citation fix resolved the Section GG failure** (90% Conv baseline: Section GG failed → after citation fix: Section GG passes). But **caregiver failures persist**. The PT agent has caregiver-specific instructions in "PT-SPECIFIC REQUIRED CONTENT FOR COMMON FAILURES" but isn't applying them properly in conversation mode.

## Fixes That Made PT WORSE

1. **Removing hedging**: Conv 90% → 80% (PT's soft hedging was helping, not hurting)
2. **CRITICAL citation ban**: Conv 90% → 80% (model avoids ALL citations)
3. **Stacking multiple fixes**: Conv 90% → 80% (untestable when multiple changes applied)
4. **Trimming instructions**: Conv 90% → 80% (removed important context)

## Lesson

PT's failures are domain-specific (caregiver topics), not general (hedging/citations). Don't apply SLP fixes to PT.
