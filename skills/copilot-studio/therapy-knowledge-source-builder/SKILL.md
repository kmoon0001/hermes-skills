---
name: therapy-knowledge-source-builder
description: Build structured knowledge source documents for therapy/healthcare AI agents — clinical scenario banks, competency matrices, gamification rules, and regulatory guides. Covers PDF sourcing, scenario formatting, and parallel subagent dispatch for large content generation.
triggers:
  - User asks to build knowledge sources, scenario banks, or competency quiz content for a therapy/healthcare agent
  - User provides a list of source PDFs and scenario topics to create
  - User wants to build a "competency check" or quiz-style agent for PT/OT/SLP
  - User mentions "Copilot Studio knowledge source" + clinical/therapy content
  - User asks to create "competency scenarios" or "clinical quiz questions" at scale
---

# Therapy Knowledge Source Builder

Build structured knowledge source documents for therapy/healthcare AI agents (Copilot Studio, custom GPT, NotebookLM). Covers the full pipeline: source PDF acquisition → text extraction → structured document creation → parallel subagent dispatch for large banks.

---

## 1. Knowledge Source Types

Seven standard knowledge source types for therapy competency agents:

| # | Type | Typical Size | When to Use |
|---|------|-------------|-------------|
| 1 | Clinical Scenarios Bank (PT) | 30-50pp, 30+ scenarios | Discipline-specific quiz content |
| 2 | Clinical Scenarios Bank (OT) | 30-50pp, 30+ scenarios | Discipline-specific quiz content |
| 3 | Clinical Scenarios Bank (SLP) | 30-50pp, 30+ scenarios | Discipline-specific quiz content |
| 4 | Competency Matrix | 10-15pp | Cross-discipline framework mapping |
| 5 | Culture & Teamwork Scenarios | 15-20pp, 15+ scenarios | Soft skills, ethics, communication |
| 6 | Gamification Scoring Rules | 3-5pp | Points, streaks, difficulty, compliments |
| 7 | Regulatory/Documentation Guide | 20-30pp | PDPM, Medicare, billing, compliance |

---

## 2. PDF Acquisition Pipeline

### 2.1 Batch Download with Status Checking

```bash
cd <output_dir> && curl -sL -o "<filename>.pdf" "<url>" -w "%{http_code} %{size_download}" && echo " <- label"
```

**Key checks after each download:**
- HTTP 200 + size > 10KB = valid PDF
- HTTP 200 + size < 1KB = likely HTML redirect/error page (e.g., Incapsula block)
- HTTP 403/404 = blocked or moved

### 2.2 Handling Blocked Content

| Blocker | Signal | Fix |
|---------|--------|-----|
| Incapsula / bot detection | HTML with `<META NAME="robots" CONTENT="noindex,nofollow">` and `<script src="/_Incapsula_Resource...">` | Use `browser_navigate` to open the PDF URL directly. If it loads in the browser PDF viewer (thumbnail tabs, Download button, page counter), click Download. The browser stealth features often bypass Incapsula. |
| Cloudflare challenge | Page title "Just a moment..." with checkbox | Stronger than Incapsula. Cloudflare on academic sites (e.g., SAGE journals for research.aota.org) needs membership. Flag to user — cannot automate. |
| 403 Forbidden | HTTP 403 | Content behind paywall/membership — try web_extract on the article page or find free alternative |
| 404 Not Found | HTTP 404 | URL changed — search for correct URL via web_search. Governing body sites reorganize frequently. IDDSI Framework was 404 at original URL; found current at iddsi.org/resources/framework-documents. APTA CBE 2025 was on a landing page, not direct PDF — found download link on that page. |
| Redirect to HTML | 200 OK but file is not a PDF | Check with `cat` or `head`; look for `<!DOCTYPE` or `<html>`. These are 212-byte Incapsula pages dressed as PDFs. |

**Browser bypass flow (Incapsula-protected PDFs):**
1. `browser_navigate(url="<pdf_url>")` — opens PDF in browser viewer
2. Verify it loaded: thumbnail tabs, page count (e.g. "1 / 15"), toolbar with Download
3. `browser_click(ref="<download_ref>")` — typically `@e13` in the toolbar
4. File goes to browser download directory

