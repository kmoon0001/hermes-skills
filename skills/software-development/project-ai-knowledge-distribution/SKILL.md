---
name: project-ai-knowledge-distribution
description: >-
  Distribute a centralized knowledge file (e.g. lessons-learned.md) across all
  AI coding tool configs in a project repo so every tool discovers the same
  reference. Used after updating any shared knowledge base that multiple AI
  agents (Hermes, Claude Code, Codex, Cursor, GitHub Copilot, Kiro, Antigravity)
  should all see without each one needing its own independent source.
---

# Project AI Knowledge Distribution

After creating or updating a centralized knowledge file (like `lessons-learned.md`
for Copilot Studio patterns), wire it into every AI tool config present in the
project repo. This ensures the user gets consistent advice regardless of which
tool they open the project with.

## When to use

- After a Copilot Studio debug session produced a new validated lesson
- After creating/updating any cross-cutting reference file that multiple tools should see
- When the user asks to make knowledge available in "Kiro and Codex and Cursor and Antigravity" (their common ask pattern)

## Step 1: Create the knowledge file

Place the file at the project root. Keep it self-contained — each tool's config
will just point to it rather than duplicating content.

```
./lessons-learned.md     # Copilot Studio patterns
./architecture.md        # System design decisions
./ai-context.md          # General project knowledge for AI agents
```

## Step 2: Wire into each tool config

Check which config directories exist in the repo, then add a one-line pointer
for each one:

### AGENTS.md (Codex CLI)
Add a section near the bottom:
```markdown
## Project Knowledge
- Read `./lessons-learned.md` for [topic description]
```

### CLAUDE.md (Claude Code)
Add a bullet under the development method or references section:
```markdown
- See `./lessons-learned.md` for [topic description]
```

Then add as a separate source-of-truth line:
```markdown
- **lessons-learned.md** (project root) = cross-tool knowledge base
```

### .claude/rules/ (Claude Code per-project rules)
Add a line at the top of the relevant rule file (e.g. `copilot-studio.md`):
```markdown
- Read `./lessons-learned.md` (project root) for the full [topic] reference.
```

### .github/copilot-instructions.md (GitHub Copilot)
Add a paragraph:
```markdown
For [topic] rules and validated lessons, read `lessons-learned.md` in the project root.
```

Also update the first paragraph's file list to include `lessons-learned.md`:
```markdown
...read `AGENTS.md`, `lessons-learned.md`, and the relevant files under...
```

### .cursor/rules/ (Cursor IDE)
Create a `.mdc` file with frontmatter:
```yaml
---
description: One-line description of what this rule covers
globs: "**/*.yml, **/*.yaml, **/AGENTS.md"  # match relevant file types
---
```

Body: quick-reference table of key rules + pointer to `lessons-learned.md`.

### .kiro/steering/ (Kiro)
Create a steering rule markdown file with Kiro frontmatter:
```yaml
---
inclusion: fileMatch
fileMatchPattern: "**/*.yml,**/*.yaml,**/AGENTS.md"
---
```

Body: key rules lookup table + pointer to `lessons-learned.md`.

### .kiro/skills/ (Kiro skills)
Add a references line to the relevant skill file:
```markdown
- **lessons-learned.md** (project root) — [description]
```

### .antigravity/ (Antigravity)
Antigravity is MCP-based — no instruction file. The filesystem MCP server in
its config already exposes the project root, so `lessons-learned.md` is
readable automatically. No config change needed.

## Step 3: Verify

```bash
grep -rn "lessons-learned" AGENTS.md CLAUDE.md .claude/rules/ .github/copilot-instructions.md .cursor/rules/ .kiro/steering/ .kiro/skills/ 2>/dev/null
```

Every path should produce at least one match.

## Pitfalls

- **Don't reference Hermes profile paths** (`~/.hermes/skills/...`) in project
  config files — those paths only work inside Hermes. Use `./lessons-learned.md`
  (project-root relative) instead so all tools can resolve it.
- **Update all configs in one pass** — partial updates leave some tools blind.
  Batch the grep verify above before reporting done.
- **Don't duplicate content** — keep the master copy at project root; configs
  only get one-line pointers. When the knowledge file changes, only the root
  copy needs updating.
- **Cursor .mdc frontmatter matters** — the `globs` field controls when the
  rule auto-injects. Use broad enough globs (e.g. `**/*.yml, **/*.yaml, **/AGENTS.md`)
  so it triggers on relevant file opens.
- **Kiro steering frontmatter**: must use `inclusion: fileMatch` with a
  `fileMatchPattern` that catches the relevant file types.

## Related

- `copilot-debug` skill — Phase 2 step 6 should trigger project sync after
  every retrospective (skill is pinned; sync step documented here as reference).
- `copilot-studio-development-workflow` umbrella — feeds into the debug loop.
