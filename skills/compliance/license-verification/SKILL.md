---
name: license-verification
description: "Professional license/credential verification for compliance and litigation support. Scrape state licensing boards, cross-reference facility/admin lists, generate color-coded compliance reports with email alerts. Modular per-state scrapers using Playwright + REST APIs. Fully automated/high-confidence (14): Alabama, Arizona, California, Colorado (CIM API), Idaho, Iowa (daily IBPLRoster.xlsx public roster), Kansas (KSDADS), Nebraska (PDF roster), Nevada (PDF roster), Oregon, South Carolina (2captcha reCAPTCHA v2), Texas, Washington (Socrata API), Wisconsin. Semi-automated/manual-gated (3): Alaska (DataDome requires proxy-backed solver), Tennessee (BotDetect CAPTCHA), Utah (reCAPTCHA v3 — intermittent). CMS staffing/penalty data integration for executive defense.  
**Related:** see `cms-data-matching` (data-science) for CMS Nursing Home Compare data downloads, facility name matching, and star rating lookups. Edge browser support for semi_auto.py. 2captcha centralized for validated CAPTCHA types only."
version: 0.1.0
author: Hermes Agent
tags: [compliance, license-verification, scraping, playwright, healthcare, reporting]
---

# License Verification System

Verify whether professionals hold active state licenses. Designed for compliance audits, litigation protection, and recurring monitoring. Default implementation targets nursing home administrators (NHA) but the architecture works for any state-licensed profession.

Reference: `references/confidence-scoring.md` captures the ENSG confidence/probability scoring pattern, workbook evidence columns to preserve, max-coverage base-selection pitfall, and focused `hermes-verify-*` ad-hoc verification approach for report-generator changes.
Reference: `references/final-workflow-refresh-and-supplements.md` captures the ENSG production workflow: auto-refresh feasible states, merge no-pay/public evidence after manual gates, and verify final counts/confidence columns.

## Architecture

```
Input (Excel with hidden admin names | SharePoint List)
    ↓
State Scraper (Playwright — one per state)
    ↓
Compliance Report (Excel: color-coded flags) + Email Alert
```

**Key design decisions:**
- Licenses are by PERSON, not by facility. An admin licensed in CA can work at any CA facility.
- Source of truth = user's Excel/SharePoint List. Admins should not need to re-enter names.
- Adding a facility = adding a row. No code changes.
- Monthly cadence catches expirations before compliance issues.
- For litigation: timestamped evidence + source URL required.
- **User preference: "without over complicating or causing regression"** — prefer adding features as separate scripts/functions, not rewriting existing code. Simple, incremental changes.
- **User preference: auto-open reports** — `os.startfile()` after saving, not just saving to disk.
- **User preference: "simple but powerful and actionable"** — charts should be clean and tell a story in 30 seconds, not complex dashboards.
- **User preference: "non-coding tools"** — user wants interactive CLI tools (prompts, forms) not scripts they have to edit. The Streamlit frontend and `add_facility.py` were built because user said "can it be through non coding like an option that prompts you to enter the name?".
- **User preference: "be objective on the probability of success"** — before building a feature, assess honestly whether it's feasible and what the risks are. Don't overpromise.
- **User preference: sharp scope control** — user said "anything not related to [licensing/staffing defense] or the sequelae of that I don't want." Only add data/features that directly serve the compliance defense use case. No general-purpose dashboards.

**Data source priority when a state portal has CAPTCHA:**
1. Open data API (Socrata, CKAN) — free, no CAPTCHA, often includes expiration dates
2. PDF roster — free, updated periodically
3. Paid data download — cheap per-record
4. Semi-auto browser — user solves one CAPTCHA per session
5. Manual verification — last resort

Always check for open data APIs BEFORE marking a state as blocked. Colorado (CIM) and Washington (Socrata) both have free APIs that made scrapers fully functional without Playwright. Nevada has a free PDF roster at beltca.nev.gov.

## Folder Layout

```
D:/license-verification/
├── config.json              # Email, paths, state scraper map
├── verify_licenses.py       # Main script: read → verify → report → email
├── app.py                   # Streamlit frontend (localhost:8501)
├── states/                  # One scraper per state
│   ├── california.py        # CDPH NHA — validated
│   ├── texas.py             # TULIP — validated, returns expirations
│   ├── arizona.py           # stub
│   └── ...
├── results/                 # OUTPUT verification reports (verify_all.py writes here)
│   └── verification_*.xlsx  # Timestamped: verification_2026-06-24_005925.xlsx
├── reports/                 # Older compliance reports (compliance_report_*.xlsx)
├── scripts/                 # Semi-auto, verify_one_state, etc.
└── cache/                   # Cached CMS CSV files
```

### INPUT Excel vs OUTPUT Excel

When the user asks about "the spreadsheet" or "the Excel," they almost always mean the **output report**, not the input file. Clarify which one:

- **INPUT (master facility list):** `C:/Users/kevin/Desktop/ENSG Facilities Only 6.1.26.xlsx` — 450 facilities, Col A=Location, Col F=Admin, Col I=State. This is the source data, NOT the verification output.
- **OUTPUT (verification reports):** `D:/license-verification/results/verification_*.xlsx` — timestamped, generated by `verify_all.py` or Streamlit. These are the 3-tab reports (Executive Summary + Charts + Detailed Results).
- **OLDER OUTPUT:** `D:/license-verification/reports/compliance_report_*.xlsx` — earlier report format, superseded by `results/`.

## Reading Excel with Hidden Columns

openpyxl reads hidden columns/rows automatically — no special flags needed.

```python
import openpyxl
wb = openpyxl.load_workbook('file.xlsx', data_only=True)
ws = wb['Sheet']
for row in ws.iter_rows(min_row=2, values_only=False):
    admin = row[5].value   # Column F — reads hidden column
    state = row[8].value   # Column I
```

**Config key mismatch pitfall:** If config.json uses `excel_sheet`, the code must read `config["excel_sheet"]`, not `config["sheet_name"]`. Keep them aligned.

## Data Source Preference

Prefer **SharePoint List** over Excel for ongoing data entry:

- Auto-detection of new rows via Power Automate triggers ("item created or modified")
- No file locking when multiple people edit
- Cleaner integration with Copilot Studio agents
- Excel acceptable for local prototyping, but do not build permanent infra around an Excel file if SharePoint is available

When using a SharePoint List as the source, Power Automate can trigger on new items and call an HTTP endpoint that runs the verification script.

## Email Configuration

SMTP credentials should be loaded from environment variables, with fallback to config.json:

```python
smtp_user = os.environ.get("SMTP_USER") or email_config.get("smtp_user")
smtp_password = os.environ.get("SMTP_PASSWORD") or email_config.get("smtp_pass")
```

This allows the same config file to be committed to source control without secrets.

**Config key consistency:** Email config lives under `email` in config.json. Always access via `config["email"].get("smtp_user")` — never hardcode `config["smtp_user"]`.

## California CDPH NHA Scraper Pattern (FULLY FUNCTIONAL — Detail Pages for Expiration)

**Site:** https://cvl.cdph.ca.gov/SearchPage.aspx

California’s results page only shows Name | Type | Number | Status. **To get expiration dates, the scraper must navigate to each result’s detail page** (`DetailPage.aspx?cert_holder_id=...`), parse `Expiration Date:`, and return it.

### Search flow

```python
page.check('#ContentPlaceHolderMiddleColumn_rdoLastStart')
page.fill('#ContentPlaceHolderMiddleColumn_txtLastNameStart', last_name)
page.click('#ContentPlaceHolderMiddleColumn_btnSearch2')
```

The **Last Name Starting With** search is more reliable than **Last Name, First Name** for CDPH. Use `rdoLastStart` + `txtLastNameStart` as primary search. Fall back to `rdoLastFirst` + `txtLastName`/`txtFirstName` if needed.

### Extracting results via JavaScript

Use `page.evaluate` to extract all table rows and `DetailPage.aspx` links in one shot — this avoids fragile Playwright locator loops:

```python
data = page.evaluate('''() => {
    const rows = [];
    const links = {};
    document.querySelectorAll('tr').forEach(tr => {
        const cells = Array.from(tr.querySelectorAll('td'));
        if (cells.length >= 4) {
            const text = cells.map(c => c.innerText.trim()).join('\\t');
            rows.push(text);
        }
    });
    document.querySelectorAll('a[href*="DetailPage.aspx"]').forEach(a => {
        const m = a.href.match(/cert_holder_id=(\\d+)/);
        if (m && a.innerText.trim()) links[a.innerText.trim()] = m[1];
    });
    return {rows, links};
}''')
```

Rows are tab-delimited: `NAME \t TYPE \t NUMBER \t STATUS`.

### Detail page fetch for expiration

Once the best matching result is selected, open its detail page and parse:

```python
detail_url = f"https://cvl.cdph.ca.gov/DetailPage.aspx?cert_holder_id={cert_holder_id}"
page.goto(detail_url, timeout=30000)
text = page.inner_text("body")
exp_match = re.search(r"Expiration Date:\\s*([^\\n]+)", text, re.IGNORECASE)
if exp_match:
    expiration = exp_match.group(1).strip()
```

Detail page also shows `Effective Date:` and `Status:` — use those for richer notes and status mapping.

### Status mapping from detail page

CDPH detail page statuses:
- `ACTIVE, EMPLOYABLE` → `Active` (PASS)
- `DENIED, NOT EMPLOYABLE` → `Denied` (FAIL)
- `INACTIVE` → `Inactive`
- `EXPIRED`, `REVOKED`, `SUSPENDED` → capitalized

### Name matching

CDPH result names are `LASTNAME, FIRSTNAME M.`. The `matches_name_score` helper uses `rapidfuzz.token_sort_ratio` with bonuses for substring matches. Threshold 60 is sufficient.

**Pitfall:** Do not use the “Last Name, First Name” name format (`rdoLastFirst`) for the initial search unless strictly necessary. The empty result for exact-name searches is a known limitation when the CDPH index stores names as `Last, First` and exact matching is applied inconsistently. `rdoLastStart` avoids this.

## Expiration Date Calculation Across All States

States that return parseable expiration strings but do not compute `days_until_expiry` are **under-counted** in expiration alerts. Apply this pattern to any state scraper that returns a non-empty `expiration` string:

```python
from datetime import datetime

days_until = None
if expiration:
    for fmt in ["%m/%d/%Y", "%B %d, %Y", "%Y-%m-%d", "%d-%b-%Y", "%m-%d-%Y"]:
        try:
            exp_date = datetime.strptime(expiration.strip(), fmt)
            days_until = (exp_date - datetime.now()).days
            break
        except ValueError:
            continue
```

This was applied to:
- **Alabama** — parses `Renewal Date:` and `Licensure:` but never converted to days.
- **Idaho** — parses `10-Feb-2028` but left days as `None`.
- **Wisconsin** — regex captured `\d{4}-\d{2}-\d{2}` as `granted` date (group 7 in old pattern) but threw it away. Now stores it and computes days.

**Result:** Alert logic in `verify_all.py` (`EXPIRES IN X DAYS` for 0–60 days, `EXPIRED` for negative) now triggers correctly for these states too.

## Texas TULIP Scraper Pattern (FULLY FUNCTIONAL)

**Site:** https://tulip.hhs.texas.gov/TULIP/s/public-search
**Verified:** Robert Smith Active #NFA007578, expires 2027-06-14

Texas TULIP uses Lightning Web Components with nested shadow DOM. The form has `lightning-select` and `lightning-input` components inside a custom LWC `c-rs_-public-search-l-w-c`.

### Key technique: Native select piercing

Playwright's `page.locator("select").all()` **pierces shadow DOM** and returns the native `<select>` elements inside Lightning components. This is the only reliable way to interact with the form:

```python
selects = page.locator("select").all()  # Returns 8 selects inside shadow DOM
selects[0].select_option(label="Nursing Facility Administrator")  # Program Type
page.wait_for_timeout(500)  # Wait for form re-render after selection

# RE-QUERY selects after selection — page may re-render and invalidate old references
selects = page.locator("select").all()
selects[1].select_option(label="Equals")  # First Name match type
selects[2].select_option(label="Equals")  # Last Name match type

inputs = page.locator('input[type="text"]').all()
inputs[0].fill(first_name)
inputs[1].fill(last_name)
```

### Submit button — critical gotcha

The Submit button is inside the LWC shadow DOM. Standard `page.locator('button:has-text("Submit")').click()` does NOT trigger the form submission. Use `get_by_text` which pierces shadow DOM:

```python
page.get_by_text("Submit", exact=True).first.click(force=True)
```

