# Verify → Decide → Execute Workflow

Kevin prefers this sequence when working on agent fixes. Do not skip ahead.

## The Pattern

1. **VERIFY** — Check the live agent state first. Use `dump_agent_full.cjs` or the Dataverse API. Do NOT assume the local repo matches what's in Copilot Studio. The user may be actively reworking things.

2. **DECIDE** — Present findings: what's present, what's missing, what contradicts. Propose specific changes. Get user confirmation. Do NOT blindly restore old versions — the user's rework may be intentional.

3. **EXECUTE** — After confirmation, apply changes. Patch all agents in parallel (not serial). Use the API directly (no CDP needed for instruction patches).

## Pitfalls

- **Don't wait for evals in serial.** Patch all agents, then start all evaluations. Let them run concurrently. Poll results later.
- **Don't overwrite user's work.** When the user says they've reworked an agent, fetch live state first. Add only what's missing. Combine best of both worlds.
- **Don't trust the UI.** Copilot Studio is a React SPA — tab clicks via accessibility often don't navigate. Use the API instead of trying to visually inspect.

## Example Session Flow

```
User: "im actively redoing tda. what were your fixes going to be"
Agent: [Reads fix scripts, explains what each does, does NOT execute]
User: "verify what is in the live studio ui, decide what needs to be done, then execute"
Agent: [Dumps agent state, identifies gaps, proposes changes]
User: "YES BUT FOR TDA CHECK WHAT I PUT IN... keep best of both worlds"
Agent: [Fetches live TDA, merges with missing pieces, patches all three agents in parallel]
```
