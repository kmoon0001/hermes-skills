# No-pay Utah/Tennessee public cross-reference pattern

Use this when the user asks to maximize ENSG license/name coverage without paying for rosters or CAPTCHA solves.

## Durable lesson

For Utah/Tennessee gaps, public/free sources can improve facility/person linkage but usually cannot replace official license evidence.

Recommended no-pay sequence:
1. Start from the ENSG facility spreadsheet and prior state output workbooks.
2. Preserve official Utah DOPL matches already captured; do not downgrade these.
3. Pull CMS Provider Data nursing-home provider rows (`4pq5-n9py`) and match facility name + city to get CCN.
4. Pull CMS ownership/managerial-control rows (`y2hd-n93e`) and group by CCN.
5. For each listed admin, check whether the person appears in CMS ownership/managerial-control data for the matched facility.
6. Classify separately:
   - official active Utah HFA evidence from DOPL
   - facility covered by another active listed HFA
   - public CMS person/facility linkage but license unverified
   - likely different license type / outside HFA roster (assisted living, group home, psych, intermediate care, independent living)
   - no admin in source file
   - unresolved official license not found via free sources
7. Write a workbook with explicit `What This Means`, `Next Free Step`, and `Lowest-Cost Effective Paid Step` columns so the user can decide whether to buy a roster.

## Utah-specific lesson

Do not repeatedly loop exact same Utah DOPL NOT_FOUND names as the default. Direct free POST without CAPTCHA returns invalid CAPTCHA, and repeated exact-name misses tend to be legal-name/current-admin/role-type mismatches rather than random portal flakiness.

Lowest-cost useful paid next step for unresolved Utah HFA proof remains the Active Health Facility Administrator roster (about $11.30 in this session), not the all-professions roster and not broad CAPTCHA solving.

## Tennessee-specific lesson

CMS ownership data can confirm that many listed Tennessee admins are publicly linked to the facility as operational/managerial control people, but it is not Tennessee NHA license proof. If no free official bulk export is found, use the TN Health Licensure portal manually/semi-manually for only the small remaining admin list. Avoid spending on BotDetect solvers by default; prior results were unreliable.

## Reporting preference

Kevin wants the practical answer first: how many official matches, how many public-but-unverified names, how many unresolved, and the exact workbook path. Keep the distinction clear between official license proof and public name/facility evidence.