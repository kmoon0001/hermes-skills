# Worked Example: Pacific Coast Competency Check Gamer Agent

**Built:** July 2025  
**Domain:** SNF therapy competency gamification (PT, OT, SLP)  
**GitHub:** `kmoon0001/competency-check-gamer`

## Source PDFs Collected

15 authoritative PDFs downloaded from APTA, ASHA, CMS, IDDSI, and Leading Age. Extracted ~2.5M characters of text.

| Source | Pages | Status |
|--------|-------|--------|
| APTA Core Competencies of PT Resident (2020) | 28 | ✅ |
| APTA CPI 3.0 to CAPTE 2024 Crosswalk | 2 | ✅ |
| APTA CBEPT Report 2025 (19 EPAs, 54 competencies) | 139 | ✅ |
| ASHA Dysphagia Competency Verification Tool | 23 | ✅ |
| ASHA SNF Referral Guidelines for SLP | 2 | ✅ |
| ASHA Dysphagia Services Fact Sheet | 2 | ✅ |
| IDDSI Framework Evidence Statement | 12 | ✅ |
| CMS PDPM Classification Walkthrough v2 | 38 | ✅ |
| CMS PDPM Technical Report | 186 | ✅ |
| CMS PDPM Overview Presentation | 92 | ✅ |
| CMS Medicare Benefit Policy Manual Ch.15 | 308 | ✅ |
| Leading Age PDPM FAQ | 36 | ✅ |
| AOTA Continuing Competence (Incapsula block) | - | ❌ Browser bypassed |
| AOTA Standards of Practice (Cloudflare) | - | ❌ Requires membership |
| AOTA CBE Task Force (Incapsula block) | - | ❌ Browser bypassed |

## Knowledge Sources Built

7 files, 436KB total, 136 clinical scenarios:

| File | Size | Scenarios | Content |
|------|------|-----------|---------|
| `01_pt_clinical_scenarios.md` | 82KB | 35 | PT: Clinical Reasoning (8), Patient Mgmt (8), Documentation (7), Safety/Ethics (6), Communication (6) |
| `02_ot_clinical_scenarios.md` | 90KB | 35 | OT: ADL (10), IADL (8), Cognitive Rehab (6), Splinting/UE (5), Discharge (6) |
| `03_slp_clinical_scenarios.md` | 147KB | 35 | SLP: Dysphagia (12), Cognitive-Linguistic (8), Aphasia/Motor Speech (6), Voice (3), Documentation (6) |
| `04_snf_competency_matrix.md` | 22KB | - | 8 domains × 3 disciplines with proficiency levels |
| `05_culture_teamwork_scenarios.md` | 36KB | 20 | Ethics, conflict, handoff, cultural competency, leadership |
| `06_gamification_scoring_rules.md` | 12KB | - | Points system, streaks, difficulty progression, session summaries |
| `07_pdpm_documentation_guide.md` | 33KB | 11 | PDPM classification, skilled service, audits |

## Subagent Performance

- **SLP bank (subagent):** Completed in 515s, 5 API calls, 150KB output ✅
- **PT bank (subagent):** Timed out at 600s, 2 API calls — stuck on slow model ⏱️
- **OT bank (subagent):** Timed out at 600s, 5 API calls — stuck on slow model ⏱️
- **PT bank (direct build):** Built directly via `write_file` — 84KB in one shot ✅
- **OT bank (direct build):** Built directly via `write_file` — 91KB in one shot ✅

**Lesson:** For files over 80KB, `write_file` directly is more reliable than `delegate_task` with slower models.

## Upload Manifest

Created `UPLOAD-MANIFEST.md` with copy-paste display names and descriptions for all 7 files. Upload order: matrix → scoring → PDPM → PT → OT → SLP → culture.

## Agent

Copilot Studio agent: "Pacific Coast Competency Check Gamer Agent"  
Environment: `a944fdf0-0d2e-e14d-8a73-0f5ffae23315`  
Bot ID: `7667e9b4-cb86-f111-ab0f-70a8a5ae56f8`
