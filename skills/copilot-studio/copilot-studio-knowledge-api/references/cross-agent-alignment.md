# Cross-Agent Alignment Audit

Systematic approach to align Hermes with another agent (Kiro, Codex, etc.). Use when user says "match X's setup" or "ensure we have everything X has."

## Discovery

1. Find the agent's config directory: `.kiro/`, `.codex/`, `.claude/`
2. List subdirectories: `skills/`, `steering/`, `settings/`, `powers/`, `tools/`, `memory/`
3. Identify what's relevant to the user's domain

## MCP Comparison

1. Read other agent's MCP config: `settings/mcp.json`
2. Run `hermes mcp list` to see current state
3. For each server: check if Hermes has built-in equivalent → SKIP if yes, ADD if no
4. Kevin's skip list (Hermes built-ins are better): filesystem, git, fetch, playwright, pac-cli

## Skill Comparison

1. List both agents' skills
2. Map equivalents by name/function
3. Create missing, patch partial matches
4. Adapt for Hermes tool set (Kiro Playwright MCP → Hermes browser tool)

## Steering Comparison

1. Read steering files — if procedures → skills; if rules → skill pitfalls
2. PATCH existing skills with missing steering content

## Pitfalls

- **Scope creep**: User says "copilot studio" but means "globally" — always confirm scope
- **Power vs Skill**: Kiro has both `skills/` and `powers/` directories. Powers are packages (POWER.md + mcp.json + steering/). Check both.
- **Path escaping**: Backslashes in bash MCP args get mangled. Use single quotes or forward slashes.
- **Redundant MCPs**: Don't add MCPs that duplicate Hermes built-ins. Latency + token overhead with zero benefit.
- **Memory compaction**: Use `operations` array for batch add/replace/remove in one call.
