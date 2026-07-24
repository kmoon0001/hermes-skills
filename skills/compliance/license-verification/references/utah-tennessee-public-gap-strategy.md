# Utah/Tennessee public gap strategy (session-derived)

Use when ENSG license verification is blocked on Utah or Tennessee and the user asks whether public sources can be cross-referenced before paying or doing manual lookup.

## Utah findings and workflow

- Scope from the ENSG workbook in this session: 34 Utah facility rows; 39 facility/person rows after splitting multi-admin cells.
- Targeted Utah DOPL public lookup produced 12 active Health Facility Administrator matches, 25 exact-name `NOT_FOUND`, and 2 rows with no admin listed.
- Do not spend cycles or 2captcha balance repeatedly looping the same exact Utah names. Re-running can recover an occasional portal/reCAPTCHA-v3 flake, but it usually does not solve the real blockers: legal-name mismatch, nickname, old admin, spelling, or missing admin.
- If retrying Utah public lookup, only retry with new information: legal first/middle names, aliases, alternate spelling, current administrator update, or split multi-admin ambiguity.
- Lowest-cost effective official Utah path found: DOPL data request for `Health Facility Administrator` only, `Active` only, without address/phone/email. Expected scale found during session: about 410 records and about $11.30. Avoid the broader all-status / Temporary HFA-inclusive pull (~1,691 records, ~$49.73) unless historical licenses are explicitly required.
- Cross-reference sources (CMS Care Compare/provider data, CMS ownership/affiliation, NPI Registry, facility sites/web snippets) are useful for facility/person identity clues only. They do not prove HFA licensure; Utah DOPL lookup/roster remains controlling proof.

## Tennessee findings and workflow

- Scope from the ENSG workbook in this session: 11 Tennessee facility/admin rows.
- Tennessee Health Licensure portal uses BotDetect CAPTCHA. Prior tests found image solving/vision/2captcha unreliable enough that production automation should not spend solves by default.
- Public web, Tennessee Socrata/healthdata catalog, and LicensureReports-style endpoint checks did not reveal a usable free no-CAPTCHA official NHA bulk roster/export.
- Free highest-confidence path: semi-auto/manual TN Health Licensure portal lookup for the 11 names.
- Public cross-reference sources (CMS provider data, NPI Registry, facility websites, search snippets) can help confirm facility identity and person clues, but cannot replace official Tennessee license proof.

## Alaska decision pattern

- If the user is okay with semi-manual Alaska, keep Alaska semi-auto/manual. Do not pursue proxy/DataDome/paid solver automation unless the user explicitly requires full automation.

## Reporting pattern

For gap work, generate a separate workbook rather than blending clue-only evidence into the final proof workbook. Suggested sheets:

- `Gap CrossRef Strategy`: state, facility, city, LOB, person checked, official license status/next status, official evidence, CMS match/CCN, NPI clues, web clues, recommendation.
- `Summary`: counts by status plus plain-language conclusions.
- `Web Clues`: raw search snippets/URLs.
- `Out of Norm Notes`: explicit warning that CMS/NPI/web are clues, not license proof.

User communication preference in this class of work: Kevin wants execution and concise conclusions. When asked “can we do X?”, run the targeted probes/build the workbook first when feasible, then summarize counts, cost, and next action. Avoid long speculative explanations before acting.
