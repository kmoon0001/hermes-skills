# Utah targeted public cross-reference workflow

Use this when Utah full-roster purchase is undesirable and Kevin only needs the ENSG-provided Utah facilities/admins.

## Durable lesson

For Utah, do not default to a broad paid DOPL roster. The DOPL data-request page can quote very high counts/costs if selecting broad HFA + temporary + all statuses. If a roster is needed, narrow it first:

- Health Facility Administrator only, not parent HFA + Temporary HFA
- Active only
- without address/phone/email unless explicitly needed

Observed quote during the session:

- Broad HFA + Temporary + all statuses: 1,691 records, $49.73
- Active HFA only: 410 records, $11.30

## Preferred sequence for Kevin's Utah facilities

1. Start from the user-provided ENSG workbook only. Do not expand scope to all Utah licensees unless needed.
2. Extract Utah rows and split multi-admin cells (`A / B`, `A and B`, `A & B`) into separate person checks.
3. Run targeted Utah DOPL public lookup for each listed individual.
4. Treat ACTIVE DOPL as strongest public license evidence.
5. Treat NOT_FOUND as manual/legal-name/alias review, not noncompliance.
6. Cross-reference public sources to improve identity/facility confidence, but do not use them as license proof:
   - CMS Provider Information (`4pq5-n9py`) for facility identity/CCN/address
   - CMS Ownership (`y2hd-n93e`) for owner/manager clues
   - CMS Facility Affiliation (`27ea-46a8`) for clinician affiliation context only
   - NPI Registry for identity/address clues only
   - public web snippets for alias/current-admin clues only
7. Produce a workbook that explicitly labels the pass as out-of-normal-process if using targeted public cross-reference rather than the normal final pipeline or official roster.

## Reporting rules

Include these notes in the workbook/report:

- Scope: Utah only; only user-provided facilities/admins.
- Public-source pass: no statewide roster purchase/export.
- DOPL ACTIVE is primary-source public evidence.
- CMS/NPI/web confirm context or identity only; they do not prove HFA licensure.
- NOT_FOUND means no exact active HFA match under the provided name; could be nickname/legal-name/current-admin mismatch.
- Multi-admin cells were split and checked independently.
- If CAPTCHA/retry behavior is used, flag it as out-of-normal-process.

## Automation pitfall fixed

`states/utah.py` originally waited for the exact `**/search.html**` URL after submit. Utah sometimes renders usable public result text even when Playwright does not observe that URL transition, producing false timeout errors. Safer pattern:

- click submit
- attempt `wait_for_url` with short timeout
- ignore timeout
- attempt `wait_for_load_state('networkidle')`
- parse whatever body text is available

This avoids false ERROR rows when results are present.
