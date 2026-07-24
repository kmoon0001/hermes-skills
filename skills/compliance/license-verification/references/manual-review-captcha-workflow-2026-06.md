# Manual-review disclaimer and CAPTCHA workflow notes (2026-06)

Use this reference when producing ENSG final license-verification workbooks or explaining remaining manual-review rows.

## Manual-review wording

Put this disclaimer directly in generated spreadsheets when manual-review rows exist:

> NEEDS MANUAL REVIEW does not mean the administrator failed license verification. It means automation did not produce enough official, reliable evidence to make a final PASS/FAIL compliance or legal determination. Manual-review rows should be confirmed by a human through the state board, official portal, roster, paid data download, or documented semi-automated browser workflow before relying on them for legal/compliance action.

Also include the current manual-review drivers where applicable:
- Alaska: DataDome security; proxy-backed DataDome workflow not validated.
- Tennessee: BotDetect CAPTCHA; ImageToText/vision solving tested unreliable for production PASS/FAIL.
- Utah: unresolved rows after official DOPL active-HFA/no-pay evidence merge; public/CMS-only evidence is triage, not license proof.

## Workbook implementation pattern

When writing Excel reports with openpyxl:
1. Add an Executive Summary section titled `MANUAL REVIEW DISCLAIMER`.
2. Add a dedicated `Manual Review Notes` sheet.
3. Include manual counts by state and next steps.
4. Keep `NEEDS MANUAL REVIEW` separate from FAIL in charts, summary, and explanations.
5. Preserve public/CMS evidence notes for triage, but do not promote public-only evidence to official PASS/FAIL.

## Focused ad-hoc verification pattern

If no canonical test suite exists, create a temp script under:
`C:/Users/kevin/AppData/Local/Temp/hermes-verify-*.py`

Verify at minimum:
- Python compile for changed executable files.
- Generated workbook includes `Manual Review Notes`.
- Disclaimer text is present.
- Final counts stayed stable: total rows, PASS/FAIL/manual, manual by state.
- Temp script is cleaned up.

Describe this as targeted ad-hoc verification, not a suite-green result.

## CAPTCHA-service reality check

2captcha support by class:
- reCAPTCHA v2: validated for South Carolina in this project.
- reCAPTCHA v3: token acquisition works, but Utah portal scoring is intermittent; do not rely on it without live acceptance validation.
- AWS WAF: 2captcha has `AmazonTaskProxyless`, but it needs fresh websiteKey, iv, and context captured from the page.
- DataDome: 2captcha has `DataDomeSliderTask`, but it is not proxyless. It requires captchaUrl, exact userAgent, and proxy fields (proxyType, proxyAddress, proxyPort, optionally proxyLogin/proxyPassword). Proxy quality matters; banned IPs may return unsolvable/proxy errors.
- BotDetect/image CAPTCHA: 2captcha can use ImageToTextTask for normal image CAPTCHAs, but Tennessee BotDetect was not reliable enough for production license decisions. Prefer semi-auto/manual unless a future workflow is validated on real ENSG rows.

## Semi-auto path

For remaining manual rows, prefer the existing Edge-based semi-auto workflow before inventing new solver logic:
`python semi_auto.py TENNESSEE`
`python semi_auto.py UTAH`
`python semi_auto.py ALASKA`

The user can solve/handle the portal in Edge, then the script batch-searches admins and writes JSON under `results/`. Treat semi-auto JSON as evidence that still needs merge/validation rules before changing final PASS/FAIL output.