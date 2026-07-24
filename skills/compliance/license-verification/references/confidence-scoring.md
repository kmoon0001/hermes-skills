# ENSG Confidence Scoring and Ad-hoc Verification Pattern

Use this when Kevin asks whether the Excel report includes the detailed evidence or wants a probability/confidence score for license results.

## Workbook evidence columns to preserve

For the ENSG no-pay/gap workbook, keep the small-detail columns visible rather than only summarizing verbally:

- Official License Evidence
- Public Name Evidence
- CMS Facility / CMS CCN
- CMS Match Score
- CMS Public Manager Candidates
- What This Means
- Next Free Step
- Lowest-Cost Effective Paid Step

For the full final ENSG report, keep source/evidence fields plus CMS risk fields and add confidence columns:

- Confidence Score %
- Confidence Tier
- Confidence Basis

For Utah/Tennessee no-pay/gap workbooks, use clearer labels:

- Accuracy Probability %
- Confidence Tier
- Confidence Basis
- Confidence Method sheet explaining the scoring model

## Confidence scoring semantics

Be explicit that the score is an evidence-based probability estimate for prioritization, not a legal guarantee.

For the full final report, the score estimates likelihood that the PASS/FAIL/NEEDS MANUAL REVIEW classification is accurate.

For gap/no-pay workbooks, the score estimates likelihood that the row's stated classification is accurate, not necessarily the probability that the person is licensed.

Recommended scoring bands:

- HIGH: 90%+ — official board/API/roster evidence, source-file fact, or strong direct evidence.
- MEDIUM: 70-89% — useful evidence but not definitive license proof, or conservative official NOT FOUND/alias ambiguity.
- LOW: below 70% — manual portal lookup, CAPTCHA blocked state, missing definitive evidence, or credential-type ambiguity.

Conservative defaults used successfully:

- Official board/API/roster PASS: about 96-99 depending on source and captured URL/expiration/note.
- Official NOT FOUND/FAIL: about 87-92; keep below positive official matches because aliases/name changes can overturn it.
- CMS/public-only relationship confirmation: about 76-85.
- Manual/CAPTCHA blocked rows: about 30-35.
- Different-license-type/outside-HFA inference: about 60-70.
- Missing admin in source file: about 90 for the missing-admin classification only.

## Generator implementation pattern

In `verify_all.py`, add a pure helper such as `confidence_details(row) -> (score, tier, basis)` and call it inside `write_results_excel` when writing rows. Add summary metrics for average confidence and High/Medium/Low counts.

In `build_final_max_coverage.py`, keep backward compatibility with older workbooks by extending the row-normalization key list; missing confidence fields should normalize to blank. When choosing a base workbook for a max-coverage final report, prefer the workbook with the most definitive PASS/FAIL rows, then use modified time as a tie-breaker. Do not blindly choose the newest modified workbook because old files can receive newer timestamps after copy/edit.

For no-pay/gap workbooks, a small standalone script can copy the workbook, append confidence columns, color tiers, and add a `Confidence Method` sheet. Keep this script deterministic and independent of live scraping.

## Verification pattern after changing report generators

If there is no canonical test suite, create a focused temporary verification script under the OS temp directory with filename prefix `hermes-verify-`. For Kevin's Windows profile, use `C:/Users/kevin/AppData/Local/Temp` or Python `tempfile` to create the file safely.

The ad-hoc script should verify behavior, not merely syntax:

1. Unit-level scoring bands for official PASS, manual/CAPTCHA, and official NOT FOUND rows.
2. Generated workbook headers include confidence columns and summary rollups.
3. Backward compatibility reading older no-confidence workbooks.
4. Max-coverage base selection prefers definitive PASS/FAIL coverage over mtime.
5. No-pay/gap workbook confidence columns and method sheet are present.

After running, remove the temporary verification script when possible and report the result as targeted ad-hoc verification, not as full suite green.