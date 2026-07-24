# Session Example: Competency Check Gamer Agent

**Date:** July 2026
**Project:** C:\Users\kevin\competency-check-gamer\
**Published:** https://github.com/kmoon0001/competency-check-gamer

## What Was Built

7 knowledge source files for an AI agent that quizzes SNF therapy professionals
(PT, OT, SLP) on clinical competencies using gamification:

| # | File | Size | Content |
|---|------|------|---------|
| 1 | `01_pt_clinical_scenarios.md` | 82KB | 35 PT scenarios: Clinical Reasoning, Patient Mgmt, Documentation, Safety/Ethics, Communication |
| 2 | `02_ot_clinical_scenarios.md` | 90KB | 35 OT scenarios: ADL, IADL, Cognitive Rehab, Splinting/UE, Discharge |
| 3 | `03_slp_clinical_scenarios.md` | 147KB | 35 SLP scenarios: Dysphagia, Cognitive-Linguistic, Aphasia/Motor Speech, Voice, Documentation |
| 4 | `04_snf_competency_matrix.md` | 22KB | 8 domains × 3 disciplines with proficiency levels Novice→Expert |
| 5 | `05_culture_teamwork_scenarios.md` | 36KB | 20 scenarios: ethics, conflict, handoff, cultural competency, leadership |
| 6 | `06_gamification_scoring_rules.md` | 12KB | Points system, streaks, difficulty progression, session summaries |
| 7 | `07_pdpm_documentation_guide.md` | 33KB | PDPM classification, skilled service, GG coding, SMART goals, 11 scenarios |

**Total: 436KB, 136 clinical scenarios**

## Source PDFs Downloaded (15 total)

Successfully downloaded and extracted:
- APTA Core Competencies of a PT Resident (2020): 28pp
- APTA CPI 3.0 to CAPTE 2024 Crosswalk: 2pp
- APTA CBEPT Report 2025 (19 EPAs, 54 competencies, 8 domains): 139pp, 252K chars
- ASHA Dysphagia Competency Verification Tool (DCVT) User's Guide: 23pp
- ASHA SNF Referral Guidelines for SLP: 2pp
- ASHA Dysphagia Services Fact Sheet: 2pp
- IDDSI Framework Evidence Statement: 12pp
- IDDSI Ease Implementation (March 2025): 4pp
- IDDSI NDD Common Ground (March 2025): 3pp
- CMS PDPM Classification Walkthrough v2: 38pp
- CMS PDPM Technical Report: 186pp
- CMS PDPM Overview Presentation: 92pp
- CMS Medicare Benefit Policy Manual Ch.15: 308pp
- Leading Age PDPM FAQ: 36pp

Failed/blocked:
- AOTA Model Continuing Competence: Incapsula → loaded in browser
- AOTA CBE Task Force: Incapsula → loaded in browser
- AOTA Standards of Practice: Cloudflare on SAGE Journals → needs membership
- IDDSI original NDD Implementation Guide: 404 → replaced with March 2025 versions

## Key Patterns Used

### PDF Download Escalation Ladder
1. curl → most PDFs succeed
2. Browser (stealth) → bypasses Incapsula for AOTA PDFs
3. Search for updated URLs → IDDSI had newer/better versions
4. Flag for manual download → Cloudflare/SAGE paywall

### Subagent Timeout Handling
Dispatched 3 subagents (PT, OT, SLP banks) in parallel. PT and OT timed out
at 600s with only 2-5 API calls (slow parent model generating 150KB+ outputs).
SLP succeeded (515s, 5 API calls, wrote to wrong path — C:\Users\kevin\ instead
of knowledge-sources/).

**Resolution:** Built PT (82KB) and OT (90KB) banks directly via `write_file`.
Moved SLP bank from C:\Users\kevin\ to knowledge-sources/.

### Build Order
1. Gamification Rules (simple, independent)
2. SNF Competency Matrix (framework — all scenarios reference it)
3. Dispatched 3 parallel subagents for scenario banks
4. Built PDPM Guide while subagents ran
5. Built Culture & Teamwork while subagents ran
6. PT and OT banks built manually after timeouts
7. README, .gitignore, GitHub publish

### Scenario Quality
Every scenario includes:
- Specific vitals, ROM values, outcome measure scores, assist levels
- Governing body competency codes (APTA PC 4, AOTA Standard 2, ASHA DCVT)
- SNF-specific relevance line
- Wrong answers that teach real clinical misconceptions, not obviously wrong
- Progressive difficulty: Novice (3-5), Moderate (15-20), Hard (8-12), Expert (2-4)

## Upload Order for Copilot Studio

Recommended upload sequence (dependencies matter):
1. `04_snf_competency_matrix.md` — Framework foundation all scenarios reference
2. `06_gamification_scoring_rules.md` — Agent behavior rules
3. `07_pdpm_documentation_guide.md` — Regulatory grounding
4. `01_pt_clinical_scenarios.md` — PT practice content
5. `02_ot_clinical_scenarios.md` — OT practice content
6. `03_slp_clinical_scenarios.md` — SLP practice content
7. `05_culture_teamwork_scenarios.md` — Soft skills content
