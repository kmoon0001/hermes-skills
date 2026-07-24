# Power BI Report Structure: One Clinical Outcomes Dashboard

## Report Details
- **Report Name**: One Clinical Outcomes Dashboard
- **Report ID**: `327a2c21-f64b-4dab-8ee5-edc31f9123cd`
- **Workspace**: My workspace
- **URL**: `https://app.powerbi.com/groups/me/reports/327a2c21-f64b-4dab-8ee5-edc31f9123cd/7b2d3705c13dd1b2750d?experience=power-bi`

## Pages
1. **Therapy Episodes - Current Therapy Patients** — Part B Therapy Tool with patient treatment tracks
2. **Clinical Outcomes - Current Patient** — Individual patient clinical outcomes
3. **ADLs and Ambulation** ← THIS IS THE KEY PAGE for declining scores
4. **Abilities Care - Current Patients** — Abilities Care program patients

## ADLs and Ambulation Page Structure

### Summary Cards (top)
- Avg Functional Score (e.g., 3.41)
- Patients w Improvement (e.g., 31.7%)
- Patients w Decline (e.g., 19.5%)
- Walking 10 Ft Exclusions (e.g., 73.2%)

### Slicers/Filters
- **Facility Detail** — dropdown to filter by facility (e.g., "Hurricane Health & Rehab")

### Main Table Columns
| Column Name | Description | Example Values |
|---|---|---|
| Patient Name | Patient name with ID | BRYCE MELANIE (179164419) |
| Previous Assessment Date | Earlier assessment date | 2/19/2026 |
| Latest Assessment Date | Most recent assessment date | 5/21/2026 |
| Avg Functional Score | Average across all categories | 2.60 |
| Previous Eating | Earlier eating score | 5.00 |
| Latest Eating | Most recent eating score | 5.00 |
| Previous Sit to Lying | Earlier sit-to-lying score | 3.00 |
| Latest Sit to Lying | Most recent sit-to-lying score | 3.00 |
| Previous Sit to Stand | Earlier sit-to-stand score | 3.00 |
| Latest Sit to Stand | Most recent sit-to-stand score | 1.00 |
| Previous Toilet Transfer | Earlier toilet transfer score | 3.00 |
| Latest Toilet Transfer | Most recent toilet transfer score | 1.00 |
| Previous Walking 10 Feet | Earlier walking score | 3.00 |
| Latest Walking 10 Feet | Most recent walking score | 3.00 |
| **Total Declined** | **Count of categories that declined** | **2** |
| Total Improved | Count of categories that improved | 0 |

### Score Scale
- Scores range from 1-5 (1 = dependent, 5 = independent)
- 88.00 = Not applicable / excluded from assessment
- A decline = Latest score < Previous score in any category
- **Total Declined > 0** is the trigger for alerts

### Functional Categories (5 total)
1. **Eating** — ability to eat independently
2. **Sit to Lying** — ability to transition from sitting to lying down
3. **Sit to Stand** — ability to stand up from sitting
4. **Toilet Transfer** — ability to transfer to/from toilet
5. **Walking 10 Ft** — ability to walk 10 feet (high exclusion rate ~73%)

## Data Access for Power Automate

### Option A: Power BI Connector (Recommended)
Use the "Run a query against a dataset" action in Power Automate:
- Workspace: My workspace
- Dataset: One Clinical Outcomes Dashboard
- Query: Filter for `Total Declined > 0`

### Option B: Playwright Scraping (Fallback)
If Power BI connector doesn't work, use Playwright headed mode to scrape the table:
```bash
export PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"
"$PWCLI" open "https://app.powerbi.com/groups/me/reports/327a2c21-f64b-4dab-8ee5-edc31f9123cd/7b2d3705c13dd1b2750d?experience=power-bi" --headed
# User signs in, then navigate to ADLs and Ambulation tab
# Extract table data via snapshot/eval
```

### Option C: Export to Excel (NOT AVAILABLE)
"Analyze in Excel" is disabled for this report. Cannot export directly from Power BI UI.

## Facility Mapping
The Power BI report may use different facility names than the SharePoint DOR roster. Known mappings:
- Power BI shows "Hurricane Health & Rehab" as a facility name
- SharePoint DOR roster uses names like "Alamitos West", "Beachside", etc.
- **VERIFY** the facility name mapping when building the flow — the slicer dropdown shows all available facility names