### Race condition retry

The LWC form sometimes doesn't fully render before interaction. Add retry logic:

```python
for attempt in range(2):
    result = _try_texas_search(...)
    if result.get("status") not in ("ERROR", "NOT FOUND"):
        return result
    if attempt == 0:
        time.sleep(1)
```

Results are tab-delimited: Last Name | First Name | NFA License Status | License Number | License Issue Date | License Initial Date | License Expiration Date | Unemployable

### Texas final-report cleanup rules

- Split alternate-admin cells on `/` and `&`; try each full name before marking the facility unresolved. Example: `Shaun Baldwin / Joshua Lewis` matched Shaun Baldwin as Active/PASS.
- If TULIP returns the person name but leaves both `NFA License Status` and `License Number` blank, classify it as `NOT FOUND` / FAIL, not UNKNOWN/manual. It means Texas has that name in the public search but no NFA license/status on file.
- Treat `Provisional` as PASS for Texas/NFA reporting unless the state source indicates revoked/expired/disciplinary status.

**Bulk search** is available (max 900 records) but requires SSN + DOB — not useful.

## State Scraper Interface

Every scraper must match this signature:

```python
def verify_<state>(admin_name: str) -> dict:
    return {
        "status": "Active|Inactive|Expired|NOT FOUND|ERROR|SKIPPED|LIMITED",
        "expiration": "MM/DD/YYYY|YYYY-MM-DD|",
        "url": "https://...",
        "note": "...",
        "days_until_expiry": int | None
    }
```

**Expiration date formats:** Accept both `%m/%d/%Y` (CA/states) and `%Y-%m-%d` (TX). Parse with a fallback format list instead of hardcoding one.

## Gap strategy references

- `references/utah-tennessee-public-gap-strategy.md`: Utah/TN gap workflow. Key rule: do not loop Utah exact-name searches unless trying a new legal name/alias; cheapest official Utah path is Active HFA roster only. TN BotDetect remains semi-auto/manual; CMS/NPI/web are clue-only, not license proof.

## Existing State Scraper Status

| State | Status | Notes | Board URL |
|-------|--------|-------|-----------|
| Alabama | ✅ Functional | ACTIVE, license #2353, renewal 10/31/2026. Parses Renewal Date + Licensure with days calculation. ASP.NET WebForms. | http://www.alboenha.alabama.gov/licensees.aspx |
| Alaska | 🟡 Semi-automated | DataDome CAPTCHA on CBPL search page. Use `semi_auto.py` — user solves CAPTCHA once per session, then batch processes all AK facilities. Form field is `OwnerEntityName` (single field). | https://www.commerce.alaska.gov/cbp/main/Search/Professional |
| Arizona | ✅ Functional | NCIA Board at Thentia Cloud. Active #NCA-002062, expires 2028-02-14. | https://aznciab.portalus.thentiacloud.net/webs/portal/register/#/ |
| California | ✅ Functional | CDPH NHA search. Opens DetailPage.aspx for expiration dates. Active #00007647, expires 2027-01-21. ASP.NET WebForms. | https://cvl.cdph.ca.gov/SearchPage.aspx |
| Colorado | ✅ Functional | CIM open data API (no CAPTCHA, free). Returns expiration dates. License types: NHA, MSNHA, NHATPE, TNHAP. | https://data.colorado.gov/resource/7s5z-vewr.json |
| Idaho | ✅ Functional | edopl.idaho.gov Name field #Dd-11. Active #NHA-1492, expires 10-Feb-2028. Parses expiration + days calculation. Name-only search works without board selection. | https://edopl.idaho.gov/OnlineServices/?link=PubSearch |
| Iowa | ✅ Functional | Use the public daily FileCloud roster `IBPLRoster.xlsx` instead of the Amanda Angular mat-select search form. Downloads from `https://filecloud.idph.state.ia.us/url/PLRosters`, extracts Nursing Home Administrators, caches `cache/iowa_nha_roster.json`, and handles multi-admin cells like `Amanda Birch / Leah Nelson`. Verified 9/9 ENSG Iowa rows PASS. | https://filecloud.idph.state.ia.us/url/PLRosters |
| Kansas | ✅ Functional | KSDADS glsuite portal (no CAPTCHA). Detail pages show expiration + status. License type: "Adult Care Home Administrator". | https://ksdadsv7prod.glsuite.us/glsuiteweb/Clients/ksdads/public/verification/LicVerification.aspx |
| Nebraska | ✅ Functional | PDF roster with admin names. Free, updated monthly. | https://dhhs.ne.gov/licensure/Documents/LTCRoster.pdf |
| Nevada | ✅ Functional | PDF roster at beltca.nv.gov — no CAPTCHA needed. Downloads NFA PDF, parses with pdftotext. 100 admins listed. All 3 ENSG facilities verified. | http://beltca.nv.gov/current-administrators/ |
| Oregon | ✅ Functional | OHLO search. Active #P-10229922, expires 2/28/2027. Tab-delimited results. | https://elite.hlo.state.or.us/OHLOPublicR |
| South Carolina | ✅ Functional (2captcha) | SC LLR requires reCAPTCHA v2. **2captcha workers CAN solve it** ($0.003/solve). Module: `states/south_carolina.py`. Verified: Lacey Smith ACTIVE #124419. Form fields: `#ctl00_ContentPlaceHolder1_UserInputGen_txt_lastName`, submit via JS click (hidden button). Also works with `semi_auto.py` (free, manual solve). | https://verify.llronline.com/LicLookup/LTC/LTC.aspx?div=35 |
| Tennessee | 🟡 Semi-automated | **BUG:** semi_auto.py uses `verify.tn.gov` which redirects to Commerce site (NO NHA data). Correct URL is `internet.health.tn.gov/Licensure/` (BotDetect CAPTCHA). Form fields: txtFirstName, txtMiddleName, txtLastName, drpProfessions=2514 (NHA). CAPTCHA field: `c_default_ctl00_pagecontent_captchacode`. Audio CAPTCHA disabled (400). OCR-resistant. ~11 facilities. | https://internet.health.tn.gov/Licensure/ |
| Texas | ✅ Functional | TULIP LWC shadow DOM. Active #NFA012571, expires 2027-01-26. | https://tulip.hhs.texas.gov/TULIP/s/public-search |
| Utah | 🟡 Semi-automated | DOPL License Lookup has reCAPTCHA v3. Playwright can get tokens but headless scoring is intermittent (~30-50% success). Use `semi_auto.py` for reliability, or paid data download ($0.01/record). ~34 facilities. | https://secure.utah.gov/llv/search/index.html |
| Washington | ✅ Functional | WA Open Data Socrata API (no CAPTCHA, free). Returns expiration dates. Dataset: qxh8-f4bd. | https://data.wa.gov/resource/qxh8-f4bd.json |
| Wisconsin | ✅ Functional | DSPS License Lookup. Active #4062-65, Brianna L Klemp, granted 2019-08-02. **No expiration date shown** — WI only shows Granted date. Status (Active/Inactive) is reliable. | https://license.wi.gov/s/license-lookup |

## Report Format (3-Tab Excel)

The verification output is a 3-tab Excel workbook:

### Tab 1: Executive Summary (opens first — tells the story in 30 seconds)
- **Key Metrics:** Total verified, PASS/FAIL/Manual counts, expired licenses, expiring within 60 days, missing admins
- **CMS Staffing & Compliance:** Average star rating, low staffing count, penalty count, abuse flags
- **Flagged Items Table:** Sorted by CRITICAL → MEDIUM → LOW severity
  - CRITICAL: expired license, abuse flag, license not verified
  - MEDIUM: expiring soon (≤60d), low CMS staffing rating (1-2 stars), 3+ penalties
  - LOW: high RN turnover (>50%), blocked states
- **Recommended Actions:** Priority-coded action items (CRITICAL/HIGH/MEDIUM/LOW)

### Tab 2: Charts (visual for presentations)
- **Pie Chart:** License Verification Status (PASS/FAIL/Manual Review %)
- **Bar Chart:** CMS Overall Star Rating Distribution (1-5 stars)
- **Bar Chart:** CMS Staffing Rating Distribution (1-5 stars)
- **Horizontal Bar:** License Expiration Timeline (Expired → 30d → 60d → 90d → 180d → 365d → 1yr+)

### Tab 3: Detailed Results (raw data for drilling down)
All facilities with every data column (license + CMS). Color-coded:
- **Green fill:** PASS (active license)
- **Red fill:** FAIL (not found, expired, errors)
- **Yellow fill:** NEEDS MANUAL REVIEW (blocked states)
- **Bold red:** Expiration alerts (≤60 days or expired)

### Output filename
Use timestamped filenames (`verification_YYYY-MM-DD_HHMMSS.xlsx`) to avoid `PermissionError` when the previous report is still open in Excel.

### Final max-coverage report
When Kevin asks for the "final report Excel spreadsheet with as many administrators on it as possible," the deliverable is a single workbook containing every admin row from the master file, not only the states that completed in the latest run. If a full `verify_all.py` run hangs or times out, use the safest complete workbook as the base, refresh improved states with single-state runs, merge refreshed rows by `(State, Facility, Admin Name)`, normalize legacy labels (`VERIFIED` -> `PASS`), and explicitly mark low-confidence CAPTCHA states as `NEEDS MANUAL REVIEW` rather than pretending they are verified.

`build_final_max_coverage.py` should also merge the newest targeted supplemental correction workbooks after the base/single-state reports, so expensive problem-state fixes are preserved without rerunning a full state every time. Current patterns include:
- `texas_unresolved_refresh_*.xlsx`
- `california_unresolved_refresh_*.xlsx`
- `california_jeffrey_beltran_refresh_*.xlsx`
- `california_timeout_retry_*.xlsx`
- `idaho_unknown_retry_*.xlsx`

Use `--skip-refresh --no-email` for safe ad-hoc verification; it should still discover latest single-state reports and supplemental correction files. See `references/final-report-max-coverage.md`.

### Desktop shortcuts + separate GUI workflow
Kevin wants two separate user-facing entry points, not one combined frontend:
- **Click-and-forget desktop shortcut**: `ENSG License Report - Click and Forget.lnk` -> `run_final_report_click_and_forget.cmd` -> `python build_final_max_coverage.py`; builds final max-coverage workbook, logs to `logs/click_and_forget_latest.log`, and emails final report.
- **Web GUI shortcut**: `ENSG License Verification - Web GUI.lnk` -> `launch_web_gui.cmd` -> `python -m streamlit run app.py`; opens dashboard/settings/report viewer and stays separate from the unattended report runner.

The permanent builder is `build_final_max_coverage.py`: find latest complete 426-row workbook, refresh configured high-confidence states from `config.json`, merge by `(State, Facility, Admin Name)`, gate AK/TN/UT to manual, write `FINAL_ENSG_max_admin_coverage_*.xlsx`, then email only the final report. For implementation/verification details, see `references/desktop-shortcuts-and-final-report-gui.md`.

## Auto-Detection of New Facilities

Compare row count against stored snapshot. New rows → auto-process.

When SharePoint is the source, Power Automate triggers on item creation. When using Excel, a watcher script detects file modifications and re-runs.

## Alabama ALBONEHA Scraper Pattern (VALIDATED)

**Site:** http://www.alboenha.alabama.gov/licensees.aspx

Classic ASP.NET WebForms. Search by name, then parse the result page.

```python
page.check("#ctl00_ContentPlaceHolder1_UserInputGen_rdoSearchByName")
page.fill("#ctl00_ContentPlaceHolder1_UserInputGen_txtLastName", last_name)
page.fill("#ctl00_ContentPlaceHolder1_UserInputGen_txtFirstName", first_name)
page.click("#ctl00_ContentPlaceHolder1_UserInputGen_btnSearch")
page.wait_for_load_state("networkidle", timeout=15000)
text = page.inner_text("body")
```

Parsing uses regex on the result text:
- License Number: `re.search(r"License Number:\s*(\d+)", text, re.IGNORECASE)`
- Status: look for "Active" / "Inactive" / "Expired"
- Renewal Date: parse after "Renewal Date:" label

**Pitfall:** The result text contains non-breaking spaces (`\xa0`) and mixed line breaks. Use `\s*` in regex and strip whitespace from captures.

## Arizona NCIA Board Scraper Pattern (FULLY FUNCTIONAL)

**Site:** https://aznciab.portalus.thentiacloud.net/webs/portal/register/#/
**Verified:** Conner Monks Active #NCA-002062, expires 02/14/2028

