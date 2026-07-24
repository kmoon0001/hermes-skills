# Utah targeted public lookup notes

Use this when Kevin only needs Utah HFA verification for the facilities/admins in his provided ENSG workbook, not a statewide Utah roster.

## Key lesson
Do not default to buying Utah's full professional list. Utah's DOPL data-request form can produce very large/expensive lists if the profession/status filters are too broad.

Observed filters/costs on 2026-06-28:
- Full professional download without filtering: ~1,020,832 records / ~$10,208.32.
- Health Facility Administrator + Temporary HFA, all statuses: 1,691 records / $49.73.
- Health Facility Administrator only, Active only, without address/phone/email: 410 records / $11.30.
- Kevin's input workbook had only 32 Utah facility/admin rows and 29-32 unique person names after splitting multi-admin cells, so targeted lookup is often preferable before purchase.

## Preferred workflow for Utah when scope is Kevin's facilities only
1. Read `C:\Users\kevin\Desktop\ENSG Facilities Only 6.1.26.xlsx`.
2. Filter rows where state is Utah. In the current workbook shape used by the project, admin is row index 5 and state is row index 8.
3. Split multi-admin cells on `/`, ` and `, and `&`; flag the row as `MULTI-ADMIN CELL SPLIT`.
4. Query Utah DOPL public lookup only for the provided names using Health Facility Administrator, not the whole roster.
5. Treat `ACTIVE` exact/strong matches as public evidence.
6. Treat `NOT_FOUND` as manual review, not final noncompliance. Common causes: nickname/legal-name mismatch, middle name, stale admin list, spelling variation, temporary HFA category, or intermittent Utah/reCAPTCHA behavior.
7. Produce an Excel workbook with a Summary sheet and a detail sheet. Include an explicit `Out-of-norm / manual-review note` column because this is outside the normal full roster/state module process.

## Utah public lookup pitfall
The Utah public lookup sometimes completes the POST and renders result text while Playwright never observes the exact `**/search.html**` URL transition. Do not hard-fail solely on URL wait timeout; after submit, best effort wait for URL/network idle, then parse current body text. This avoids false `ERROR` rows.

## Data-request page filter details
For the paid roster page (`https://secure.utah.gov/datarequest/professionals/index.html`):
- Parent HFA checkbox may include both HFA and Temporary HFA.
- Specific HFA-only value observed: `231_232l`.
- Temporary HFA value observed: `231_233l`.
- Active status value observed: `481`.
- If buying, select: HFA only + Active + without address/phone/email unless the user explicitly needs inactive/temporary/address/contact fields.

## Reporting language
When using this targeted public route, call it an ad-hoc/targeted public-source pass, not the canonical full-state roster pipeline. Clearly state that license number and expiration may not be captured from public result text and that `NOT_FOUND` is manual review.