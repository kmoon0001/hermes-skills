---
name: agent-builder-orchestrator
description: End-to-end Copilot Studio agent builder. ONE-SHOT pipeline: load this skill, provide a natural language description, and it runs architect → crafter → QA gate → deploy → test → iterate to 95%+. Closes the loop from requirements to production-ready agent. The "master" skill that coordinates all others.
version: 1.0.0
tags: [copilot-studio, orchestrator, pipeline, end-to-end]
---

# Agent Builder Orchestrator

## When to Use
- "Build an agent that does [X]"
- "I need a [discipline] [workflow] agent"
- User provides a description and wants a fully built, deployed, and tested agent
- **One load is all you need.** This skill chains architect → crafter → QA → deploy → eval → iterate.

## How to Use
1. Load `agent-builder-orchestrator`
2. User provides a description (or says "build [agent name]")
3. Pipeline runs automatically through all phases
4. Each phase calls the appropriate sub-skill and passes its output to the next
5. Only pause for user input at architect interview questions and deploy approval

---

## Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   agent-builder-orchestrator                             │
│                                                                          │
│  PHASE 0 ──→ LOAD agent-architect                                       │
│  ├── Interview user (8 questions)                                       │
│  └── Produce _agent_spec.yaml                                           │
│                                                                          │
│  PHASE 1 ──→ LOAD agent-crafter                                         │
│  ├── Read _agent_spec.yaml                                              │
│  ├── Generate ALL topic YAML files (per pattern templates)              │
│  ├── Generate instructions (componenttype 15)                           │
│  ├── Generate settings + conversation starters                          │
│  └── Write files to workspace                                           │
│                                                                          │
│  PHASE 2 ──→ LOAD agent-qa-gate                                         │
│  ├── Check G1-G11 against spec + generated YAML                         │
│  ├── Check G12 (editor-render via cua-driver)                           │
│  ├── Produce _qa_report.yaml                                            │
│  └── If FAIL → report blocking issues, STOP                             │
│      If PASS → continue                                                 │
│                                                                          │
│  PHASE 3 ──→ DEPLOY                                                     │
│  ├── [USER APPROVAL] "Ready to deploy to [environment]?"                 │
│  ├── PATCH each topic YAML to Dataverse (botcomponents)                  │
│  ├── PATCH instructions (componenttype 15)                              │
│  ├── Update settings                                                    │
│  └── pac copilot publish                                                 │
│                                                                          │
│  PHASE 4 ──→ VERIFY LIVE UI                                             │
│  ├── Open topic in browser via cua-driver                               │
│  ├── Confirm canvas renders (editor not blank)                          │
│  ├── Send test message in test pane                                     │
│  └── Confirm real response (not "Loading up...")                        │
│                                                                          │
│  PHASE 5 ──→ EVAL & ITERATE                                             │
│  ├── LOAD eval-optimization-loop                                        │
│  ├── Run SR eval → analyze failures → fix → re-run                     │
│  ├── Run Conv eval → analyze failures → fix → re-run                   │
│  └── Loop until both ≥ target OR plateau                               │
│                                                                          │
│  PHASE 6 ──→ REPORT                                                     │
│  ├── Final scores (SR + Conv)                                           │
│  ├── Topic inventory (created)                                          │
│  ├── Publish status                                                     │
│  ├── Editor-render confirmation                                         │
│  └── Any remaining P1 issues for awareness                               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Details

### Phase 0: Architecture (load agent-architect)
1. Ask the 8 interview questions in sequence from `agent-architect`
2. After each answer, synthesize into the structured spec fields
3. After all 8: produce complete `_agent_spec.yaml`
4. Save to workspace root

**Output:** `_agent_spec.yaml`

### Phase 1: Crafting (load agent-crafter)
1. Read `_agent_spec.yaml`
2. For each topic in spec.topics:
   - Select the correct pattern template (A/B/C/D/E) based on `topic.pattern`
   - Template parameters: `{topic_name}`, `{discipline}`, `{document_type}`, `{note_type}`, etc. from spec
   - Write to `topics/{topic_name}.mcs.yml`
