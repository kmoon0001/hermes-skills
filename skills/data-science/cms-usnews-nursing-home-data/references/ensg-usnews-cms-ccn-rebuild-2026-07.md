# ENSG US News/CMS Spreadsheet — CCN Rebuild Lesson (July 2026)

Use this reference when refining the Ensign/US News Nursing Home Ratings workbook or any similar CMS + US News facility spreadsheet.

## Key lesson

Do **not** rely on fuzzy facility-name matching when the source workbook already contains CMS Certification Numbers (CCNs). In this session, fuzzy matching produced plausible but wrong CMS rows for some facilities because many facilities share similar branding, e.g. multiple `Legend Oaks`, `Healthcare Resort`, `Trucare`, and renamed facilities.

Correct approach:
1. Treat the source workbook's CMS CCN as the primary key.
2. Normalize CCNs to 6 digits (`035270`, not `35270` or `35270.0`).
3. Download live CMS Provider Data (`4pq5-n9py`) from data.cms.gov.
4. Rebuild all CMS-derived columns by exact CCN lookup.
5. Only fall back to fuzzy matching when the source has no CCN.
6. Add an audit sheet showing old CCN, source CCN, rebuilt CCN, CMS provider name, status, and changed fields.

## Concrete result from this workbook

Workbook:
`C:\Users\kevin\Desktop\US News Nursing Home Ratings 2026.xlsx`

Source file:
`C:\Users\kevin\Desktop\ENSG Facilities Only 6.1.26.xlsx`

After rebuilding CMS columns by exact original ENSG CCN:
- 336 / 336 facilities verified by exact CMS CCN.
- 0 missing CMS matches.
- 21 old fuzzy-matched CCNs corrected.
- 1,318 individual CMS cells refreshed/corrected/normalized.
- Final `Data Confidence` column set to `✅ Verified by CMS CCN` for all rows.

Important caveat: `Verified by CMS CCN` means the workbook matches CMS source-of-record for that CCN. It does **not** mean PBJ staffing/turnover data is independently perfect; staffing/turnover remains self-reported and lagged.

## Recommended workbook organization

Final sheet order should be:
1. `Summary` — clean dashboard: verification counts, US News counts, CMS overall counts, risk flags, state breakdown.
2. `Facility Ratings` — main data; include `Data Confidence` column.
3. `Discrepancies` — original ENSG vs live US News mismatch list with explanation.
4. `CMS Verification Audit` — row-level transparency for CCN rebuild.
5. `Action Items` — regenerated from corrected CMS data, severity-sorted.
6. `Data Sources & More` — methodology, reliability guide, caveats, short-seller/attack context if relevant.

## Accuracy wording to use with Kevin

Short version:
> CMS columns are now 100% verified against CMS by exact CCN for all 336 facilities. The source CMS staffing/turnover metrics still have normal CMS/PBJ caveats because they are self-reported and lagged.

Avoid saying:
> Everything is 100% accurate.

Better:
> The workbook is 100% matched to CMS source-of-record by CCN; the underlying CMS self-reported fields still carry CMS source limitations.
