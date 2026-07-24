# Utah DOPL workarounds for ENSG NHA/HFA verification

Context: Utah DOPL License Lookup (`https://secure.utah.gov/llv/search/index.html`) protects name/profession searches with reCAPTCHA v3. Kevin wants Texas, California, and Utah to work consistently in the final max-coverage report.

## What was tested

### Live lookup mechanics
- Search form action is `/llv/search/index.html` with hidden CSRF token `_csrf`.
- Profession checkbox for Health Facility Administrator is `item153_1` with value `551`.
- Page JavaScript loads `https://www.google.com/recaptcha/api.js?render=6LcQUqIUAAAAAG7lgG1BfDlhvVUuFP26QsY4Eq6_` and calls:
  - `grecaptcha.execute(document.getElementById('recaptchaSiteKey').value, {action: 'search'})`
  - writes token into `g-recaptcha-response-name`
  - submits the form.
- Direct POST without a reCAPTCHA token returns the search page again; no results.
- Browser-generated token + direct Playwright `context.request.post()` still returned the search page, not results.
- 2captcha reCAPTCHA v3 tokens are intermittent: one test can return parseable results while another is rejected/times out back to the search page. This is expected because v3 is score-based, not just token-validity based.

### Page/scripts checked
- `https://secure.utah.gov/llv/js/app-functions.js?v=20221213` contains no alternate JSON/AJAX license API; it only wraps reCAPTCHA and submits the form.
- The search page links to official data-request endpoints:
  - `https://secure.utah.gov/datarequest/professionals/index.html`
  - `https://secure.utah.gov/datarequest/index.html`

## Recommended workaround hierarchy

1. **Official Utah data request/download — preferred stable path**
   - URL: `https://secure.utah.gov/datarequest/professionals/index.html`
   - Page title: “Professions Licensed in Utah”.
   - Offers full/download lists including Name, License type, License status.
   - Cost shown on page: minimum $5.00 search fee includes first 200 records; full list price $0.01 per record.
   - Address/phone/email requires DOPL approval, but ENSG license verification only needs name/license type/status.
   - If Kevin obtains a Health Facility Administrator list, place it under `D:/license-verification/cache/utah_roster/` and implement Utah like Iowa/Nevada: parse roster, match admins, merge into final workbook. This is the best way to make Utah click-and-forget.

2. **Semi-auto Edge session — practical free path**
   - Use a real Edge browser/persistent profile, user solves/passes reCAPTCHA once, then script searches all Utah admins.
   - This is more reliable than headless/2captcha because reCAPTCHA v3 uses IP reputation, cookies, and browser behavior.
   - Keep it separate from unattended click-and-forget so the final report does not claim Utah is verified unless the semi-auto correction workbook exists.

3. **2captcha/headless v3 — do not treat as production**
   - Tokens can be obtained, but Utah can reject low-score tokens.
   - Do not put this into the unattended report as a high-confidence state unless a sustained batch run proves reliability.

## Final report policy

Until a Utah roster/download or successful semi-auto correction workbook exists:
- Keep Utah rows as `NEEDS MANUAL REVIEW` in `build_final_max_coverage.py`.
- Do not downgrade Utah failures to FAIL just because a headless/2captcha attempt was rejected; that is an automation-confidence failure, not proof the admin is unlicensed.
- When a Utah roster/import is added, remove Utah from manual gates only after ad-hoc verification confirms all 32 Utah rows are covered.

## Future implementation sketch: Utah roster import

Expected files:
- `D:/license-verification/cache/utah_roster/*.xlsx` or `*.csv`

Parser steps:
1. Load newest file from `cache/utah_roster/`.
2. Identify columns by header aliases:
   - name: `Name`, `Licensee Name`, `Full Name`
   - type: `License Type`, `Profession`, `Classification`
   - status: `Status`, `License Status`
   - number: `License #`, `License Number`, `Credential Number`
3. Filter license/profession containing `Health Facility Administrator` or HFA/NHA equivalent.
4. Match ENSG admin names with same normalization used elsewhere (`First Last`, `Last, First`, slash-separated alternates).
5. Return ACTIVE/PASS for active statuses; revoked/expired/suspended/denied as FAIL; ambiguous rows as NEEDS MANUAL REVIEW.
6. Add a targeted correction workbook pattern such as `utah_roster_refresh_*.xlsx` to `final_report.supplemental_report_patterns`.

## User-facing guidance

When Kevin asks “is there no workaround for Utah?”, answer directly:
- “There is no reliable fully unattended scrape of the live portal yet.”
- “The real workaround is Utah’s official paid data download, or semi-auto Edge.”
- Avoid overexplaining; Kevin wants the shortest path to reducing manual rows.