3. Generate instructions text using the template in agent-crafter §Instructions Generation
   - Use spec.instructions_outline for section ordering
   - Apply generation rules (no unconditional bans, no hard source restrictions, EVAL CONTEXT required)
4. Generate settings per spec.settings
5. Generate conversation starters
6. Write agent.mcs.yml or equivalent
7. Validate: pyyaml safe_load on each file
8. Report: "Created N topic files, instructions, settings"

**Output:** Topic YAML files + instructions + settings

### Phase 2: QA Gate (load agent-qa-gate)
1. Run QA checks G1-G11 against the generated files
2. For G12 (editor render): only possible if browser is available and user approves
3. Produce `_qa_report.yaml`

**Decision:**
- **PASS** → proceed to Phase 3
- **FAIL** → report blocking issues with severity + line references. STOP. Do NOT deploy.
  - For each failure, show the exact topic file + the YAML snippet that violates the check
  - Offer to fix and re-run Phase 1+2, or let user fix manually

### Phase 3: Deploy
Before deploy, ask user:
- "Ready to deploy [agent_name] to [environment]? This will PATCH live topics and publish. [y/N]"
- Environment defaults to the one in spec or last `pac auth create` target

Deploy steps:
1. `pac auth create --environment <org_url>` (if not already)
2. For each topic YAML: PATCH `botcomponents` data field
   ```bash
   # If az is working:
   TOKEN=$(az account get-access-token --resource "https://<org>.crm.dynamics.com/" --query accessToken -o tsv)
   curl -X PATCH "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<id>)" \
     -H "Authorization: Bearer $TOKEN" -H "If-Match: *" \
     -H "Content-Type: application/json" \
     -d "{\"value\": \"<yaml_content>\"}"
   ```
   If `az` is 401-blocked (this machine): ask user to use browser code editor OR
   defer to a session where `az` works.
3. PATCH instructions (componenttype 15 data)
4. **G15: Pre-Publish Checklist** (from agent-qa-gate G15) — validate before publishing:
   - No duplicate topics, no null content, check sync status isn't stuck
   - Verify no orphan flow references (G14)
5. Publish:
   ```bash
   pac copilot publish --bot <bot_id> --environment https://<org>.crm.dynamics.com/
   ```
6. **G16: Post-Publish Verification** — query `synchronizationstatus` directly:
   ```python
   url = f'{BASE}/bots({botId})?$select=synchronizationstatus,publishedon'
   # Parse lastFinishedPublishOperation.status — do NOT trust CLI exit code
   ```
   - If `Status: Failed` → inspect `diagnosticDetails[].diagnosticList[]` for root cause
   - If `Status: Succeeded` → confirm `publishedon` is recent (< 2 min ago)
7. **CRITICAL:** After publish, if the Copilot Studio tab was open, Shift+Reload
   to clear UI cache. Otherwise stale cached state may overwrite API fixes.

**Alternative: Microsoft manage-agent CLI** (if VS Code extension is installed):
```bash
# Clone an existing agent to local workspace:
cd ~/workspace
node /path/to/manage-agent.bundle.js clone --environment-url <org> --agent-id <botId> --output-dir ./agent-workspace

# Push changes back:
cd ./agent-workspace
node /path/to/manage-agent.bundle.js push --environment-url <org>

# Verify differences before push:
node /path/to/manage-agent.bundle.js changes --environment-url <org>
```
The manage-agent CLI uses the VS Code extension's LanguageServerHost LSP binary — same protocol as the extension. It handles authentication via interactive browser login (tokens cached ~90 days).

**For production deployment, prefer surgical solution packaging** (Phase 3a) over individual PATCH+topic-publish.

