# Nevada & Colorado Site Analysis — 2026-06-23

## Nevada

**Tested URL:** https://www.beltca.nevada.gov/

- SSL cert error (`ERR_CERT_COMMON_NAME_INVALID`) blocks Playwright by default.
- With `--ignore-certificate-errors` the page loads, but the **homepage has no license lookup form**.
- Navigation: Home / Board / Licensing / Current Administrators / Forms / Disciplinary Actions / Contact.
- "Current Administrators" section exists but is static content (no search form).
- **Conclusion:** No automated NHA lookup possible. Options: phone/email the board, CMS Provider of Services, or public records request.

## Colorado

**Tested URLs:**
- `https://dpo.colorado.gov/COHPC` → redirects to HPPP, returns CloudFront 403 for Playwright.
- `https://www.beltca.nevada.gov/` (mistaken — this is Nevada)
- `https://dora.colorado.gov/check-a-license` → old URL, does not return NHA data.

**Conclusion:** NHA verification blocked by CloudFront + CAPTCHA. No reliable automated workaround found. Options: CMS Provider of Services or public records request.

## Iowa

**Tested URLs:**
- `https://amanda-portal.idph.state.ia.us/ibpl/portal/#/dashboards/index` → JavaScript verification blocks automation.
- `https://dial.iowa.gov/i-need/records` → informational page only, no NHA search.

**Conclusion:** No automated NHA lookup possible. Contact DIAL or Amanda Portal support for bulk roster.
