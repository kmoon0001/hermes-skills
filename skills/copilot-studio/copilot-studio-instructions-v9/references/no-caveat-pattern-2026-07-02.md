# No-Caveat Standards Check — Proven Pattern (July 2 2026)

## What it is
A block inserted into specialist agent instructions that prevents the agent from asking for documents during evaluation. Instead of "I'd need to see the note" or "please provide the document", the agent gives a conditional determination.

## Template (replace PT/OT/SLP as needed)
```
PT EVAL NO-CAVEAT STANDARDS CHECK
- For eval questions that ask "can you check", "does my note include", "is this compliant", "can you audit", or "can you verify" without providing note text: give a direct standards-based compliance screen.
- State: "Compliant only if the PT note includes..." then list the required elements.
- Apply to measurable goals, skilled justification, standardized outcome measures, clinical reasoning, weight-bearing status, ICD-10/CPT linkage, wound care, transfer training, discharge rationale, recertification, and denial risk.
- Keep answer plain text. Do not ask for the note. Do not use mock-audit framing. Make missing source text a supporting point, not the main answer.
```

## Insertion point
Insert before `RESPONSE FORMAT` section in the agent instructions.

## Results
| Agent | Before | After | Delta |
|-------|--------|-------|-------|
| OT | 69% | 97% | +28 |
| PT | 84% | 99% | +15 |

Both agents had SOLID existing instructions (6-section format, scoring strictness, response instructions). The no-caveat block was the ONLY change for OT. PT also had full instructions restored.

## Additional hardening (OT-specific)
OT also had its RESPONSE BEHAVIOR strengthened:
- Old: "Never start with 'I can help' or 'To determine'. Just audit it directly."
- New: "Never defer with 'To determine...' or 'To audit...'. Never ask for the document. Never say 'please provide'. Just audit it."

This more explicit language produces a 28-point improvement on its own.
