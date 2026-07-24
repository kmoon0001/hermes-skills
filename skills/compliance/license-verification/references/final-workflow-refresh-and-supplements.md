# ENSG license final workflow: automatic refresh + evidence supplements

Use this for ENSG NHA license verification final workbooks.

## Production workflow expectation

Kevin wants the final report workflow to be production-first:

1. Refresh every feasible/high-confidence automated state each run, not just a small default subset.
2. Use 2captcha where the portal flow is validated (currently South Carolina reCAPTCHA v2).
3. Do not spend/pretend on CAPTCHA types already shown unreliable unless a new validated workflow exists:
   - Tennessee BotDetect image CAPTCHA: keep manual/semi-auto unless a reliable portal solution is proven.
   - Alaska DataDome: requires captchaUrl + exact userAgent + residential/proxy config; proxyless 2captcha is not enough.
   - Utah reCAPTCHA v3: intermittent; prefer official public evidence or roster import when available.
4. Merge supplemental public/manual evidence after broad manual gates, so official evidence can override a manual gate while CMS/public-only evidence remains NEEDS MANUAL REVIEW.
5. Produce the production workbook, verify row counts/status counts/confidence columns, then create/expand a formal testing suite.

## Implementation pattern proven in-session

- `build_final_max_coverage.py` should refresh all feasible states by default:
  AL, AZ, CA, CO, ID, IA, KS, NE, NV, OR, SC, TX, WA, WI.
- Apply manual gates for AK/TN/UT first, then merge supplemental evidence afterward.
- A no-pay/public-evidence supplement can be auto-built from `results/no_pay_maximal_ut_tn_public_pass_*.xlsx`.
- Only convert definitive official Utah DOPL active HFA evidence to PASS.
- Keep Tennessee BotDetect and public/CMS-only evidence as NEEDS MANUAL REVIEW with detailed notes.
- Retry transient California timeout rows with a focused supplemental workbook rather than letting a full-state refresh downgrade known good rows.

## Verification pattern

Until a formal suite exists, use a temp `C:/Users/kevin/AppData/Local/Temp/hermes-verify-*.py` script to verify:

- final workbook exists;
- `Detailed Results` has 426 rows;
- confidence columns are present;
- PASS/FAIL/MANUAL counts match expected production output;
- no-pay supplement builds from the source workbook;
- Utah official evidence rows become PASS;
- California timeout/manual rows are cleared when retry supplement succeeds.

Clean up the temp verification script and explicitly call it ad-hoc verification, not canonical suite green.
