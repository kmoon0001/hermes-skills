---
name: update
description: Root-cause-first Copilot Studio update workflow. Use for /update requests, live topic/YAML repairs, Dataverse PATCH work, publish debugging, and syncing project AI guidance across Hermes, AGENTS, Kiro, Cursor, Antigravity, VS Code, and Codex.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [copilot-studio, dataverse, yaml, root-cause, project-sync, hooks]
    related_skills: [copilot-studio-validate, project-ai-knowledge-distribution, copilot-studio-manage-agent]
---

# /update

## Purpose

Use this skill when the user asks `/update`, asks to update Copilot Studio project guidance, or asks to fix/debug Copilot Studio agents, topics, publish failures, Dataverse PATCHes, or YAML/Power Fx issues.

Primary rule: root-cause first. Do not make live changes until the exact cause is known and the user explicitly asks for changes.

## Hard Rules

1. Read-only first: query live Dataverse/Copilot Studio state before patching.
2. Live UI is truth; local YAML is backup unless the user explicitly says to push it.
3. Never rewrite Copilot Studio YAML quoting, block scalars, formulas, or node structure unless explicitly asked.
4. Never remove clinical, compliance, regulatory, or guardrail content. Only add safety layers.
5. After any approved PATCH, re-query the exact live row and verify the persisted `data` field.
6. Do not trust `pac copilot publish` alone. It can be stale, cached, or silent.
7. If the user says diagnosis/root cause/stop/don't do anything: inspect only and report exact cause.

## Copilot Studio YAML / Power Fx Pitfalls

- `!IsBlank(x)` is invalid Power Fx. Use `Not(IsBlank(x))`.
- Global variables use `Global.variableName`, not `System.Var.Topic.variable`.
- Bare YAML scalars containing `:` can break parsing.
- Bare Power Fx object expressions like `={ contentBytes: ... }` can break YAML parsing because of colons/braces.
- Quoting can also be wrong when the schema expects a formula. Do not guess; compare against known-good live topics or docs.
- `yaml.safe_load` is not enough for Copilot Studio semantics. Use it only to catch YAML syntax errors, then inspect formula semantics separately.
- **EDITOR-BREAKING SCHEMA (high-value pitfall):** A topic `data` YAML that Dataverse accepts AND that PUBLISHES/validates fine can STILL **blank the authoring canvas and break the code editor** if the schema is not one the Copilot Studio editor can deserialize. Concrete case: a Question node with `inputType: file[]` + `property: turn.uploadedFiles` was PATCHed + published successfully (HTTP 204; the agent even worked in the test pane) but the authoring canvas rendered empty and the code editor would not load. The deserialize failure is silent — no error, just a frozen/blank editor. **Mitigation:** after ANY Dataverse PATCH to a topic `data` field, verify the EDITOR renders (open the topic in Copilot Studio and confirm nodes appear), NOT just that PATCH returned 204 / publish succeeded. If the canvas is blank after a PATCH, the `data` schema is the suspect — restore the known-good backup and re-implement with a schema the editor supports (see references/editor-breaking-schema.md).

## Required Workflow

1. Capture the user's scope: diagnose only, patch, publish, or sync guidance.
2. If diagnosing: perform read-only Dataverse/UI/file checks only.
3. Pull live topic/component data from Dataverse, not stale local backups.
4. Identify exact bad line(s), topic ID, and why the parser/validator rejects them.
5. Stop and report root cause unless the user explicitly approved a patch.
6. If patching: patch only the minimal field/line needed.
7. Re-query live Dataverse and diff the persisted field to prove only intended lines changed.
7.5. **Render check (critical after topic `data` PATCH):** open the topic in the Copilot Studio authoring canvas and confirm nodes actually render. A 204 PATCH + successful publish does NOT prove the editor can deserialize the `data` — a silent schema mismatch blanks the canvas (see EDITOR-BREAKING SCHEMA pitfall). If the canvas is blank, restore the known-good backup immediately.
8. Publish only if explicitly requested.
9. If a reusable process lesson was learned, update memory/skill/project guidance and run the sync hook.

## Project Guidance Sync Hook

When updating Copilot Studio rules, memories, skills, hooks, steering, or agent guidance, also update project AI context files where present:

- `copilot-studio-root-cause-rules.md` — central source of truth
- `AGENTS.md`
- `HERMES.md`
- `CLAUDE.md`
- `.cursorrules`
- `.cursor/rules/*.mdc`
- `.kiro/steering/*.md`
- `.kiro/skills/*.md`
- `.kiro/hooks/*.kiro.hook`
- `.github/copilot-instructions.md`
- `.vscode/*.md`
- `CODEX.md`
- `.codex/*.md`
- `.antigravity/*.md`

Run the helper script from this skill when available:

```bash
python ~/.hermes/profiles/coding-profile/skills/update/scripts/sync_copilot_studio_ai_context.py "D:/my agents copilot studio"
```

Completion criteria:
- central root-cause file exists
- pointer block exists in AGENTS/HERMES/CLAUDE/CODEX/Cursor/Kiro/GitHub/VS Code/Antigravity/Codex files that exist or can be safely created
- Kiro hook exists to remind future agents to sync guidance
- no live Copilot topic was patched unless explicitly requested

## Dataverse Query Pattern

Use `az rest` for auth and direct API calls:

```bash
az account get-access-token --resource "https://<org>.crm.dynamics.com" --query accessToken -o tsv
```

Topic query:

```text
/api/data/v9.2/botcomponents?$filter=_parentbotid_value eq '<botId>' and componenttype eq 9&$select=botcomponentid,name,data,description,statecode
```

After PATCH, always re-query the same `botcomponentid` and verify the exact persisted `data`.

## Publishing

- Prefer Copilot Studio UI publish when validation visibility matters.
- `pac copilot publish` can be stale/silent; do not treat it as sole proof.
- Correct bound action: `POST /api/data/v9.2/bots(<botId>)/Microsoft.Dynamics.CRM.PvaPublish`.
- `PvaPublish` may return HTTP 200 with empty response if validation fails before useful job creation.

## Common Pitfalls

1. Patching before root cause is known.
2. Trusting a 204/exit-0 without re-querying persisted data.
3. Treating one visible error as the only error; scan full live YAML text.
4. Breaking YAML by unquoting expressions containing `:` or `{}`.
5. Breaking formulas by quoting values the schema expects as expressions.
6. Restructuring topic YAML to satisfy a guessed cause.
7. Publishing during diagnosis-only work.
8. Updating Hermes memory/skills but forgetting project AI configs.
9. Trusting a 204 PATCH + successful publish as proof the topic is healthy. The authoring canvas can still be blank if the `data` schema isn't editor-deserializable (silent failure). Always do the render check (step 7.5).

## Verification Checklist

- [ ] User scope honored: read-only vs patch vs publish.
- [ ] Root cause includes exact file/topic/line/pattern.
- [ ] No live topic changes occurred without explicit approval.
- [ ] If patched, persisted Dataverse data was re-queried and diffed.
- [ ] **If a topic `data` field was PATCHed: authoring canvas render-checked (nodes visible, code editor opens).** Blank canvas = restore backup.
- [ ] Project guidance sync ran after reusable lesson updates.
- [ ] AGENTS.md, HERMES.md, CLAUDE.md, Cursor, Kiro, Antigravity, VS Code, and Codex pointers are present where possible.

## References

- `references/editor-breaking-schema.md` — silent topic-`data` PATCH failure: schema validates at publish but blanks the authoring canvas / breaks the code editor (reproduction, recovery, editor-compatible alternatives).
