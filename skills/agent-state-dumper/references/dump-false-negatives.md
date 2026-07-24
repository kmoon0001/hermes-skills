# Dump Script False Negatives — July 2 2026

The `dump_agent_full.cjs` summary flags use literal string matching in the instruction YAML:

- `hasResponseFormat` — checks for "RESPONSE FORMAT" (uppercase with space)
- `hasNoCaveat` — checks for "NO-CAVEAT" (uppercase with hyphen)
- `hasEvalSafe` — checks for "EVALUATION-SAFE"

## Known false negatives

| Agent | Flag | False? | Why |
|-------|------|--------|-----|
| SLP | hasResponseFormat: MISSING | YES | SLP uses "Use this FORMAT for audit responses:" (no "RESPONSE" prefix) |
| SLP | hasNoCaveat: MISSING | YES | SLP uses "Do NOT ask for the note first. Provide the full compliance checklist" (no "NO-CAVEAT" keyword) |
| PT (post-patch) | hasNoCaveat: YES | OK | PT now has "PT EVAL NO-CAVEAT STANDARDS CHECK" block |

## Mitigation
When the dump says MISSING for SLP, manually verify. The JSON-keyed format won't match the regex but may still have equivalent content. After reverting SLP to 6-section format, these flags should show YES.
