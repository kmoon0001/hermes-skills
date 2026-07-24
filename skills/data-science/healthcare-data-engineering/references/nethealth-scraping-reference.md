# NetHealth Rehab Optima — Desktop App & ClickOnce Reference

> Investigated 2025-07-03. Updated 2025-07-03 with ClickOnce desktop deployment discovery.
> **NetHealth Rehab Optima is a ClickOnce desktop application, NOT a traditional web app.** The page at `login.therapy.nethealth.com` is a launcher, not a forms-auth portal.

## Platform Identity

| Property | Value |
|----------|-------|
| Product | Optima for Skilled Nursing / Care Operations Manager |
| Vendor | Net Health Systems, Inc. |
| Launcher URL | `https://login.therapy.nethealth.com/` |
| ClickOnce Deploy Server | `client.therapy.nethealth.com` |
| ClickOnce Manifest | `GiftRAP.Client.application` |
| Desktop App Name | **Care Operations Manager** |
| Tech Stack | .NET ClickOnce (WPF/WinForms desktop), deployed via `dfsvc.exe` |
| App Size | ~333 MB |
| Support | `optima-support@nethealth.com` |

## How to Launch — Organization Code, Not Username/Password

The login page is an organization-code-based launcher, not a traditional login:

1. Navigate to `https://login.therapy.nethealth.com/`
2. Page shows: **"Please enter your organization code and click RUN"**
3. Single field: **"OrgCode"** + **"RUN"** button
4. Enter org code (e.g., **"ENSG"**) → click RUN
5. Browser prompts: "Do you want to open GiftRAP.Client.application?" from `ensg.therapy.nethealth.com`
6. Click Open → **ClickOnce security warning**: "Do you want to run this application?"
   - Name: "Care Operations Manager"
   - From: `client.therapy.nethealth.com`
   - Publisher: "Net Health Systems, Inc."
7. Click Run → Windows `dfsvc.exe` (ClickOnce Deployment Service) downloads 333 MB
8. App auto-installs and launches after download

## ClickOnce Deployment Details

