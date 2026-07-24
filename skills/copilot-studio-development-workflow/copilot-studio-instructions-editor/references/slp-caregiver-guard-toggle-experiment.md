# SLP caregiver guard toggle experiment

Use this as a compact evidence record for SLP Conversation failures involving caregiver competency, caregiver cognitive capacity, or caregiver safety guard topics.

## Context

SLP Conversation had plateaued at 90%. The remaining failures were caregiver-topic cases with otherwise relevant answers but bad citation behavior:

- Placeholder citation footnotes such as `[1]: cite:1 "Citation-1"`.
- Bracket citation definitions (`[2]: cite:2`, `Citation-2`, etc.).
- Duplicated answer blocks after guard-topic routing.
- Grader labels included incomplete/relevance/citation failures even when the clinical content was mostly present.

A broad agent-level source-anchor/instruction patch was tested and saved/published/read-back verified. It regressed SLP Conversation to 35% because the guard topics amplified citation artifacts across many cases. Rolling the instructions back restored the known 90% baseline.

## Reversible topic-disable experiment

Because visual topic textarea edits did not persist and durable topic YAML editing was not immediately available, the safer experiment was to turn guard topics OFF rather than delete them.

Topics turned OFF:

- `Caregiver Competency Audit`
- `SLP Conv Guard - Caregiver Competency`
- `SLP Conv Guard - Caregiver Cognitive Capacity`
- `SLP Conv Guard - Caregiver Safety`

After toggling, verify rows in the Topics table show `Off`, then publish the agent before rerunning evals.

## Result

Fresh SLP Conversation run after all four caregiver topics were OFF:

- Run: `Evaluate SLP_Specialist 260613_1231`
- Data type: Conversation
- Score: 95%
- Pass: 19/20
- Fail: 1/20

The caregiver safety test passed with `SLP Conv Guard - Caregiver Safety` OFF:

- `Check if the caregiver safety documentation meets compliance requirements.` → Pass

The remaining failure was:

- `Evaluate the caregiver’s competency documentation for compliance with Medicare standards.` → Fail

Failure detail still showed citation-footnote artifacts in the fallback answer:

- `[1]: cite:1 "Citation-1"`
- `[2]: cite:2 "Citation-2"`
- `[4]: cite:4 "Citation-4"`

## Guidance for future sessions

- Prefer OFF over DELETE when experimenting with guard topics; OFF is reversible and preserves the topic for later YAML repair.
- Do not assume caregiver safety must remain ON. In this evidence, safety passed with the guard OFF.
- Do not apply broad SLP source-anchor rewrites to solve caregiver-only failures; this can collapse score.
- If trying for 100%, target only the remaining caregiver competency citation artifact. Best options:
  1. durable topic YAML/code-editor patch that forces prose-only citations and no footnote definitions, or
  2. a very narrow caregiver-competency instruction change that does not introduce a global `Source Anchors` section.
- Always rerun a fresh 20-case Conversation eval from the known config details URL and inspect the failed row before keeping/reverting.
