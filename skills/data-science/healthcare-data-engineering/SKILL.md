---
name: healthcare-data-engineering
description: >
  Systematic methodology for investigating and extracting data from healthcare SaaS platforms
  (EHRs, nursing home management, rehab platforms). Covers API discovery, auth flows, data model
  mapping, deterministic rule design, and feasibility synthesis. Includes clinical data modeling
  patterns (MDS/RAI coding, CMI classifications, cross-system mismatch detection).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [healthcare, api-extraction, mds-rai, cms-coding, snf, rehab, nlp-audit, missed-opportunity]
    category: data-science
    related_skills: [research, web-scraping-anti-detection, playwright-patterns]
---

# Healthcare Data Engineering

## When This Skill Activates

Use when the user asks about:
- Pulling/querying/extracing data from healthcare SaaS platforms (PointClickCare, Epic, Cerner, NetHealth, etc.)
- Automating MDS/RAI assessment reporting or CMS coding audits
- Detecting billing/coding mismatches across healthcare systems
- Building pipelines from healthcare EHR/rehab/nursing home platforms
- Investigating whether a healthcare vendor offers an API, FHIR endpoints, bulk exports, or scraping surfaces

## Core Methodology: Parallel Investigation

When tasked with pulling data from a healthcare system, run three independent investigations IN PARALLEL:

### ① Platform Technical Discovery (Subagent/Web Research)
Research both systems simultaneously:

**API Availability Check:**
- Developer portal URL (`developer.[vendor].com`)
- REST API documentation existence
- Authentication model (OAuth2, SAML, API keys, service accounts)
- Rate limits, pagination, sandbox environments
- Structured export formats (JSON/XML vs PDF reports only)

**Data Access Tiers:**
- Fine-grained REST endpoints (what data per endpoint?)
- Bulk export tools (CSV downloads, scheduled reports, Data Center-style exports)
- HL7/FHIR interface support (often available via health system integration layer, not direct to end-user)
- Third-party SDKs, open-source integrations, community tools

**Fallback Surfaces:**
- Screen scraping feasibility (web framework used, CSRF tokens, anti-bot measures)
- Browser automation viability (Playwright/Selenium patterns)
- Manual export workflows that can be scripted

### ② Clinical Domain Mapping (Agent-Known Knowledge)
Map the clinical/billing concepts the user cares about to actual data fields. For SNF nursing homes specifically:

- **MDS/RAI section codes** → exact item identifiers (e.g., K0300 = swallowing difficulty)
- **CMI diagnostic categories** → what they mean clinically and in billing terms (SB = dysphagia w/ nutritional consequence)
- **Cross-references** → how sections link (Section K ↔ AA Section eating impairment ↔ BB Section nutrition status)
- Use the clinical mapping reference file (`references/clinical-mapping.md`) as starting knowledge

### ③ Rule Engine Design (Agent Logic)
Design deterministic mismatch rules BEFORE seeing API results, so you're ready to code immediately once access is confirmed:

```python
# Pattern: Rule template
IF <condition_from_system_A_field_X> AND <condition_from_system_B_field_Y>:
    FLAG = "specific_mismatch_type"
    # Reasoning documented in rule description
    
ELIF partial_evidence_pattern:
    FLAG = "needs_manual_review"
    
ELSE:
    PASS  # Clean match
```

Key principle: focus on OBJECTIVE, verifiable mismatches — not subjective clinical judgment.

## Output Deliverables

After all three investigation tracks complete, synthesize into:

1. **Feasibility Assessment** — Go/no-go per system, preferred approach per system
2. **Architecture Diagram** — Pipeline flow from data sources through rule engine to output
3. **Prototype Code** — Working script using whichever approach is viable (API calls, scraping, hybrid)
4. **Known Gaps** — What we couldn't determine yet (needs live login testing, vendor contact, etc.)

## Pitfalls

