---
name: knowledge-source-library-build
description: Build complete Copilot Studio knowledge source libraries from authoritative source documents — PDF download, text extraction, structured markdown authoring, upload manifest creation, and publish. Proven on healthcare competency agents (PT/OT/SLP). Covers the hybrid approach (authoritative PDFs + curated scenario banks), file structure, scenario format, subagent timeout pitfall, and computer-use patterns.
category: copilot-studio
---

# Knowledge Source Library Build

Build a complete knowledge source library for a Copilot Studio agent from authoritative source documents. Proven end-to-end on healthcare therapy competency agents.

## When to Use

- Building knowledge sources for a new agent that needs grounding in professional/regulatory standards
- Converting governing body PDFs into structured, agent-consumable markdown
- Creating scenario-based quiz/practice content alongside reference material
- Any domain where you have both authoritative source documents AND need curated educational content

## The Hybrid Approach

**Download authoritative PDFs for grounding AND create curated scenario banks.** This gives the agent both context (from governing body documents) and structured content (from curated scenarios).

### Phase 1: Source PDF Collection

Download from governing bodies. Try curl first; fall back to browser for Incapsula/Cloudflare-protected sites.

**Extract text** with `pdfplumber` (primary) or `pymupdf` (fallback):
```python
import pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
```

### Phase 2: Knowledge Source File Structure

Build these files for a complete competency agent:

| # | File | Content | Target Size |
|---|------|---------|-------------|
| 1-3 | Discipline scenario banks (×3) | 35 scenarios each with clinical reasoning, incorrect analysis, SNF relevance | 80-150KB |
| 4 | Cross-discipline competency matrix | Governing body standards mapped to practice domains | 20-35KB |
| 5 | Culture/teamwork scenarios | 15-20 interdisciplinary ethics/communication scenarios | 35-40KB |
| 6 | Gamification/scoring rules | Points system, streaks, difficulty progression, session format | 10-15KB |
| 7 | Regulatory documentation guide | Classification, compliance, audit reference with scenarios | 30-35KB |

### Scenario Format (mandatory fields)

Every scenario must include:
- Domain, competency code, difficulty, format
- Patient presentation (2-4 sentences)
- Scenario (2-4 sentences)
- Question
- Options (for MC)
- Correct answer with clinical reasoning (3-5 sentences citing standards)
- Incorrect answer analysis (why each wrong answer is wrong)
- SNF/domain relevance line

### Phase 3: Building Large Files

**PITFALL: Subagent timeout.** `delegate_task` subagents time out at 600s when generating 100KB+ scenario files using slower models. Only 1 of 3 completed when building 35-scenario banks.

**Fix:** Build large files directly via `write_file` rather than delegating to subagents. For files over 80KB, build each directly in sequence. Reserve subagents for smaller tasks (<30KB output) or with faster models.

### Phase 4: Upload Manifest

Create `UPLOAD-MANIFEST.md` with a table:

| # | File | Display Name | Description |
|---|------|-------------|-------------|
| 1 | filename.md | Clean Human-Readable Name | 1-2 sentence description with specific retrieval terms |

Upload order: framework/matrix first → scoring/rules → regulatory guide → scenario banks → culture/teamwork last.

### Phase 5: Publishing

1. **GitHub:** Push knowledge sources only (gitignore PDFs and extracts). Clean repo with README.
2. **Copilot Studio UI:** Knowledge file uploads require the UI — no Dataverse API exists for uploading file bytes. Path: Agent → Knowledge → Add knowledge → Upload files. For each: paste Display Name + Description from manifest, toggle Official source ON, Save, verify "Ready."
3. **Publish agent:** After all files show "Ready," publish via UI button or `pac copilot publish --bot <botId>`.

## Computer Use for Copilot Studio

When trying to drive Copilot Studio via Windows desktop automation:

- **Chrome address bar:** `set_value` fails (no ValuePattern). Use foreground `click` + `type_text` with pixel coordinates. Chromium may still drop keystrokes.
- **Page content:** Copilot Studio page content often doesn't appear in UIA AX tree — only Chrome chrome (toolbar, bookmarks). Use `max_elements` to increase capture depth.
- **MCP tools** (`mcp__cua_driver__*`) are more reliable than `computer_use` for Windows. Use `get_accessibility_tree` → `get_window_state` → act by element index.
- **Better approach:** Open the agent URL and provide the upload manifest with copy-paste names/descriptions. The actual file upload through the file picker dialog is too unreliable via automation.

## Reference Files

- `references/healthcare-competency-kb-build-example.md` — Worked example: Pacific Coast Competency Check Gamer Agent (PT/OT/SLP therapy competency quiz agent). Full file inventory, manifest, and scenario counts.