**Finding corrected URLs:**
1. When a direct PDF 404s, search the org's resources page
2. IDDSI: canonical page is `iddsi.org/resources/framework-documents`
3. APTA reports: landing page has embedded viewer with actual download link
4. CMS: PDFs at `cms.gov/.../Downloads/<filename>.pdf` — search `site:cms.gov filetype:pdf`

### 2.3 PDF Text Extraction

Use `pdfplumber` (preferred — handles tables well) or `pymupdf`:

```python
import pdfplumber, os, json

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

**Pitfall:** Some PDFs are actually HTML error pages with `.pdf` extension. Check `os.path.getsize() > 10000` before attempting extraction. pdfplumber will throw `No /Root object! - Is this really a PDF?` on HTML files.

---

## 3. Scenario Format Template

Use this exact format for ALL clinical scenarios. Consistency is critical for agent parsing.

```markdown
### Scenario [N]: [Descriptive Title]
**Domain:** [APTA Domain / AOTA Standard / Clinical Area]
**Competency:** [Specific competency code, e.g., PC 4, PR 1] (PT only)
**Difficulty:** [Novice | Moderate | Hard | Expert]
**Format:** [Multiple Choice | Select All That Apply | Free Text | Prioritization | Matching]

**Patient Presentation:**
[2-4 sentences: age, diagnosis, relevant history, current status, SNF setting]

**Scenario:**
[2-4 sentences: specific clinical situation, assessment findings, what needs to be done]

**Question:**
[Clear, specific question — one decision point]

**Options:** (for multiple choice)
A) [Option A — plausible but incorrect when applicable]
B) [Option B]
C) [Option C]
D) [Option D]

**Correct Answer:** [Letter and text]

**Clinical Reasoning:**
[3-5 sentences: WHY correct, citing guidelines/evidence/governing body standards]

**Incorrect Answer Analysis:**
- [Option X]: Why it's wrong / common misconception
- [Option Y]: Why it's wrong
- [Option Z]: Why it's wrong

