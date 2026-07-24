# Topic 800-Character Limit Fix

**Pattern:** Topics with `Keep response under 800 characters.` in `additionalInstructions` cause conversation failures.

## Root Cause

Unenforceable character limits (`"Keep response under 800 characters."`, `"Max 800 characters per section"`) force the model to truncate or produce incomplete responses. Since the model cannot reliably count characters, this introduces non-deterministic truncation. The grader penalizes responses that are incomplete or lack supporting detail.

## Evidence (June 14, 2026)

- SLP Conv dropped 90% → 85% when 3 topics had `Keep response under 800 characters.`
- Removing the limit from "Analyze SLP Evaluation Report" fixed the "refuses to help" failure for that specific topic (was Fail → Pass)
- BUT 3 OTHER topics (Daily Therapy Note, Progress Note x2) still had the 800-char limit and continued failing
- OT SR jumped 90% → 98% when instruction-level unenforceable limits were removed

## Fix Procedure

**⚠️ CRITICAL: Do NOT replace the entire topic YAML with a template-export version.** Template exports may be days/weeks old and lack trigger query and modelDescription updates added since export. Replacing the full YAML can cause 7%+ score regression (evidenced June 16, 2026: OT/PT SR 94% → 87-88%).

**Correct approach — surgical line deletion only:**

For each topic that has `Keep response under 800 characters.` in `additionalInstructions`:

1. Open the topic → More → Open code editor
2. **Find the SINGLE line** containing `Keep response under 800 characters.` or `Max 800 characters`
3. **Delete only that line** — do NOT change anything else in the YAML
4. Optionally, add a replacement line: `Be concise but complete — prioritize accuracy and actionable findings over strict length limits.`
5. Type one character at the end + Backspace (triggers React dirty state)
6. Click Save

**Topics to ALWAYS scan (all agents):**
- All `Analyze *` audit topics (Evaluation, Daily Note, Progress Note, Recertification, Discharge)
- **Conversational boosting (CB) topic** — handles ALL unmatched queries; its 800-char limit affects every topic fall-through
- Insurance Denial Risk / General Knowledge / Clinical Standards topics
- Caregiver Competency topics

**CB topic note:** The CB topic is frequently overlooked during batch fixes because it's a system topic (OnUnknownIntent). Its 800-char limit affects all questions that don't match specific topics — this is typically the majority of general-knowledge questions in SR test sets.

## Topics to Scan (SLP_Specialist, June 14)

From the SLP Conv 85% run (17/20 pass, 3 fail):
- Analyze SLP Daily Therapy Note — had `Keep response under 800 characters per section.` AND `Max 800 characters per section. Total response max 2400 chars.`
- Analyze SLP Evaluation Report — had `Keep response under 800 characters.` (removed June 14, and that topic changed from Fail → Pass)
- Analyze SLP Progress Note — was clean (no 800 limit)

Other topics in the SLP agent that should be checked:
- Analyze SLP Discharge Summary
- Analyze SLP Recertification Note
- Dysphagia Analysis Audit
- General SLP Clinical Inquiry

## Verification

After fixing, publish the agent and trigger a new conversation evaluation. The 800-char limit fix alone can recover 5-15% on conversation scores when multiple topics are affected.
