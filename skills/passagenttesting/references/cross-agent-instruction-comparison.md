# Cross-Agent Instruction Comparison Technique

When one agent passes evaluation but another fails the same type of test, compare their
agent-level instructions side-by-side to find critical differences.

## Process

1. Read both agents' instructions from Dataverse (`componenttype eq 15`, `$select=data`)
2. Parse the YAML `data` field for the `instructions: |` block
3. Compare these sections:
   - **RESPONSE FORMAT header** — "for ALL" vs "for full audits only"
   - **RESPONSE FORMAT scope list** — is "caregiver competency" included?
   - **RESPONSE BEHAVIOR** — does it say "using the RESPONSE FORMAT" or list multiple formats?

## SLP vs OT Case Study (June 16, 2026)

**SLP had Conv stuck at 80-86% despite guard activation. OT Conv at 95%.**

Comparison revealed:

| Section | OT (PASSING) | SLP (FAILING) |
|---------|-------------|---------------|
| RESPONSE FORMAT header | `Use for ALL document-related questions` | `Use for full document audits only` |
| Scope list | evaluation, daily note, progress note, recert, discharge, **caregiver competency, compliance check, audit request** | evaluation, daily note, progress note, recert, discharge |
| Response behavior | `using the RESPONSE FORMAT` | `checklist, score/risk framework, escalation summary, or routing answer` |

**Impact:** SLP's "full document audits only" meant general questions got unstructured responses.
The grader expects Classification, Score X/100, Compliance Findings for ALL document-related
questions — SLP was producing free-text answers that scored lower.

**Fix:** Align SLP's RESPONSE FORMAT header and scope with OT's pattern:
1. `full document audits only` → `ALL document-related questions`
2. Add caregiver competency, compliance check, audit request to scope
3. Standardize response behavior to `using the RESPONSE FORMAT with the available context`

## Why This Matters

SLP's test set mixes audit questions and general clinical inquiries. The conditional format
("only for full audits") causes the model to skip the structured output for ~40% of questions,
but the grader still expects structured output. This creates a ceiling effect — guard activation,
model changes, and KB improvements won't push Conv past ~86% until the format issue is fixed.
