# ENSG US News / CMS Spreadsheet Accuracy Lessons — July 2026

## Key correction

Do not rely on fuzzy facility-name matching for CMS fields when the source ENSG workbook already contains CMS CCNs.

In the July 2026 US News Nursing Home Ratings workbook, fuzzy matching produced some wrong CMS CCNs even though the original ENSG source workbook (`ENSG Facilities Only 6.1.26.xlsx`) had the correct CMS CCN in column H. Rebuilding CMS columns by exact source CCN fixed the issue.

## Correct workflow

1. Treat the original ENSG workbook as the facility roster source:
   - Column A: original US News entry
   - Column H: CMS CCN
   - Column I: CMS Provider Name
   - Column K: LOCATION/display name
   - Columns R/S: City/State

2. Download live CMS Provider Data API dataset `4pq5-n9py` in pages of 1,500 rows.
   - Larger page sizes (e.g. 5,000) may return HTTP 400.
   - Endpoint pattern:
     `https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0?limit=1500&offset=N&format=csv&results=true&count=false&keys=false`

3. Normalize CCNs:
   - Strip whitespace
   - Remove trailing `.0`
   - Keep digits only
   - Left-pad to 6 digits

4. Match every facility by exact CCN first.
   - If source CCN exists and is found in CMS, set Data Confidence = `✅ Verified by CMS CCN`.
   - Only use fuzzy name matching as a fallback when the source workbook has no CCN or the CCN is absent from CMS.

5. Rebuild all CMS columns from the CMS API record after CCN match:
   - Overall Rating
   - Staffing Rating
   - CNA/LPN/RN/Total staffing hours
   - adjusted nurse hours
   - weekend hours
   - PT hours
   - total/RN/admin turnover
   - case-mix index
   - health inspection rating / survey score
   - QM ratings
   - ownership, beds, census, chain
   - Special Focus / Abuse
   - fines, fine amount, payment denials, total penalties
   - CMS CCN

6. Add a `CMS Verification Audit` sheet with:
   - original ENSG CMS CCN
   - old workbook CMS CCN
   - new verified CMS CCN
   - CMS Provider Name / City / State
   - status
   - fields changed
   - notes

7. Regenerate Summary and Action Items after rebuilding CMS fields. Do not leave summary/risk counts based on stale fuzzy-match data.

## Result from July 2026 run

- 336 / 336 facilities verified by exact CMS CCN
- 0 missing CMS matches
- 21 old fuzzy-matched CCNs corrected
- 1,318 CMS cells refreshed/corrected/normalized
- Confidence column changed from mixed Verified/Approximate/No Match to all `✅ Verified by CMS CCN`

## Transparency language to use

`Verified by CMS CCN` means the spreadsheet accurately reflects CMS Provider Data for that facility's CMS Certification Number on the source date. It does **not** mean CMS self-reported staffing/turnover data is independently perfect. PBJ staffing/turnover still has known self-reporting, audit, and lag limitations.

## Desktop delivery pattern

When the user says they cannot see the workbook:

1. Keep the final workbook visible with an obvious name:
   `OPEN THIS - US News Nursing Home Ratings 2026.xlsx`
2. Move old copies/backups/scripts to a dated archive under Documents, not permanent deletion:
   `Documents/Hermes Desktop Cleanup Archive/<date>-usnews-and-work-artifacts/`
3. Keep a `cleanup_manifest.json` listing moved files.
4. Do not delete the Excel `~$...xlsx` lock file while the workbook is open; it disappears when Excel closes.
