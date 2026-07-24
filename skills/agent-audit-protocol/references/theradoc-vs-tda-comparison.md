# TheraDoc Workbench vs Therapy Documentation Assistant — Comparison

## Agents Compared

| Agent | Bot ID | Purpose |
|-------|--------|---------|
| **TheraDoc Workbench** | `e09954e1-4af8-47c6-8ef4-d1d9335bf2e6` | Post-session PT/OT/SLP documentation (AI generates polished note from card-based intake) |
| **Therapy Documentation Assistant** | `f5a9bca6-c07d-f111-ab0e-0022480b04f7` | Therapy note generation via free-text Q&A |
| **TheraDoc (standalone)** | `855c7dda-ad19-4734-a8cd-df366c48f3d2` | IsDefault=True — primary published source |

## Architecture Comparison

| Dimension | TheraDoc Workbench | Therapy Doc Assistant | Winner |
|-----------|-------------------|---------------------|--------|
| **Input method** | 20 AdaptiveCards with button clicks + 56 ChoiceSet dropdowns | 85 free-text Question nodes — user types everything | **TheraDoc** |
| **Topic count** | 33 | 27 | **TheraDoc** |
| **SASC nodes** | 22 | 16 | **TheraDoc** |
| **Test coverage** | 210 eval cases | 100 | **TheraDoc** |
| **KB files** | 21 | 13 | **TheraDoc** |
| **SharePoint sources** | 2 | 2 | Tie |
| **Flow automation (OCR)** | 2 InvokeFlowAction | 0 | **TheraDoc** |
| **Braindump (free-text→note)** | Parse Brain Dump flow + NetHealth Narrative KB | None | **TheraDoc** |
| **clearTopicQueue rate** | 96% (22/23) | 94% (17/18) | Tie |
| **CPT codes** | 97110, 97112, 97530, 97535, 97542 | Same + 97116, 97140 | **TDA** (has 2 more) |
| **SLP CPT codes (92521-92526)** | Missing | Missing | Tie |
| **ICD-10 codes** | Missing | Missing | Tie |
| **CMS grounding** | 130 CMS references + 54 Ch15 + 39 Jimmo | 26 CMS + 8 Ch15 + 4 Jimmo | **TheraDoc** (5x deeper) |
| **APTA/AOTA/ASHA** | 7/5/5 | 11/6/6 | Tie (slightly TDA) |
| **NetHealth references** | 8 | 4 | **TheraDoc** |
| **SOAP structure** | Strong (169 refs) | Weak (82 refs) | **TheraDoc** |
| **Plan of Care refs** | 49 | 1 | **TheraDoc** |
| **Duration/frequency refs** | 70 | 3 | **TheraDoc** |

## TheraDoc Strengths
- **Card-based intake** — clinicians click buttons, AI generates note. 20 cards with 118 text inputs + 56 dropdowns + 8 toggles.
- **Discipline-specific workflows** — 6 topic sets per discipline (PT/OT/SLP): Daily Note, Evaluation, Progress, Recert, Discharge, Treatment Encounter.
- **Braindump feature** — dedicated Power Automate flow (`TheraDoc - Parse Brain Dump`) + NetHealth Narrative Format KB. Clinicians type freely, AI structures the note.
- **Knowledge sources** — 33 KBs including CMS manuals, AOTA/APTA/ASHA standards, NetHealth guide, PDPM documentation, audit triggers.
- **Entity KBs** — 8 picklist entities: Discipline, Pain Scale, Note Type, Diet Texture, Sets/Reps, Assist Level, Rest Period, Walking Distance.
- **Deep CMS grounding** — 130 CMS references, 54 Chapter 15, 39 Jimmo.

## TDA Strengths
- **CPT code ClosedListEntity** — has 97116 Gait Training and 97140 Manual Therapy as named options (TheraDoc missing these).
- **Governing body mentions** — slightly more APTA/AOTA/ASHA (11/6/6 vs 7/5/5).
- **Slightly lower complexity** — fewer topics, fewer SASC, easier to understand.

## Verdict
TheraDoc Workbench is significantly more developed and mature. The TDA's one useful contribution is the CPT code ClosedListEntity — specifically **97116 Gait Training** and **97140 Manual Therapy** — which should be added to TheraDoc's dropdowns.

## TheraDoc Publish Blockers (as of 2026-07-16)

| Status | Issue | Details |
|--------|-------|---------|
| ✅ Fixed | responseCaptureType | 22/22 SASC nodes patched |
| ✅ Fixed | "under 4 sentences" | Removed from instructions |
| ✅ Fixed | AuditExistingNote | Replaced BeginDialog refs (removed from 20 topics) |
| ✅ Fixed | WelcomeStart | Redirected to ConversationStart |
| ✅ Fixed | ComplianceAuditV2 | Activated (was Inactive) |
| ✅ Fixed | InvokeFlowAction→InvokeConnectedAction | Reverted/removed from 2 topics |
| ✅ Fixed | SASC variable: missing | Added `variable: Topic.Answer` to 22 SASC |
| ❌ Remaining | Output binding errors (MPC_* fields) | Master Patient Context topic has 50+ output bindings not matching destination flow |

## Environment
- Therapy AI Agents Dev: `https://orgbd048f00.crm.dynamics.com/`
- Bot: `e09954e1-4af8-47c6-8ef4-d1d9335bf2e6`
- Gateway env: `a944fdf0-0d2e-e14d-8a73-0f5ffae23315`
- Tenant: `03cc92c3-986c-4cf4-ae27-1478cf99d17f`
