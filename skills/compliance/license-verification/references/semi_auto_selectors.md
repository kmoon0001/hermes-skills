# Semi-Auto Selectors — Updated 2026-06-24

Verified page elements for `scripts/semi_auto.py` and headless scrapers.

## CRITICAL: Navigate Back Before Each Search

After clicking submit, the page changes to results — the search form no longer exists. The next `page.fill()` times out. Fix: before each search (except the first), `page.goto(config["url"])` back to the search page. Without this, every search after the first times out with `Timeout 30000ms exceeded. waiting for locator("#fullName")`.

## South Carolina

**URL:** https://verify.llronline.com/LicLookup/LTC/LTC.aspx?div=35

| Field | Selector |
|-------|----------|
| Last Name | `#ctl00_ContentPlaceHolder1_UserInputGen_txt_lastName` |
| First Name | `#ctl00_ContentPlaceHolder1_UserInputGen_txt_firstName` |
| Submit | `#ctl00_ContentPlaceHolder1_btn_find` |

- Find button is `visibility: hidden` until reCAPTCHA solved.
- reCAPTCHA iframes present at URL path `.../recaptcha/api2/anchor`.

## Tennessee

**URL:** https://verify.tn.gov/ → redirects to https://search.cloud.commerce.tn.gov/

**BLOCKED:** The new portal is a Next.js app for Commerce & Insurance licenses (Accountancy, Contractors, etc.). It does NOT have Nursing Home Administrator data. NHA licenses are managed by the Department of Health, not Commerce & Insurance. The Health portal (`internet.health.tn.gov/Licensure/`) has CAPTCHA. TN remains BLOCKED — only 11 facilities.

**Old selectors (no longer work):**
| Field | Selector |
|-------|----------|
| Last Name label target | `#-33701226759` |
| First Name label target | `#177334431563` |
| Submit | `button:has-text("Search")` |

- Inputs had dynamic IDs; matched by label text.
- **PITFALL (2026-06-24):** verify.tn.gov now redirects to Commerce & Insurance portal — wrong board for NHA.

## Utah

**URL:** https://secure.utah.gov/llv/search/index.html

| Field | Selector |
|-------|----------|
| Name Search | `#fullName` (single field — has ID, NOT `input[type='text']`) |
| Submit | `input[type='submit'][value='Search']` |

- Single "Name Search" field with `id="fullName"` and `name="fullName"`.
- Two submit buttons; target by `value="Search"` (not `value="Submit"`).
- Must check "HEALTH FACILITY ADMINISTRATOR" checkbox for NHA results.
- The `semi_auto.py` script detects single-field portals when `selector_last == selector_first` and fills the full name.
- **PITFALL (fixed 2026-06-24):** Initially used `input[type='text']` which matched the wrong field (Utah.gov search bar). The correct selector is `#fullName`.

## Washington (BLOCKED — now using Socrata API)

**URL:** https://wahelms.my.site.com/s/license-search

| Field | Selector |
|-------|----------|
| Last Name | `#lastName` |
| First Name | `#firstName` |
| Submit | `button:has-text('Search')` |

- **SUPERSEDED:** WA Open Data Socrata API at `data.wa.gov/resource/qxh8-f4bd.json` is free, no CAPTCHA, includes expiration dates.

## Kansas (BLOCKED — now using KSDADS glsuite portal)

**URL:** https://prolicenseverify.ks.gov/

| Field | Selector |
|-------|----------|
| Last Name | `#lastName` |
| First Name | `#firstName` |
| Submit | `button:has-text('Search')` |

- **SUPERSEDED:** KSDADS glsuite portal at `ksdadsv7prod.glsuite.us/glsuiteweb/Clients/ksdads/public/verification/LicVerification.aspx` has no CAPTCHA.

## Alaska

**URL:** https://www.commerce.alaska.gov/cbp/main/Search/Professional

| Field | Selector |
|-------|----------|
| Program | `#ProgramId` (value=35 for Nursing Home Administrators) |
| License Type | `#LicenseTypeId` (value=234 for Nursing Home Administrator) |
| Owner Name | `#OwnerEntityName` (single field, NOT separate last/first) |
| Search | `#search` (anchor tag with `data-deptsubmitform="true"`) |

- **CAPTCHA:** DataDome blocks headless Playwright (returns 403 with captcha-delivery.com).
- The form uses a single "Owner Last or Entity Name" field — there are NO separate first/last name fields.
- Results table has 10 columns including Expiration Date (MM/DD/YYYY format).

## Colorado (BLOCKED — now using CIM API)

**URL:** https://dpo.colorado.gov/COHPC

- **SUPERSEDED:** Colorado CIM open data API at `data.colorado.gov/resource/7s5z-vewr.json` is free, no CAPTCHA, includes expiration dates.

## Lessons Learned

- `--ignore-certificate-errors` allows loading Nevada's site but it has no public license lookup tool.
- Colorado `dpo.colorado.gov/COHPC` returns CloudFront 403 for bots.
- Persistent Chrome profiles do NOT bypass reCAPTCHA v3 — the token is session-bound and re-evaluates on every load.
- Stealth plugins do NOT bypass reCAPTCHA v3.
- The real workaround for CAPTCHA-blocked states is the semi-automated browser approach.
- **Check open data portals before marking as BLOCKED.** Colorado (CIM) and Washington (Socrata) both have free APIs.
- **Alaska form field is `OwnerEntityName`** — not separate last/first name fields.
