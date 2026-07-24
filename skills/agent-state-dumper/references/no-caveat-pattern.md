# No-Caveat Pattern

The "ask-for-document" error is one of the three root failure patterns for Copilot Studio therapy audit agents. The fix: inject a NO-CAVEAT STANDARDS CHECK block into the instructions.

## The Block

```
OT EVAL NO-CAVEAT STANDARDS CHECK
- For eval-style questions that ask "can you check", "does my note include", "is this compliant", "can you audit", or "can you verify" without providing note text, give a direct standards-based compliance screen instead of leading with an inability to confirm.
- State the finding as: "Compliant only if the [discipline] note includes..." then list the required elements for that exact requested item.
- Apply this to [list agent-specific domains].
- Keep the answer plain text. Do not ask first for the note, do not use mock-audit framing, and do not make missing source text the main answer.
```

## Where to Insert

Insert BEFORE the `RESPONSE FORMAT` section in the instructions. This ensures the model reads the no-caveat rule before it considers the format it should use.

## How to Check

After patching, run `dump_agent_full.cjs` and verify `hasNoCaveat: true` in the summary.

## When to Use

Apply whenever an agent's evaluation failures show "ask for document" or "unable to score without text" patterns. This is one of the three root patterns (alongside missing RESPONSE FORMAT and first-sentence truncation).

## Agent-Specific Blocks Used

- **OT:** `OT EVAL NO-CAVEAT STANDARDS CHECK` — domains: ADL/IADL, functional cognition, adaptive equipment, UE, splinting, caregiver competency, skilled justification, discharge, recertification, baseline/current comparison, denial risk.
- **PT:** `PT EVAL NO-CAVEAT STANDARDS CHECK` — domains: measurable goals, skilled justification, standardized outcome measures, clinical reasoning, weight-bearing status, ICD-10/CPT linkage, wound care, transfer training, discharge, recertification, denial risk.
- **TDA:** `TDA NO-CAVEAT` — one-liner: "For any eval question that references a document type without providing text, produce a full scored audit (assume typical document, score 75/100 Moderate, list common missing elements). NEVER ask the user to submit or provide a document."
