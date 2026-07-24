# Utah targeted public cross-reference workflow

Use when Kevin wants Utah coverage for only the provided ENSG facilities/admins and wants anything out-of-normal-process explicitly noted.

## Durable workflow

1. Scope to the ENSG workbook first, not the statewide Utah roster.
   - Source workbook: `C:\Users\kevin\Desktop\ENSG Facilities Only 6.1.26.xlsx`.
   - Utah rows use `STATE == Utah`.
   - Admin field is `EXECUTIVE DIRECTOR`; split multi-admin cells on `/`, ` and `, and `&`.
   - Keep blank-admin rows as `NOT_RUN` / source-data issue, not dropped.

2. Use Utah DOPL public lookup as the controlling public license source.
   - Portal: `https://secure.utah.gov/llv/search/index.html`.
   - Profession checkbox for public lookup: `item153_1` = Health Facility Administrator.
   - Search targeted names only; do not scrape/buy full roster unless needed.
   - The public lookup may return results while Playwright misses the exact `**/search.html**` URL transition. After submit, wait briefly for URL/networkidle but still parse the current body text instead of treating URL wait timeout as failure.

3. Cross-reference other public sources for identity/context only.
   - CMS Care Compare Provider Information dataset `4pq5-n9py` confirms facility identity/CCN/address/beds/ownership type.
   - CMS Ownership dataset `y2hd-n93e` gives owner/manager clues, not HFA license proof.
   - CMS Facility Affiliation dataset `27ea-46a8` gives clinician affiliations; identity/context only, not HFA proof.
   - NPI Registry can help with person identity/address/taxonomy, but HFA administrators often will not have relevant NPIs.
   - Public web snippets/facility pages are clues only; never upgrade to compliant solely from web/CMS/NPI without DOPL/official roster evidence.

4. Confidence rules.
   - `ACTIVE` Utah DOPL HFA match = strongest public evidence.
   - `NOT_FOUND` means no exact active HFA match under the provided name; it is manual review, not final noncompliance. Common causes: nickname, middle/legal name, stale admin list, spelling, multiple admins, temporary HFA category mismatch.
   - If Utah roster purchase is acceptable, prefer filtered `Active` + `Health Facility Administrator` only. Prior quote: 410 records / about $11.30. Avoid full/all-status/all-profession download.

5. Reporting rules.
   - Include an `Out-of-normal-process` note in the workbook when using maximal public cross-reference instead of the normal final pipeline or official purchased roster.
   - Include source columns: Utah DOPL, CMS Provider Information, CMS Ownership, CMS Facility Affiliation, NPI Registry, Web Search Evidence.
   - Keep manual-review rows; do not omit unresolved people.

## Pitfalls learned

- Utah DOPL public lookup is intermittent; retry targeted failures, but do not loop indefinitely.
- Do not overclaim from CMS/NPI/web. They support identity matching; license status must come from DOPL or official roster.
- Full Utah data request can be expensive because it includes statewide records and inactive/expired/temporary statuses. Filter to `Active` HFA only when purchasing.
- Search-engine HTML endpoints may block with 403/429; preserve the block as a source limitation, not as negative proof.