**SNF Relevance:** [1-2 sentences: why this matters specifically in skilled nursing facility context]
```

### Format Rules

- Every scenario MUST have a "SNF Relevance" line — distinguishes SNF-specific content from general clinical content
- Clinical details must include specific numbers where appropriate (vital signs, ROM degrees, outcome measure scores, distances, weights, assist levels)
- Reference governing body standards in Clinical Reasoning (APTA Domain/Competency, AOTA Standard, ASHA Practice Portal/DCVT)
- Difficulty "Hard" scenarios must have multiple comorbidities, atypical presentations, or ethical dimensions
- Wrong answer options should represent COMMON CLINICAL MISCONCEPTIONS, not random wrong answers

---

## 4. Competency Matrix Structure

When building a cross-discipline competency matrix for SNF:

### 4.1 Domain Mapping

Map all three disciplines to unified SNF practice domains. Standard 8-domain structure:

1. Clinical Reasoning & Evidence-Based Practice
2. Patient Management & Intervention
3. Communication & Interpersonal Skills
4. Documentation
5. Safety, Ethics & Professionalism
6. Education & Teaching
7. Practice Management & Systems
8. Reflective Practice & Professional Development

### 4.2 Matrix Table Format

Each domain gets a table:

```
| # | PT Competency (APTA CBEPT 2025) | OT Competency (AOTA 2021) | SLP Competency (ASHA DCVT) | Proficiency Levels |
|---|-------------------------------|--------------------------|---------------------------|-------------------|
| X.Y | KP 1: [description] | [AOTA equivalent] | [ASHA equivalent] | Novice → Expert |
```

### 4.3 Proficiency Level Definitions

Use consistent definitions across disciplines:
- **Novice:** Entry-level, requires direct supervision, follows protocols
- **Advanced Beginner:** Developing independence, recognizes patterns
- **Competent:** Independent practitioner, manages typical cases
- **Proficient:** Advanced, manages complex cases, serves as resource
- **Expert:** Mastery, intuitive, innovates, teaches others

### 4.4 Key Source Documents

| Discipline | Primary Framework Source |
|-----------|------------------------|
| PT | APTA CBEPT Report 2025: 8 Domains, 54 Competencies, 19 EPAs |
| OT | AOTA 2021 Standards for Continuing Competence: 5 Standards |
| SLP | ASHA Dysphagia Competency Verification Tool (DCVT) + SNF Referral Guidelines |

---

## 5. Gamification Rules Structure

When building gamification scoring rules for a clinical quiz agent:

### Required Sections
1. **Points System** — per-question-type scoring with partial credit rules
2. **Streak Mechanics** — counter, milestones, compliment messages, reset messages
3. **Difficulty Progression** — level triggers, downgrade triggers, per-domain tracking
4. **Narrative & Engagement** — session framing, domain selection, XP/levels/badges
5. **Feedback & Rationale** — correct answer feedback, incorrect answer feedback, "I don't know" feedback
6. **Session Summary** — end-of-session report with domain breakdown, accuracy, suggested next practice
7. **Anti-Frustration Features** — skip option, hint system, review mode, difficulty reset
8. **Research Basis** — cite gamification literature (Singhal 2019, Chou 2012, Buckley 2016, etc.)

### Research Citations to Include
- Singhal et al. (2019) — "Twelve Tips for Incorporating Gamification into Medical Education" (MedEdPublish, PMC10712530)
- Chou (2012) — Octalysis gamification framework
- Gorbanev et al. (2018) — Systematic review of serious games in medical education
- Fontijn & Hoonhout (2007) — Three core sources of fun: accomplishment, discovery, bonding
- Buckley et al. (2016) — Intrinsic vs extrinsic motivation in gamification

---

## 6. Parallel Subagent Dispatch Pattern

For large knowledge source builds (3+ banks of 30+ scenarios each), dispatch subagents in parallel:

### 6.1 When to Dispatch

Dispatch when:
- 3+ independent knowledge sources need creation
- Each source is 30+ pages of original content
- Content is discipline-specific (PT, OT, SLP) and doesn't depend on each other
- You have the framework references extracted and ready

Do NOT dispatch when:
- Sources depend on each other (build sequentially)
- Sources share a common framework that hasn't been built yet (build the framework first, then dispatch)
- Each source is small (< 10 scenarios)

### 6.2 ⚠️ Subagent Timeout Risk (CRITICAL)

**Subagents inherit the parent model.** On slower models (deepseek-v4-pro, some OpenAI models during rate-limiting), subagents can TIME OUT at the 600-second limit before completing 35-scenario documents. This happened in the initial build: 2 of 3 subagents timed out with only 2-5 API calls completed. Each scenario bank is 80-150KB and requires significant generation time.

**Mitigation strategy:**

1. **Prefer building directly** for scenario banks on slower models. The parent agent can write the full file in one `write_file` call (tested: 84KB PT bank = one successful write). This avoids the subagent overhead and timeout risk entirely.

2. **If dispatching subagents:** Only dispatch when the model is fast enough to complete ~150KB of generation within 600 seconds. This typically means models like claude-sonnet-4, gpt-4o, or equivalent. If unsure, build the first bank yourself and time it — if one bank takes >10 minutes, don't dispatch the others.

3. **Fallback when subagents time out:** Don't re-dispatch. Build the timed-out banks directly using `write_file` with the same format template and scenario specifications. This was the successful recovery pattern: the SLP bank completed via subagent (147KB), PT and OT were built directly (82KB and 91KB).

4. **Subagent results check:** Always verify subagent output before trusting it. Check file size (should be >50KB for 35 scenarios), count scenarios (`grep -c "### Scenario"`), and verify format compliance. A subagent that "completed" might have produced partial output.

### 6.3 Context Payload

Each subagent needs in its context:
1. The exact scenario format template (Section 3 above)
2. The complete list of required scenarios with topic descriptions
3. The governing body competency framework for that discipline
4. Format rules and pitfalls
5. Target audience specification

### 6.4 Build Order

1. **First** — Build the Gamification Rules and Competency Matrix yourself (they're smaller and inform everything else)
2. **Then** — Dispatch the scenario banks in parallel OR build them directly if model speed is uncertain
3. **While waiting** — Build the Culture & Teamwork and PDPM documents
4. If subagents time out — build remaining banks directly with `write_file`

---

## 7. Pitfalls

- **Generic scenarios:** Avoid scenarios that could apply to any clinical setting. Every scenario must have SNF-specific details (MDS coding, PDPM implications, Medicare Part A context, interdisciplinary SNF team dynamics).
- **Missing "SNF Relevance" line:** This is the most common omission. Check every scenario before finalizing.
- **Vague clinical data:** "Patient has weakness" → fix: "Patient has R LE strength 3+/5, L LE 4/5, requires CGA for transfers." Use real numbers.
- **Wrong answers that are obvious:** Every distractor should represent a real clinical misconception that practicing therapists actually make. Test: "Would a reasonable clinician choose this?"
- **Over-long patient presentations:** 2-4 sentences max. If you need more, the scenario is too complex — split into two.
- **AOTA content blocked:** AOTA.org uses Incapsula bot protection. Many AOTA PDFs cannot be downloaded via curl. Use browser_navigate to open the PDF URL — the browser stealth features often bypass Incapsula. The AOTA 5 Standards framework is well-documented and can be cited from secondary sources.
- **IDDSI URLs drift:** The URL format changes. The canonical resources page at `iddsi.org/resources/framework-documents` always has current links. Search there first. The original NDD-to-IDDSI guide was superseded by March 2025 "Ease IDDSI Implementation" and "Common Ground Between NDD and IDDSI" guides.
- **APTA CBE Report URL:** The 2025 report with 19 EPAs and 54 competencies is at a landing page (apta.org/.../therapy-essential-outcomes...), not a direct PDF. Find the download link on that page — it's typically `/contentassets/.../cbept-report-2025.pdf`.
- **Subagent timeout on large generation:** Subagents on slower models (deepseek-v4-pro) timed out at 600s on 35-scenario banks (80-150KB output). Only 2-5 API calls completed before timeout. Build large scenario banks directly via `write_file` on these models rather than dispatching subagents. See Section 6.2 for full mitigation strategy.
- **PDF extraction performance:** pdfplumber extraction of large PDFs (186-308 pages) can take 60-175 seconds per file. The CMS Benefit Policy Manual (308pp, 1.7MB) took 175s. Plan for this — extract in batches and let the user know it's working.
- **PDFs that are actually HTML:** Files with `.pdf` extension but <1KB size are almost certainly HTML error pages. Check with `cat` before attempting pdfplumber extraction. pdfplumber throws `No /Root object! - Is this really a PDF?` on HTML files.
- **Subagent output verification:** Never trust subagent output without checking. After a subagent "completes": verify file size (>50KB for 35 scenarios), count scenarios (`grep -c "### Scenario"`), and spot-check format compliance (every scenario has Patient Presentation, Question, Options/Correct Answer, Clinical Reasoning, Incorrect Answer Analysis, SNF Relevance). A subagent that reports "completed" may have produced truncated or malformed output.

---

## 8. Verification Checklist

Before declaring a knowledge source complete:

- [ ] Every scenario has all required sections (Patient Presentation through SNF Relevance)
- [ ] Clinical reasoning cites a governing body standard (APTA/AOTA/ASHA)
- [ ] Wrong answers include analysis of WHY they're wrong
- [ ] Difficulty levels are consistent (Hard has comorbidities/atypical/ethical dimensions)
- [ ] Numbers and measurements are specific and realistic
- [ ] No scenario could be copy-pasted to a different clinical setting without modification
- [ ] File size is appropriate for the type (see Section 1 size ranges)
- [ ] Cross-references between knowledge sources are consistent (matrix domain names match scenario domain tags)

---

## References

- `references/scenario-format-template.md` — Copy-paste template for clinical scenarios
- `references/snf-competency-domains.md` — The 8 SNF practice domains with discipline mappings
