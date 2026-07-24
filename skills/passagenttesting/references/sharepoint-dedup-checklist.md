## SharePoint Verification Before Deduplication

Before removing individual knowledge sources, verify they exist in the shared SharePoint folder:

**Playwright method to list SharePoint files:**
1. Navigate to SharePoint URL while authenticated
2. Wait for FluentUI to render file grid
3. Extract file names via `document.querySelectorAll('[role="listitem"]', '[data-sp-a11y-id="doc"]')`
4. Compare with individual knowledge source names

**Critical files found in Pacific Coast Therapy Swarm → Core Clinical Manuals:**

| File | Duplicate In |
|------|--------------|
| MDS 3.0 RAI Manual 2026.pdf | SLP: CMS MDS 3.0 Section GG |
| Medicare Benefits Policy Manual Chapter 15.pdf | TDA: Medicare Benefit Policy Manual |
| PDPM-*.pdf (4 files) | TDA: Patient-Driven Payment Model, SNF PDPM |
| Clinical Decision Support CMS-Jimmo-Coverage.md | TDA: Clinical Decision Support |
| CFRs that apply to Medicare Part B.docx | SLP: 42 CFR 424.24 (potentially) |

**NOT found in SharePoint (safe to keep as individual):**
- Medicare Program Integrity Manual Chapter 3
- Medicare Secondary Payer Outpatient Therapy Guidelines
- 42 CFR 424.24 (specific section - may differ from broad CFRs.docx)

## Description Verification Method

To check if a description is blank/generic without clicking each source:

1. Open Knowledge page via CDP with Network intercept
2. Capture all API calls to `/knowledgeSources` endpoint
3. Parse response for `description` field length and content
4. Flag: `description === ''` or `description.includes('searches information contained in')`

**MS Learn warning**: Sources with blank descriptions are randomly selected by GPT filter, causing "Not cited" failures even when content exists.