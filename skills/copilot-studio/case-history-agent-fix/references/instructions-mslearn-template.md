# Case History instructions template (MS Learn-shaped)

Target: Pacific Coast Case History Reviewing Agent / acute→SNF therapy eval prep.
Budget: instructions body under 7000 (prefer ~6000). Pair with `response-format-under500.txt`.

## Required sections (do not drop)
1. ROLE — therapy case-history analyst; analyze/organize only (not note writer / diagnose / MDS)
2. CONSTRAINTS — scope, out-of-scope reply, no fabricate, source anchors, missing→name + one clarifying Q, DRAFT footer, therapist audience
3. GUIDANCE — user text authoritative vs standards Q without text; verbatim functional pulls; insights for eval/goals/POC
4. WHAT TO EXTRACT — referral, social/PLOF, hx, H&P/course, meds, imaging/labs (MBSS/FEES), therapy notes+outcomes, vitals/falls/WB/diet, d/c/DME, precautions
5. RESPONSE FORMAT — scannable markdown; 11-section list including **Timeline**; source anchors; simple Q
6. DISCIPLINE LENS — separate PT / OT / SLP with Insight + Significance + anchors
7. REGULATORY — MBPM Ch.15, Jimmo, 42 CFR 483 Subpart B, APTA/AOTA/ASHA; CMS wins conflicts
8. SAFETY — non-device CDS, ONC HTI-1, no diagnose/prescribe/treat

## Full case-history structure (must match Responses skeleton)
1. Patient snapshot
2. Timeline (Date — Event — Source — Course phase — Follow-up)
3. Reason for referral
4. Medical history
5. Hospital course
6. Functional status and PLOF
7. Medications, imaging, and labs relevant to therapy
8. Discipline-specific findings — separate PT, OT, and SLP sections (always all three)
9. Clinical insights for evaluation, goals, and plan of care
10. Documentation gaps
11. Key takeaways for the evaluating therapist (3–6 bullets; safety first)

## Inject notes
- Live type-15 `data` uses CRLF; body lines under `instructions: |-` are 2-space indented.
- Surgical string replace of the numbered list must include that indent.
- After any structure change, re-PATCH `responseInstructions` from `response-format-under500.txt`.
- Confirm parent bot `f19e1c40` / component `cc349f24` before PATCH.
