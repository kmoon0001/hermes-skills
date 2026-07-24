# Platform Investigation Checklist

> Template for systematically investigating a healthcare SaaS platform's programmatic data access surface.
> Run this checklist for each platform independently, then compare findings to choose the best approach per system.

## Phase 1: API Discovery

- [ ] **Developer portal exists?** Check `developer.[vendor].com`, search `[vendor] developer portal`
- [ ] **Public REST API documented?** Look for OpenAPI/Swagger specs, API reference docs
- [ ] **Authentication model:** OAuth2, SAML, API keys, service accounts, or none?
- [ ] **Auth endpoints:** Where to get tokens? (authorization URL, token URL, scopes)
- [ ] **Sandbox available?** Test environment for development without touching production data
- [ ] **Rate limits?** Requests per minute/hour, pagination model
- [ ] **FHIR/HL7 support?** Many healthcare platforms support FHIR even when they don't advertise a REST API
- [ ] **SOAP/HL7 interfaces?** Legacy integration path, especially for ADT feeds

## Phase 2: Data Coverage

For each data domain needed, check:

- [ ] **Patient/Resident data:** Demographics, MRN, admit/discharge dates, payer
- [ ] **Clinical assessments:** MDS/RAI sections, assessment dates, scores
- [ ] **Diagnoses:** ICD codes, diagnosis types, active/inactive status
- [ ] **Medications:** Orders, MAR records, administration times
- [ ] **Therapy encounters:** Session dates, therapist type, notes
- [ ] **Care plans:** Goals, interventions, linked to assessments
- [ ] **Diet/nutrition:** Diet orders, texture modifications, nutritional status
- [ ] **Vitals/labs:** Measurements, lab results, observation data

## Phase 3: Fallback Surfaces

If no API or insufficient API coverage:

- [ ] **Bulk export tools:** CSV/Excel/PDF download, scheduled reports, data warehouse exports
- [ ] **Built-in reporting:** Can report output be parsed programmatically?
- [ ] **Screen scraping:** What's the web framework? (React SPA, ASP.NET MVC, Angular, jQuery)
- [ ] **Auth for scraping:** CSRF tokens, session cookies, MFA requirements?
- [ ] **Anti-bot measures:** New Relic, reCAPTCHA, Cloudflare, rate limiting?
- [ ] **Manual workflow automation:** Can a manual export step be scripted as part of a pipeline?

## Phase 4: GitHub/Community Research

- [ ] **GitHub API search:** `https://api.github.com/search/repositories?q=[vendor]+api&sort=stars`
- [ ] **api-evangelist repos:** Check `api-evangelist/[vendor]` for mirrored API docs
- [ ] **Stack Overflow:** Search for `[vendor] API integration [use case]`
- [ ] **Reddit/forums:** Nursing home admin forums, rehab management communities
- [ ] **Third-party SDKs:** Any open-source tools, n8n nodes, or integration libraries?

## Phase 5: Synthesis

- [ ] **Primary approach:** API > FHIR > Bulk Export > Scraping
- [ ] **Auth requirements:** What credentials does the user need to provide?
- [ ] **Data freshness:** Real-time, near-real-time, or batch-only?
- [ ] **Implementation effort:** Estimate based on approach complexity
- [ ] **Maintenance risk:** How likely is this to break? How hard to fix?

## Output Format

For each platform, produce a structured summary:

```markdown
### [Platform Name]

| Property | Value |
|----------|-------|
| Base URL | |
| Auth | |
| Endpoints Found | N |
| Key Data Available | |
| Key Data Missing | |
| Primary Approach | |
| Fallback Approach | |
| Feasibility | ⭐⭐⭐⭐⭐ |
```
