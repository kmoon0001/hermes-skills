---
name: knowledge-source-builder
description: Build structured knowledge source documents for AI agents from authoritative PDFs and frameworks — download, extract, author, and publish. Covers curl→browser escalation for bot-blocked PDFs, pdfplumber extraction, scenario authoring, parallel subagent delegation with timeout fallback, and GitHub publishing.
category: copilot-studio
---

# Knowledge Source Builder

End-to-end workflow for building upload-ready knowledge source markdown files
from authoritative PDFs, framework documents, and clinical standards. Used when
the user needs to create knowledge bases for Copilot Studio agents, custom GPTs,
NotebookLM, or any agent that consumes structured knowledge documents.

## Triggers

Use this skill when the user asks to:
- Build knowledge sources / knowledge base for an AI agent
- Create clinical scenario banks from governing body standards
- Download and process authoritative PDFs into agent-usable content
- Assemble a structured knowledge repository from multiple source documents

## Workflow

### Phase 1: Source Acquisition

1. **Map the source list.** Identify all authoritative PDFs/web pages needed.
   Group by governing body (APTA, AOTA, ASHA, CMS, etc.) and priority tier.

2. **Download: curl first.** Most government and association PDFs are direct-downloadable.
   ```bash
   curl -sL -o "filename.pdf" "$URL" -w "%{http_code} %{size_download}"
   ```
   Valid = HTTP 200 + size > 10KB. 403, small HTML, or Incapsula/Cloudflare pages = blocked.

3. **Blocked? Escalate to browser.** Playwright's stealth features bypass Incapsula
   and many Cloudflare challenges that block curl. Navigate to the PDF URL — if
   it renders in the built-in viewer, click Download.
   ```
   browser_navigate(url="https://example.com/blocked.pdf")
   browser_click(ref=<download_button_element>)
   ```

4. **404? Search for updated URL.** Framework documents get reorganized. Search
   for the document title on the source site — newer versions often exist at
   different paths. Also try `web_search("document title PDF site:source.org")`.

5. **Journal paywalls (SAGE/Cloudflare).** Some publications (AJOT via
   research.aota.org) use aggressive Cloudflare protection. Flag these for the
   user to download manually — they typically require institutional access.

### Phase 2: Text Extraction

Use `pdfplumber` via `execute_code`:

```python
import pdfplumber, os, json

pdf_dir = "downloaded-pdfs"
out_dir = "extracted-texts"

for pdf_file in sorted(os.listdir(pdf_dir)):
    if not pdf_file.endswith('.pdf'): continue
    pdf_path = os.path.join(pdf_dir, pdf_file)
    txt_path = os.path.join(out_dir, pdf_file.replace('.pdf', '.txt'))

    with pdfplumber.open(pdf_path) as pdf:
        pages_text = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(f"=== PAGE {i+1} ===\n{text}")
        full_text = "\n\n".join(pages_text)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
```

Also extract tables for structured data (classification matrices, competency
tables, coding crosswalks):
```python
tables = []
for i, page in enumerate(pdf.pages):
    for j, table in enumerate(page.extract_tables()):
        tables.append({"page": i+1, "table_index": j, "data": table})
```

Large PDFs (300+ pages) take 30-60 seconds. Run extraction for all PDFs in
a single `execute_code` call for efficiency.

### Phase 3: Framework Understanding

Read the key sections of extracted framework documents before writing scenarios:
- Competency domains, descriptions, and specific competency statements
- Proficiency levels or rating scales
- Clinical categories, classification logic, decision matrices
- Scenario-relevant details (e.g., GG coding rules, IDDSI levels, ROM parameters)

Use `read_file` with `offset`/`limit` to page through large texts. Search for
section markers like "Domains of Competence", "Entrance to Practice
Competencies", or the domain names.

### Phase 4: Knowledge Source Authoring

Build self-contained markdown files. Each knowledge source should have:

**Structure:**
- Version header with date, governing body, framework reference
- Framework overview (the standards/competencies being tested)
- Scenarios in consistent format (see `references/scenario-format-template.md`)
- Summary table (scenario index with category, difficulty, format)

