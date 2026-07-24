---
name: memory-to-skill-categorization
description: "Workflow for organizing persistent knowledge: identify memory entries that belong in skills, create/categorize skills by domain, and keep memory as a slim index. Use when memory is full, when the user asks to organize/compact knowledge, or when a memory entry contains procedural/technical details better suited to a skill."
version: 1.0.0
author: Hermes Agent
tags: [memory, skills, organization, categorization, knowledge-management]
---

# Memory-to-Skill Categorization

## When to Use

- Memory is near/full (>80% of 2,200 chars)
- User asks to organize, compact, or categorize knowledge
- Memory contains multi-line technical details, procedures, configs, or project specifics
- A recurring topic has outgrown a memory entry

## Cross-Session Handoffs

When the user wants to run `/new`, keep memory as a compact index rather than a progress log. Preserve stable paths and safety boundaries, add an exact `session_search` phrase, and include volatile state only when omitting it could damage work (for example, known uncommitted files). Replace the existing project pointer instead of adding duplicates. Do not repeatedly rewrite memory for every late asynchronous notification unless the actionable handoff materially changes.

For the full checklist, including active background delegations and verification of subagent-written files, read `references/cross-session-handoffs.md`.

## Decision Rule: Memory vs Skill

**Keep in MEMORY** (short, personal, index-style):
- Who the user is (name, role, preferences)
- Active pointer lines: "TOPIC → see skill: skill-name"
- One-liner context that helps every session (e.g., "ALL CAPS = casual")
- Cross-cutting preferences not domain-specific

**Move to SKILL** (detailed, procedural, domain-specific):
- Project details (repo paths, configs, IDs, URLs)
- Technical procedures (how to do X step by step)
- Pitfalls and workarounds for specific tools
- API endpoints, credentials references, data schemas
- Anything longer than 2 lines that's only relevant to one domain

## Categorization Workflow

### Step 1: Audit Current Memory

Read all memory entries. For each entry, ask:
1. Is this a SHORT pointer or preference? → Keep in memory
2. Is this DETAILED technical/project info? → Candidate for skill
3. Does a skill already exist for this topic? → Replace with pointer
4. No skill exists? → Create one (Step 2)

### Step 2: Map Entries to Skill Categories

Use these categories (match Hermes skill system):

| Category | What Goes Here |
|----------|---------------|
| `compliance` | License verification, regulatory, audit defense |
| `copilot-studio` | Copilot Studio agents, topics, evaluations |
| `copilot-studio-development-workflow` | Copilot Studio dev/deploy pipelines |
| `productivity` | Power Automate, SharePoint, Outlook, Teams, reporting |
| `email` | SMTP config, email sending, OAuth2 |
| `github` | Git workflows, PRs, repo management |
| `devops` | Infrastructure, cron, deployment |
| `data-science` | Jupyter, analysis, visualization |
| `mlops` | ML models, inference, training |
| `software-development` | Debugging, planning, testing patterns |
| `creative` | Design, diagrams, media generation |
| `research` | Papers, monitoring, knowledge bases |

### Step 3: Check for Existing Skills

Before creating a new skill, check `skills_list` for existing skills that might already cover the topic. Common overlaps:
- Power Automate flow details → `power-automate-declining-metrics`
- SMTP/email config → `outlook-smtp-oauth2` or `himalaya`
- License verification → `license-verification`
- Copilot Studio anything → check `copilot-studio-*` skills first

If an existing skill already has the info, just replace the memory entry with a pointer.

### Step 4: Create Skill (if needed)

If no skill exists:

```
skill_manage(action='create', name='topic-name', category='category-name', content=SKILL_CONTENT)
```

Skill content structure:
- YAML frontmatter (name, description, version, tags)
- Overview section (what this skill covers)
- Key IDs/Paths/Configs section (quick reference)
- Step-by-step procedures
- Pitfalls section
- References section (if needed)

### Step 5: Replace Memory with Pointers

Replace detailed memory entries with one-liner pointers:

```
TOPIC NAME → see skill: skill-name
```

Or for skills with specific sections:

```
TOPIC DETAIL → see skill: skill-name (Section Name)
```

### Step 6: Verify

After reorganization:
- Memory should be <50% full
- Every pointer should reference a real, existing skill
- No duplicate info between memory and skills
- User profile/preferences stay in memory (not skills)

## Anti-Patterns

- **Don't create skills for one-off facts** — if it's a single fact (e.g., "user's email is X"), keep it in memory
- **Don't duplicate across skills** — if two skills need the same info, put it in one and reference it from the other
- **Don't put ephemeral state in skills** — "latest report is verification_2026-06-24.xlsx" goes stale; keep project STRUCTURE in skills, latest outputs in memory or session search
- **Don't delete memory entries without replacing** — always replace with a pointer, never just remove
- **Don't create overly broad skills** — "everything about ENSG" is too wide; split into license-verification, power-automate, email-config

## Quick Reference: Memory Pointer Format

```
SHORT TOPIC LABEL → see skill: skill-name
SHORT TOPIC LABEL → see skill: skill-name (Section Name)
SHORT TOPIC LABEL → see skill: skill-name + other-skill-name
```

Examples:
```
ENSG LICENSE PROJECT → see skill: license-verification
Email/SMTP config → see skill: outlook-smtp-oauth2
Power Automate ADL flow → see skill: power-automate-declining-metrics
Copilot Studio dev → see skill: copilot-studio-development-workflow
```

## Maintenance

Run this categorization workflow:
- When memory exceeds 80% usage
- When a new project/domain is completed
- When the user asks to organize knowledge
- After major milestones that generate lots of context
