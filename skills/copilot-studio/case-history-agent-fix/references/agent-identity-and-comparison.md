# Case History family — identity + comparison (Therapy AI Agents Dev)

Env: `orgbd048f00` / Therapy AI Agents Dev. Live snapshot validated 2026-07-16/17.

## Quick pick

| User intent | Use this bot |
|-------------|--------------|
| SNF therapy **initial eval prep** from acute chart; PT/OT/SLP lenses; scannable full report | **Pacific Coast Case History Reviewing Agent** `f19e1c40` |
| Hospital-stay **chronology**, intake dump, short timeline bullets | **Case_History_Assistant** `aed96eb7` |
| Longitudinal SBAR / MDS / PDPM / IDT / fleet connected agents | **Pacific Coast Case Historian V2** `ad635500` |

## Side-by-side: Assistant vs Reviewing Agent

| Dimension | Case_History_Assistant | Pacific Coast Case History Reviewing Agent |
|-----------|------------------------|---------------------------------------------|
| Bot ID | `aed96eb7-dd80-f111-ab0e-70a8a59d4e65` | `f19e1c40-f07e-f111-ab0e-70a8a5b24e56` |
| Schema | `cr917_CaseHistoryAssistant` | `cr917_CaseHistoryReviewingAgent` |
| Type-15 | `568d5ddd-…` | `cc349f24-…` |
| Mission | Longitudinal timeline + intake/admission collection + synthesis | Acute→SNF **therapy eval prep** analyst |
| Audience | General clinical documentation workflow | Licensed PT / OT / SLP evaluating therapists |
| Instructions size | ~3.5K body; **no** `responseInstructions` | ~5.5–6K body + RI ~500 (must stay aligned) |
| Default format | 2–3 bullets, &lt;800 chars, **no headers/markdown** | Friendly scannable markdown; 11-section report |
| Full structure | Only when user says full report / complete summary | Default full case-history shape with Timeline + separate PT/OT/SLP |
| Citations | Inline by document name; ban `[1]` style | `[Source — Date — value]`; passage course-phase + follow-up |
| Discipline lens | None | Mandatory PT / OT / SLP Insight + Significance |
| Regulatory | Thin / general | CMS MBPM Ch.15, Jimmo, 42 CFR 483, APTA/AOTA/ASHA |
| Model hint (live) | GPT55Chat | GPT5Chat |
| Auth | Integrated; Sign-in **active** | Integrated; Sign-in **inactive** |
| Fallback | Apology only — **no SASC** | SASC + files + KBs + show answer + clearTopicQueue |
| Conv boosting | SASC present; often missing SendActivity of answer | SASC + SendActivity + clearTopicQueue |
| Custom clinical topics | Case History Collection; Hospital Stay Timeline; Timeline Synthesis | Clinical Analysis; Document Intake; Multi-Discipline Summary; Clinical Safety Boundaries |
| Intake | File upload Question (FilePrebuiltEntity) early | Document Intake: paste &gt;100 chars → Clinical Analysis; else upload/paste |
| Knowledge | Thin SSKS; no type-14/16 packs observed | 16 files (type 14) + Core Clinical Manuals + Therapy Shared Knowledge (type 16) |
| Clinical Analysis / collection | applyModelKnowledge false on collection; DoNotSearchFiles | Clinical Analysis: applyModelKnowledge **false** + SearchSpecificFiles (do not flip — -11pp regression) |
| Eval cases (approx) | ~200 — timeline/meds/demographics/compile | ~320 — therapy-heavy (diet texture, anticoagulants, fall risk, WB, swallow, etc.) |
| Safety footer | AI-generated analysis — clinical professional review… | DRAFT — CLINICAL REVIEW REQUIRED + ONC HTI-1 |

## Similarities (both Assistant + Reviewing)

- Same env; Integrated auth; web browsing OFF; code interpreter OFF
- Documentation analysis tools — not note writers / not diagnose-treat engines
- Extract clinical history from records via SearchAndSummarizeContent patterns
- Human-in-the-loop disclaimers
- Catch-all quality (Fallback/ConvBoost) dominates eval more than niche matched topics

## Case Historian V2 (third bot — do not merge)

| Field | Value |
|-------|--------|
| Bot ID | `ad635500-cf47-f111-bec5-70a8a5b1c3a3` |
| Schema | `auto_agent_XRF5I` |
| Role | Fleet longitudinal documentation: SBAR, MDS 3.0, PDPM, multi-discipline, denial risk |
| Architecture | Many audit topics + connected agents (QM Coach, TheraDoc, Dashboard, Command Center) |
| Pipeline ref | `copilot-studio-pipeline/references/pacific-coast-case-historian-v2.md` |

## Fix-protocol applicability

- **Reviewing Agent**: full skill steps (Fallback, ConvBoost, clearTopicQueue, leave Clinical Analysis alone).
- **Case_History_Assistant**: same **catch-all class** applies (apology Fallback = highest-impact fix). Do **not** copy Reviewing Agent 11-section therapy report without an explicit product decision — Assistant’s instructions intentionally default to short non-markdown bullets and PHI-redaction posture.
- **Case Historian V2**: different skill surface (fleet topics + connected agents); use pipeline/historian refs, not this skill’s Clinical Analysis rules blindly.

## Disambiguation traps

1. User voice: “Pacific Coast case history assistant” often means **Reviewing Agent** (`f19e1c40`), not `Case_History_Assistant`.
2. “PCCH” historically maps to **Case Historian** (`ad635500`), not Reviewing Agent.
3. Always resolve by **botid** from Dataverse, not display nickname alone.