### Phase 3a: Surgical Solution Packaging (alternative deploy — for moving between envs)
When deploying between environments (staging → dev), use surgical solution packages:
1. Export the source agent as a solution: `pac solution export --name <solution> --managed`
2. Extract and scrub the zip per `surgical-solution-packaging.md`:
   - Remove `<Entities>`, `<EntityRelationships>`, `<Workflows>` from customizations.xml
   - Rewrite `<RootComponents>` to contain only the target bot's schema
   - Extract only `botcomponents/<schema>*` and `bots/<schema>*` entries
3. Repackage and import: `pac solution import --path ./Surgical.zip --publish-changes --force-overwrite`
4. Verify bot exists and is active after import

### Phase 4: Live UI Verification
1. Open `.../bots/<botId>/adaptive/<topicId>` in browser
2. Confirm `flow-editor-container` has visible child nodes (Question, Condition, Action)
3. If blank → **CRITICAL FAILURE**. Revert. The YAML has an editor-invalid node.
4. Send 1 test message in test pane
5. Confirm bot responds with a real answer (not "Loading up..." hang)

### Phase 5: Eval & Iterate (load eval-optimization-loop)
1. Run Conv eval first (20 cases, faster signal)
2. Analyze failures using eval-optimization-loop analyzer
3. Apply fixes (batch by category)
4. Re-run Conv → confirm improvement
5. Run SR eval (100 cases)
6. Analyze, fix, re-run
7. Loop until both ≥ spec.sr_target and spec.conv_target
8. If plateau: document remaining failures, exit

### Phase 6: Report
Final summary:
```
=== Agent Builder Report: [agent_name] ===
Spec: [purpose]
Topics created: N
  - [topic 1] — [pattern]
  - [topic 2] — [pattern]
QA Gate: PASS (12/12)
Deploy: [timestamp]
Publish: Succeeded [timestamp]
Editor render: CONFIRMED
Eval: SR = [N]%  Conv = [N]%  (target ≥ [N]%)
Status: READY
Remaining P1: [N] (non-blocking)
```

---

## Error Recovery Patterns

### QA Gate FAIL
- Report which gate(s) failed with exact file + line + expected vs actual
- Recommend: "Run agent-crafter with corrected spec" OR "Manual fix in files"
- Do NOT proceed to deploy until QA PASS

### Publish FAIL
- Check `synchronizationstatus` diagnostic details for exact componentId + errorCode
- Common causes: missing EndDialog, system topic PATCH, SearchSpecificFiles left in
- Fix the error, re-PATCH, re-publish
- If `pac copilot publish` returns stale "Failed [timestamp]", try Shift+Reload browser then UI publish

### Eval Stuck Run
- Poll with long timeout (seq 1 50, 30s intervals)
- If stuck >2x normal duration: treat as backend flake, wait for timeout, re-start

### Editor Blank
- REVERT immediately. The YAML can't render. Fix the root cause (likely file[] or turn.uploadedFiles).
- Re-run Phase 1+2 before attempting deploy again.

---

## References (authoritative)
- `agent-architect` — Phase 0 (interview + spec)
- `agent-crafter` — Phase 1 (YAML generation + pattern templates)
- `agent-qa-gate` — Phase 2 (12-gate verification)
- `agent-audit-protocol` — deeper structural audit if QA needs expansion
- `eval-optimization-loop` — Phase 5 (run, analyze, fix, iterate)
- `agent-builder` — alternative for single-topic additions (not full build)
- `copilot-studio-yaml-reference` — YAML schema reference
- `copilot-studio-validate` — schema validation
- `references/theradoc-workbench-optimization.md` — 45-topic optimization case study with 30+ fix patterns
- Microsoft Learn Copilot Studio: https://learn.microsoft.com/microsoft-copilot-studio/
- Topic Authoring: https://learn.microsoft.com/microsoft-copilot-studio/authoring-create-edit-topics
- Evaluation: https://learn.microsoft.com/microsoft-copilot-studio/advanced-ai-evaluation
- Knowledge Sources: https://learn.microsoft.com/microsoft-copilot-studio/knowledge-copilot-studio
