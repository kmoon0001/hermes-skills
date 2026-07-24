# Final production confidence workflow pattern (2026-06)

Use this reference when updating or verifying the ENSG license-verification production workflow after a max-coverage workbook run.

## Durable workflow lessons

- The final workbook should preserve every facility/admin row and avoid definitive claims for unreliable CAPTCHA/manual states.
- Add evidence-based confidence/probability columns to the workbook when presenting legal/compliance verification results:
  - `Confidence Score %`
  - `Confidence Tier`
  - `Confidence Basis`
- Treat confidence as an evidence-weighted probability estimate for prioritization, not a legal guarantee.
- Apply manual gates before merging stronger supplemental official evidence. This lets broad AK/TN/UT safety gates remain conservative while allowing official no-pay/public roster evidence to override a manual row when it is strong enough.
- Utah pattern: official DOPL active HFA evidence can become PASS; public/CMS-only, unresolved, likely non-HFA, or credential-type ambiguity rows remain NEEDS MANUAL REVIEW.
- Tennessee pattern: preserve public/CMS evidence in notes, but do not turn BotDetect-blocked rows into PASS unless an official no-CAPTCHA source is validated.
- Alaska pattern: keep manual unless a proxy-backed DataDome solver workflow is validated.

## Production builder pattern

`build_final_max_coverage.py` should:
1. Select the complete prior workbook with the highest definitive PASS/FAIL coverage, using mtime only as a tiebreaker.
2. Refresh the configured high-confidence states by default.
3. Merge latest single-state refresh outputs.
4. Apply manual gates to unresolved low-confidence states.
5. Build and merge a no-pay/public evidence supplement when `results/no_pay_maximal_ut_tn_public_pass_*.xlsx` exists.
6. Merge targeted correction workbooks after manual gates so high-quality corrections win by `(state, facility, admin)`.
7. Write one final workbook with confidence rollups in Executive Summary and per-row confidence fields in Detailed Results.

## Frontend/docs/shortcut update checklist

When changing the production workflow, update all user entry points together:

- `README.md`
- `CHECKLIST.md`
- `docs/verification-log.md`
- `docs/steering.md`
- `docs/skills.md`
- `docs/final-production-workflow.md`
- Streamlit frontend `app.py`
- `run_final_report_click_and_forget.cmd`
- `launch_web_gui.cmd`
- latest-workbook shortcut such as `open_latest_final_report.cmd`

For Streamlit long-running subprocesses, run the workflow unbuffered with `python -u ...` so progress output appears while the job is running.

## Ad-hoc verification pattern when no canonical suite exists

If the repo has no canonical test/lint/build command, create a temporary focused verification script under an OS-safe temp path:

- Directory: `C:/Users/kevin/AppData/Local/Temp`
- Filename prefix: `hermes-verify-`
- Use `tempfile.mkstemp(...)` or equivalent to avoid quoting/path issues.
- Run it against the changed behavior.
- Clean it up afterward when possible.
- Report it explicitly as targeted ad-hoc verification, not suite green.

A good focused verifier for this workflow checks:

- Python compile/import for changed executable files.
- Config contains all feasible refresh states and supplemental merge patterns.
- Frontend text/behavior references confidence/no-pay workflow and uses `python -u` for long runs.
- Docs mention confidence scoring, manual-state policy, and shortcuts.
- Shortcuts point to intended dashboard/final/open-latest workflows.
- `python build_final_max_coverage.py --skip-refresh --no-email` succeeds.
- Final workbook has 426 rows, expected PASS/FAIL/MANUAL counts, confidence columns, expected confidence tiers/average, and expected manual-by-state counts.
- Git working tree is clean and local HEAD matches `origin/master` after commit/push, if the task included sync.

## Communication preference observed

For this user/project, minimize narration once the user asks to execute. Report the concrete artifact paths, counts, verification command/result, commit SHA, and any remaining blockers. Avoid long theoretical explanations unless asked.
