## Conditional vs Unconditional RESPONSE FORMAT (Session 2026-06-09)

This is the single most impactful finding from the SLP/PT/OT regression debugging session.

### The Three Versions

| Version | Directive | SLP SR | SLP Conv | PT SR | PT Conv | OT SR | OT Conv |
|---------|-----------|--------|----------|-------|---------|-------|---------|
| v3 | "When full text IS provided: use RESPONSE FORMAT" | 95% | 70% | 90% | 65% (before fix) | 100% | — |
| v4 | "Always use RESPONSE FORMAT for any audit question" | **95%** | **95%** | 90% | 80% | 84% (v3) | 80% (v3) |
| v5 | "For full audits: use FORMAT. For general: natural answer" | 87% | 95% | 90% | 80% | 84% | 65% |

### Key Insight

**v4 is the best default.** Unconditional RESPONSE FORMAT is what the grader expects for almost all question types. The exception is when a conversation test set contains explicitly non-audit questions like "I have a general clinical inquiry." For those, use the v5 approach but ONLY target the format removal to specific conversation tests.

### Takeaway
- For **single-response** tests: always use unconditional RESPONSE FORMAT
- For **conversation** tests with general-knowledge questions: be cautious — unconditional format can drop conversation scores if the test set includes non-audit items
- The safest text (achieved both at 95% on SLP): "Always use the RESPONSE FORMAT above for any document-related or audit question."
