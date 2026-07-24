# Captcha Blocks and Lightning Component Fixes

## Session: 2026-06-22/23 License Verification — Full State Audit

### CAPTCHA/Security-Blocked States (do not retry)
- **Alaska** — HTTP 403 for all automated requests. No workaround.
- **Colorado** — CAPTCHA ("Let's confirm you are human") before any search. DPO site has CAPTCHA; old DORA URL doesn't return NHA data.
- **Iowa** — Amanda Portal requires JavaScript verification. DIAL records page is informational only. No reliable NHA-only search found.
- **Kansas** — reCAPTCHA present on page load (before form interaction). prolicenseverify.ks.gov has "Adult Care Home Administrator" profession but block prevents automation.
- **Nebraska** — reCAPTCHA on License Lookup. No public API.
- **Nevada** — SSL certificate mismatch (ERR_CERT_COMMON_NAME_INVALID).
- **South Carolina** — reCAPTCHA on LLR. Find button is visibility:hidden until CAPTCHA solved.
- **Tennessee** — CAPTCHA on License Verification Home.
- **Utah** — reCAPTCHA on DOPL License Lookup (secure.utah.gov).
- **Washington** — reCAPTCHA on HELMS (Salesforce-based).

### Lightning Web Component (LWC) Techniques — Texas TULIP
**Status:** FULLY FUNCTIONAL (verified 2026-06-23)

**Native select piercing:** `page.locator("select").all()` pierces shadow DOM.

**Race condition:** Re-query selects after Program Type selection (LWC re-renders).

**Submit button:** `page.get_by_text("Submit", exact=True).first.click(force=True)` — standard click does NOT trigger LWC form submission.

**Retry pattern:** 2 attempts with 1s sleep for intermittent LWC render failures.

### Arizona — NCIA Board (not AZ Care Check)
**Status:** FULLY FUNCTIONAL (verified 2026-06-23)
AZ Care Check searches facilities, not individuals. NCIA Board at aznciab.portalus.thentiacloud.net is the correct NHA source.

### Iowa — Amanda Portal (not DIAL)
**Status:** BLOCKED — requires JavaScript verification.
DIAL page is informational only. Amanda Portal at amanda-portal.idph.state.ia.us has the actual search but requires JS enablement that's not easily automated.

### Idaho — DOPL edopl Portal
**Status:** FULLY FUNCTIONAL (verified 2026-06-23)
edopl.idaho.gov has a Name field with ID `#Dd-11`. The custom React comboboxes for Board and License Type are not needed — Name-only search works.
Verified: Calene Cole Active #NHA-1492, expires 10-Feb-2028.
Parser: tab-separated results. Look backward 1-2 lines for license number (`[A-Z]{3}-\d+`), current line contains Status and Expiration.

### Nebraska — PDF Roster (CAPTCHA Alternative)
**Status:** FULLY FUNCTIONAL (verified 2026-06-23)
License Lookup requires reCAPTCHA, but DHHS publishes a free monthly PDF roster:
https://dhhs.ne.gov/licensure/Documents/LTCRoster.pdf
Requires `pdfplumber`. Search for admin name, look backward for 6-digit license number and facility name.

### Stealth Library Testing — reCAPTCHA v3 Research
**Tested:** `playwright-stealth`, `pydoll`, SeleniumBase CDP, persistent Chrome profiles, storage state persistence.

**Result:** None bypass reCAPTCHA v3. The CAPTCHA still appears with:
- Perfect stealth fingerprint (no `navigator.webdriver`, correct plugins, WebGL vendor)
- Saved Chrome profile with cookies
- Headless=False with real Chrome
- Storage state loaded between sessions

**Why:** reCAPTCHA v3 is server-side scoring based on IP reputation + cookie history + behavioral patterns. Client-side stealth libraries can't fake a long cookie history or residential IP.

**Free workaround:** Semi-automated browser — user solves ONE CAPTCHA per state per month, then tool searches all names automatically. ~10 minutes manual work/month for 6 states.
