# Aggressive Language = Regression Evidence (June 16-17, 2026)

## The Pattern

Any instruction containing ALL-CAPS enforcement words (CRITICAL, MANDATORY, NEVER, ALWAYS) or grader threats ("The grader will FAIL") causes 5%+ regression.

## Evidence Table

| Agent | Date | Aggressive Phrase | Score Before | Score After | Δ |
|-------|------|-------------------|-------------|-------------|---|
| PT | Jun 17 | "CRITICAL: NEVER use numbered citations like cite:1, Citation-1, [1]: cite:1, or [1][2][3]. Always cite... The grader will FAIL responses using numbered citations." | 90% Conv | 85% Conv | -5% |
| PT | Jun 17 | "MANDATORY — when asked about caregiver education or competency, ALWAYS include ALL of: ... Do not skip any element." | 90% Conv | 85% Conv | -5% |
| SLP | Jun 16 | "Write as if you have the document in front of you." | 94% SR | 91% SR | -3% |
| PT | Jun 17 | Stacking: CRITICAL citation + MANDATORY caregiver + removed conciseness | 85% Conv | 80% Conv | -5% |

## Root Cause

Per MS Learn: "The system treats agent instructions similar to code. The wrong code might break your system." Aggressive language causes the model to overcorrect — it either:
1. Avoids the behavior entirely (drops all citations when told "CRITICAL: NEVER cite:1"), OR
2. Fabricates to comply ("write as if you have the document" → makes up scores)

## Safe Language Templates

| Context | ❌ Aggressive (Regression) | ✅ Safe (Proven) |
|---------|--------------------------|-------------------|
| Citations | "CRITICAL: NEVER use numbered citations like cite:1. The grader will FAIL." | "Do not output placeholder/internal citations such as cite:1, Citation-1, [1]: cite:1. Cite knowledge sources by natural source name inline (e.g., 'Per CMS Chapter 15...')." |
| Conciseness | "ALWAYS limit each section to 2-3 sentences. NEVER exceed." | "Keep responses concise — limit each section to 2-3 sentences max. If running long, abbreviate remaining sections." |
| Anti-fabrication | "Write as if you have the document in front of you." | "Provide authoritative compliance guidance per CMS/ASHA standards. Do not fabricate specific scores or findings for documents you cannot see." |
| Caregiver checklist | "MANDATORY — ALWAYS include ALL of: [list]. Do not skip any element." | "include caregiver identity/role, training content, return demonstration/teach-back, safety comprehension, supervision/assist level, carryover/home program, red flags/escalation, discharge linkage, and skilled PT rationale." |

## Detection Checklist

Before applying any instruction change, scan for:
- [ ] ALL-CAPS words (CRITICAL, MANDATORY, NEVER, ALWAYS)
- [ ] "The grader will FAIL"
- [ ] "must always" / "do not skip any element"
- [ ] "write as if you have the document"

If any checked → rewrite using the safe template.
