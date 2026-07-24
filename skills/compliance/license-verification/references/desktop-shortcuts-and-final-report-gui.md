# Desktop shortcuts + final max-coverage GUI workflow

Session learning: Kevin wants two separate entry points for ENSG license verification:

1. **Click-and-forget desktop shortcut**
   - Shortcut name: `ENSG License Report - Click and Forget.lnk`
   - Target: `D:/license-verification/run_final_report_click_and_forget.cmd`
   - CMD runs: `python build_final_max_coverage.py`
   - Purpose: non-interactive final max-coverage report generation, then email final workbook.
   - Log: `D:/license-verification/logs/click_and_forget_latest.log`
   - This path should be separate from the Streamlit/web GUI.

2. **Web GUI desktop shortcut**
   - Shortcut name: `ENSG License Verification - Web GUI.lnk`
   - Target: `D:/license-verification/launch_web_gui.cmd`
   - CMD runs: `python -m streamlit run app.py`
   - Purpose: visual dashboard, report viewing/downloading, settings/account swaps, manual user exploration.

## Final max-coverage builder pattern

Permanent script: `D:/license-verification/build_final_max_coverage.py`

Design:
- Find the latest complete workbook with at least 426 Detailed Results rows.
- Refresh configured high-confidence states from `config.json` (`final_report.refresh_states`, currently Iowa + South Carolina).
- Set `DISABLE_EMAIL=1` for intermediate `verify_all.py <STATE>` refreshes so only the final merged workbook emails.
- Merge refreshed rows by `(State, Facility, Admin Name)`.
- Normalize legacy result labels (`VERIFIED` -> `PASS`, `ERROR` -> `NEEDS MANUAL REVIEW`).
- Force low-confidence CAPTCHA states from `final_report.manual_states` (Alaska, Tennessee, Utah) to `NEEDS MANUAL REVIEW` with clear notes.
- Write `results/FINAL_ENSG_max_admin_coverage_YYYY-MM-DD_HHMMSS.xlsx`.
- Email only the final workbook using `verify_all.send_email_alert`.

Fast verification command that avoids CAPTCHA spend/email while proving the permanent builder works:

```bash
cd D:/license-verification
python build_final_max_coverage.py --skip-refresh --no-email
```

Expected workbook invariants after this session:
- 426 rows
- 17 states
- Executive Summary, Charts, Detailed Results tabs
- Known current counts: 311 PASS, 26 FAIL, 89 NEEDS MANUAL REVIEW
- Alaska, Tennessee, Utah should be NEEDS MANUAL REVIEW by high-accuracy policy.

## Web GUI additions

`app.py` should include:
- `Visual Dashboard` tab with metrics/charts from latest `FINAL_ENSG_max_admin_coverage_*.xlsx`.
- `Settings` tab to edit email recipients, `final_report.refresh_states`, and replace 2captcha API key locally.
- `Run Verification` should call `build_final_max_coverage.py`, not raw `verify_all.py`, because Kevin wants the comprehensive max-coverage workbook.

## Config conventions

`config.json`:

```json
"email": {
  "to": ["kevinmoon7@gmail.com", "lee85lisa@gmail.com"],
  "from": "123713644@ensignservices.net",
  "smtp_server": "smtp.office365.com",
  "smtp_port": 587,
  "use_tls": true
},
"final_report": {
  "refresh_states": ["IOWA", "SOUTH CAROLINA"],
  "manual_states": ["ALASKA", "TENNESSEE", "UTAH"],
  "open_after_run": false
}
```

`verify_all.py` should parse `email.to` as either a list or comma/semicolon-separated string.

## 2captcha account swap convention

Centralized solver (`captcha_solver.py`) should load `TWOCAPTCHA_API_KEY` from:
1. Process environment
2. Project-local `D:/license-verification/.env`
3. Hermes profile `.env`

The GUI Settings tab writes/replaces the project-local key so Kevin can visually swap 2captcha accounts without editing code.

## Required ad-hoc verification for this workflow

When changing any of these files (`app.py`, `build_final_max_coverage.py`, launcher CMDs, `captcha_solver.py`, `states/south_carolina.py`, `verify_all.py`), create a temp verifier under `C:/Users/kevin/AppData/Local/Temp` using `tempfile.mkstemp(prefix="hermes-verify-", suffix=".py")` and clean it up.

Minimum checks:
- `py_compile` changed Python files.
- CMD files exist and point to separate workflows.
- Desktop `.lnk` files exist if shortcut creation was part of the task.
- `config.json` has requested recipients and final_report settings.
- `app.py` contains Dashboard/Settings and calls `build_final_max_coverage.py`.
- `captcha_solver` capability map and SC central-client import are present.
- `python build_final_max_coverage.py --skip-refresh --no-email` creates a 426-row, 17-state final workbook with expected tabs and manual gates.

Do not call the fast check full-suite green; describe it as focused ad-hoc verification.