**Critical discovery:** AZ Care Check (`azcarecheck.azdhs.gov`) searches FACILITIES, not individual NHA administrators. The correct source is the **NCIA Board** (Nursing Care Institution Administrators and Assisted Living Facility Managers) at the Thentia Cloud portal.

The NCIA Board site is a single-page app (Thentia Cloud). Search works by entering a name and clicking Search — no login required:

```python
page.goto("https://aznciab.portalus.thentiacloud.net/webs/portal/register/#/")
page.wait_for_load_state("networkidle", timeout=15000)
page.wait_for_timeout(2000)

# Select Individual License (radio button)
page.locator('input[name="registerType"]').first.click()
page.wait_for_timeout(500)

# Fill search
page.locator('input[name="keywords"]').fill(admin_name.strip())
page.wait_for_timeout(200)

# Click Search
page.locator('button:has-text("Search")').click()
page.wait_for_load_state("networkidle", timeout=15000)
page.wait_for_timeout(2000)
```

Results are tab-delimited: License Number | First Name | Last Name | License Type | License Status | License Expiration Date | Disciplinary Action

## Oregon OHLO Scraper Pattern (FULLY FUNCTIONAL)

**Site:** https://elite.hlo.state.or.us/OHLOPublicR
**Verified:** David Horn Active #P-10229922, expires 2/28/2027

Classic ASP.NET WebForms with specific element IDs:

```python
page.locator("#CPH1_txtsrcApplicantLastName").fill(last_name)
page.locator("#CPH1_txtsrcApplicantFirstName").fill(first_name)
page.locator("#CPH1_btnGoFind").click()
page.wait_for_load_state("networkidle", timeout=15000)
```

Results are tab-separated. Column layout (0-indexed):
- 0: (empty)
- 1: Licensee Name (format: "LASTNAME, FIRSTNAME M")
- 2: License No.
- 3: Status (Active/Inactive/Expired)
- 4: Active Through (expiration date, format M/D/YYYY)
- 5: City, State, Zip
- 6: License Type (e.g., "P - Permanent - Nursing Home Administrator")
- 7: Board

**Parser:** Skip header row (Licensee Name). Filter for "Active" status. Prefer NHA license type. Expiration format is `M/D/YYYY` (no leading zeros).

## Wisconsin DSPS Scraper Pattern (FULLY FUNCTIONAL — NO EXPIRATION DATE)

**Site:** https://license.wi.gov/s/license-lookup
**Verified:** Brianna L Klemp Active #4062-65, granted 2019-08-02

**CRITICAL: WI does NOT show expiration dates.** The portal shows a "Granted" date, which is when the license was first issued. Do NOT use this as the expiration date — it will show licenses as "expired from 2019" when they're actually active. Set `expiration = ""` and `days_until_expiry = None`.

Salesforce Lightning-style grid with custom combobox for search type.

### Search flow:
1. Click "Select Search By" text to open dropdown
2. Click "Individual Name" option
3. Fill `lastName` and `firstName` inputs (appear after selection)
4. Click Search button

```python
page.get_by_text("Select Search By").click()
page.wait_for_timeout(1000)
page.get_by_text("Individual Name").click()
page.wait_for_timeout(1000)
page.locator('input[name="lastName"]').fill(last)
page.locator('input[name="firstName"]').fill(first)
page.get_by_role("button", name="Search").click()
```

### Result parsing — regex pattern

The page uses `\r\n\t\r\n` as field separators (each field on its own line with tabs). Use regex:

```python
pattern = (
    r'(\d+\s*-\s*\d+)\s*\n'
    r'Nursing Home Administrator\s*\n'
    r'(\w+)\s*\n'
    r'([^\n]+)\s*\n'
    r'([^\n]*)\s*\n'
    r'([^\n]+)\s*\n'
    r'([^\n]+)\s*\n'
    r'(\d+)\s*\n'
    r'(\d{4}-\d{2}-\d{2})\s*\n'
    r'(Active|Inactive|Expired|Revoked|Suspended)'
)
```

Groups: 0=LicenseNum, 1=Type, 2=Name, 3=DBA, 4=City, 5=State, 6=Zip, 7=Granted, 8=Status

**Note:** WI doesn't show expiration date in the listing, only Granted date.

## Colorado CIM Open Data API Pattern (FULLY FUNCTIONAL — NO PLAYWRIGHT)

**API:** https://data.colorado.gov/resource/7s5z-vewr.json
**Dataset:** Professional and Occupational Licenses for Colorado
**Verified:** Emily Amschel Active #3010, exp 2027-02-28; Eddy Boyles Active #1867

Colorado's DORA license lookup has CAPTCHA, but the state publishes all license data via the Colorado Information Marketplace (CIM) — a free Socrata open data API. No Playwright needed.

### Query pattern

```python
import urllib.parse, urllib.request, json

NHA_TYPES = ("NHA", "MSNHA", "NHATPE", "TNHAP")
type_clause = " OR ".join(f"licensetype='{t}'" for t in NHA_TYPES)
where = f"({type_clause}) AND upper(lastname)='{last_name.upper()}'"
params = urllib.parse.urlencode({"$where": where, "$limit": "20"})
api_url = f"https://data.colorado.gov/resource/7s5z-vewr.json?{params}"

req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
```

### Response fields
- `lastname`, `firstname`, `middlename`, `entityname`
- `licensetype` (NHA, MSNHA, NHATPE, TNHAP)
- `licensenumber`
- `licenseexpirationdate` (ISO: `2027-02-28T00:00:00.000` — slice to `[:10]` for date)
- `licensestatusdescription` (Active, Expired, Revoked, Suspended)
- `city`, `state`
- `linktoverifylicense` (URL object)

### Key notes
- The `in()` clause does NOT work with Socrata — use `OR` instead.
- NHA license types are coded: `NHA`, `MSNHA`, `NHATPE`, `TNHAP`.
- All active NHAs expire on the same date (2027-02-28 in current data).
- No rate limiting observed, but keep `$limit` reasonable.

**Lesson:** When a state portal has CAPTCHA, check if the state has an open data portal (Socrata, CKAN, etc.) with license data. This pattern may work for other states.

## Washington Open Data Socrata API Pattern (FULLY FUNCTIONAL — SUPERSEDES HELMS)

**API:** https://data.wa.gov/resource/qxh8-f4bd.json
**Dataset:** Health Care Provider Credential Data (2.42M rows, daily updates)
**Verified:** Matthew Payne Active #NHA.NH.61348152, exp 09/22/2026

Washington's HELMS portal has reCAPTCHA, but the state publishes all healthcare provider credential data via a Socrata open data API. Same pattern as Colorado CIM.

### Query pattern

```python
import urllib.parse, urllib.request, json

where = f"upper(credentialtype) like '%NURSING HOME%' AND upper(lastname)='{last_name.upper()}'"
params = urllib.parse.urlencode({"$where": where, "$limit": "20"})
api_url = f"https://data.wa.gov/resource/qxh8-f4bd.json?{params}"

req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
```

### Response fields
- `credentialnumber` — License number (e.g., NHA.NH.61348152)
- `lastname`, `firstname`, `middlename`
- `credentialtype` — "Nursing Home Administrator License"
- `status` — Active/Expired/Revoked
- `expirationdate` — MM/DD/YYYY format
- `firstissuedate`, `lastissuedate`
- `actiontaken` — Disciplinary action indicator

### Key notes
- Credential type is "Nursing Home Administrator License" (not just "NHA")
- Expiration dates are in MM/DD/YYYY format (not ISO)
- Bonus score for Active status when matching names
- Same Socrata SODA 3.0 API as Colorado — reusable pattern

## Kansas KSDADS glsuite Portal Pattern (FULLY FUNCTIONAL)

**Portal:** https://ksdadsv7prod.glsuite.us/glsuiteweb/Clients/ksdads/public/verification/LicVerification.aspx
**Verified:** Ethan Dean Active #4280, exp 06/30/2028

Kansas prolicenseverify.ks.gov has reCAPTCHA, but the KSDADS (Kansas Department for Aging and Disability Services) glsuite portal has no CAPTCHA. It covers "Adult Care Home Administrators" (Kansas equivalent of NHA).

### Search flow

```python
page.goto(KS_URL, timeout=30000)
page.wait_for_load_state("networkidle", timeout=15000)
page.fill("#waLastName", last_name)
if first_name:
    page.fill("#waFirstName", first_name)
page.click("#btnSubmit")
page.wait_for_load_state("networkidle", timeout=15000)
```

### Results format
Results table: Details (link) | First Name | Middle Name | Last Name | License Number | License Type

Filter for "Adult Care Home Administrator License" (exclude "Temporary" variants).

### Detail page for expiration/status
Click "Details" link to get the full record. The page has a two-column layout where labels and values are in SEPARATE sections with a gap.

**Critical parsing pitfall:** Labels (Expiration Date:, Status:) appear on lines 7-16. Values appear on lines 19-28. They are NOT adjacent. Parse by:
1. Find "Disciplinary Action:" label to mark end of label section
2. Search for MM/DD/YYYY dates after that point — the SECOND date is the expiration (first is issue date)
3. Search for status words (active/inactive/expired) after that point

```python
lines = [l.strip() for l in text.split("\n") if l.strip()]
label_end = 0
for i, line in enumerate(lines):
    if "Disciplinary Action" in line:
        label_end = i
        break

dates_found = []
for i in range(label_end, len(lines)):
    line = lines[i]
    if len(line) == 10 and line.count("/") == 2:
        try:
            datetime.strptime(line, "%m/%d/%Y")
            dates_found.append(line)
        except ValueError:
            pass
    if line.lower() in ("active", "inactive", "expired", "revoked", "suspended"):
        status = line

# Expiration is the second date (after issue date)
if len(dates_found) >= 2:
    expiration = dates_found[1]
```

## Nebraska PDF Roster Scraper Pattern (FULLY FUNCTIONAL)

**Site:** https://dhhs.ne.gov/licensure/Documents/LTCRoster.pdf
**Verified:** Kristie Kallemeyn #324003 (MONROE HEALTHCARE), Alice Smith #034001 (VSL ALLIANCE)

Nebraska's License Lookup requires reCAPTCHA, but the state publishes a free monthly PDF roster of all Long Term Care facilities with administrator names and license numbers.

### How it works:
1. Download the PDF from the DHHS URL
2. Parse with pdfplumber
3. Search for admin name (case-insensitive)
4. Look backward in the text for license number (6-digit) and facility name

```python
import pdfplumber, urllib.request, tempfile, os, re

tmp_path = os.path.join(tempfile.gettempdir(), "nebraska_roster.pdf")
urllib.request.urlretrieve("https://dhhs.ne.gov/licensure/Documents/LTCRoster.pdf", tmp_path)

with pdfplumber.open(tmp_path) as pdf:
    text = ""
    for page in pdf.pages:
        text += (page.extract_text() or "") + "\n"
os.unlink(tmp_path)

# Search for "Kristie Kallemeyn, Administrator" in text
# Look backward for license number (6-digit on FAX line)
# Look for facility name before "Total Licensed"
```

**Pitfall:** The license number appears on a line with "FAX:" — extract the 6-digit number from that line. The facility name appears on a line with "Total Licensed" — extract the text before that phrase.

**Expiration rule:** Nebraska LTC licenses expire March 31st each year (stated in the PDF header). Calculate expiration rather than scraping:
```python
today = datetime.now()
if today.month < 3 or (today.month == 3 and today.day <= 31):
    expiration = f"{today.year}-03-31"
else:
    expiration = f"{today.year + 1}-03-31"
```

**Note:** Requires `pip install pdfplumber`. The roster is updated on or about the 15th of each month.

## Nevada BELTCA PDF Roster Pattern (FULLY FUNCTIONAL — NO CAPTCHA)

**Site:** http://beltca.nv.gov/current-administrators/
**PDF:** http://beltca.nv.gov/uploadedFiles/beltcanvgov/content/CEU_Program/Licensed%20Nursing%20Facility%20Administrators.pdf
**Verified:** Nathan Lant #826 (Active, exp 8/31/2026), Seth Anderson #801 (Active, exp 6/30/2026), Whitney Wilding #817 (Active, exp 10/31/2027)

Nevada's BELTCA site at `beltca.nevada.gov` has an SSL cert mismatch (redirects to `http://beltca.nv.gov`). The "Current Administrators" page has PDF rosters for all administrator types — no CAPTCHA, no login required.

### Available PDFs
- Licensed Nursing Facility Administrators (NFA) — **this is the one we need**
- Licensed Residential Facility Administrators (RFA)
- Licensed Health Services Executives (HSE)

