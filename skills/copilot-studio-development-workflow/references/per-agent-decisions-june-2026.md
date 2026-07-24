# Per-Agent Decisions — June 10, 2026 Session

## OT_Specialist

| Decision | Value | Evidence |
|----------|-------|----------|
| RESPONSE FORMAT | Conditional ("for full audits only") | Mixed test set (general + audit). Unconditional crashed conv 85%→55%. |
| "Allow ungrounded" | ON | OFF crashed conv 50%→10%→5%. |
| Guard topics | **DELETED** | Hardcoded record_ids (e.g., "12345") in responses conflict with evaluation varied IDs (OT13579, OT22334). All ON: 55%. Partial ON: 60%. All OFF: 25% (no structured intake). DELETED all 12 per user direction Jun 10. |
| Citation rules | Soft ("when applicable") | Strict "ALWAYS cite in EVERY response" combined with Allow Ungrounded OFF crashed to 10%. |
| Topic bloat | Reduce 200+ → 20 | 200+ duplicate question-phrase topics (each matching an eval test question) created routing chaos. Deleted all duplicates, kept 12 named topics + 8 system topics. |
| Instructions version | v9 | Conditional format + soft citations + no anti-patterns |

## SLP_Specialist

| Decision | Value | Evidence |
|----------|-------|----------|
| RESPONSE FORMAT | Unconditional ("Always use") | Test set is 100% audit questions. Conditional dropped SR 95%→87%. |
| "Allow ungrounded" | ON | OFF dropped SR 95%→86% and Conv 95%→70%. |
| Classification line | "SLP vs SLPA scope" | Was "OTR vs COTA scope" (copy-paste from OT template). Fixed Jun 10. |
| Guard topics | N/A | No guard topics on SLP. |

## PT_Specialist

| Decision | Value | Evidence |
|----------|-------|----------|
| RESPONSE FORMAT | Conditional ("for full audits only") | Mixed test set. Unconditional dropped conv 90%→80%. |
| "Allow ungrounded" | ON | Already ON. |
| Classification line | "PT vs PTA scope" | Was "OTR vs COTA scope" (copy-paste from OT template). Fixed Jun 10. |
| Guard topics | OFF | Conv at 95-100% without them. Kiro assessment correct: "overdoing topics." |

## TDA (Therapy Documentation Audit)

| Decision | Value | Evidence |
|----------|-------|----------|
| Evaluation type | Single-response (100 cases) + Conversation (20 cases) | Two separate test sets |
| Single-response peak | 96% (Jun 10 1:36 AM) | Before instructions were added |
| Single-response regression | 96% → 91% → 86% → 87% | Degradation after short instructions added |
| Conversation | Stable at 95% | Unaffected by single-response regression |
| \"Allow ungrounded\" | ON | Needed for free-text document audit against guidelines |
| Deep reasoning | ON | Premium feature enabled |
| Response formatting | EMPTY (0/500) | ROOT CAUSE of single-response regression |
| Instructions (old) | 378 chars, jargon-heavy | "XAI rationale", "HITL" — too short, too technical |
| Instructions (new) | 1185 chars, structured format | RISK LEVEL → FINDINGS → RATIONALE → RECOMMENDATIONS → CONFIDENCE |
| Response formatting (new) | Bullet-point rules with risk level bolding | Pending manual entry (textarea not accessible via CDP) |
| Root cause | Instructions too short + no formatting rules + deep reasoning ON = inconsistent single-response output | Model had no output structure guidance for single-response evaluation |
| Instructions anti-patterns to avoid | "XAI", "HITL", "returns sourced" without structure template | Write in full plain English, provide explicit output templates |
| See also | `references/single-response-quality-optimization.md` |
