# Agent Workflow Rules for CS Automation

## Script Execution Discipline

**Critical:** When writing a script for Copilot Studio automation, RUN it immediately
in the same turn — never write a script and return an empty response waiting for
the next turn. The user expects execution, not file delivery alone.

Pattern: writeFile → terminal(run) → results in one response.

This prevents the "You just executed tool calls but returned an empty response"
frustration loop. The write + run must happen atomically in a single agent turn.

## CB YAML Changes — Publish After Every Save

After saving CB YAML in the code editor, PUBLISH the agent immediately. CB changes
only take effect after publish — the evaluation system runs against the published version.

## Compare Meaning 0.50 Threshold

Per Microsoft Learn: The 0.50 threshold is a **semantic similarity score** (0-1 scale),
not a "50% accurate" rate. It means "accept responses that are at least 50%
semantically similar to the expected answer." This catches cases where the response
is substantively correct but uses different wording than the expected answer.

## Never Force Citations

Adding "Must cite per response" or "Always include regulatory reference" to
CB `additionalInstructions` causes `completeness: No` + `groundedness: No` grader
failures. The model forces citations where none naturally exist in the knowledge
source. Use: "Cite when naturally applicable — do not force a citation where none exists."
