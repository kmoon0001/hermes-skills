# Iowa roster and CAPTCHA architecture update (2026-06-28)

## Durable lesson

For license-verification states, do not chase CAPTCHA automation when a roster/API/PDF exists. Build accuracy-first source selection into the workflow:

1. Open data API / daily roster / PDF roster
2. No-CAPTCHA public portal
3. Validated CAPTCHA solver on the exact portal
4. Semi-auto Edge/manual challenge solve
5. Manual board/public-record request

## Iowa: FileCloud public roster beats Amanda Portal automation

- Source URL: `https://filecloud.idph.state.ia.us/url/PLRosters`
- Downloaded folder suggested filename: `pl.zip`
- Useful file inside zip: `IBPLRoster.xlsx`
- NHA rows have:
  - folder: `Nursing Home Administrators`
  - subtype: `Nursing Home Administrator` or `Nursing Home Administrator Provisional`
  - columns observed: data date, folder, subtype, status, license number, issue/expiration dates, first name, last name, address fields
- Cache extracted NHA rows to `cache/iowa_nha_roster.json`; repeated openpyxl scans over the full workbook are slow.
- Split Excel admin cells on `/`, `;`, `and`, `&` so cells like `Amanda Birch / Leah Nelson` pass if either listed admin has an active NHA/provisional license.

Verified ENSG Iowa examples:

| Admin | Status | License | Expiration |
|---|---|---:|---|
| Steven Mulford | ACTIVE | 080974 | 2027-12-31 |
| Keith McAndrews | ACTIVE | 136722 | 2027-12-31 |
| Leah Nelson | ACTIVE | 116302 | 2027-12-31 |
| Dirk Timm | ACTIVE | 118358 | 2027-12-31 |
| Danielle Grove | ACTIVE provisional | 135724 | 2027-09-30 |
| Amanda Birch / Leah Nelson | ACTIVE provisional via Amanda Birch | 132346 | 2027-05-05 |

Integrated check: `python verify_all.py IOWA` generated a 9-row Detailed Results report with 9/9 PASS.

## 2captcha architecture notes

Centralize solving in `captcha_solver.py`; state modules should call it only after source selection decides CAPTCHA is the best option.

Supported API task names from 2captcha docs:

- reCAPTCHA v2: `RecaptchaV2TaskProxyless` — production validated for South Carolina.
- reCAPTCHA v3: `RecaptchaV3TaskProxyless` — tokens can be acquired, but Utah may reject low scores.
- AWS WAF: `AmazonTaskProxyless` — requires fresh `websiteKey`, `iv`, `context`; result includes `captcha_voucher` and `existing_token`.
- DataDome: `DataDomeSliderTask` — requires `captchaUrl`, exact browser `userAgent`, and proxy fields (`proxyType`, `proxyAddress`, `proxyPort`, optional login/password). There is no proxyless DataDome task in the current 2captcha docs.
- Image/BotDetect: `ImageToTextTask` exists, but Tennessee BotDetect was empirically unreliable; do not default to paid image solving.

## Alaska / Tennessee gating

- Alaska CBPL DataDome should stay `NEEDS_MANUAL` unless a proxy-backed DataDome solve is explicitly configured and live-validated.
- Tennessee BotDetect should stay `NEEDS_MANUAL`; user-run semi-auto is higher confidence than image/vision solving.

## Ad-hoc verification pattern

When editing this project and no canonical test suite applies:

1. Create a temp script under `C:/Users/kevin/AppData/Local/Temp` with `tempfile.mkstemp(prefix="hermes-verify-", suffix=".py")`.
2. In the script, run:
   - `py_compile` on touched Python files
   - focused module assertions using real ENSG admins
   - integrated single-state run such as `python verify_all.py IOWA` if workflow/report code changed
   - read the generated workbook with openpyxl and assert row counts/PASS values
3. Delete the temp script in a `finally` block.
4. Report it as **ad-hoc verification**, not full suite green.

SMTP AUTH disabled errors from Outlook are email-delivery blockers only; if the report workbook is generated and validated, the verification workflow passed.