| Property | Value |
|----------|-------|
| Org-specific subdomain | `ensg.therapy.nethealth.com` (varies by organization) |
| Deployment Service | `dfsvc.exe` |
| Manifest File | `GiftRAP.Client.application` |
| Install Location | `%LOCALAPPDATA%\Apps\2.0\` (standard ClickOnce cache) |
| Trust Level | Medium (publisher-signed, user approval required) |

## Automation Approaches (Post-Discovery)

### Option A: cua-driver Desktop Automation (Best)
Since this is a desktop app, use cua-driver to drive it directly:
- Capture the running app window after launch
- Navigate menus: Reports → SLP Evaluation Export → CSV/Excel
- Patient lookup → Therapy tab → individual evaluations
- Much more reliable than web scraping

### Option B: Re-launch via Browser + cua-driver
1. Open Edge → `login.therapy.nethealth.com`
2. Type org code → click RUN
3. Handle download prompt + security warning via cua-driver clicks
4. Wait for `dfsvc.exe` download → capture launched desktop app

### Option C: Local Database (Check First)
ClickOnce cache may contain a local database:
- Check: `%LOCALAPPDATA%\Apps\2.0\` for `.mdf`, `.sqlite`, `.db` files
- `dir /s %LOCALAPPDATA%\Apps\2.0\*.mdf *.sqlite *.db`
- If found, query directly — bypasses all UI automation

## Reports Console — Direct Access from Login Screen

**CRITICAL DISCOVERY (2025-07-03):** The login screen has a **\"&Reports Console\"** button that opens the full reports directory WITHOUT selecting a facility or completing login. This means report exports can be automated without navigating the full application.

### How to Access
1. At the \"Select Operating Unit\" screen (after org code RUN):
   - User field: `eg.kmoon` (auto-populated)
   - Facility list: ~15+ facilities scrollable
   - Button: **\"&Reports Console\"** (right side, near Login/Cancel buttons)
2. Click opens the full ENSG-level Reports window titled \"ENSG - Ensign Services Net Health Therapy\"
3. Reports are listed in a WinForms DataGridView with Name + Description columns
4. Double-click a report to run it; most support CSV/Excel export

### Verified Report Catalog (ENSG, rows 0-50 of ~100+, observed 2025-07-03)

| Row | Report Name | Relevance to SLP OMI |
|-----|------------|---------------------|
| 0 | ADT Interface Message Status | HL7 interface monitoring |
| 2-3 | Care Provider Daily Schedule (1.0/2.0) | Appointment schedules with discipline |
| 4-6 | Clinical Outcome Measures (Chart/Worksheet/Table) | Clinical outcomes comparison |
| 21 | Missing Signatures Report | Electronic signature management |
| 28-30 | **nethealth_therapy_census.csv / csv1 / csvV3** | ⭐⭐⭐⭐⭐ CSV export: ALL treatments per patient with discipline, service codes, treatment minutes, physician, wing, response to treatment. **Filter by Discipline=SLP for all SLP data.** |
| 31 | Part B Cap Management | Billed amounts, cap balance, ICD9 codes |
| 33 | **Patient Details** | ⭐⭐⭐⭐ Patient diagnosis (ICD codes!), precautions, short term goals, scheduling |
| 34 | Patient Encounters Report | Treatment minutes by day/discipline/mode/payer/therapist |
| 36 | **PDPM Calculation Worksheet by Patient** | ⭐⭐⭐⭐⭐ PDPM/CMI calculations — directly relevant to coding audits |
| 38-40 | Section GG Assessments / Outcome Detail / Summary | Functional outcome measures |

### Reports Still to Explore (further down the list, beyond row 50)
Look for names containing: SLP, Speech, Evaluation, Assessment, Diagnosis, ICD, Swallowing, Dysphagia, CMI, Diet, Nutrition, Order, Coding.

### Automation Pattern
```
# cua-driver workflow for weekly CSV extract:
1. Launch → Run ENSG → Select Operating Unit appears
2. Click \"Reports Console\" button (bypasses facility login)
3. Double-click \"nethealth_therapy_census.csv\"
4. Set date range → Run → Save CSV to known path
5. Double-click \"Patient Details\" → same process
6. Cron job: Python script reads both CSVs, filters SLP discipline, merges on MRN, applies mismatch rules
```

### Known Facilities (ENSG org, from Select Operating Unit list)
Alamitos West [V42], Beachside [K39], Brookfield [220], Camino [459], Coventry Court [K40], Downey Care [599], Mainplace Post Acute [597], New Orange Hills [K41], Pacific Haven [V66], Palm Terrace [K34] — and more below the scroll. Facility codes in brackets are the unit identifiers.

## cua-driver Automation Notes

### WinForms Grid Scrolling Quirks
The Reports Console uses a WinForms DataGridView with a scrollbar whose Page Down button is NOT always indexed in the UIA tree (appears as un-indexed Thumb between indexed Page Up and Line Down). Workarounds:
- **Set scrollbar value directly:** `set_value` on the ScrollBar element with a numeric value (0-100) — works reliably
- **Key-based paging:** `press_key` with `key=\"pagedown\"` — works on the focused grid
- **Avoid:** Clicking Page Down by element index (inconsistent indexing across captures)
- **Avoid:** Using `scroll` action — SB_LINEDOWN messages don't reliably scroll WinForms grids

### ClickOnce Security Warning Handling
After clicking RUN, expect two dialogs:
1. **Browser download prompt:** \"Do you want to open GiftRAP.Client.application?\" — click Open
2. **Windows ClickOnce security warning:** \"Application Run - Security Warning\" — click Run button (element has `id=btnInstall`)

Monitor process list for `dfsvc.exe` and `GiftRAP.Client.exe` to confirm launch.

## Discovery Pattern (Reusable)

This was found by noticing the login page had an **OrgCode field + RUN button instead of username/password**. Before committing to web scraping for any healthcare platform, check if the "login page" is actually a **desktop app launcher**. Signs:
- OrgCode / company code fields instead of username/password
- "RUN" or "Launch" buttons instead of "Sign In"
- `.application` file downloads (ClickOnce manifest)
- `dfsvc.exe` processes appearing after launch

## API Availability: NONE

- ❌ No public REST API, developer portal, FHIR/HL7 interface, or SDK
- ❓ Internal API may exist (used by desktop client — discoverable via network monitoring)

## Feasibility Rating (Revised)

| Factor | Rating | Notes |
|--------|--------|-------|
| Launch automation | ⭐⭐⭐⭐⭐ | Org code only — no password, no CSRF |
| Desktop automation | ⭐⭐⭐⭐⭐ | cua-driver drives the running desktop app |
| Data extraction | ⭐⭐⭐⭐ | Reports menu likely has CSV/Excel export |
| Local DB access | ⭐⭐⭐ | Possible if SQLite/MDF in ClickOnce cache |
| Maintenance | ⭐⭐⭐⭐ | Desktop apps more stable than web UIs |
| Web scraping | ⭐ N/A | No web app to scrape — desktop app |
