# Agent-Specific Failure Patterns (June 2026)

## PT_Specialist — Conv 90% (2/20 fail)

**Failure 1:** "assess the PT evaluation for Section GG compliance"
- Grader: "One or more answers didn't cite knowledge sources"
- Agent response: comprehensive audit with NO inline citations

**Failure 2:** "check the PT evaluation for completeness of caregiver education"
- Same grader pattern: missing citations

**What WORKS (90% baseline):** Soft citation ban + conciseness + hedging removal
**What REGRESSES:** CRITICAL/NEVER language → 85%, MANDATORY → 85%, stacked fixes → 80%

## SLP_Specialist — Conv 100%, SR 95%

**Conv failures (80% baseline):** hedging + cite:1 + truncation
**SR failures (95%):** fabricated scores for unseen documents

**What WORKS:** Balanced guidance + soft citation + conciseness

## OT_Specialist — SR 99%, Conv 100% (no failures identified)

## TDA — SR 96%, Conv 100% (routing agent, different failure modes)

## Cross-Agent Rule: Model Ceiling

All agents cluster 94-97% SR. Similar scores ≠ shared bug.
NEVER copy fixes without per-agent root cause analysis.
