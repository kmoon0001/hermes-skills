# Final max-coverage report workflow

Use this when the user asks for the final Excel report with as many administrators included as possible.

## Goal
Produce one timestamped Excel workbook with every administrator row from the ENSG master file, while preserving high-confidence verification results and marking low-confidence CAPTCHA states as manual instead of inventing results.

## Pattern
1. Prefer a fresh `python verify_all.py` full run when it can complete.
2. If the full run hangs or exceeds tool timeouts, do not keep waiting blindly. Use the most recent complete 426-row workbook as the base.
3. Refresh newly improved states with single-state runs, e.g.:
   - `python verify_all.py IOWA`
   - `python verify_all.py "SOUTH CAROLINA"`
4. Merge refreshed rows into the complete base workbook keyed by `(State, Facility, Admin Name)`.
5. Normalize legacy result labels before writing the final workbook:
   - `VERIFIED` -> `PASS`
   - `ERROR` -> `NEEDS MANUAL REVIEW` when it represents workflow failure rather than license failure
6. Force manual-gated states to `NEEDS MANUAL REVIEW` when high-accuracy policy says automation is unreliable:
   - Alaska: DataDome needs captchaUrl + matching userAgent + residential/proxy config
   - Tennessee: BotDetect image solving unreliable
   - Utah: reCAPTCHA v3 scores intermittently reject tokens
7. Write a new final file under `results/` using a clear name like:
   - `FINAL_ENSG_max_admin_coverage_YYYY-MM-DD_HHMMSS.xlsx`
8. Verify the workbook with an ad-hoc temp script under `C:/Users/kevin/AppData/Local/Temp/hermes-verify-*.py`.

## Verification checklist
The temp script should open the final workbook and assert:
- `Detailed Results` sheet exists
- headers start with `State, Facility, Admin Name, License Status, Result`
- expected row count is present (426 for the current ENSG master)
- expected state count is present (17 for the current ENSG master)
- result counts make sense
- spot-check refreshed states (Iowa and South Carolina in the 2026-06-28 run)
- Alaska/Tennessee/Utah are manual-gated if not independently validated

## Session example from 2026-06-28
Final workbook produced:
`D:/license-verification/results/FINAL_ENSG_max_admin_coverage_2026-06-28_045739.xlsx`

Counts from the initial 2026-06-28 max-coverage build:
- 426 rows
- 17 states
- 311 PASS
- 26 FAIL
- 89 NEEDS MANUAL REVIEW

After targeted refresh/parser fixes on 2026-06-28, final reduced workbook:
`D:/license-verification/results/FINAL_ENSG_max_admin_coverage_2026-06-28_085935.xlsx`

Reduced counts:
- 426 rows
- 17 states
- 327 PASS
- 53 FAIL
- 46 NEEDS MANUAL REVIEW

Manual review after reduction is only hard CAPTCHA/manual states:
- Alaska: 3 (DataDome)
- Tennessee: 11 (BotDetect)
- Utah: 32 (reCAPTCHA v3 scoring)

Resolved cleanup states:
- Nevada: 3/3 PASS via BELTCA PDF roster
- Texas: 86 PASS / 24 FAIL / 0 manual; slash-separated admin cells are tried as alternates; blank Texas NFA status/license rows are definitive FAIL, not manual
- California: 85 PASS / 3 FAIL / 0 manual after timeout retries; `Revoked Not Employable` classifies as FAIL
- Idaho: 13 PASS / 2 FAIL / 0 manual; parser handles same-row `Nursing Home Administrator License\tNAME\t\tActive\tEXP\tNo`
- South Carolina: 8 PASS / 1 FAIL via centralized 2captcha

Spot checks:
- Iowa `Amanda Birch / Leah Nelson` -> ACTIVE / PASS, #132346
- South Carolina `Raymond Tiller` -> ACTIVE / PASS
- Idaho `Emily Chrislip`, `James Empey`, `Sean Stock` -> ACTIVE / PASS after parser fix
- Texas `Shaun Baldwin / Joshua Lewis` -> Active / PASS matching alternate Shaun Baldwin
- Alaska, Tennessee, Utah -> NEEDS MANUAL REVIEW by high-accuracy policy

## Pitfall: do not leave a hanging builder script
A generated one-off script (`build_final_max_report.py`) hung because imports/full-state setup were slow and gave no progress output. It was removed and replaced by the safe workbook-merge workflow. If you create a one-off builder, either make it deterministic and fast or delete it after use; do not leave a stale script that looks canonical.
