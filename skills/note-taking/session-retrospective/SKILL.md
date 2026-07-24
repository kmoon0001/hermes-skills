---
name: session-retrospective
description: Session retrospective and flow optimization — review recent interactions to identify friction, repeated mistakes, and optimization opportunities. Produces actionable improvements to skills, memory, and workflow patterns. Mirrors Kiro's /learn workflow, adapted for Hermes.
category: note-taking
---

# Session Retrospective & Flow Optimization

## Usage
Say: "Run a retrospective" or "Review our recent sessions"

## Purpose
Review recent interactions to identify friction, inefficiencies, repeated mistakes, and optimization opportunities. Produces actionable improvements to skills, memory, hooks, and workflow patterns.

## When to Use
- End of a work session or sprint
- After encountering repeated friction or errors
- Before starting a new phase of work
- When switching between contexts and noticing gaps

## Workflow

### Phase 1: Gather Evidence
1. Review current conversation history for patterns (use session_search)
2. Check recent git commits for context on what was attempted
3. Read any error logs, failed commands, or retried operations
4. Identify tool calls that were unnecessary or redundant
5. Note where the agent asked questions it should have known the answer to

### Phase 2: Categorize Findings

| Category | What to Look For |
|----------|-----------------|
| **Repeated Mistakes** | Same error hit multiple times, same wrong assumption made |
| **Unnecessary Tool Calls** | Reading files already in context, redundant searches |
| **Missing Context** | Agent didn't know something it should have (add to memory/skills) |
| **Workflow Friction** | Manual steps that could be automated |
| **Cross-Repo Gaps** | Knowledge from one project that would help in another |
| **Slow Patterns** | Sequential operations that could be parallel |
| **Scope Creep** | Agent doing more than asked, over-engineering |

### Phase 3: Produce Actionable Outputs

For each finding, recommend ONE of:
- **Skill creation/update** — Package a repeatable workflow into a skill
- **Memory note** — Store a fact the agent should remember
- **No action** — One-off issue, not worth codifying

### Phase 4: Implementation

Apply the changes directly:
1. Create/update skills for repeated workflows
2. Save key facts to memory
3. Report summary to user

## Output Format

```
## Retrospective Summary — [Date]

### Problems Encountered
1. [Problem] → [Root cause] → [Fix type]

### Efficiency Gaps
1. [Pattern] → [Optimization]

### Cross-Session Insights
1. [Insight] → [Where to store it]

### Changes Applied
- [ ] [Skill/Memory]: [What changed]
```

## Scope Rules
- Focus on patterns, not one-off typos
- Only create skills for issues that occurred 2+ times
- Keep skills concise — rules, not essays
- Don't over-engineer: if a simple memory note fixes it, do that