- **Don't assume APIs exist.** Many healthcare platforms hide features behind non-public interfaces. Always check bulk export options as fallback.
- **Don't confuse health-system integration layer with end-user API.** HL7/FHIR often available to facility IT staff but NOT to end-users who just have login credentials. This distinction matters — clarify early.
- **Clinical mappings change with RAI manual versions.** Always note which version of the manual your field references come from (current is v3.8 for SNF RAI). Old mappings break on new assessments.
- **Separate integration credentials from interactive user sessions.** For a vendor-approved API or service account, implement the documented OAuth/token-refresh flow and least-privilege scopes. Never build refresh/keep-alive logic around an individual clinician's browser session, cookies, MFA, or idle/absolute timeout; it bypasses an ePHI security control and produces unreliable audit behavior. When staff report rapid PCC/EHR web logoffs, diagnose the tenant timeout, SSO/session lifetime, browser cookie policy, VPN/proxy/load-balancer session affinity, device clock, and network stability. The supported usability solution is enterprise SSO plus Windows Hello/FIDO2/passkeys on managed devices, not auto-clickers, artificial page refreshes, or browser keep-alive extensions.
- **Gated dev portals hide docs behind login, not absence of API.** Many healthcare vendors (PCC, Epic, Cerner) require partnership applications to access API docs. Before concluding "no API exists," search GitHub for `api-evangelist/{vendor}` repos — they mirror OpenAPI specs, Postman collections, and schemas for many healthcare platforms. Also search `https://api.github.com/search/repositories?q={vendor}+api&sort=stars` for third-party integration repos that reveal endpoints and auth patterns even when the official docs are gated. PCC's full API spec was discoverable this way despite their SPA dev portal showing nothing without login.
- **Check for desktop EHR clients before committing to web scraping.** Some healthcare platforms offer both web and desktop versions. Desktop clients often have local databases (SQLite, SQL Server Express) that can be queried directly — more reliable than web scraping. Search `C:\Program Files\`, `C:\Program Files (x86)\`, and `%APPDATA%` for vendor-named directories. If found, explore `.mdf`, `.sqlite`, `.db` files. Desktop apps also often have CSV/Excel export in the Reports menu — automating via cua-driver is more stable than fragile web scrapers.

  **Also check if the login page is actually a desktop app launcher.** Many EHR/therapy platforms use ClickOnce deployment where the "login" page has an organization code (not username/password) and a RUN/Launch button. Example: NetHealth Rehab Optima at `login.therapy.nethealth.com` shows an OrgCode field + RUN button — entering the org code triggers a `GiftRAP.Client.application` ClickOnce download from `client.therapy.nethealth.com`, deploying the 333 MB "Care Operations Manager" desktop app via `dfsvc.exe`. Signs to look for: OrgCode/company-code fields instead of username/password, "RUN"/"Launch" buttons, `.application` file downloads, and `dfsvc.exe` processes after launch. - **Reports consoles often bypass login entirely.** Desktop EHR apps frequently offer a "Reports Console" button directly on the facility/login selection screen — before selecting a facility. This means reports can be automated without logging into a specific facility. Always check the login/selection screen for Reports or Export buttons before assuming login is required. NetHealth's login screen has a "&Reports Console" button that opens the full report catalog directly.

- **WinForms DataGridView scrollbars are unreliable with element-indexed clicks.** When driving desktop EHR reports consoles via cua-driver, the scrollbar's Page Down button may not be consistently indexed in the UIA tree across captures. Workaround priority: (1) `set_value` on the scrollbar element to jump directly to a percentage, (2) `press_key(key="pagedown")` after clicking the grid to focus it, (3) avoid clicking Page Down by index — it may map to Line Down or a different button on subsequent captures.

See `references/clinical-mapping.md` for detailed MDS/RAI field definitions and SLP CMI category-to-field mappings.
See `references/platform-checklist.md` for the structured investigation checklist template.
See `references/mismatch-rule-framework.md` for extendable rule templates and scoring logic.
See `references/pcc-api-reference.md` for PointClickCare REST API v2 endpoints, auth, schemas, application form details, and known gaps (updated 2025-07-03).
See `references/nethealth-scraping-reference.md` for NetHealth Rehab Optima ClickOnce desktop deployment, OrgCode-based launcher, cua-driver automation, and local database discovery patterns.
See `templates/pipeline_starter.py` for a copy-and-modify starter pipeline with PCC API client, rule engine, and CSV output.

## File Locations

```
healthcare-data-engineering/
├── SKILL.md                       ← This file
├── references/
│   ├── clinical-mapping.md        ← SLP CMI categories, MDS Section K fields, mismatch rules
│   ├── platform-checklist.md      ← API investigation checklist template
│   ├── mismatch-rule-framework.md ← Extensible rule engine patterns
│   ├── pcc-api-reference.md       ← PointClickCare REST API v2 (endpoints, auth, schemas, application form)
│   └── nethealth-scraping-reference.md ← NetHealth Rehab Optima ClickOnce desktop app + OrgCode launcher
└── templates/
    └── pipeline_starter.py        ← Copy-and-modify pipeline: PCC client + rules + CSV output
```
