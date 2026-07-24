# PT Conv Failure Analysis — June 17, 2026

## Baseline: PT Conv 90% (18/20 pass, 2/20 fail)

### Failure 1: Section GG Compliance
- **Question:** "assess the PT evaluation for Section GG compliance and highlight any deficiencies"
- **Grader:** "One or more answers didn't cite knowledge sources"
- **Agent response:** Comprehensive Section GG audit with classification, score (82/100), missing elements, recommendations — but NO inline citations to CMS Chapter 15 or APTA standards
- **Root cause:** Agent produces complete audits but omits citations entirely in conversation mode

### Failure 2: Caregiver Education
- **Question:** "check the PT evaluation for completeness of caregiver education and suggest enhancements"
- **Grader:** Same — "didn't cite knowledge sources"
- **Root cause:** Same pattern — comprehensive response without citations

### Failed Fix Attempts

| Fix | Result | Why It Failed |
|-----|--------|--------------|
| CRITICAL citation ban | 90%→85% | Aggressive language scared model into avoiding ALL citations |
| CRITICAL + conciseness + hedging removal (stacked) | 90%→80% | Too many changes at once per MS Learn |
| MANDATORY caregiver sections | 90%→85% | Aggressive enforcement language caused overcorrection |
| Soft citation requirement ("EVERY response MUST include") | 90%→90% | No improvement, no regression. Citation requirement alone not enough |
| Restored baseline (no changes) | 90% | Stable baseline |

### Recommended Next Steps (MS Learn-aligned)

1. **Check PT knowledge source descriptions** — Are they descriptive enough for GPT retrieval? The PT agent has 5+ knowledge sources. If descriptions are blank, the model can't route to the right source for caregiver/Section GG topics.
2. **Add explicit citations to PT-SPECIFIC sections** — Instead of a global citation requirement, add citations directly into the caregiver and Section GG instruction sections. Example: "When discussing caregiver competency, cite: 'Per CMS Chapter 15 §410.60, caregiver training must include...'"
3. **Test ONE change at a time** — Per MS Learn: "Make one change at a time and notice the effect."

### Key Insight
PT's failures are NOT about hedging or citation FORMAT (no cite:1 in responses). They're about citation PRESENCE — the agent simply doesn't cite sources in conversation mode. This is a different problem from SLP (which had cite:1 format and hedging language).