### How it works
1. Download the NFA PDF roster via HTTP (URL-encode spaces)
2. Extract text with `pdftotext -layout` (preserves column alignment)
3. Parse each line: `Last, First Middle    License#    Status    OrigDate    ExpDate`
4. Match ENSG admin names against the roster
5. Return status, license number, and expiration date

### Parser pattern
```python
import subprocess, re

result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'],
                       capture_output=True, text=True, timeout=30)
lines = result.stdout.split('\n')

for line in lines:
    line = line.strip()
    if not line or 'Administrator Name' in line or 'LICENSED' in line:
        continue
    # Match: Name  License#  Status  OrigDate  ExpDate
    m = re.match(
        r"^(.+?)\s{2,}(\d+)\s+(Active|Inactive|Expired|...)"
        r"\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})",
        line
    )
    if m:
        name_raw = m.group(1).strip()
        name_parts = name_raw.split(", ", 1)
        last = name_parts[0].strip()
        first_middle = name_parts[1].strip() if len(name_parts) > 1 else ""
        full_name = f"{first_middle} {last}"
        # m.group(2)=license, m.group(3)=status, m.group(4)=orig_date, m.group(5)=exp_date
```

### Name matching
Use two-pass matching:
1. Exact match: `a["name"].lower() == admin_name.lower()`
2. First + Last match: `a["last"].lower() == search_last and a["first"].lower().startswith(search_first)`
3. Last name only (weaker): only if exactly one candidate

**Pitfall:** Names in the PDF use "Last, First Middle" format with middle initials. The ENSG Excel uses "First Last" format. Always split on `, ` and reconstruct as `First Middle Last`.

**Roster update frequency:** Updated quarterly (last updated 03/31/2026 in current PDF). Check the "Last Updated" date at the top of the PDF.

## Utah DOPL Playwright + reCAPTCHA v3 Pattern (INTERMITTENT)

**Site:** https://secure.utah.gov/llv/search/index.html
**Profession:** Health Facility Administrator (checkbox `item153_1`)
**Status:** Works ~30-50% of attempts. reCAPTCHA v3 scores headless browsers inconsistently.

### Key technique: Click submit button, not form.submit()

Utah's reCAPTCHA v3 form does NOT work with `form.submit()` or `requestSubmit()`. The only reliable submission method is clicking the actual submit button:

```python
# Get reCAPTCHA v3 token
pg.evaluate("""
    () => {
        return new Promise((resolve) => {
            const siteKey = document.getElementById('recaptchaSiteKey');
            grecaptcha.execute(siteKey.value, {action: 'search'}).then(token => {
                document.getElementById('g-recaptcha-response-name').value = token;
                resolve();
            });
        });
    }
""")

# MUST click the button — form.submit() does NOT work
submit_btn = pg.query_selector("input[type='submit']")
submit_btn.click()

# Wait for URL change — NOT expect_navigation (which fails intermittently)
pg.wait_for_url("**/search.html**", timeout=15000)
```

### Results page structure

After submission, the page navigates to `/llv/search/search.html`. Results are multi-line:
```
NAME\tCITY\t
PROFESSION
LICENSE_TYPE
\tLICENSE#\tSTATUS
```

**Critical:** Names are in ALL CAPS (e.g., "KIRK RODNEY PLAYER"). The parser must handle:
1. ALL CAPS names (not just mixed case)
2. Tab-separated status lines (`7946637-1501\tACTIVE`)
3. Header lines that look like names ("City\tProfession\tLicense #")

### Parser must skip header lines
```python
skip_words = ["LICENSEE NAME", "CITY", "STATUS", "LICENSE #",
              "SEARCH RESULTS", "DO ANOTHER", "PLEASE NOTE"]
is_header = any(sw in prev.upper() for sw in skip_words)
if is_header:
    continue
```

### Why it's intermittent
reCAPTCHA v3 scores requests on IP reputation + cookie history + behavioral patterns. Headless Chromium from a datacenter IP gets a low score (~0.1-0.3) while real browsers get 0.9+. The token is technically valid but the server may reject low-score tokens. Factors that help:
- Adding `--disable-blink-features=AutomationControlled` to Chrome args
- Setting realistic viewport (1920x1080) and locale
- Removing webdriver detection: `Object.defineProperty(navigator, 'webdriver', {get: () => undefined})`
- Adding 1s delay before token request (more human-like)

Even with all these, success rate is ~30-50%. For reliable Utah coverage, use `semi_auto.py` or the paid data download.

## Utah DOPL Workarounds (reCAPTCHA v3 live lookup is not click-and-forget)

**Live lookup:** https://secure.utah.gov/llv/search/index.html
**Official data request:** https://secure.utah.gov/datarequest/professionals/index.html
**Cost shown:** $0.01/record, minimum $5.00 for first 200 records

Utah DOPL License Lookup requires reCAPTCHA v3. Browser-side and 2captcha tokens can be obtained, but the portal rejects low-score sessions intermittently; do not treat headless/2captcha Utah as production unless a sustained batch run proves reliability.

Preferred stable workaround: order/download the Utah “Professions Licensed in Utah” list filtered to **Health Facility Administrator**. The page states the list includes Name, License type, and License status; address/phone/email needs DOPL approval but is not required for ENSG verification. Once Kevin obtains the file, implement Utah like Iowa/Nevada: put it under `D:/license-verification/cache/utah_roster/`, parse the newest roster, match admins, and merge a `utah_roster_refresh_*.xlsx` correction workbook into the final report.

Practical free workaround: a separate semi-auto Edge workflow. Use Kevin’s real browser/session, let him pass reCAPTCHA, then batch-search all Utah admins and save a Utah correction workbook. Keep this separate from the unattended shortcut.

Until a roster/download or semi-auto correction workbook exists, keep Utah in `NEEDS MANUAL REVIEW`; a rejected reCAPTCHA v3 token is an automation-confidence failure, not proof the admin is unlicensed.

See `references/utah-dopl-workarounds.md` for tested mechanics and implementation sketch.

## Iowa Public Roster Pattern (FULLY FUNCTIONAL — PREFERRED OVER AMANDA PORTAL)

**Source:** https://filecloud.idph.state.ia.us/url/PLRosters
**File:** `IBPLRoster.xlsx` inside downloaded `pl.zip`
**Verified:** 9/9 ENSG Iowa facilities PASS, including `Amanda Birch / Leah Nelson` multi-admin cell.

Do NOT automate the Amanda Angular mat-select form unless the public roster disappears. The FileCloud roster is higher accuracy, faster, and no CAPTCHA/Angular fragility.

Pattern:
1. Open FileCloud URL with Playwright and click the `Download Folder` button.
2. Extract `IBPLRoster.xlsx` from the zip.
3. Filter rows where `folder == "Nursing Home Administrators"` and subtype is `Nursing Home Administrator` or `Nursing Home Administrator Provisional`.
4. Cache extracted NHA rows to `cache/iowa_nha_roster.json`; scanning the full workbook repeatedly is slow.
5. Split workbook admin cells on `/`, `;`, `and`, `&` so `Amanda Birch / Leah Nelson` can match either person.

Roster columns observed: data date, folder, subtype, status, license number, original issue, issue, expiration, first name, last name, address/city/state fields. Expiration can be parsed to ISO `YYYY-MM-DD`.

See `references/iowa-roster-and-captcha-architecture.md` for implementation and ad-hoc verification details.

## Idaho edopl Portal Pattern (NEEDS REFINEMENT)
## Iowa DIAL/Amanda Portal Pattern (SUPERSEDED — USE FILECLOUD ROSTER)

The DIAL page and Amanda Portal are no longer the preferred route for ENSG NHA verification. Amanda has Angular mat-select complexity and is slower than the public roster. Use the FileCloud `IBPLRoster.xlsx` pattern above instead.

## Kansas prolicenseverify Pattern (SUPERSEDED — USE KSDADS)

**Old site:** https://prolicenseverify.ks.gov/
**Status:** BLOCKED — reCAPTCHA on page load. The KSDADS glsuite portal (see above) is the working alternative.

## Colorado DORA Scraper Pattern (SUPERSEDED — USE CIM API)

**Old site:** https://dpo.colorado.gov/COHPC (redirects to HPPP)
**Status:** The DORA license lookup at `apps.colorado.gov/dora/licensing/Lookup/LicenseLookup.aspx` has CAPTCHA. However, Colorado publishes all license data via the CIM open data API (see "Colorado CIM Open Data API Pattern" above). Use the API instead.

## Partial Re-Verification (When One State Fails)

When a state scraper fails during a full `verify_all.py` run (e.g., asyncio loop error, timeout, CAPTCHA), you do NOT need to re-run the entire 20-minute verification. Instead:

1. **Re-verify just the failed state** — write a quick script that loads the master Excel, filters to that state, and runs only that state's scraper:
```python
import openpyxl, json, time
from states import texas  # or whichever state

wb = openpyxl.load_workbook(EXCEL_PATH)
ws = wb.active
facilities = []
for r in range(2, ws.max_row + 1):
    if 'TEXAS' in str(ws.cell(r, 9).value or '').upper():
        admin = str(ws.cell(r, 6).value or '').strip()
        if admin and admin.lower() not in ('nan', 'none', ''):
            facilities.append(admin)

results = []
for admin in facilities:
    r = texas.verify_texas(admin)
    results.append({"admin": admin, **r})
    time.sleep(0.5)

with open("results/texas_results.json", "w") as f:
    json.dump(results, f)
```

2. **Merge into existing report** — load the existing Excel report, find rows for that state, and update the license status/result/expiration columns with the new data. Save to a new timestamped filename.

3. **Save partial results as JSON** — during re-verification, save after every 10 facilities so a crash doesn't lose all progress. On re-run, skip already-verified admins.

This approach fixed all 110 Texas facilities in ~8 minutes instead of re-running the full 20-minute verification.

## Adding New State Scrapers (Procedure)

1. Find the state licensing board's public search URL via web search.
2. Determine search fields available: name-only is preferred; facility-only is LIMITED.
3. If name-based: write a Playwright script that fills the form and parses results.
4. **Test the scraper individually with a real admin name from the Excel before committing.**
5. **If the test passes, commit the scraper, then move to the next state. Do not batch-write stubs and test later.**
6. Add the scraper to `states/<state>.py`, import it in `verify_licenses.py`, and register it in `STATE_SCRAPERS` and `config.json["states"]`.

**Workflow rule: verify one state at a time.** Build → test with real data → commit → next state. This prevents carrying forward broken selectors across many files at once.

## Idaho edopl Portal Pattern (FULLY FUNCTIONAL)

**Site:** https://edopl.idaho.gov/OnlineServices/?link=PubSearch
**Verified:** Calene Cole Active #NHA-1492, expires 10-Feb-2028

The Name field uses the ID `Dd-11`. The Board and License Type fields are custom React comboboxes that are difficult to automate — but searching by Name alone works without selecting a board.

```python
page.locator('#Dd-11').fill(admin_name.strip())
page.locator('#Dd-11').press("Enter")
page.wait_for_load_state("networkidle", timeout=15000)
```

Results are tab-separated. The line containing the matched name also contains Status and Expiration. Look backward 1-2 lines for the license number (format `[A-Z]{3}-\d+`, e.g. `NHA-1492`).

**Parser logic:**
- Find the line containing the admin name.
- Primary same-row format from the current portal looks like: `\tNursing Home Administrator License\tEMILY CHRISLIP\t\tActive\t14-Sep-2028\tNo`. Split on tabs, drop empty fields, then parse `parts[0]=license type`, `parts[1]=name`, `parts[2]=status`, `parts[3]=expiration`.
- Support both `FIRST LAST` and `LAST, FIRST M` names in the same-row parser.
- Fallback older layout: look backward 1-2 lines for license number pattern `^[A-Z]{3}-\d+$`, then parse status/expiration from the current row.
- Expiration format: `10-Feb-2028` (DD-Mmm-YYYY).

## Tennessee — THREE URLs, Only One Has NHA Data

Tennessee has three separate portals. **Only the Health Department portal has NHA license data.**

| URL | Redirects to | Has NHA? | Notes |
|-----|-------------|----------|-------|
| `verify.tn.gov` | `search.cloud.commerce.tn.gov` | **NO** | Commerce & Insurance site. Covers cosmetology, real estate, contractors — NOT health licenses. semi_auto.py currently points here by mistake. |
| `internet.health.tn.gov/Licensure/` | (stays) | **YES** | Health Department portal. BotDetect CAPTCHA (ASP.NET WebForms). This is the correct NHA source. |
| `internet.health.tn.gov/LicensureReports/` | (stays) | **YES** | Report generator. jQuery AJAX + CSRF tokens. No CAPTCHA but form submission via Playwright fails. |

