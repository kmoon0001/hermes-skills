# Ensign / US News / CMS authoritative evidence package pattern (Jul 2026)

Use this reference when the user asks for an evidence-only counter-report, public-response package, or patient/staff advocacy guide built from the Ensign US News/CMS workbook.

## Task shape

User wanted a package that was:
- evidence based only;
- backed by authoritative sources;
- accurate and reproducible;
- useful for countering a short-seller narrative;
- separate from a patient/staff closure and justice guide.

## Durable workflow

1. Start from the current final workbook on Desktop:
   - `C:\Users\kevin\Desktop\OPEN THIS - US News Nursing Home Ratings 2026.xlsx`
2. Treat exact CMS CCN matches as the data foundation.
3. Use primary/authoritative sources only:
   - CMS Provider Data Catalog dataset `4pq5-n9py`.
   - CMS Provider Data Catalog About page.
   - CMS Five-Star Quality Rating System page and Nursing Homes Technical Details.
   - CMS PBJ Staffing Data Submission page.
   - SEC Ensign 10-K filing.
   - Hunterbrook's own methodology/disclosure page for conflict and methodology admissions.
   - eCFR 42 CFR 483.10 for resident rights.
   - OSHA whistleblower complaint page.
   - NLRB Employee Rights / protected concerted activity page.
   - DOL Wage and Hour complaint page.
   - Consumer Voice Get Help / ombudsman and state complaint links.
   - DOJ/SEC short-seller enforcement examples only as context, not as proof of Hunterbrook wrongdoing.
4. Generate a package with these files:
   - `00_PRINTABLE_EVIDENCE_BRIEF.html` — quick visual/printable version.
   - `01_FULL_EVIDENCE_DOSSIER.md` — full source-backed report.
   - `02_ONE_PAGE_TLDR.md` — short briefing.
   - `03_RESPONSE_SCRIPT.md` — response/talking points.
   - `04_PATIENT_STAFF_JUSTICE_GUIDE.md` — separate lawful patient/staff advocacy guide.
   - `05_SOURCE_LEDGER.md` — source table and reproducibility notes.
   - `charts/*.svg` — dependency-free charts so matplotlib is not required.
   - a copied source workbook for reproducibility.
5. Create charts as plain SVG when Python plotting libraries are not installed. Do not record missing matplotlib as a durable problem; the durable lesson is: dependency-free SVG charts are adequate and portable for this task.

## Evidence posture / language guardrails

Do say:
- "Show me the CCN, date range, and CMS field. We'll verify it."
- "Some facility-level issues are real and require action."
- "Hunterbrook disclosed a short ENSG position and described its dollar figures as estimates."
- "The accurate way to discuss quality is facility-by-facility using reproducible CMS data."

Do not say:
- "All accusations are lies."
- "CMS proves every facility is good."
- "Hunterbrook committed fraud" unless a regulator/court says so.
- Personal-life attacks, private dirt, rumor, or anonymous claims.
- Blanket denial of staffing/compliance problems when CMS shows facility-level risk flags.

## Off-record / rumor quarantine pattern

When the user asks to include or investigate rumor, personal-life dirt, unverifiable claims, or accusatory wording such as "Hunterbrook committed fraud":

1. Keep the evidence package clean and authoritative.
2. Create a separate folder such as `99_QUARANTINE_DO_NOT_PUBLISH_OFF_RECORD` under the package root.
3. Put only guardrails, triage templates, and public/professional conflict analysis there — not private-life dirt or doxxing material.
4. Mark it clearly `DO NOT PUBLISH / DO NOT SEND TO PRESS / COUNSEL TRIAGE ONLY`.
5. For each quarantined item require: source, date, exact claim, verification status, why it matters, legal/reputation risk, and disposition.
6. If the user asks to "look into his personal life," pivot to public professional background, source credibility, conflicts of interest, Form ADV/IAPD, author/editor roles, and disclosed business model. Refuse private-life dirt while still producing useful professional counter-ammunition.

Safe professional-conflict wording:

"Hunterbrook's own disclosures show a nontraditional structure: an investigative media entity, an affiliated investment adviser, disclosed short exposure to ENSG at publication, potential derivative exposure, possible later trading changes without update obligation, and litigation/reform partnerships tied to reporting. Those facts do not prove wrongdoing, but they are directly relevant to readers, regulators, counsel, and courts evaluating bias, motive, methodology, and market impact."

For Hunterbrook specifically, useful public/professional sources include:
- Hunterbrook About page for business model: litigation partnerships + investment monetization, Media/Capital under common control.
- Hunterbrook Ensign methodology for short ENSG disclosure, positions may change, possible derivatives/swaps/options exposure, no obligation to update, and as-is/no-guarantee language.
- SEC IAPD / Form ADV for Hunterbrook Capital LP public adviser record, CRD/SEC/CIK, and ownership/control roles. Do not make disciplinary-history claims from OCR/PDF extraction alone; verify visually in IAPD/ADV first.
- Hunterbrook team/author pages for public author/editor chain. Use roles and publication responsibility only, not personal attacks.

## Patient/staff closure guide pattern

Keep this separate from corporate defense. The guide should help convert suffering into dated, reportable, official-channel issues:
- resident grievance and 42 CFR 483.10 rights;
- Long-Term Care Ombudsman;
- State Survey Agency;
- Adult Protective Services / Medicaid Fraud Control Unit / state AG where appropriate;
- OSHA for safety retaliation;
- NLRB for protected concerted activity around working conditions;
- DOL WHD for wage/hour issues.

Add a clear anti-retaliation / anti-harassment warning: do not harass reporters, former employees, critics, residents, or staff; do not bury complaints; preserve records and route issues to proper official channels.