# Current Agent State — June 2026

## Bot IDs (Environment: Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f)

| Agent | Bot ID | Type |
|-------|--------|------|
| OT | 73b45e98-af7a-443a-aa12-6d8a05118530 | Audit |
| PT | 593407f3-539b-490f-84ac-d74e13216c81 | Audit |
| SLP | 6e437a77-a5dc-4984-90eb-4924eab10006 | Audit |
| TDA | 4d0ed0d3-30f6-f011-8406-000d3a37eba2 | Routing |

## Canonical Instruction Files

All files in `D:/my agents copilot studio/`:

| Agent | File | Chars | Format | Status |
|-------|------|-------|--------|--------|
| OT | `ot_instructions_v9_final.txt` | ~6,000 | Unconditional RF | STABLE 99%/100% — DO NOT TOUCH |
| PT | `pt_instructions_consolidated.txt` | 3,957 | Conditional RF | HYBRID formula, needs eval |
| SLP | `slp_instructions_consolidated.txt` | 3,626 | Conditional RF | HYBRID formula, needs eval |
| TDA | `tda_instructions_consolidated.txt` | 2,589 | Routing (no RF) | HYBRID formula, needs eval |

Backup files:
- `pt_instructions_final.txt` — pre-hybrid baseline
- `slp_instructions_fixed.txt` — pre-hybrid baseline
- `tda_instructions_fixed.txt` — pre-hybrid baseline

## Score History (last known, June 18 2026 ~2:30 AM)

| Agent | SR (3-run avg) | Conv (3-run avg) | Latest |
|-------|---------------|-----------------|--------|
| OT | 98% (99/96/100) | 98% (95/100/100) | 95% Conv |
| PT | 88% (88/94/82) | 77% (90/85/55) | 88% SR |
| SLP | 92% (90/94/-) | 80% (75/80/85) | 75% Conv |
| TDA | 83% (91/85/73) | 95% (100/95/90) | 100% Conv |

## What Went Wrong (June 17-18 2026)

1. **OT-style simplification** — Copying OT's short format to PT/SLP/TDA caused massive regressions
2. **Aggressive language** — CRITICAL/MANDATORY/MUST checklists in instructions caused 5-15% regression each
3. **Inline citation requirement** — "Cite INLINE" caused PT 95%→85% regression
4. **Wrong files pasted** — SLP got OT-style (3K) instead of correct version (4.8K)
5. **Too many stacked changes** — Multiple rewrites without testing between each

## Fix Strategy (HYBRID Formula)

OT behavioral patterns + discipline-specific content:
- Copy OT's 6 behavioral patterns (ban weak phrases, format-per-question, conciseness)
- KEEP discipline-specific content sections
- Soft language only (no CRITICAL/MANDATORY/MUST)
- Checklists go in topic YAML, NOT agent instructions
- One change at a time, test after each
