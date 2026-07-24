# Post-migration audit: Documentation Defense → Therapy AI Dev

Validated 2026-07-16 Pacific.

## IDs

| | Value |
|--|--|
| Source env | PCCA Package `pccapackage.crm.dynamics.com` |
| Source botid | `9e7b871d-1d80-f111-ab0f-000d3a5b0d6c` |
| Target env | Therapy AI Agents Dev `orgbd048f00.crm.dynamics.com` |
| Target botid | `2e08ac68-bdef-481e-9c04-6a349c79d6c0` |
| Schema | `crbee_PacCoastDocumentationDefenseAgent` |
| Transport solution | `DocDefenseTransport` unmanaged |

## Inventory after import

- Topics 21 · FileKB 14 · Instructions 1 · type 19 evals present
- Sync: Provisioned + Synchronized after explicit publish (~10:45 PM Pacific)

## First-pass P0/P1 (audit protocol)

**P0**
- `modelNameHint: GPT55Chat` → fix to GPT5Chat
- Fallback: no SASC
- All 5 SASC missing `responseCaptureType: FullResponse` (Audit topic, Medicare Q, MAC Appeal, Managed Care Contract, Conversational boosting)
- Hollow: Thank you
- Several system topics missing EndDialog

**P1**
- `responseInstructions` effectively empty (len ~1)
- Missing modelDescription on many custom topics
- Weak auto-desc on Part B LCR PDF KB
- Soft "use only approved knowledge sources" → abstention risk

**Already good**
- Mission + EVALUATION CONTEXT present
- Core audit topics have SASC + EndDialog + clearTopicQueue
- No `file[]` / `turn.uploadedFiles`
- Strong CMS KB set (Ch.15, Jimmo, 42 CFR, PDPM, LCR, MAC LCD)

## Hermes skills to apply next

| Gap | Skill / pattern |
|-----|-----------------|
| Fallback SASC | agent-audit-protocol D8 + case-history-agent-fix catch-all pattern |
| responseCaptureType bulk | Pattern A |
| Instructions + Responses | copilot-studio-agent-instructions |
| Eval after fixes | eval-optimization-loop |

## Local artifacts

`C:\Users\kevin\Desktop\docdef_migrate\` — zip, audit_report.json, audit_docdef.py, live_instructions.txt
