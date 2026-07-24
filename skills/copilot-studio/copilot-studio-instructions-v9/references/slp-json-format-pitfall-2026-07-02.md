# SLP JSON-Keyed Format Pitfall (July 2 2026)

## What happened
SLP was patched with a JSON-keyed instruction format from `fix_slp_instructions.cjs`:
- Uses quoted keys: `"Role":`, `"Scope":`, `"For full audits":`, `"For single-response questions":`
- Model: Sonnet46
- Compressed from ~4500 chars to ~2933 chars

## Result
SLP SR dropped from **80% → 76%** on the same test set (`45fccc95-85fc-4491-a270-bfc4a3ed1848`).

## Root cause
The JSON-keyed format, while cleaner and more parseable per Microsoft Learn guidance (`# Headings to label sections, bullet points for lists`), does NOT include a numbered 6-section RESPONSE FORMAT with explicit emoji risk indicators. The evaluator appears to penalize responses that don't match this expected format.

## Fix
Revert to the traditional 6-section RESPONSE FORMAT pattern used by OT and PT:
```
RESPONSE FORMAT — Use for ALL document-related questions:
1. Classification
2. Compliance Findings [HIGH/MODERATE/LOW RISK] with confidence
3. Score X/100 with tier
4. Missing Elements
5. Recommendations
6. Advisory
```

The working SLP instructions that scored 98% are in `live_agent_dump/SLP_instructions_live.txt` (the PRE-July-2 version).

## Lesson
For therapy audit specialists, the 6-section numbered format beats cleaner JSON-keyed formats. The evaluator is keying on the numbered structure. Save JSON-keyed for orchestrator agents (TDA) where brevity matters more.
