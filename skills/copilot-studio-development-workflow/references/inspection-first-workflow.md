# Inspection-First Workflow (Mandatory)

## CRITICAL RULE

**Before touching any live Copilot Studio agent — reading topics, making PATCH calls, editing instructions, or uploading knowledge — you MUST load `agent-comprehensive-inspection` and run all 12 domains first.**

This is not optional. Skipping the inspection leads to:
- Ad-hoc analysis that misses systemic issues
- User frustration ("did you do the full inspection using our skills?")
- Fixes applied in wrong priority order
- Missing connections between domains (e.g. trigger phrases that reference un-uploaded KBs)

## Workflow

1. User asks about a Copilot Studio agent → load `agent-comprehensive-inspection` skill
2. Run Domain 1 through Domain 12 systematically
3. Present findings as PASS/FAIL per sub-check with severity flags (CRITICAL > HIGH > MEDIUM > LOW)
4. Conclude with a ranked fix priority list
5. Only THEN begin patching — start with CRITICAL items first

## What To Do If The Inspection Skill Is Missing
If `agent-comprehensive-inspection` is not available, use the preflight check: load `copilot-studio-preflight` and run through the 12-domain checklist manually using the copilot-studio YAML reference and MS Learn docs.

## Pitfall: Analysis-Before-Inspection
When the user asks to "look at" or "evaluate" an agent, the instinct is to start reading files and making assessments. **Resist this.** Always load the inspection skill first. The user's question "did you do the full inspection using our skills?" is the signal this rule was violated.

Applied: Pacific Coast Documentation Defense Agent, July 2026.
