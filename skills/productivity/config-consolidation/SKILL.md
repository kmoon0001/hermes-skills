---
name: config-consolidation
description: Keep Hermes configuration lean, non-redundant, and current. Run dedup checks when skills/steering overlap, merge when counts exceed limits, and maintain clean file organization.
category: productivity
---

# Config Consolidation

## Managed Skills
- powerautomate-office-scripts

Keep Hermes config lean. Every skill/memory should have ONE clear purpose with no overlap.

## File Limits

| Folder | Max | Action if exceeded |
|--------|-----|--------------------|
| skills/ | 8 per category | Merge smallest/most-overlapping |
| steering/ | 3 files | Merge by concern area |
| memory | 75% char budget | Compact, merge, or remove stale entries |

## Naming Convention

- skills: `{domain}-{function}.md` (e.g., `copilot-studio-knowledge-api.md`)
- Use hyphens, lowercase, descriptive names
- Category folders group by domain

## Consolidation Triggers

1. New skill created → check for overlap with existing skills
2. Session ends with new learnings → update existing skills (don't create new ones)
3. Memory exceeds 75% → compact entries before adding
4. Skill count in a category exceeds 8 → merge smallest/most-overlapping

## Merge Strategy

### When Two Skills Overlap
- Keep the one with more content/usage
- Move unique sections from smaller into larger
- Delete smaller with `absorbed_into` pointing to larger
- Update any cross-references

### When Memory Overlaps
- If two entries cover the same topic → merge into one shorter entry
- If an entry is stale/task-specific → remove (not memory's purpose)
- If an entry became a skill → remove from memory, note in skill

### Steering vs Skills vs Memory
- **Steering** = rules and constraints (DO / DON'T / NEVER)
- **Skills** = how-to procedures and patterns (HOW to do it)
- **Memory** = durable facts and preferences (WHO / WHAT / WHERE)
- If a skill has rules → move to steering
- If steering has procedures → move to skill

## Dedup Decision Matrix

| New item about... | Check against... | Action if overlap |
|-------------------|-----------------|-------------------|
| Copilot Studio API | `copilot-studio-knowledge-api`, `copilot-studio-live-patch` | Merge into most-used |
| Copilot Studio topics | `cdp-instructions-injection`, `agent-builder-pipeline` | Merge into pipeline |
| Knowledge sources | `knowledge-source-builder`, `copilot-studio-knowledge-api` | Merge by scope |
| Agent building | `agent-builder-pipeline`, `copilot-studio-agent-builder` | Pipeline is primary |
| Evaluation | `eval-triage-framework`, `eval-optimization-loop` | Triage is authoritative |
| Healthcare compliance | `clinical-swarm-guardrails`, `clinical-swarm-deployment` | Guardrails is rules |
