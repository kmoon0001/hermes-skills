# NetHealth Rehab Optima (Care Operations Manager)

## Architecture

- **Product:** NetHealth Rehab Optima (marketed as "Optima for Skilled Nursing")
- **Internal codename:** Care Operations Manager / GiftRAP
- **Executable:** `GiftRAP.Client.exe` (ClickOnce deployment)
- **Deployment:** ClickOnce from `client.therapy.nethealth.com`
- **Platform:** .NET WinForms desktop application
- **Auth:** Organization-code based (no username/password)
- **Login URL:** `https://login.therapy.nethealth.com/`
- **Org code example:** "ENSG" (Ensign Services)

## Installation

1. Navigate to `https://login.therapy.nethealth.com/`
2. Enter organization code (e.g., `ENSG`) in the `OrgCode` field
3. Click `RUN` button (`id=launchButton`)
4. Browser downloads `GiftRAP.Client.application` from `ensg.therapy.nethealth.com`
5. ClickOnce security dialog appears: "Do you want to run this application?"
   - Name: "Care Operations Manager"
   - Publisher: "Net Health Systems, Inc."
6. Click `Run` → download (333 MB) → auto-install → auto-launch
7. App window title: `ENSG - Ensign Services Net Health Therapy`

## Login Screen

After launch, a "Select Operating Unit" dialog appears:
- Username field: displays current user (e.g., `eg.kmoon`)
- Facility list: scrollable list of facilities with codes (e.g., `Alamitos West Health Care Center [V42]`)
- **Reports Console button:** Available on login screen without selecting a facility
- **Login button:** Select a facility and log in

## Reports Console — Key Reports for SLP CMI

Access via the `Reports Console` button on the login screen or within the app.

### Most Valuable Reports

| Report | Contents | Export Format |
|--------|----------|---------------|
| **Service Log Matrix** | Patient service codes, treatment minutes, units, therapist names, **diagnosis codes**, onset date, start of care — filterable by discipline | Grid → export |
| **nethealth_therapy_census.csv** | End of Day summary of ALL treatments per patient with Discipline, treatment minutes, physician, wing, service codes, response to treatment | CSV |
| **Patient Details** | Patient diagnosis (ICD codes), precautions, short term goals, scheduling | Grid → export |
| **PDPM Calculation Worksheet by Patient** | PDPM/CMI calculations per patient | Grid → export |
| **Patient Encounters Report** | Treatment minutes by day, discipline, mode, payer, therapist | Grid → export |
| **Therapy Census Report** | Patient census, progress reports, certifications, planned discharge, responsible therapist | Grid → export |
| **Clinical Outcome Measures** (Chart/Worksheet/Table) | Clinical outcomes comparison — prior function, baseline, discharge | Grid → export |

### Reports Console UI

- **Filter box** at top — type to search (e.g., `speech`, `eval`, `diagnosis`, `diet`)
- **Group by Category** checkbox
- **Show Descriptions** checkbox
- **Show User Reports Only** checkbox
- **Run** button — run selected report
- **Close** button
- Report list is sortable by clicking column headers

## Automation Notes

- WinForms DataGridView scrollbar has broken UIA patterns — see `windows-cua-driver` skill for workarounds
- Reports can be exported as CSV (confirmed for `nethealth_therapy_census.csv`, likely others)
- The app launches its own Chrome instances for some views
- Session timeout shows "Kevin Moon is logged on" with Resume/Logout

## Automation Strategy

1. Launch via ClickOnce URL (re-downloads if not installed, launches if already installed)
2. Click "Reports Console" on login screen (no facility selection needed!)
3. Filter for target report
4. Select and Run
5. Export output (CSV where available)
6. Parse CSV with Python pipeline
