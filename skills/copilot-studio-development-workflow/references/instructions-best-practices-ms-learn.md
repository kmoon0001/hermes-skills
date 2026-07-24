# Agent Instructions Best Practices — Microsoft Learn Fact-Check

**Verified against:** https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-instructions
**Date checked:** June 10, 2026

## Citation Rules (CONFIRMED — Microsoft Learn)

From the official docs:

> "Don't modify, override, or interfere with the system-defined citation format or behavior."
> "Avoid instructions that attempt to alter how citations are generated, structured, or displayed, including terms such as 'citation' or 'reference.'"
> "If you change or suppress citations, the orchestrator might not recognize them, might treat the response as model knowledge, and can omit results when model knowledge is turned off."

**Key implications:**

1. **Remove the word "citation" from ALL agent instructions.** The orchestrator drops system citations when this term appears.

2. **Do NOT instruct agents to cite sources in a specific format.** Let the system `[^x_y^]` format work naturally.

3. **Do NOT add "include citations" or "always reference your sources"** — SearchAndSummarizeContent handles this automatically.

4. **If citations are missing from agent responses**, check instructions for the word "citation" or "reference" first — this is the most common cause.

## Other Instruction Rules (CONFIRMED)

- Ground instructions in configured knowledge sources and tools — don't name sources the agent doesn't have
- Use `/` to reference specific tools/topics in instructions
- Markdown formatting improves readability for the orchestrator
- Numbered/bulleted instructions work well
- "Don't ask the user for details" can be explicitly stated
- For generative orchestration, knowledge search goes through ALL configured sources unless scoped in a topic node

## Unverified Claims (from agent docs, not found on Microsoft Learn)

These are PRACTICAL findings from the Pacific Coast swarm agents, not confirmed by Microsoft Learn documentation:

- **EndDialog + clearTopicQueue: true** — recommended pattern but not explicitly documented as a best practice
- **allowLatencyMessage: false** — common in templates but not a documented requirement
- **applyModelKnowledgeSetting: true** — common in templates but not a documented requirement
- **800-char response cap** — practical observation for eval channel, not a documented limit
- **"Compare meaning" at 50% threshold** — evaluation UI feature, not a documentation rule