**semi_auto.py bug:** The TN config uses `https://verify.tn.gov/` which redirects to the Commerce site (no NHA data). The correct URL for semi_auto is `https://internet.health.tn.gov/Licensure/`. Fix selectors for BotDetect CAPTCHA form before running.

### Tennessee Health Portal — Reverse Engineering Details

**Portal:** `https://internet.health.tn.gov/Licensure/`
**Tech:** ASP.NET WebForms + BotDetect CAPTCHA (image-based, NOT reCAPTCHA)

**Form fields (ASP.NET naming convention):**
- `ctl00$PageContent$txtFirstName` — First name
- `ctl00$PageContent$txtMiddleName` — Middle name
- `ctl00$PageContent$txtLastName` — Last name (required for search)
- `ctl00$PageContent$txtCity` — City filter
- `ctl00$PageContent$drpStates` — State dropdown (values: AL, AK, etc.)
- `ctl00$PageContent$drpProfessions` — Profession dropdown
  - Value `2514` = "Nursing Home Administrator"
  - Value `9999` = "ALL"
- `ctl00$PageContent$txtLicense` — License number
- `ctl00$PageContent$btnSubmit` — Submit button
- `c_default_ctl00_pagecontent_captchacode` — BotDetect CAPTCHA text input

**ASP.NET hidden fields (required for POST):**
- `__VIEWSTATE` — Page state (large base64, ~4500 chars)
- `__VIEWSTATEGENERATOR` — Fixed value: `BAEED252`
- `__EVENTVALIDATION` — Form validation token (~1200 chars)
- `__EVENTTARGET` — Empty string for normal submit
- `__EVENTARGUMENT` — Empty string

**CAPTCHA analysis:**
- BotDetect image CAPTCHA (250x40 JPEG, ~3.5KB)
- OCR (pytesseract) gives garbage — BotDetect is OCR-resistant
- Audio CAPTCHA endpoint exists but returns 400 (disabled by site)
- Headless browser gets 403 (IP blocking from datacenter IPs)
- Form submission without CAPTCHA → redirects to `SearchError.aspx`
- Session cookie: `ASP.NET_SessionId` (required for CAPTCHA validation)

**Why automated solving is hard:**
- reCAPTCHA v3 / DataDome can sometimes be bypassed with residential proxies
- BotDetect image CAPTCHAs are specifically designed to resist OCR
- Audio CAPTCHA (which Whisper could transcribe) is disabled on this portal
- The only reliable approaches are: (1) semi_auto.py with manual solve, or (2) paid CAPTCHA service (2captcha ~$0.003/solve)

**Data last updated:** Shows "Data Last Updated: [date]" on the page — current as of session date.

### LicensureReports Portal (Report Generator — NOT for individual lookup)

**Portal:** `https://internet.health.tn.gov/LicensureReports/`
**Tech:** jQuery AJAX + CSRF tokens, no CAPTCHA on the reports page

This is a bulk report generator, NOT an individual license lookup. It can generate CSV/Excel reports of all licensees by board/profession. However:
- Board and Profession dropdowns load dynamically via AJAX (`FetchProfessionsByBoard`)
- Profession depends on Board selection (another AJAX call)
- Form uses `__RequestVerificationToken` CSRF token (changes per session)
- Report generation may be async (polling for file download)

**Potential approach (not yet implemented):**
1. Load the reports page
2. Extract CSRF token from page metadata
3. Select Board → Profession via AJAX calls
4. Submit report request
5. Poll for/download the generated CSV

This could bypass the individual-search CAPTCHA by getting a bulk export instead. Worth investigating if semi_auto.py proves too slow for 11 facilities.

## Kansas prolicenseverify Pattern (SUPERSEDED — USE KSDADS)

**Old site:** https://prolicenseverify.ks.gov/
**Status:** BLOCKED — reCAPTCHA on page load. Use the KSDADS glsuite portal instead (see "Kansas KSDADS glsuite Portal Pattern" above).

## Colorado DORA Pattern (BLOCKED — CAPTCHA)

**Site:** https://dpo.colorado.gov/COHPC
**Status:** BLOCKED — site shows "Let's confirm you are human" CAPTCHA before any search. No workaround found. The old DORA URL (dora.colorado.gov/check-a-license) doesn't return NHA data.

## Semi-Automated Browser (`semi_auto.py`)

For states blocked by CAPTCHA/reCAPTCHA/CloudFront/hCaptcha/JS verification. Opens a real Chrome window with a persistent profile. You solve ONE CAPTCHA per state per session, then the script auto-searches all admin names.

**Implemented states (8):** Alaska (DataDome), Colorado (CloudFront), Iowa (JS verification), Kansas (reCAPTCHA), South Carolina (reCAPTCHA), Tennessee (BotDetect CAPTCHA), Utah (reCAPTCHA), Washington (Salesforce reCAPTCHA)

**Browser:** Uses Microsoft Edge by default (`channel="msedge"` in Playwright). Change to Chrome by removing the `channel` parameter.

**Usage:**
```bash
python semi_auto.py              # Interactive — prompts for state
python semi_auto.py UTAH         # CLI arg — skips prompt, opens Chrome directly
```

**Time investment:** ~5-10 minutes per state per month (one CAPTCHA solve, then batch processing).

**Usage:**
```bash
python semi_auto.py              # Interactive — prompts for state
python semi_auto.py UTAH         # CLI arg — skips prompt, opens Chrome directly
```

**CLI argument support:** `semi_auto.py` accepts the state name as a command-line argument (`sys.argv[1]`), skipping the interactive `input()` prompt. This is useful for non-interactive terminals.

**Chrome profile locking:** `launch_persistent_context` locks the Chrome profile directory. If Chrome was previously running (even from a killed process), the next launch fails with "Opening in existing browser session." Fix: `taskkill //F //IM chrome.exe` before running, and remove `SingletonLock`/`SingletonSocket`/`SingletonCookie` files from the profile directory.

**Single-field portals:** When `selector_last == selector_first` (e.g., Utah uses `#fullName` for both), the script fills the full name into the single field instead of trying to fill two separate fields.

**Key selectors:**
- **South Carolina:** `#ctl00_ContentPlaceHolder1_UserInputGen_txt_lastName`, `#ctl00_ContentPlaceHolder1_UserInputGen_txt_firstName`, `#ctl00_ContentPlaceHolder1_btn_find`
- **Tennessee:** Dynamic ID inputs matched by label text. Submit: `button:has-text("Search")`
- **Utah:** `#lastName`, `#firstName`, `input[type='submit'][value='Search']`
- **Washington:** `#lastName`, `#firstName`, `button:has-text('Search')`
- **Kansas:** `#lastName`, `#firstName`, `button:has-text('Search')`
- **Alaska:** `select[name='Program']` (pre-submit hook selects "Nursing Home Administrators"), `input[name='OwnerLastName']`, `input[name='OwnerFirstName']`, `input[value='Search']`
- **Colorado:** `#lastName`, `#firstName`, `input[value='Submit']`
- **Iowa:** `input[name='lastName']`, `input[name='firstName']`, `button[type='submit']`

**Pre-submit hooks:** Alaska needs to select "Nursing Home Administrators" from a Program dropdown before searching. `semi_auto.py` supports `pre_submit` hooks in the state config for this.

## Master Verifier (`verify_all.py` + `run_nightly.py`)

Reads Excel, runs all state verifiers, writes color-coded Excel report.

```bash
python run_nightly.py
```

Output: `D:\license-verification\results\verification_YYYY-MM-DD.xlsx`

### Result Classification
- **PASS:** status is ACTIVE/FOUND + license is active
- **FAIL:** status is NOT FOUND/INACTIVE/EXPIRED/REVOKED/SUSPENDED
- **NEEDS MANUAL REVIEW:** BLOCKED, NEEDS_MANUAL, or ERROR

### Expiration Alerts
Any license expiring within 60 days (or already expired) gets an alert in the "Expiration Alert" column: `EXPIRES IN X DAYS` or `EXPIRED`.

### Error Handling
- Empty admin names in Excel → skipped (logged in summary)
- State not in `STATE_VERIFIERS` → logged in "states with issues" section
- Scraper exception → recorded as ERROR with traceback in note

## CAPTCHA/Blocked State Workarounds

For states blocked by CAPTCHA, reCAPTCHA, 403, or SSL errors, consider these alternatives:

### 1. Semi-Automated Browser (`scripts/semi_auto.py`) — RECOMMENDED for all blocked states
Open a real Chrome window (non-headless, persistent profile), user solves ONE CAPTCHA, then script batch-processes all facilities for that state. Only 1 CAPTCHA per state per month. **Time cost: ~5-10 minutes/month per state.** Implemented states: AK, CO, IA, KS, SC, TN, UT, WA.

**Why this works:** DataDome, reCAPTCHA v3, and CloudFront all evaluate browser behavior + IP reputation. A real Chrome window with your residential IP + manual CAPTCHA solve establishes a trusted session. The persistent profile retains cookies across runs.

### 2. Paid CAPTCHA Services (2captcha) — Use only after portal-specific validation
2captcha.com supports several relevant task types, but support ≠ production accuracy. Centralize this logic in `captcha_solver.py` and prefer open rosters/APIs first.
- **reCAPTCHA v2 (South Carolina): ✅ WORKS** — 2captcha workers solve it reliably. Module: `states/south_carolina.py`; verified Lacey Smith ACTIVE #124419.
- **reCAPTCHA v3 (Utah): ⚠️ INTERMITTENT** — Tokens can be obtained, but the portal may reject low-score tokens. Treat as low-confidence unless manually verified.
- **AWS WAF:** 2captcha API task is `AmazonTaskProxyless`; requires fresh `websiteKey`, `iv`, and `context` captured from the challenged page.
- **DataDome:** 2captcha API task is `DataDomeSliderTask`; requires `captchaUrl`, exact browser `userAgent`, and caller-owned/residential proxy settings. There is no proxyless DataDome task in the current docs. Alaska should stay semi-auto until this proxy-backed flow is validated.
- **BotDetect (Tennessee): ❌ NOT RELIABLE** — tested 0% accuracy with workers/free vision models. Do not spend solves by default.

Key: `TWOCAPTCHA_API_KEY` in .env. Setup script: `setup_2captcha.py`. Always test the specific CAPTCHA implementation before paying.

### 3. Public Records Requests
File formal public records requests with each state board for a list of all active NHA licensees. Most states provide CSV/Excel for free or $5-25. Takes 1-2 weeks but gives complete, reusable dataset.

### 3. Board Direct Contact
Call each state's NHA board, explain compliance verification needs. Many boards will mail/email current rosters or set up bulk verification.

### 4. CMS Provider Data (FREE, ALL STATES)
Free federal dataset at data.cms.gov of all Medicare-certified nursing homes. Covers all 15,000+ facilities nationwide. Updated monthly. Shows facility data (CCN, ownership, ratings, staffing) but may not include individual NHA names. Useful for cross-referencing facility certification status.

