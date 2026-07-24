---
name: persistent-context-cleanup
description: "Use when maintaining Hermes persistent context files, memory, AGENTS/HERMES guidance, skills, and other long-lived agent knowledge. Audits for overlap, compacts wording, moves procedures into skills, preserves useful behavior, and requires approval for early destructive changes."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, memory, skills, cleanup, context, token-reduction]
    related_skills: [memory-to-skill-categorization, hermes-agent-skill-authoring, hermes-agent]
---

# Persistent Context Cleanup

## Overview

Maintain Hermes persistent context as a lean operating manual, not a junk drawer. The goal is lower token load with no loss of useful behavior: preserve working guidance, remove duplicates, shorten prose, and move domain-specific procedures into focused skills.

Follow Andrej Karpathy-style `AGENTS.md` principles: plain text, direct instructions, sharp headings, few words, durable facts only, and examples/commands only where they change behavior.

## Scope

Operate only inside the active Hermes profile unless the user explicitly authorizes another profile:

- Profile skills under the active profile's `skills/` tree
- Profile memories/user profile via the memory tool when possible
- Project-local `AGENTS.md`, `HERMES.md`, `CLAUDE.md`, `skills.md`, or similar files only when the current workdir or user instruction makes them in scope
- Cron/script files created for this maintenance workflow

Never touch another profile's skills/plugins/cron/memories unless explicitly directed.

## Weekly Workflow

1. Discover context sources.
   - Identify active profile paths from system hints, `hermes config path`, and available files.
   - Search for `AGENTS.md`, `HERMES.md`, `CLAUDE.md`, `skills.md`, memory files, and locally created skills.
   - Completion criterion: every candidate file is classified as in-scope, out-of-scope, or needs approval.

2. Back up before edits.
   - Create a timestamped backup directory under the active profile, e.g. `maintenance/backups/YYYYMMDD-HHMMSS/`.
   - Copy any file that may be changed.
   - For memory changes, record proposed `memory` operations in the report before applying them.
   - Completion criterion: rollback source exists for every edited file or memory operation.

3. Audit for sediment.
   - Mark duplicates, stale task progress, expired artifact IDs, bloated prose, and domain procedures living in memory.
   - Keep user preferences, stable environment facts, and pointer lines.
   - Move technical procedures, project details, pitfalls, and commands into existing skills when possible.
   - Completion criterion: each finding has an action: keep, compact, move-to-skill, delete, or ask.

4. Apply safe compaction.
   - Prefer targeted patches over rewrites.
   - Do not delete useful working guidance.
   - Replace long memory entries with pointer lines only after the target skill exists and contains the detail.
   - Co-locate rules with their concept; remove old wording when adding the replacement.
   - Completion criterion: net token load decreases or organization improves without losing behavior.

5. Approval gate for early runs and risky changes.
   - For the first 3 weekly runs, do not remove memory entries or delete files automatically. Produce a review report with proposed changes and ask Kevin to approve.
   - After the first 3 runs, auto-apply only low-risk compaction. Still ask before deleting files, removing memories with uncertain value, changing credentials/configs, or touching cross-profile content.
   - Completion criterion: risky changes are left as proposals, not applied.

6. Verify.
   - Re-read changed files.
   - Validate edited skills have required frontmatter and non-empty body.
   - Ensure every memory pointer references a real skill.
   - Run `hermes cron list` if cron files/jobs were changed.
   - Completion criterion: report includes changed paths, skipped risky items, and verification results.

## Memory Rules

Keep memory short and declarative:

- User preferences and durable identity facts stay in user profile/memory.
- Domain details become `TOPIC → see skill: skill-name` pointer lines.
- Completed task logs, PR numbers, commit SHAs, old report filenames, and temporary blockers are removed or left out.
- Procedures belong in skills, not memory.
- When memory is near full, consolidate by replacing long domain entries with pointers in one atomic memory operation.

## Skill Rules

Use existing skills before creating new ones. Update a skill when it already owns the topic. Create a new skill only when a recurring procedure has no home.

Good cleanup edits:

- Tighten descriptions to trigger classes.
- Add concrete pitfalls discovered from past work.
- Move bulky references into `references/`.
- Delete duplicate/no-op prose while preserving checkable criteria.

## Weekly Report Format

Write a concise report with:

- Run number or date
- Files inspected
- Changes applied
- Proposed changes needing approval
- Memory entries suggested for replace/remove
- Skills updated or created
- Verification results
- Next recommended cleanup

Save reports under the active profile, e.g. `maintenance/reports/context-cleanup-YYYYMMDD.md`.

## Common Pitfalls

1. Deleting hard-won guidance because it looks verbose. Compact first; delete only if duplicated or stale.
2. Moving preferences into skills. Preferences should remain in memory/user profile.
3. Creating tiny duplicate skills. Patch the existing domain skill instead.
4. Directly editing another profile. Stay inside the active profile unless explicitly authorized.
5. Letting reports become the new clutter. Keep them dated and separate from always-loaded context.

## Verification Checklist

- [ ] Active profile only, unless explicitly authorized
- [ ] Backup made before edits
- [ ] No credentials or secrets exposed in reports
- [ ] Skills validate after edits
- [ ] Memory is shorter or better indexed
- [ ] Risky deletions are proposed, not applied
- [ ] Report saved with applied/proposed/verified sections