**Build order (dependency-aware):**
1. Gamification scoring rules (independent, defines the game mechanics)
2. Competency matrix (cross-discipline framework — all scenarios reference it)
3. PDPM documentation guide (regulatory grounding)
4. Discipline-specific scenario banks (PT, OT, SLP — parallelizable)
5. Culture/teamwork scenarios (soft skills, independent)

### Phase 5: Parallel Subagent Building

For large projects (3+ banks of 30+ scenarios), dispatch subagents:

```python
delegate_task(tasks=[
    {"goal": "Create PT scenario bank: 35 scenarios...",
     "context": "FULL framework + format template + all 35 required scenario specs..."},
    {"goal": "Create OT scenario bank: 35 scenarios...",
     "context": "FULL framework + format template + all 35 required scenario specs..."},
    {"goal": "Create SLP scenario bank: 35 scenarios...",
     "context": "FULL framework + format template + all 35 required scenario specs..."},
])
```

**Subagent context must be COMPLETE.** Subagents have no access to your
extracted PDFs or session state. Include in context:
- The full governing body framework (all domain names, all competency statements)
- The EXACT scenario format template (not just a description — the template itself)
- The specific list of scenarios to create (titles + domain + difficulty + format)
- The target audience and clinical setting

**Pitfall: Subagent timeout.** Subagents inherit the parent model. If the
parent model is slow at generating large outputs (150KB+), subagents may hit
the 600s timeout with few API calls completed. The transcript will show status
`timeout` with only 2-5 API calls. When this happens:
- Do NOT re-dispatch — the same model will time out again
- Build the timed-out files yourself with `write_file` — you have the full context
- The parent session can produce the complete file in one shot

**Pitfall: Subagent writes to wrong path.** Subagents may write files to
`C:\Users\kevin\` instead of the project directory. After completion,
check the file location and move it to `knowledge-sources/`.

### Phase 6: Publish to GitHub

```bash
cd project-dir
git init
git config user.name "Name"
git config user.email "email@example.com"
# .gitignore: downloaded-pdfs/, extracted-texts/, __pycache__/
git add -A
git commit -m "Initial commit: <project description>"
gh repo create repo-name --public --source=. --remote=origin --push \
  --description "one-line description"
```

Then update README with completion status and push a follow-up commit.

### Phase 7: Gap Handling

Some sources will be inaccessible. Mitigations in priority order:
1. Try alternative URLs on the source organization's site
2. Use newer/updated versions of the same content (search the org's site)
3. Use `web_extract` on the organization's web pages for equivalent content
4. Fill gaps from the user's domain expertise
5. Flag remaining gaps in README with clear "needs manual download" notes

## Pitfalls

- **Conflicting weight-bearing orders in SNF records:** The operative note,
  hospital discharge summary, and SNF admission orders may disagree. Never
  proceed with weight-bearing until the order is clarified with the surgeon.
- **Incapsula on AOTA/association sites:** Curl returns a tiny HTML page with
  Incapsula robot detection. Browser with stealth features usually bypasses.
- **PDFs that aren't PDFs:** Some URLs return HTML error pages with 200 status
  codes. Validate with `pdfplumber.open()` — if it throws "No /Root object",
  the file is not a PDF.
- **Subagent timeout on large outputs:** Slow parent model + 150KB+ output =
  timeout. Build manually rather than re-dispatching.
- **Windows CRLF warnings in git:** Harmless. `git add` normalizes line endings.

### Phase 8: Load into Copilot Studio (if applicable)

If the target is a Copilot Studio agent, load `copilot-studio-knowledge-api`
for programmatic knowledge source creation via Dataverse API. Key constraints:
- Only **PublicSiteSearchSource** (web-crawl to GitHub repo) and SharePoint
  sources are creatable via API — NO file uploads (PDF/MD/DOCX) via API
- File uploads require the Copilot Studio UI file picker
- The gateway publishv2 API is preferred for publishing after knowledge changes

## References

- `references/scenario-format-template.md` — The canonical scenario format
  template with all required fields and an annotated example
- `references/competency-check-gamer-session.md` — Worked example: building
  the 7-file, 136-scenario Competency Check Gamer knowledge base from 15 PDFs,
  plus Dataverse API creation and gateway publish (see `copilot-studio-knowledge-api`)
