# Git Workflow — Dirty Repo Triage, Commit, Push & Live Sync

When picking up an interrupted or handoff session (from Codex, another agent, or a previous session), follow this structured workflow to avoid committing unrelated changes or pushing broken YAML.

## 1. Orient — Read Steering Files & Check Git State

```
git status --short --branch
git log --oneline --decorate -n 12
git diff --stat
git diff --name-status
git ls-files --others --exclude-standard
```

Always read `AGENTS.md`, `CLAUDE.md`, and any `.kiro/steering/` files first — they encode the active environment, bot IDs, known issues, and workflow preferences.

## 2. Triage Diffs — Group by Agent & Purpose

A large dirty worktree (100+ files) is common after batch fix operations. Categorize changes into groups:

- **Group A — In-scope changes**: Files for the targeted agent/fix (modified topics, GPT prompts, steering files)
- **Group B — Fleet-wide collateral**: Changes applied across many agents by a batch script (e.g. comment block removal, line-ending normalization, EndDialog additions). Often NOT intended for this branch.
- **Group C — Untracked clutter**: Debug artifacts, backup folders, fix scripts, new topic files. Usually should stay untracked.

**Rule of thumb:** Keep one agent/environment per commit. Do NOT stage Group B or C without explicit direction. When in doubt, commit Group A only — the user can always amend.

## 3. Validate YAML Before Staging

Copilot Studio topic YAML must be parseable. Always validate modified `.mcs.yml` and `.topic.yaml` files:

```python
python3 -c "
import yaml, sys
for f in sys.argv[1:]:
    with open(f) as fh:
        data = yaml.safe_load(fh)
    kind = data.get('kind', '?')
    print(f'OK: {f} — kind={kind}')
" path/to/topic1.mcs.yml path/to/topic2.mcs.yml
```

Key checks:
- `kind: AdaptiveDialog` for topics, `kind: AgentDialog` for agent definitions
- No YAML syntax errors (Python yaml.safe_load will error otherwise)
- Valid trigger structure (`OnRecognizedIntent` / `OnUnknownIntent`)
- No unquoted special characters in `activity:` strings (commas, question marks, apostrophes break CB YAML parser)
- Line-ending normalization (CRLF→LF) is cosmetic but should be consistent

## 4. Scope Commits — One Agent, One Message

```
git add -- path/to/validated-file
git diff --cached --stat     # confirm what's staged
git commit -m "fix(TDA): add Topic.Answer variable to SearchAndSummarizeContent for answer persistence"
```

Commit message format: `type(scope): description`
- `fix(TDA):` — bug fix in Therapy Documentation Agent
- `feat(TheraDoc):` — new feature or topic
- `chore:` — steering files, CI, gitignore
- `docs:` — AGENTS.md, CLAUDE.md updates

**Never `git add -A` without triaging first.** The 200-file dirty worktree is the norm, not an exception.

## 5. Push to Remote

```bash
git push                           # pushes current branch to tracked upstream
git log --oneline --decorate -n 3  # verify push landed
```

## 6. Sync/Publish Copilot Studio Live Agent

Local git commits are NOT enough to claim live readiness. Push changes to the Dataverse `botcomponents` table and publish:

**Push via Dataverse REST API PATCH** (when LSP push fails):
```
az account get-access-token --resource <orgUrl>
PATCH /api/data/v9.2/botcomponents({id}) with { "data": "<yaml_content>" }
Verify by re-querying the record
```

**Publish via gateway API or pac:**
```
pac copilot publish --environment <orgUrl> --bot <botId>
# OR
POST /api/botmanagement/v1/environments/{envId}/bots/{botId}/publishv2-operations
```

## 7. Verify Live State

- Re-query Dataverse botcomponents to confirm PATCH landed
- Check `synchronizationstatus` on bot entity for publish state
- Run evaluation or Direct Line test to verify behavior
- **Do not claim sync or publish success based only on a local commit.**

## 8. Pitfalls

- The folder name (`Prod/` vs `Dev/`) is a workspace label, NOT the live environment. Check `.mcs/conn.json` or PAC auth context.
- Copy-pasted/re-named agent folders (`clone-cc`, `clone-db`, `hardened_historian`, etc.) are typically stale — do not commit their changes.
- Debug artifact directories (`live-debug-*`, `live-repair-*`, `backup_*`) contain session-specific exports — keep untracked.
- The `gitignore` may not cover `.bak/` or `backup_*/` directories — they'll show as untracked unless explicitly ignored.
- When coming from a Codex handoff, validate that Codex's scope (e.g. "commit, push, sync all appropriate changes") is well-defined before acting. A rich handoff prompt with specific triage steps is a signal that automation was stuck on scope ambiguity.
- User preference: Kevin does NOT want to be asked scope questions on large dirty worktrees. Commit Group A (the targeted agent's files) and push. Ask only when ALL groups are ambiguous.
- After editing topic YAMLs, ALWAYS re-query Dataverse botcomponents `data` field to confirm changes landed before publishing. File-only validation is NOT enough.
- Modified `Prod/` topics may map to the DEV agent in pac — the `Prod/` folder is just a workspace name.