### 5. Paid Data Downloads
Some states offer paid CSV/Excel downloads:
- Utah: $0.01/record, minimum $5 (https://secure.utah.gov/datarequest/professionals/index.html)
- Nebraska: Free PDF roster (already implemented)

For ~32 Utah facilities: **~$0.32/month** after $5 initial setup.

### 6. AJAX Reverse-Engineering (TN LicensureReports, experimental)
Tennessee's LicensureReports portal (`internet.health.tn.gov/LicensureReports/`) uses jQuery AJAX with CSRF tokens. Possible approach:
1. Use Chrome DevTools Network tab to identify actual API endpoint
2. Extract CSRF token from page metadata or cookies
3. Make direct POST requests with valid token + session cookies

**Note:** This is the report generator, NOT the individual lookup. The individual lookup at `internet.health.tn.gov/Licensure/` uses BotDetect CAPTCHA. Semi-auto browser is faster and guaranteed.

### 7. Stealth Plugins Don't Bypass reCAPTCHA v3 / DataDome
playwright-stealth and similar anti-detection libraries hide automation signals (webdriver flag, navigator properties) but do NOT bypass reCAPTCHA v3 or DataDome. These score based on IP reputation + cookie history + behavioral patterns — a datacenter IP with no cookie history will still get flagged even with perfect browser fingerprint stealth. Residential proxies + session persistence are the only programmatic workaround without a solving service.

### 8. Persistent Context Session Storage
Saving cookies/storage state between runs does NOT bypass reCAPTCHA v3 or DataDome. The token is bound to the session/IP combination and expires quickly. We tested loading a saved Chrome profile into Playwright — the site still shows reCAPTCHA because reCAPTCHA v3 re-evaluates on every load.

Interactive script — no coding needed. Prompts for facility name, state, and administrator name. Adds the facility to the master Excel and runs verification automatically.

```bash
python add_facility.py
```

Flow:
1. Prompts for: Facility name, State (abbreviation or full name), Administrator name
2. Validates state is recognized
3. Adds a new row to the master Excel (ENSG Facilities Only 6.1.26.xlsx)
4. Runs the appropriate state verifier
5. Displays result with expiration alerts
6. Saves individual result to `results/on_demand_YYYY-MM-DD_HHMMSS.xlsx`

States shown as "working" vs "blocked" before the user enters the state, so they know what to expect.

## Roster Reconciliation (`reconcile.py`)

Compare any facility roster (xlsx/csv) against the master Excel. Detects mismatches and runs license verification on flagged rows.

```bash
python reconcile.py
```

Prompts for the comparison file path. Auto-detects columns by header name (Location, Facility, Director, Admin, State). Falls back to position-based detection (same layout as master).

### Issues detected:

| Type | Severity | Meaning |
|------|----------|---------|
| ADMIN MISSING IN MASTER | HIGH | Facility exists but no admin listed |
| ADMIN MISMATCH | HIGH | Same facility, different admin between files |
| ADMIN FACILITY MISMATCH | HIGH | Same admin at different facilities |
| ADMIN MISSING IN FILE | MEDIUM | Admin in master but blank in uploaded file |
| STATE MISMATCH | MEDIUM | Same facility, different state |
| NEW FACILITY | INFO | In uploaded file but not in master |
| MISSING FROM FILE | WARNING | In master but not in uploaded file |

For HIGH/MEDIUM issues, the script offers to run license verification automatically on the flagged admins. Saves a multi-sheet Excel report to `results/reconcile_YYYY-MM-DD_HHMMSS.xlsx`.

## Pitfalls

0. **Playwright sync API inside asyncio loop (Streamlit, Jupyter, etc.).** When a scraper using `sync_playwright` is called from within an asyncio event loop (e.g., Streamlit's "Add Facility" tab, Jupyter notebook), it crashes with "Playwright Sync API inside asyncio loop. Please use the Async API instead." ALL facilities for that state show identical "NEEDS MANUAL REVIEW" errors with the same error message in the note. **Symptom:** Every facility in a state has the exact same error text. **Fix:** Add asyncio detection at the top of the scraper:

```python
import asyncio

def _is_asyncio_running():
    try:
        loop = asyncio.get_running_loop()
        return loop is not None
    except RuntimeError:
        return False
```

Then in the search function, if asyncio is running, run sync Playwright in a thread:
```python
if _is_asyncio_running():
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_sync_search, ...)
        return future.result(timeout=60)
```

The thread runs in a fresh context with no event loop, so sync_playwright works normally. (Fixed 2026-06-24 in texas.py — all 110 TX facilities were affected.)

0b. **CMS state name matching — full names vs abbreviations.** Excel often stores state as full names ("Arizona", "California") but CMS data uses abbreviations ("AZ", "CA"). The `match_facility()` function must try BOTH. When state input is full name, also try the abbreviation from `STATE_MAP`. When abbreviated, also try full name. Without this, 0% of CMS matches will succeed. (Fixed 2026-06-24 in `cms_data.py`.)
0b. **Wisconsin "Granted" date ≠ Expiration date.** The WI DSPS portal shows a "Granted" date in the results, NOT an expiration date. The original scraper incorrectly used this as the expiration, showing licenses as "expired from 2019" when they were actually active. WI does not expose expiration in the search results. Set `expiration = ""` and `days_until_expiry = None` for WI. (Fixed 2026-06-24.)
0c. **Texas `_try_texas_search` needs explicit `page=None`.** The helper function must accept `page` as a parameter. Call with `page=None` from `verify_texas()` so it can create its own browser when no shared page is provided. Without this, `UnboundLocalError` crashes all TX verifications. (Fixed 2026-06-24.)
1. **Shadow DOM select piercing.** Playwright's `page.locator("select").all()` pierces shadow DOM and returns native `<select>` elements inside Lightning/LWC components. This is the most reliable way to interact with Salesforce Lightning forms. Do NOT try to click `lightning-combobox` elements directly — they fail with "Could not compute box model" errors.
2. **LWC race conditions.** Lightning Web Components re-render the DOM after selection changes. Always re-query `selects = page.locator("select").all()` after selecting Program Type, and add `page.wait_for_timeout(500)` between selections.
3. **LWC Submit button.** Standard `page.locator('button:has-text("Submit")').click()` does NOT trigger form submission on LWC forms. Use `page.get_by_text("Submit", exact=True).first.click(force=True)` which pierces shadow DOM and dispatches the click correctly.
4. **Retry on intermittent failures.** LWC forms sometimes fail to render fully before interaction. Add retry logic (2-3 attempts with 1s sleep) for any scraper that uses Lightning components.
5. **CDPH expiration requires extra click.** Results page shows Active/Inactive only; no date.
6. **Salesforce Lightning inputs** — standard Playwright `.fill()` does NOT work on `<lightning-input>`. Use `.click()` + `keyboard.type()`. However, for Texas TULIP, the native `<select>` and `<input type="text">` elements ARE accessible via standard locators.
7. **Excel file locking.** Use `data_only=True`, handle lock gracefully.
8. **Headless detection.** Add realistic user agent + random delays.
9. **Rate limiting.** Add 0.5-1s delay between requests.
10. **Name mismatches.** Normalize to uppercase, use rapidfuzz token_sort_ratio. Handle "First Last", "Last, First", and "First Last / Second Name" formats.
11. **Multiple admins per facility.** Split on `/` and check each separately.
12. **Config key drift.** If `config.json` uses `excel_sheet`, code must reference `config["excel_sheet"]`, not `config["sheet_name"]`. Same for `report_folder` vs `report_output`.
13. **Expiration date formats vary.** CA uses MM/DD/YYYY; TX uses YYYY-MM-DD; OR uses M/D/YYYY; AK uses 10-Feb-2028. Parse with a format fallback loop.
14. **Generic form selectors fail on custom UIs.** Do not build a "one form handler fits all" abstraction. Each state scraper must handle its own specific form elements (ASP.NET WebForms, Salesforce Lightning, React components, etc.). Test each scraper individually with a real admin name before integrating.
15. **ASP.NET WebForms sites** use `ctl00$ContentPlaceHolder1$btnSearch` style button names. Inspect the actual form before hardcoding selectors.
16. **AZ Care Check searches facilities, NOT individuals.** The site at `azcarecheck.azdhs.gov` is for facility lookup, not NHA verification. The correct Arizona NHA source is the NCIA Board at `aznciab.portalus.thentiacloud.net`.
17. **CAPTCHA / reCAPTCHA blocks automation but check for alternatives first.** Detect early (first request returns CAPTCHA page or reCAPTCHA badge appears in DOM). Before marking SEMI-AUTOMATED, check for: free PDF rosters (NE has one), paid data downloads (UT offers $0.01/record), public records requests, or CMS Provider Data.
18. **Language selection overlays.** Colorado DORA loads a "Select Language" dropdown before the search form is usable. Detect by checking for `select` with text "Select Language" or similar; select the first option or skip if no English option. Language selection prevents search form interaction.
19. **Each state has its own NHA verification URL.** Do NOT use the generic DORA/DOPL/KSBN main pages. Search for the specific NHA board URL (e.g., NCIA Board for Arizona, OHLO for Oregon, DSPS for Wisconsin, prolicenseverify.ks.gov for Kansas, edopl.idaho.gov for Idaho).
20. **Excel column mapping.** The ENSG Excel has: Col 0=LOCATION, Col 5=EXECUTIVE DIRECTOR, Col 8=STATE. Use `row[8]` for state and `row[5]` for admin name. The file path is `C:/Users/kevin/Desktop/ENSG Facilities Only 6.1.26.xlsx`.
21. ** Wisconsin DSPS result format uses `\r\n\t\r\n` separators.** Each field is on its own line with tabs between. Standard `split('\t')` won't work — use regex pattern matching instead.
22. ** Oregon OHLO results use standard tab separation** but the header row must be skipped (check for "Licensee Name" in first column). Expiration format is `M/D/YYYY` (no leading zeros).
23. **South Carolina reCAPTCHA hides the Find button.** The SC LLR LTC form at `LTC.aspx?div=35` has a Find button with `visibility: hidden` until reCAPTCHA is solved. The reCAPTCHA element is present in the DOM (`g-recaptcha-response` textarea). No stealth plugin bypasses this — it's server-side scoring.
24. **playwright-stealth does NOT bypass reCAPTCHA v3.** Stealth plugins hide automation signals but reCAPTCHA v3 scores on IP reputation + cookie history + behavior. Only residential proxies + session persistence work programmatically.
25. **Sites that load after `--ignore-certificate-errors` may still have no usable functionality.** Nevada's site (`beltca.nevada.gov`) loads after SSL error is ignored, but the homepage contains only links — no public license lookup form exists.
26. **Dynamic ID inputs require label-based selection.** Tennessee (`verify.tn.gov`) uses random IDs for inputs (`-33701226759`, `177334431563`). Match inputs by their associated `<label for="...">` text, not by ID.
27. **Colorado old URL (dora.colorado.gov) doesn't return NHA data.** The real NHA site is `dpo.colorado.gov/COHPC` which uses CloudFront and blocks automated requests. Mark as SEMI-AUTOMATED.
28. **Idaho DOPL edopl portal** uses `#Dd-11` for the Name field. Custom React comboboxes for Board/License Type are hard to automate, but Name-only search works without board selection.
29. **Kansas prolicenseverify has reCAPTCHA on page load.** The Profession dropdown has "Adult Care Home Administrator" and the form accepts firstName/lastName, but reCAPTCHA blocks submission. KSBN is for nursing only. Mark as SEMI-AUTOMATED.
30. **Iowa: use the FileCloud `IBPLRoster.xlsx` public roster, not Amanda Angular.** The Amanda Portal has complex Angular mat-selects, but the public FileCloud folder `https://filecloud.idph.state.ia.us/url/PLRosters` downloads `IBPLRoster.xlsx` with NHA rows. This produced 9/9 ENSG Iowa PASS. Cache extracted NHA rows to JSON because scanning the full workbook repeatedly is slow.
31. **Alaska CBPL Professional Search uses DataDome CAPTCHA.** The URL `commerce.alaska.gov/cbp/main/Search/Professional` has DataDome anti-bot protection (returns 403 with `captcha-delivery.com`). **Semi-auto browser is the only reliable workaround** — user solves DataDome challenge once per session, then batch processes all facilities. The form has a single "Owner Last or Entity Name" field (`input[name='OwnerLastName']` or `OwnerEntityName`).
33. **DataDome and reCAPTCHA v3 cannot be bypassed programmatically without residential proxies.** Stealth plugins (playwright-stealth, undetected-chromedriver) hide automation signals but do NOT bypass these protections. They score based on IP reputation + cookie history + behavioral patterns + TLS fingerprint. Semi-auto browser (real Chrome, user solves CAPTCHA once) is the only reliable free workaround.
34. **Empty admin names in Excel should be handled gracefully.** `verify_all.py` skips facilities with no admin and logs them in the summary.
35. **Check open data portals before marking a state as BLOCKED.** Many states publish license data via Socrata/CKAN open data APIs (e.g., Colorado CIM at `data.colorado.gov`). Search for `site:data.colorado.gov <state> license` or `<state> open data professional license`. These APIs are free, no CAPTCHA, and often include expiration dates. Colorado's CIM API (`7s5z-vewr.json`) made the scraper fully functional without Playwright.
36. **Alaska CBPL form field is `OwnerEntityName` (single field).** The old scraper used `OwnerLastName`/`OwnerFirstName` which don't exist. The form has a single "Owner Last or Entity Name" field.
37. **Nebraska LTC licenses expire March 31st each year.** This is stated in the PDF header. Calculate the expiration date rather than trying to scrape it — it's the same for all licensees.
38. **Socrata `in()` clause doesn't work.** When querying Socrata APIs (Colorado CIM, Washington Open Data), the `in()` function fails with 400 errors. Use `OR` instead: `licensetype='NHA' OR licensetype='MSNHA'`.
39. **ASP.NET two-column label/value layouts.** Some ASP.NET portals (Kansas KSDADS) display labels and values in separate sections with a gap. Labels appear on lines 7-16, values on lines 19-28. They are NOT adjacent. Parse by finding the label section end, then searching for values (dates, status words) after that point.
40. **Kansas KSDADS license type is "Adult Care Home Administrator"** — not "Nursing Home Administrator". Filter results by this type and exclude "Temporary" variants.
41. **Washington Socrata credential type is "Nursing Home Administrator License"** — search with `upper(credentialtype) like '%NURSING HOME%'` for partial match.
42. **Tennessee verify.tn.gov redirects to Commerce site (no NHA data).** `verify.tn.gov` redirects to `search.cloud.commerce.tn.gov` — the Commerce & Insurance portal that covers cosmetology, real estate, contractors. It does NOT have NHA license data. The correct NHA portal is `internet.health.tn.gov/Licensure/` (BotDetect CAPTCHA). The LicensureReports portal at `internet.health.tn.gov/LicensureReports/` is a report generator with jQuery AJAX + CSRF tokens. ~11 TN facilities.
43. **Timestamped output filenames prevent PermissionError.** If the verification Excel is open in Excel when the next run finishes, `wb.save()` fails with `PermissionError: [Errno 13]`. Use `verification_YYYY-MM-DD_HHMMSS.xlsx` instead of `verification_YYYY-MM-DD.xlsx`.
44. **openpyxl chart imports must be inside the function.** `from openpyxl.chart import BarChart, PieChart, Reference` should be inside `write_results_excel()` to avoid import errors if openpyxl version doesn't support charts. The `DataPoint` import from `openpyxl.chart.series` is also needed for pie chart coloring.
45. **Texas `_try_texas_search` requires explicit `page=None` parameter.** The helper function must accept `page` as a parameter — do NOT rely on closure. Call with `page=None` from `verify_texas()` so it can create its own browser when no shared page is provided.
46. **User preference: auto-open reports after generation.** Use `os.startfile(str(path))` (Windows) to open the Excel file immediately after saving. The user expects the report to appear on screen, not just be saved to disk.
47. **`fails` is already an int, not a list.** In `write_results_excel`, `fails = sum(1 for r in results if r["overall"] == "FAIL")` returns an int. Do NOT call `len(fails)` — it's `TypeError: object of type 'int' has no len()`. Use `fails` directly in f-strings.
48. **Semi-auto must navigate back to search page before each search.** After clicking submit, the page changes to results — the search form no longer exists. The next `page.fill()` times out waiting for `#fullName` (or whatever the field selector is). Fix: before each search (except the first), `page.goto(config["url"])` back to the search page and wait for `networkidle`. Without this, every search after the first one times out with `Timeout 30000ms exceeded. waiting for locator("#fullName")`. (Fixed 2026-06-24 in semi_auto.py.)
49. **Utah reCAPTCHA may not trigger on first searches.** The Utah portal has reCAPTCHA but single searches often work without solving it. The CAPTCHA challenge may only appear after multiple rapid searches. If the CAPTCHA does appear, the user must solve it manually in the Chrome window before pressing ENTER in the terminal.
50. **BotDetect audio CAPTCHAs may be disabled.** Tennessee's BotDetect CAPTCHA has an audio endpoint (`get=sound`) but it returns 400 Bad Request — the site administrator has disabled audio CAPTCHAs. Before relying on audio CAPTCHA + Whisper transcription, test the audio endpoint first. If it returns 400, audio solving is not an option.
51. **Whisper can transcribe BotDetect audio CAPTCHAs (when enabled).** faster-whisper `base` model transcribes BotDetect audio that spells out each character ("T-A-R-W-J-3"). Clean with `re.sub(r'[^a-zA-Z0-9]', '', raw_text)`. Works on sites that haven't disabled audio CAPTCHA.
52. **Tennessee has THREE portals — only one has NHA data.** `verify.tn.gov` → Commerce site (no NHA). `internet.health.tn.gov/Licensure/` → Health portal (has NHA, BotDetect CAPTCHA). `internet.health.tn.gov/LicensureReports/` → Report generator (bulk export, no individual CAPTCHA). semi_auto.py currently points to the wrong one.
53. **Clarify ambiguous terms before dispatching research.** When user says "MoA" or "MoE", they may be referring to a feature in the tool (Hermes /model menu), not a research paper. Don't dispatch background research tasks without confirming what the user means. Ask first — "Do you mean the Hermes feature or the research paper?" — instead of assuming and wasting tokens on irrelevant research.
54. **Utah reCAPTCHA v3: form.submit() does NOT work.** The Utah DOPL portal's reCAPTCHA v3 form ignores `form.submit()` and `requestSubmit()`. The only reliable submission method is clicking the actual submit button element (`input[type='submit']`). After clicking, use `pg.wait_for_url("**/search.html**")` instead of `expect_navigation()` which fails intermittently. The form action is `/llv/search/index.html` but results load at `/llv/search/search.html`.
55. **Nevada SSL cert mismatch — use HTTP, not HTTPS.** `beltca.nevada.gov` has an SSL certificate for the wrong domain. The site redirects to `http://beltca.nv.gov` (HTTP). Use HTTP for all requests. The PDF roster URL has spaces that must be URL-encoded (`%20`).
56. **PDF roster parsing with pdftotext -layout preserves columns.** When parsing PDF rosters (Nebraska, Nevada), use `pdftotext -layout` instead of plain `pdftotext`. The `-layout` flag preserves column alignment, making it possible to parse tabular data. Plain `pdftotext` merges columns and destroys the structure.
57. **Tennessee BotDetect CAPTCHA field ID is `ctl00_PageContent_CaptchaCodeTextBox`.** The hidden BotDetect field `c_default_ctl00_pagecontent_captchacode` is NOT the input field — it's a session token. The actual text input where users type the CAPTCHA answer is `ctl00_PageContent_CaptchaCodeTextBox`. Using the wrong ID causes "Please complete Captcha" error even with correct CAPTCHA text.
58. **OpenRouter free vision models are simpler to set up than Gemini.** OpenRouter key (https://openrouter.ai/keys) works immediately with no project setup. Gemini requires Google Cloud project creation + API enablement if the key hits 429. Use `google/gemma-4-26b-a4b-it:free` model for vision tasks.
59. **Free vision models (~26B params) cannot reliably read distorted BotDetect CAPTCHAs.** Tested with Gemma 4 26B on Tennessee BotDetect — reads characters but gets ~70% wrong on distorted text. BotDetect specifically designs CAPTCHAs to resist ML vision. For production use, stick with semi_auto.py or paid CAPTCHA service.

60. **Semi-auto submit button may be hidden after CAPTCHA solve.** Tennessee's BotDetect CAPTCHA page has the submit button (`#ctl00_PageContent_btnSubmit`) visually hidden (CSS `display:none` or `visibility:hidden`) until the CAPTCHA is validated. Playwright's `page.click()` times out waiting for visibility. Fix: use JavaScript click which works on hidden elements:
```python
selector = config["selector_submit"]
try:
    page.evaluate("document.querySelector(arguments[0]).click()", selector)
except:
    page.click(selector, timeout=5000)
```
This pattern applies to any state where the submit button is hidden behind CAPTCHA validation.

61. **Edge browser support in semi_auto.py.** Added `channel="msedge"` to `launch_persistent_context()`. This uses Microsoft Edge instead of Chromium. Edge is often already installed on Windows and may have better CAPTCHA reputation than headless Chromium. To revert to Chromium, remove the `channel` parameter.

62. **Tennessee URL fix applied to semi_auto.py.** Changed from `https://verify.tn.gov/` (redirects to Commerce site, no NHA) to `https://internet.health.tn.gov/Licensure/` (health portal with BotDetect CAPTCHA). Selectors updated to match ASP.NET WebForms IDs: `#ctl00_PageContent_txtLastName`, `#ctl00_PageContent_txtFirstName`, `#ctl00_PageContent_btnSubmit`.

63. **2captcha does NOT work on BotDetect CAPTCHAs.** Tested 2captcha.com ($0.003/solve) on Tennessee BotDetect — 0% accuracy. Human CAPTCHA workers cannot read the distorted BotDetect images. 2captcha DOES work for reCAPTCHA v2/v3 (Utah, South Carolina) but NOT for BotDetect (Tennessee) or DataDome (Alaska). Always test the specific CAPTCHA type before paying for a solving service.

64. **Free vision models are 0% accurate on BotDetect CAPTCHAs.** Tested google/gemma-4-26b-a4b-it:free (OpenRouter) on 10 different Tennessee BotDetect CAPTCHAs. All 10 were wrong. The model reads characters but gets them wrong on distorted text. BotDetect specifically designs CAPTCHAs to resist ML vision. Semi_auto.py is the only reliable free approach.

65. **After editing verification code, create ad-hoc verification evidence with a temp script.** If no canonical pytest/lint/build exists, write a focused temporary script under `C:/Users/kevin/AppData/Local/Temp` using `tempfile.mkstemp(prefix="hermes-verify-", suffix=".py")`, run it against the changed behavior, and delete it in `finally`. Summarize as **ad-hoc verification**, not full suite green. For this project, include `py_compile` of touched modules, real-admin checks, and at least one integrated `python verify_all.py <STATE>` report check when workflow code changed.

66. **Single-state `verify_all.py` runs are the fastest integration check.** `python verify_all.py IOWA` should load only the target state's Excel rows, generate a timestamped workbook under `results/`, and the verifier can open the Detailed Results tab to assert expected row counts and PASS/FAIL values. SMTP AUTH failures are email-delivery blockers, not verification failures, if report generation succeeded.

## CMS Staffing/Penalty Data Integration (for Executive Defense)

When the accusation is "unlicensed administrators + low staffing", the Excel must prove both compliance AND actual staffing levels. The `cms_data.py` module pulls from CMS Provider Data (free, no auth):

**Data sources:**
- Provider Info: `data.cms.gov/provider-data/dataset/4pq5-n9py` — 14,651 facilities, includes star ratings, staffing hours, turnover, penalties
- Penalties: `data.cms.gov/provider-data/dataset/g6vv-u9sr` — 16,572 penalty records with dates, types, amounts

**Columns added to verification Excel:**

| Column | Source | What it proves |
|--------|--------|----------------|
| CMS Overall Rating | Provider Info | 1-5 star overall quality |
| CMS Staffing Rating | Provider Info | 1-5 star staffing-specific |
| CMS Health Rating | Provider Info | 1-5 star inspection score |
| RN Hours/Resident/Day | Provider Info | Actual RN staffing level |
| Total Nursing Hours/Resident/Day | Provider Info | Total nurse staffing |
| Staff/RN/Admin Turnover | Provider Info | Staffing stability |
| Total Penalties | Provider Info | # of CMS penalties |
| Total Fines $ | Provider Info | Dollar amount of fines |
| Payment Denials | Provider Info | CMS payment denials |
| Complaint Deficiencies | Provider Info | # deficiencies from complaints |
| Abuse Flag | Provider Info | CMS abuse investigation flag |
| Penalty Details | Penalties | Specific penalties last 3 years |

**Matching:** Fuzzy match by facility name + state. Normalizes names (removes LLC/Inc, punctuation, extra spaces). Try exact match first, then substring containment.

**Caching:** Downloads CSV files to `cache/` directory, refreshes weekly. One `init_cms_cache()` call at startup loads all data into memory for fast lookups.

**Key pattern:** Match facility by name + state against CMS data, not by CCN. CMS uses different facility names than the Excel sometimes. Fuzzy matching with `setintersection` on normalized words works well.

**Implementation:** `cms_data.py` module with:
- `init_cms_cache()` — call once at startup, downloads CSVs to `cache/`, refreshes weekly
- `get_facility_cms(facility_name, state)` — returns dict with all CMS fields
- `match_facility(name, state, data)` — normalizes names (strips LLC/Inc/punctuation), tries exact match then substring containment with word overlap scoring. MUST handle both full state names ("Arizona") and abbreviations ("AZ") — see pitfall #0.
- Integrated into `verify_all.py` via `**get_facility_cms()` spread into each result row

## Gemini API Key Setup for Vision Model (FREE)

Google Gemini 2.0 Flash is the best free vision model for CAPTCHA reading.

**Setup steps:**
1. Go to https://aistudio.google.com/apikey
2. Sign in with a personal Gmail account (NOT a Workspace/school account)
3. Click "Create API Key"
4. If 429 error on first use: create a NEW Google Cloud project first
   - Go to https://console.cloud.google.com/
   - Create new project → Enable Generative Language API → Create API key
5. Key format: starts with `AIza...`
6. Save to Hermes .env: `GEMINI_API_KEY=your_key_here`

**Free tier limits:** 15 requests/minute, 1500 requests/day
**Workspace accounts:** Share quota across all users — may hit 429 immediately

## Vision Model + CDP Approach for Tennessee BotDetect (EXPERIMENTAL — LOW SUCCESS RATE)

Tennessee's BotDetect CAPTCHA is image-based (250x40 JPEG, ~3.5KB). Audio
endpoint returns 400 (disabled). OCR gives garbage. The remaining option is
a vision-capable LLM to read the CAPTCHA screenshot.

**Detailed guide:** `references/gemini-vision-captcha.md`

### How it works
1. Use Playwright CDP to capture the CAPTCHA image element
2. Send screenshot to a vision-capable LLM
3. LLM reads the CAPTCHA text
4. Type the CAPTCHA answer and submit

### CAPTCHA input field (CRITICAL — wrong ID was used initially)
The correct field ID is `ctl00_PageContent_CaptchaCodeTextBox` (NOT `c_default_ctl00_pagecontent_captchacode` which is a hidden BotDetect field).

```python
page.fill("#ctl00_PageContent_CaptchaCodeTextBox", captcha_text)
```

### CDP capture pattern
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(...)
    page = context.new_page()
    page.goto("https://internet.health.tn.gov/Licensure/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # Screenshot the CAPTCHA image
    captcha_img = page.query_selector("img.BDC_CaptchaImage")
    if captcha_img:
        captcha_img.screenshot(path="captcha.png")
        # Send to vision API for transcription
```

### Free vision model options (tested)

**OpenRouter free models (RECOMMENDED — simpler setup):**
- `google/gemma-4-26b-a4b-it:free` — best free vision model tested
- Setup: get key at https://openrouter.ai/keys (free, no project setup)
- Save to .env: `OPENROUTER_API_KEY=sk-or-...`

**Google Gemini (alternative — more setup required):**
- `gemini-2.0-flash` — excellent vision, 15 req/min free
- Setup: get key at https://aistudio.google.com/apikey
- Pitfall: Workspace/school accounts hit 429 immediately — use personal Gmail
- If 429: create new Google Cloud project → enable Generative Language API → create key

**Ollama + LLaVA:** Local, unlimited, but slower (not tested for CAPTCHAs)

### tested results — free models struggle with BotDetect
Free vision models (Gemma 4 26B) read CAPTCHAs but get characters wrong ~70% of the time. BotDetect specifically designs distorted text to resist ML vision. The model might read "PTAA3F" when the actual CAPTCHA is "PT4A3F" — one character off fails the whole submission.

**Recommendation:** For reliable Tennessee coverage, use semi_auto.py
(user solves CAPTCHA once, then auto-searches all 11 admins). The vision
approach is experimental and not reliable enough for production use.

**Actual test results (2026-06-27):** Tested Gemma 4 26B free model on 10 different Tennessee BotDetect CAPTCHAs. Result: 0/10 correct (0% accuracy). The model reads characters but gets them wrong on distorted text. BotDetect specifically designs CAPTCHAs to resist ML vision. Semi_auto.py is the only reliable free approach.

## OVERLAPPING SKILLS

This skill (`license-verification`) supersedes `nha-license-verification` (regulatory-automation category). The older skill covers the same NHA workflow but is less comprehensive — it lacks CMS data integration, charts, add_facility.py, reconcile.py, and the detailed state-specific patterns. If the curator consolidates, absorb `nha-license-verification` into this skill and delete the old one.

## Streamlit Frontend (BUILT)

**File:** `app.py` — single Python file, runs at `http://localhost:8501`

```bash
cd D:/license-verification
streamlit run app.py
```

Preferred user entry point: desktop shortcut `ENSG License Verification - Web GUI.lnk` -> `launch_web_gui.cmd`. Keep this separate from the click-and-forget report shortcut.

**6 pages (tabs in main content — no sidebar):**
1. **📊 Run Verification** — runs `build_final_max_coverage.py` to produce the comprehensive final workbook; do not use raw `verify_all.py` here because Kevin wants all administrators preserved.
2. **➕ Add Facility** — form fields for facility name, state (dropdown), admin name; verifies license and adds to master Excel
3. **🔄 Reconcile Rosters** — file upload (xlsx/csv), compares against master, shows flagged issues by severity
4. **📁 View Reports** — lists all reports in `results/`, open/download buttons
5. **📈 Dashboard** — visual metrics/charts from the latest `FINAL_ENSG_max_admin_coverage_*.xlsx` workbook
6. **⚙️ Settings** — visually edit email recipients, refresh states, and project-local 2captcha key

**Key details:**
- Uses `os.startfile()` to auto-open reports after generation
- State dropdown includes all 17 states with working/blocked indicators
- Reconcile page shows issues grouped by type with severity icons (🔴 HIGH, 🟡 MEDIUM, 🟠 WARNING, 🔵 INFO)
- Reports page shows file size, modification date, and download buttons
- Install: `pip install streamlit` (one dependency)

## Data Request / Download Intake Automation

Reference: `references/utah-public-crossref.md` captures the Utah targeted-public-lookup + CMS/NPI/web cross-reference workflow, confidence rules, and pitfalls. Use it when Kevin wants maximal public-source answers for only the provided ENSG facilities/admins, with out-of-normal-process notes.

For paid/public-record roster workarounds (especially Utah, Tennessee, Alaska), use project script `D:/license-verification/data_request_automation.py`.

Capabilities:
- `--create-email-drafts` writes `.eml` request drafts under `cache/data_requests/email_drafts/` without sending.
- `--scan-downloads --hours 72` imports recent roster-like files from `C:/Users/kevin/Downloads` into `cache/data_requests/<STATE>/received/`.
- `--import-file <path> --state UTAH --build-supplements` imports a specific roster and, for Utah CSV/XLSX, builds `results/utah_roster_refresh_*.xlsx`.
- `--build-final` rebuilds the final workbook while merging `utah_roster_refresh_*.xlsx` and not forcing Utah to manual review.
- `--poll-email` can download roster attachments from IMAP when `IMAP_HOST`, `IMAP_USER`, and `IMAP_PASSWORD` are configured; do not ask Kevin to paste mailbox passwords in chat.

User-facing helper: `D:/license-verification/import_data_request_downloads.cmd` scans Downloads, builds supplements, builds final report, and opens the workbook.

Email/account helper: `D:/license-verification/email_settings.py` manages non-secret mail settings.
- Current Gmail profile: `python email_settings.py --imap-profile gmail --smtp-profile gmail --report-to kevinmoon7@gmail.com,lee85lisa@gmail.com --show`
- ENSG Outlook profile: `python email_settings.py --imap-profile ensg --smtp-profile ensg --report-to kevinmoon7@gmail.com,lee85lisa@gmail.com --show`
- Desktop helpers: `use_gmail_email_settings.cmd` and `use_ensg_email_settings.cmd`.
- Passwords are not printed or requested in chat. For Gmail, use a Google App Password for `IMAP_PASSWORD`/`SMTP_PASSWORD`; normal Google password usually will not work.

Utah DOPL roster ordering: see `references/utah-dopl-data-request.md` for the live-site handoff workflow. Key points: use the data request page, select only Health Facility Administrator, choose without address/phone/email unless directed otherwise, fill Kevin's name/Gmail, leave phone/payment for Kevin, then import the emailed/downloaded roster with `data_request_automation.py`.

Important caveats:

Important caveats:
- Do NOT automate payment/CAPTCHA checkout; Kevin should complete those in the browser.
- Never merge fake/test roster files; delete any ad-hoc test supplemental workbook before final report generation.
- Utah stays manually gated in normal `build_final_max_coverage.py`; only the data-request automation script overrides manual states for a roster-backed final build.

## Utah targeted public-source pass

When Kevin says he only needs Utah results for the facilities he provided, do not default to a full Utah roster purchase. First run a targeted public DOPL lookup pass against only the Utah facility/admin names from the ENSG workbook, split multi-admin cells, and flag anything outside the normal process. `NOT_FOUND` means manual alias/legal-name review, not final noncompliance. If buying Utah data is still needed, prefer the narrow paid filter: Health Facility Administrator only + Active only + without address/phone/email; this was observed as much cheaper than broad HFA/all-status or full professional downloads.

See `references/utah-targeted-public-lookup.md` for exact Utah filter values, cost observations, reporting language, and the Playwright timeout pitfall.

## Utah targeted-public-source fallback

When Kevin says he only needs his provided facilities/admins, do **not** jump straight to a broad Utah roster. First run a targeted public-source pass over the Utah rows in the ENSG workbook, split multi-admin cells, and mark anything out-of-normal-process in the workbook. DOPL `ACTIVE` is strong public license evidence; CMS/NPI/web sources are identity/context clues only; `NOT_FOUND` is manual/legal-name/alias review, not final noncompliance. Details and source hierarchy: `references/utah-public-cross-reference.md`.

## References

- `references/no-pay-ut-tn-public-crossref.md` — no-pay Utah/Tennessee gap workflow: use CMS Provider Data + CMS ownership/managerial-control data to separate official DOPL matches, public facility/person linkage, likely non-HFA license-type rows, and unresolved cases before deciding on paid Utah roster or TN manual lookup.

Open only what you need:

- `references/utah-data-request.md` — Utah DOPL data request roster cost-control notes: active HFA-only filtering, form values, pricing observations, and when to prefer targeted lookup over paid bulk roster.

- `references/2captcha-integration.md` — 2captcha API setup, usage patterns, cost estimates, what works/doesn't work (reCAPTCHA yes, BotDetect no)
- `references/cms-data-sources.md` — CMS Provider Data datasets, CSV download URLs, key columns, matching strategy, caching (concise quick-reference)
- `references/executive-defense-data.md` — CMS Provider Data datasets, state open data APIs, recommended columns for executive defense against staffing/licensing accusations
- `references/executive-data-sources.md` — CMS Provider Data datasets, state open data APIs, and recommended columns for executive dashboards
- `references/excel-charts-pattern.md` — openpyxl chart patterns (pie, bar, horizontal bar) with code snippets
- `references/final-report-max-coverage.md` — building the final all-admin Excel workbook by merging a complete base report with refreshed high-confidence state runs
- `references/desktop-shortcuts-and-final-report-gui.md` — click-and-forget desktop shortcut, separate Streamlit GUI shortcut, final max-coverage builder, email/config conventions, and ad-hoc verification checklist

- `references/cdph-nha-scraper.md` — California scraper details (detail page pattern, JS extraction, name matching)
- `references/texas-tulip-scraper.md` — Texas scraper details
- `references/project-scaffold.md` — Project structure and setup
- `references/verification-log-2026-06-22.md` — Session test results per state
- `references/verification-log-2026-06-23.md` — 2026-06-23 full state run with real Excel names, semi-auto expansion, master verifier
- `references/captcha-blocks-and-lightning-fixes.md` — CAPTCHA/reCAPTCHA blockers, language overlays, Lightning combobox fixes, Arizona filter limitation
- `references/semi-automated-captcha-bypass.md` — Semi-automated browser approach for CAPTCHA-blocked states, state configs, usage guide
- `references/semi_auto_selectors.md` — Verified selectors for AK, CO, IA, KS, SC, TN, UT, WA
- `references/expiration-days-calculation.md` — Universal days_until_expiry calculation pattern
- `references/iowa-roster-and-captcha-architecture.md` — Iowa FileCloud roster pattern, CAPTCHA-solver architecture rules, DataDome/AWS WAF task requirements, and temp-script ad-hoc verification pattern
- `references/nevada-utah-techniques.md` — Nevada PDF roster parsing, Utah Playwright + reCAPTCHA v3, Tennessee BotDetect analysis (2026-06-27)
- `references/utah-dopl-workarounds.md` — Utah-specific workaround hierarchy: official paid data download, semi-auto Edge, why 2captcha/headless v3 is not click-and-forget
- `references/data-request-automation.md` — Data-request/download intake automation: email drafts, Downloads watcher/import, Utah roster supplemental merge, and ad-hoc verification pattern

## Scripts

- `scripts/verify_one_state.py` — Run a single state scraper against one admin name for fast validation.
- `scripts/semi_auto.py` — Semi-automated browser for CAPTCHA-blocked states (AK, CO, IA, KS, SC, TN, UT, WA). Opens a real Chrome window, waits for the user to solve ONE CAPTCHA, then auto-searches all admin names for that state. Saves results to `results/`.
- `scripts/verify_all.py` — Master verifier: reads Excel, runs all state scrapers, writes PASS/FAIL/NEEDS MANUAL REVIEW Excel with expiration alerts and summary.
- `scripts/run_nightly.py` — Nightly wrapper around `verify_all.py` with timestamps and error handling.
