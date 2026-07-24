---
name: agent-builder
description: Scaffold, build, and deploy a Copilot Studio agent or topic from a spec. Adapted from Kiro's full-agent-audit into the Hermes harness. Use when creating a new agent, adding a topic, or doing a from-spec build of a Pacific Coast or Ensign therapy compliance agent. Bakes in the hard-won lessons - pac auth over az, editor-render gate, commit-before-change, and the File plus Text dual-input pattern.
---

# agent-builder (Hermes-adapted, from Kiro)

Build or scaffold a Copilot Studio agent / topic from a spec, then deploy and
verify in the live UI. This is the BUILD path (greenfield + additive topic adds).
For iterative score-improvement loops, load `agent-optimizer` instead.

## When to use
- "Build a new agent for <X>"
- "Add a topic that does <Y> to <agent>"
- "Scaffold the <agent> structure"
- First-time agent creation or a net-new capability topic

## Hard rules (non-negotiable)
1. **Auth = `pac` not `az`.** See copilot-studio-common-reference §Auth Patterns.
2. **Never ship `inputType: file[]` or `turn.uploadedFiles`** — breaks editor (blank canvas freeze).
   Use the File+Text dual-input pattern (copilot-studio-common-reference §File+Text Dual-Input Pattern).
3. **Commit before every change.** `git init` → `git add -A` → `git commit -q`. Strict `.gitignore`.
4. **Live UI = source of truth.** After deploy, run the editor-render gate
   (copilot-studio-common-reference §Editor-Render Gate). 204 ≠ done.
5. **Additive only.** Do not remove capabilities/nodes unless the user approves.

## Build workflow (ordered)

### 0. Setup & auth
Primary: `pac auth create --environment https://pccapackage.crm.dynamics.com/`
Fallback: `az login --tenant 03cc92c3-986c-4cf4-ae27-1478cf99d17f`
Full auth reference: copilot-studio-common-reference §Auth Patterns

### 1. Local repo + backup (commit-before-change)
```
cd /c/Users/kevin/Desktop
git rev-parse 2>/dev/null || git init
printf '*\n!topic1_*.yaml\n!.gitignore\n' > .gitignore   # strict: track only fix files
# pull current live topic as backup BEFORE editing:
#   write FetchXML to query.xml, run: pac org fetch -xf query.xml > live_backup.xml
git add -A && git commit -q -m "backup before build"
```

### 2. Author the topic YAML
Use `copilot-studio-author-topic` templates. Minimum structure:
- `#` comment line as first line (required for type-9 topic data).
- `kind: Topic` header with `name:`, `conversationStarter:`.
- At least 5 trigger phrases.
- Every branch ends in an endpoint (EndDialog / SendActivity / Message).
- OnError handler with structured JSON.

### 3. File+Text dual-input pattern (USE THIS, not file[])
For document-upload topics, use a 3-branch ConditionGroup — DO NOT use file[]:
```
- kind: Question
  id: question_doc_input
  variable: init:Topic.DocumentText
  prompt: Paste therapy documentation text, or upload PDF(s) for audit.
  entity: StringPrebuiltEntity
- kind: ConditionGroup
  id: conditionGroup_input_check
  conditions:
    - id: branch_file
      condition: "=!IsBlank(Topic.DocumentText)"      # text pasted
      actions:
        - kind: SearchAndSummarizeContent
          id: sasc_text
          userInput: "=Topic.DocumentText"
          # ... audit prompt
    - id: branch_upload
      condition: "=!IsBlank(First(System.Activity.Attachments))"   # file uploaded
      actions:
        - kind: SearchAndSummarizeContent
          id: sasc_file
          # platform auto-attaches uploaded file content to SASC
          userInput: "=Topic.DocumentText"
    - id: branch_none
      condition: "=true"
      actions:
        - kind: GotoAction
          id: goto_back
          action: question_doc_input      # re-ask
```
Rule: Branch1 attachments → file path. Branch2 text → SASC. Branch3 → GotoAction
back to Question. Never skip the text-check or the GotoAction.

### 4. Validate before deploy
Load `copilot-studio-validate` and run schema + LSP checks on the YAML.

### 5. Deploy (PATCH live + publish)
PATCH the `botcomponent` `data` field via Dataverse. Preferred channel is `pac`
authenticated; since `pac` has no generic PATCH verb, use the browser session OR
`az` token when available:
- If `az` works: `curl -X PATCH .../api/data/v9.2/botcomponents(<id>) -H "Authorization:
  Bearer $TOKEN" -H "If-Match: *"` with `{"data":"<yaml>"}`.
- If `az` 401s: use `pac` session indirectly — restore via the Copilot Studio UI
  code-editor (paste corrected YAML) OR wait for `az login`. NEVER ship file[].
Then publish:
```
pac copilot publish --bot 9e7b871d-1d80-f111-ab0f-000d3a5b0d6c --environment https://pccapackage.crm.dynamics.com/
```
Verify publish really succeeded (not cached):
```
pac org fetch -xf syncstatus.xml   # bot synchronizationstatus -> lastFinishedPublishOperation.status == "Succeeded"
```
### 6. EDITOR-RENDER GATE (prevents freezes)

See copilot-studio-common-reference §Editor-Render Gate. Do NOT skip this step.

## Deliverables
- Local YAML file(s) committed in git.
- Published agent verified in live UI (canvas renders + test message works).
- Short status: what was built, publish status, any caveats.

## Pitfalls (from real incidents)
Common pitfalls across all skills: copilot-studio-common-reference §Common Pitfalls.
- **`file[]`/`turn.uploadedFiles` → blank canvas.** Use dual-input pattern.
- **`az` 401 on pccapackage → use `pac auth create`.**
- **`pac copilot list` stale** → check `synchronizationstatus`, not the list.

## Relationship to Full Pipeline
`agent-builder` is for single-topic additions or small agent scaffolding. For a
**complete end-to-end build** (requirements → all topics → QA gate → deploy →
test → iterate to 95%+), load `agent-builder-orchestrator` instead — it chains
architect → crafter → QA gate → deploy → eval in one shot.

## References
- `references/editor-freeze-diagnostic.md` — full root-cause + recovery for the blank/frozen
  authoring canvas (the file[] trap, pac vs az write-channel reality, recovery steps).
  Read this the moment a canvas renders blank or "code editor won't load."
- `agent-builder-orchestrator` — full end-to-end pipeline (supersedes this for complete builds)
- `agent-architect` — requirements elicitation (design phase)
- `agent-qa-gate` — 18-gate verification (run BEFORE deploy)
- Kiro source: `.codex/worktrees/3170/my agents copilot studio/.kiro/skills/full-agent-audit.md`
- `copilot-studio-author-topic`, `copilot-studio-validate`, `copilot-studio-pipeline`
- Dataverse: botcomponent parentbotid lookup, componenttype 9=topic 15=instructions
