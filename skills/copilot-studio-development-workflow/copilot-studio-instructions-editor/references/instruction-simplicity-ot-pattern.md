# OT Simplicity Pattern — The 5-Section Formula for High Stability

OT (99% SR, high stability across runs) has a proven instruction structure that other agents lack. Validated June 17, 2026 via side-by-side comparison of all 4 agents.

## The 5-Section Formula

```
1. CLINICAL ROLE — what the agent does (scope, domains, role)
2. RESPONSE BEHAVIOR — format embedded in behavior, no separate Format Rules section
3. XAI & TRANSPARENCY — confidence, citations, reasoning chain
4. CONVERSATION CONTINUITY — context tracking across turns
5. SAFETY — disclaimer, non-device, PHI rules
```

## What OT Does NOT Have (that PT/SLP DO — and it hurts them)

| Feature | OT (99%) | PT (95%) | SLP (90%) | Effect |
|---------|----------|----------|-----------|--------|
| Format Rules section | ❌ | ✅ | ✅ | Extra constraints → regression risk |
| Discipline-Specific Content section | ❌ | ✅ | ✅ | Checklists in instructions → overcorrection |
| "Must Include" language | ❌ | ✅ | ✅ | Aggressive → 5-15% regression |
| "Do NOT ask for document" pattern | ❌ | ✅ | ✅ | Negative instruction → confusion |
| Section count | 5 | 6 | 6 | Less = more stable |

## The Lesson

**More instruction sections = more constraints = more regression risk.**

OT's simplicity is its stability secret. Content that PT and SLP put in "Format Rules" and "Discipline-Specific Required Content" sections belongs in TOPIC YAML `additionalInstructions`, not agent instructions.

## Carry-Over Plan

For PT and SLP:
1. Merge "Format Rules" into RESPONSE BEHAVIOR
2. Move "Discipline-Specific Required Content" into topic YAML only
3. Remove all "Must Include" / "Do NOT" language
4. Target 5 sections like OT

For TDA:
1. Add RESPONSE BEHAVIOR section (currently missing)
2. Add XAI & TRANSPARENCY
3. Add CONVERSATION CONTINUITY
4. Keep routing-focused (shorter than audit agents)
