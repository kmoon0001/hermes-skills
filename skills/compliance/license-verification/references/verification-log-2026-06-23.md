# State Scraper Verification Log — 2026-06-23 (Updated)

## Full Test Run Results (with real Excel admin names)

| State    | Test Admin         | Status | License #     | Expiry        | Source |
|----------|-------------------|--------|---------------|---------------|--------|
| Alabama  | Hunter Wilson     | ACTIVE | 2353          | 10/31/2026    | alboenha |
| Alaska   | —                 | BLOCKED| —             | —             | DataDome CAPTCHA |
| Arizona  | Conner Monks      | Active | NCA-002062    | 02/14/2028    | NCIA Board |
| California| Adrain Smith     | Active | 00007647      | 2027-01-21   | CDPH Detail Page |
| Colorado | Emily Amschel     | Active | 3010          | 2027-02-28   | CIM API ✅ |
| Colorado | Eddy Boyles       | Active | 1867          | 2027-02-28   | CIM API ✅ |
| Colorado | William Foster    | Active | 3047          | 2027-02-28   | CIM API ✅ |
| Idaho    | Calene Cole       | ACTIVE | NHA-1492      | 10-Feb-2028   | edopl |
| Iowa     | Steven Mulford    | NOT FOUND| —           | —             | Amanda Portal blocked |
| Kansas   | Ethan Dean        | Active | 4280          | 06/30/2028   | KSDADS ✅ |
| Nebraska | Kristie Kallemeyn | Active | 324003        | 03/31/2027   | PDF Roster + March 31 rule |
| Nevada   | —                 | BLOCKED| —             | —             | SSL Error |
| Oregon   | David Horn        | Active | P-10229922    | 2/28/2027     | OHLO |
| South Carolina | Raymond Tiller | BLOCKED| —           | —             | reCAPTCHA |
| Tennessee| —                 | BLOCKED| —             | —             | AJAX form |
| Texas    | Gabriel Barraza   | Active | NFA012571     | 2027-01-26    | TULIP |
| Utah     | —                 | BLOCKED| —             | —             | reCAPTCHA |
| Washington| Matthew Payne    | Active | NHA.NH.61348152 | 09/22/2026 | Socrata API ✅ |
| Washington| Adrian Cruz      | Active | NHA.NH.61492441 | 09/29/2026 | Socrata API ✅ |
| Wisconsin| Brianna Klemp     | Active | 4062-65       | —             | DSPS |

## Summary

**Fully functional (12):** AL, AZ, CA, CO, ID, KS, NE, OR, TX, WA, WI
**Blocked (5):** AK, IA, NV, SC, TN, UT

## Session Highlights (2026-06-23)

- **Colorado:** Rewrote scraper from Playwright to CIM open data API. Free, no CAPTCHA, includes expiration dates. Tested with 3 real names — all work.
- **Washington:** Rewrote from Playwright to Socrata open data API. Free, no CAPTCHA, includes expiration dates. Tested with 2 real names — all work.
- **Kansas:** Rewrote from Playwright (reCAPTCHA blocked) to KSDADS glsuite portal. No CAPTCHA, detail pages show expiration + status. Tested with real name — works.
- **Alabama:** Added days_until_expiry calculation from renewal date (was returning None).
- **Nebraska:** Calculate expiration as March 31st each year (per state rule in PDF header).
- **Alaska:** Discovered DataDome CAPTCHA blocks headless Playwright. Marked as BLOCKED.
- **Tennessee:** Investigated Licensure Reports portal — complex AJAX form submission with dynamic dropdowns. Only 11 TN facilities, kept as BLOCKED.
- **Research pattern:** Used 3 parallel subagents to research free alternatives for 8 blocked states. Found free data sources for CO, WA, KS; no free alternatives for AK, IA, NV, SC, TN, UT.

## Key Lesson

**Check open data portals before marking as BLOCKED.** Colorado (CIM) and Washington (Socrata) both have free Socrata open data APIs with license data including expiration dates. The `in()` clause doesn't work with Socrata — use `OR` instead.

## Test Names Source

Real admin names pulled from `C:\Users\kevin\Desktop\ENSG Facilities Only 6.1.26.xlsx`.
