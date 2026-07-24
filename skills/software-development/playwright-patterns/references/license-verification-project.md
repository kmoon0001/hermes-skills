# License Verification Project Notes

Source repo: https://github.com/kmoon0001/license-verification
Local path: `D:/license-verification`

## State Coverage (June 2026)

### Fully Automated (8 states)
- AL, AZ, CA, ID, NE, OR, TX, WI
- Each has a `states/<state>.py` with `verify_<state>(admin_name, page=None)` returning `{status, expiration, url, note, days_until_expiry}`
- Playwright-based states reuse a single browser/context per state run via shared `page` parameter

### Semi-Automated via `semi_auto.py` (8 states)
- AK, CO, IA, KS, SC, TN, UT, WA
- Script opens real Chrome (`headless=False`) with persistent profile
- Config block per state: `selector_last`, `selector_first`, `selector_submit`, optional `pre_submit` hook
- Some states need no CAPTCHA solve (UT, WA, KS sometimes) but script still uses real browser

### On Hold
- NV (no public lookup tool on state site)

## CAPTCHA Reality Check
| Technique | Works? | Notes |
|-----------|--------|-------|
| Persistent cookies | Partial | Saves session between runs, but reCAPTCHA v3 re-evaluates every page |
| Stealth libs | Partial | Hides `navigator.webdriver` but doesn't solve challenge |
| Free CAPTCHA solvers | No | None reliable for reCAPTCHA v3 |
| Paid solvers (2Captcha) | Yes | ~$3/1000 solves, 426/month = ~$1.30 |
| Semi-auto real browser | Yes | User solves once per state, script does the rest |

## Ohio-Style PDF Roster Pattern
Nebraska uses a statewide PDF roster instead of online lookup:
- URL: `https://dhhs.ne.gov/licensure/Documents/LTCRoster.pdf`
- Requires `pdfplumber` or `PyPDF2`
- Parsed once per month, matches admin names locally

## Common Site Patterns
- **ASP.NET WebForms**: Look for `#ctl00_ContentPlaceHolder1_btn_find` style selectors
- **Salesforce / shadow DOM**: Use `page.get_by_text("Search", exact=True).first.click(force=True)`
- **Thentia Cloud (AZ)**: Radio button `registerType`, keywords field, Search button
- **LWC shadow DOM (TX)**: Native `<select>` accessible via Playwright pierce-through; `get_by_text` pierces shadow

## Excel Schema
- Source: `C:/Users/kevin/Desktop/ENSG Facilities Only 6.1.26.xlsx`
- Col F (index 5) = Executive Director
- Col 8 (index 8) = State
- Col A (index 0) = Facility name

## Nightly Run Entry Point
```
python run_nightly.py
```
Or on Windows Task Scheduler, use `scripts/run_nightly.bat`.

Calls `verify_all.run_verification()` which:
1. Loads facilities from Excel
2. Groups by state, looks up verifier from `STATE_VERIFIERS` map
3. For Playwright states (AL, AZ, CA, ID, OR, TX, WI): creates ONE shared browser/context for the whole state, opens a new page per admin
4. For other states (NE pdf, semi-auto, etc.): calls verifier directly
5. Runs each lookup through `verify_with_retry(verifier, admin, page=page)`
6. Writes `results/verification_YYYY-MM-DD.xlsx` with PASS/FAIL/NEEDS MANUAL REVIEW
7. If SMTP credentials configured in `config.json` or env vars, sends HTML email with summary + Excel attachment

## Nightly Run Performance
- **Before optimization**: 426 facilities × 1 new browser per admin = ~30-60 min
- **After optimization**: 1 shared browser/context per state = ~10-20 min for 7 Playwright states
- **Nebraska**: PDF download + parse, no browser needed; ~1-2s per facility
- **Semi-auto states**: skipped in nightly run (require user interaction)

## Email Configuration
Add to `config.json`:
```json
"email": {
    "to": "recipient@example.com",
    "smtp_server": "smtp.office365.com",
    "smtp_port": 587,
    "use_tls": true,
    "from": "license-verification@ensignservices.net"
}
```
Or set env vars: `SMTP_USER`, `SMTP_PASSWORD` (env vars take precedence).
**Preference**: store credentials in `.env` at project root, loaded via `python-dotenv` (`load_dotenv()`). Keep secrets out of `config.json` and git.

**Pitfall**: Microsoft 365 tenants may block SMTP AUTH with `535 5.7.139 Authentication unsuccessful, SmtpClientAuthentication is disabled`. Fix: enable SMTP AUTH in admin portal (https://aka.ms/smtp_auth_disabled), use an app password, or switch SMTP provider.

## Windows Desktop Preference
User opens configs/scripts in Notepad for editing. When opening files for the user on Windows, use `notepad <path>` rather than showing contents inline.

## Output Color Scheme
| Result | Fill | Font |
|--------|------|------|
| PASS | Green (`C6EFCE`) | Dark green (`006100`) |
| FAIL | Red (`FFC7CE`) | Dark red (`9C0006`) |
| NEEDS MANUAL REVIEW | Yellow (`FFEB9C`) | Dark gold (`9C5700`) |

## Error Patterns Observed
- **CloudFront 403**: Colorado's `dpo.colorado.gov` blocks headless browsers; moved to semi-auto
- **Alaska 403/hCaptcha**: Commerce site blocks automation; new CBPL search URL still has hCaptcha; moved to semi-auto
- **Iowa Amanda Portal**: JS verification page before search; moved to semi-auto
- **Kansas reCAPTCHA**: Visible on page load; semi-auto required
- **Arizona flaky**: Works but ~8-12 min for 52 admins; retry logic handles transient drops
- **Playwright indentation trap**: When auto-wrapping `with-block` into `if/else`, generator scripts often leave mismatched `try/except` indentation. Fix by rewriting affected verifier files manually or with an AST-aware tool, not line-munging regex.
- **Nested `else` from prior edit**: A previous automation pass accidentally inserted duplicate `else:` blocks at wrong indent levels. Symptoms: `SyntaxError: invalid syntax` at line with bare `except`. Fix: `git checkout -- states/<file>.py` then rewrite the file with correct `if page is None:` / `else:` structure.
