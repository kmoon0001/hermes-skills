---
name: agent-qa-gate
description: "Independent QA verification gate for Copilot Studio agent builds. After agent-crafter (or agent-builder) produces YAML, run this gate BEFORE deploy. Checks: YAML validity, MS Learn compliance, missing components, logic errors, infinite loops, dead branches, spec alignment. Produces PASS/FAIL verdict. If PASS, deploy and eval proceed. If FAIL, block and report."
version: 1.0.0
tags: [copilot-studio, qa, verification, gate]
---

# Agent QA Gate

## When to Use
- AFTER agent-crafter or agent-builder produces YAML
- BEFORE deploying (PATCH + publish)
- After ANY manual topic edits
- Before handing off to eval-optimization-loop

## NEVER skip the QA gate. A 204 from PATCH does NOT mean the agent is correct.

---

## QA Checklist (ALL must pass)

### G1: Spec Alignment
Read `_agent_spec.yaml` (from agent-architect). Verify the built YAML matches:

- [ ] Agent purpose matches spec.purpose
- [ ] All spec.topics exist as YAML files
- [ ] No extra topics beyond spec
- [ ] Each topic's pattern matches spec.topics[N].pattern
- [ ] Knowledge sources match spec list
- [ ] Connected agents match spec (or empty if standalone)
- [ ] Settings match spec.settings
- [ ] Instructions outline matches spec (at minimum: Role, Scope, Constraints, Response Format, EVAL CONTEXT)

**If any mismatch -> FAIL** — the build didn't implement what was designed.

### G2: Structural Integrity (per topic YAML)
Every custom topic file checked:

- [ ] Valid YAML (pyyaml safe_load passes)
- [ ] Single root `kind:` — no extra roots
- [ ] `kind: AdaptiveDialog` (for custom topics)
- [ ] `name:` matches intended topic name
- [ ] No BOM characters (no `\ufeff`)
- [ ] `activity:` strings with colons are quoted: `activity: "I need: SBAR"` not `activity: I need: SBAR`
- [ ] No `SearchSpecificFiles` or `SearchSpecificKnowledgeSources`
- [ ] No `inputType: file[]` or `property: turn.uploadedFiles` — **BLANK EDITOR FREEZE**

### G3: Termination (No Leaks, No Loops)
Every custom topic:

- [ ] Has `EndDialog` with `clearTopicQueue: true` as last action
- [ ] Has `SendActivity` before `EndDialog` (outputs =Topic.Answer) — prevents unsupportedactivity.notextresponse
- [ ] No GotoAction without exit condition (infinite loop check)
- [ ] No empty ConditionGroup elseActions (silent stop)
- [ ] OnError topic exists and is NOT blank

**System topics check:**
- [ ] ConversationStart has `EndDialog(clearTopicQueue:true)` if it has custom SendActivity
- [ ] Fallback has `SearchAndSummarizeContent` + `EndDialog` — NOT "I am not sure how to help"

### G4: SearchAndSummarizeContent Completeness
Every SASC node:

- [ ] Has `userInput` (=System.Activity.Text or =Concatenate(...))
- [ ] Has `additionalInstructions` (at least a role prompt — not empty)
- [ ] Has `responseCaptureType: FullResponse`
- [ ] Has `variable: Topic.Answer` (or `Global.Answer`) — missing variable causes `Identifier not recognized` on publish. Must be at SAME indent as `responseCaptureType`; deeper indent makes it a child property -> `Missing required property 'UserInput'` on publish.
- [ ] No `=Concatenate(...)` with `Text(Now(),...)` in `userInput` — Power Fx in userInput causes `The function 'Text' has some invalid arguments` on publish. Replace with `=System.Activity.Text` and move instruction logic to `additionalInstructions`.
- [ ] Has `allowLatencyMessage: false`
- [ ] `applyModelKnowledgeSetting` is `true` or absent
- [ ] Has `fileSearchDataSource` OR `customDataSource` OR neither (let platform search all KBs)
- [ ] No empty/bare SASC (id only — these produce zero output, -20 to -30 pts)

### G5: Question Nodes
- [ ] No `entity: FilePrebuiltEntity` on any Question — blocks text input, kills Conv evals
- [ ] If Question exists (intake/upload), entity is `StringPrebuiltEntity`
- [ ] If Question with upload, has 3-branch ConditionGroup (file/text/none) after it
- [ ] Question has `allowInterruption: false`

### G6: Trigger Phrases
- [ ] Each custom topic has >=5 trigger phrases (MS Learn minimum)
- [ ] No exact duplicate trigger phrases across topics
- [ ] No near-duplicates (Jaccard similarity < 60%)
- [ ] Trigger phrases are natural language variety (questions + commands + statements)
- [ ] No misspellings

### G7: modelDescription
- [ ] Every custom topic has a `modelDescription` field
- [ ] Describes WHAT the topic does (not implementation details)
- [ ] Unique across topics (no two with same description)
- [ ] Matches trigger intent
- [ ] Not generic ("Handles user questions")

### G8: Connected Agents & Tools
- [ ] Connected agents (if any) have `statecode=0` (active)
- [ ] No placeholder flow IDs (GUIDs like `11111111-...` or `66666666-...`)
- [ ] Schema names match live Dataverse records
- [ ] No stale connections to deprovisioned agents
- [ ] InvokeFlowAction with action: field is wrong -> use InvokeConnectedAction instead

### G9: Instructions (agent.mcs.yml or componenttype 15)
- [ ] Length 2000-6000 chars
- [ ] No BOM characters
- [ ] No mid-word splices at line boundaries
- [ ] No contradictory mandates ("prioritize completeness" + "under 4 sentences")
- [ ] EVALUATION CONTEXT section present (DATA-SPARSE + DATA-RICH subsections)
- [ ] No "No headers/markdown/tables" in responseInstructions
- [ ] No "under N sentences" length caps
- [ ] Mission clarity: agent says what it IS and IS NOT
- [ ] Source restrictions are "soft" not "hard" (use as primary reference, may use model knowledge)

### G10: Settings (agent config)
- [ ] Content Moderation: Medium for healthcare, High for general
- [ ] Model Knowledge: ON
- [ ] Semantic Search: ON
- [ ] File Analysis: ON (if agent handles documents)
- [ ] Latency Messages: OFF
- [ ] Web Search: OFF (for PHI/compliance agents)
- [ ] Conversation starters: 5-10 matching core workflows

### G11: Knowledge Sources
- [ ] All KBs have descriptive names (not "Doc1", "Untitled")
- [ ] All KBs have 1-2 sentence descriptions (critical for generative routing)
- [ ] Official toggle ON for authoritative/regulatory sources
- [ ] No duplicate content across KBs
- [ ] Files under 5MB (MS Learn eval limit)

### G12: Editor Render Test (THE MOST IMPORTANT — prevents blank canvas)
This step MUST be done with cua-driver. It's the only way to catch the file[] freeze before the user sees it.

- [ ] Open topic in Copilot Studio browser editor
- [ ] Confirm `flow-editor-container` has visible child nodes (Question, Condition, Action blocks)
- [ ] If blank -> REVERT YAML. The editor cannot render what you wrote. Fix before deploy.

### G13: Variable Scope Consistency
Every topic that uses SearchAndSummarizeContent:

- [ ] SASC output variable matches SendActivity reference: if SASC uses `variable: Global.Answer`, SendActivity must use `{Global.Answer}` (NOT `{Topic.Answer}`)
- [ ] No Topic.Answer references in topics where the SASC writes to Global.Answer (or vice versa)
- [ ] Global variables declared as Bot Variable (V2) components with matching names
- [ ] No variable name collisions across topics (two topics writing to different scopes with the same name)
- [ ] If using Topic.Answer, verify it is declared in the topic's variable: mappings (not assumed)  
- [ ] Variable initialization timeout set (default 30000ms or explicit)

**Common failure:** SASC writes to `variable: Global.Answer` but later `SendActivity` reads `{Topic.Answer}` - runtime empty output. Publish fails with `Identifier not recognized in expression: Topic.Answer`. This was the #1 blocker on a 45-topic agent with 22 SASC nodes.

**Indentation pitfall:** When adding `variable:` to an existing SASC, normalize line endings first: `data.replace('\r\n', '\n')`, edit with `\n`, then `fixed.replace('\n', '\r\n')` back. A regex that consumes trailing whitespace without normalizing first can eat the next line's indent - `variable:` lands at wrong depth -> `Missing required property 'UserInput'` on publish.

### G14: Orphan Flow Detection (Pre-Publish Gate)
Run this BEFORE every publish to catch the #1 silent publish failure:

- [ ] Query ALL active topics for InvokeFlowAction, InvokeConnectedAction, or flowId references:
  ```fetchxml
  <fetch><entity name="botcomponent"><filter>
    <condition attribute="parentbotid" operator="eq" value="{botId}"/>
  </filter></entity></fetch>
  ```
  Parse `data` fields for `flowId:` or `action: pcca_agent.action` patterns.
- [ ] For every flowId found: verify the workflow exists in the `workflows` table with `statecode=0` (Activated)
  ```fetchxml
  <fetch><entity name="workflow"><filter>
    <condition attribute="workflowid" operator="eq" value="{flowId}"/>
  </filter></entity></fetch>
  ```
- [ ] If flow not found or deactivated → **BLOCK PUBLISH**. The topic referencing it will cause:
  - "Node is unknown to the system" (for InvokeConnectedAction)
  - "Missing required property 'FlowId'" (for InvokeFlowAction without flowId)
  - Or SILENT publish failure with no useful diagnostics
- [ ] Check for managed flows (`ismanaged=True` in workflow table):
  - Managed flows CANNOT be deleted via Dataverse API (405 Method Not Allowed)
  - They MUST be removed from Copilot Studio UI → Flows tab → Remove
  - Managed flows in Draft state still block publish
- [ ] Check for `action:` field on `InvokeFlowAction` nodes (should be `flowId:`)
  - `InvokeFlowAction` with `action:` → change to `InvokeConnectedAction` with `action:`
  - `InvokeConnectedAction` is the correct kind for cross-agent action references
- [ ] No orphaned workflow definitions (workflows with no active topics referencing them but still linked to bot)

**Common source of orphan flows:** CrossAgentAuditLog and Compliance Audit flows auto-created by Copilot Studio when connecting agents. These accumulate as bots evolve and old topics are replaced. Query `workflows` table filtering `contains(name,'CrossAgent')` or `contains(name,'ComplianceAudit')` to find candidates.

**Key insight (proven 2026-07-16):** Output binding errors ("Output binding 'X' is not found, refresh this flow to get the latest bindings") are ALWAYS flow-side, NEVER topic-side. Adding 52 outputType.properties to a topic had ZERO effect on binding errors. The bindings are stored in the Power Automate flow's registered input schema, not in the topic YAML. Fix: remove/update the flow, NOT the topic.

### G15: Pre-Publish Checklist (Gate Before Deploy)
Run this gate immediately before `pac copilot publish` — it catches failures that PATCH validation misses:

- [ ] **No duplicate topics** — query botcomponents by name, verify no two active topics have the same name or overlapping trigger phrases:
  ```fetchxml
  <fetch><entity name=\"botcomponent\"><filter>
    <condition attribute=\"parentbotid\" operator=\"eq\" value=\"{botId}\"/>
    <condition attribute=\"statecode\" operator=\"eq\" value=\"0\"/>
  </filter></entity></fetch>
  ```
  Group by name — if count > 1 for any name → BLOCK
- [ ] **No NULL/empty topic content** — check all statecode=0 botcomponents have non-null `data` fields
- [ ] **Bot sync status is not stuck** — query `bots({botId})/synchronizationstatus`:
  - If `lastFinishedPublishOperation.status` = "Failed" → clear investigation first (don't publish on top of broken state)
  - If synchronization is "Synchronizing" with no progress for >5 min → wait or investigate before publish
  - If the LAST publish failed with "Could not find an entity with id //" → investigate orphan dialog references before re-publishing (cached failure)
- [ ] **All topic content parses as valid YAML** — verify every active topic's `data` field parses without yaml.YAMLError before PATCH
- [ ] **Work IQ toggle is verified** — if workIq is enabled, eval responses will be auth prompts. Check agent settings:
  ```fetchxml
  <fetch version=\"1.0\" output-format=\"xml-platform\" mapping=\"logical\">
    <entity name=\"bot\"><filter><condition attribute=\"botid\" operator=\"eq\" value=\"{botId}\"/></filter></entity>
  </fetch>
  ```
  Parse settings for `workIq` — if present and set, verify user wants it (generally OFF for healthcare agents)
- [ ] **Publish cache is stale-safe** — `pac copilot publish` may report stale cached failures. Always verify after publish by querying `synchronizationstatus` directly.

### G16: Post-Publish Verification (Gate After Deploy)
Run this immediately AFTER `pac copilot publish` completes. **Do NOT trust the CLI exit code.**

- [ ] Query `bots({botId})/synchronizationstatus` for `lastFinishedPublishOperation`
- [ ] Parse `status` field:
  - `"Succeeded"` → verify `publishedon` is within the last 2 minutes (confirming fresh publish, not cached)
  - `"Failed"` → inspect `diagnosticDetails[].diagnosticList[]` for root cause:
    - Component ID (`component=`) and action ID (`action=`) match which topic failed
    - Error codes: "Output binding" → orphan flow; "Missing required property" → schema issue; "Node is unknown" → invalid action reference
  - `"Synchronizing"` → wait 30s, retry (may still be in progress)
- [ ] Publish timestamp is fresh: compare `publishedon` from bot record (before publish) with post-publish value
- [ ] If publish succeeded but timestamp is OLD (same as before) → the publish was no-op / cached failure. Investigate diagnostics.
- [ ] **Report the actual result** — not the CLI output. `pac copilot publish` reported `Failed []` means empty error list (stale), but the API shows the real errors.

**Verification Script:**
```python
# After publish completes:
url = f'{BASE}/bots({botId})?$select=synchronizationstatus,publishedon'
req = urllib.request.Request(url, headers=H_GET)
with urllib.request.urlopen(req, timeout=15) as r:
    d = json.loads(r.read())
ss = d.get('synchronizationstatus','{}')
lfp = ss.get('lastFinishedPublishOperation', {})
status = lfp.get('status')
if status == 'Succeeded':
    print('PUBLISH: SUCCESS')
elif status == 'Failed':
    # Parse and report each error
    for detail in lfp.get('diagnosticDetails', []):
        for dl in detail.get('diagnosticList', []):
            print(f'  ERROR: {dl.get(\"errorMessage\",\"\")}')
```

### G17: Text/Content Corruption Detection
Inspect ALL content being PATCHed for corruption patterns BEFORE sending to Dataverse:

- [ ] **No duplicated section headers** — if `RESPONSE_LENGTH`, `MANDATORY_AUDIT`, or `instructions:` appears more than once in the same component, content is CORRUPTED — do NOT proceed
- [ ] **No mid-word splices** — look for text that ends abruptly mid-word followed by text from a different edit (e.g., `multifactoPT_Specialist`, `findiOT_Specialist`, `documentatiSLP`). This means PATCH operations landed at wrong cursor positions
- [ ] **No BOM characters** — strip `\\ufeff` (BOM / zero-width no-break space) before PATCH; BOM causes silent schema validation failures
- [ ] **No repeated agent identity** — if the agent's name or role phrase (e.g., `PT_Specialist - Physical Therapy`) appears more than once in the instructions block, it's duplicated content
- [ ] **No smashed-together text** — check for words concatenated at section boundaries without spaces (e.g., `requirementswith`, `requirementsments`)
- [ ] **No multiple root kinds** — verify single `kind: AdaptiveDialog` or `kind: GptComponentMetadata` per component
- [ ] **CRLF consistency** — ensure whole file uses either LF or CRLF, not mixed (mixing causes YAML parser errors in some environments)

**Common sources:** Multiple partial PATCHes to the same botcomponent, race conditions from parallel edits, paste from different encodings.

### G18: Topic Architecture Validation
Validate the agent's topic architecture matches MS Learn best practices for generative orchestration:

- [ ] **Topic count** — 8-12 custom topics per MS Learn recommendation. >15 topics → routing quality degrades (orchestrator has too many choices)
- [ ] **No bare/neglected topics** — every topic has at minimum: trigger phrases, modelDescription, SendActivity + EndDialog. Bare topics (id-only, no content) silently route incorrectly
- [ ] **Trigger phrase diversity** — each topic has 5+ trigger phrases covering: questions, commands, statements, multi-turn context
- [ ] **Trigger phrase uniqueness** — Jaccard similarity < 60% between any two topics' trigger sets
- [ ] **modelDescription alignment** — each description is unique AND accurately describes the topic's intent (not generic like "Handles user questions")
- [ ] **No GPT55Chat type references** — should be GPT5Chat (GPT55 doesn't exist, causes 400 errors on PATCH)
- [ ] **Conversation starters** — 5-10 starters that cover the agent's full capability range, each with BOTH `title:` (≤40 chars) and `text:` fields
- [ ] **Web search OFF** for any agent handling PHI, PII, or Medicare/healthcare data (fleet rule)

---

Produce a report file `_qa_report.yaml`:

```yaml
qa_version: 1.0
agent_name: "[name]"
timestamp: "[ISO 8601]"

overall: PASS            # PASS or FAIL
gates:
  G1_spec_alignment: PASS
  G2_structural: PASS
  G3_termination: PASS
  G4_sasc_completeness: PASS
  G5_question_nodes: PASS
  G6_triggers: PASS
  G7_model_descriptions: PASS
  G8_connected_agents: PASS
  G9_instructions: PASS
  G10_settings: PASS
  G11_knowledge: PASS
  G12_editor_render: PASS
  G13_variable_scope: PASS
  G14_orphan_flow_detection: PASS

failures:
  - gate: G2_structural
    topic: "topic_example"
    issue: "Missing EndDialog after SendActivity"
    severity: P0
  # ... per failure

summary:
  total_checks: 14
  passed: 13
  failed: 0
  verdict: "Agent ready for deploy and eval."
  # If FAIL:
  # verdict: "Blocked. N blocking issues found. Fix and re-run QA gate."
```

---

## Process Rules

1. **QA is independent.** The agent that builds the YAML does NOT check its own work. A separate QA run reads the files fresh.
2. **Zero tolerance on P0.** Any P0 (structural integrity, blank editor, missing EndDialog, FilePrebuiltEntity) -> FAIL, block deploy.
3. **P1 warnings pass but log.** Reusable triggers, missing modelDescription, thin trigger counts -> PASS with warnings.
4. **Editor render test is mandatory.** If cua-driver can't reach the browser window (minimized), restore it first. Do not skip this gate.
5. **Re-run QA after every PATCH.** Even a single-line fix can break YAML indentation.

## Related Skills
- `agent-architect` — produces the spec this gate checks against
- `agent-audit-protocol` — deeper 12-domain structural audit (use AFTER QA passes, before deploy)
- `agent-crafter` — produces the YAML this gate verifies
- `copilot-studio-validate` — schema validation (complements this gate)
- `eval-optimization-loop` — runs after QA passes  
- `references/orphan-flow-detection.md` — pre-publish flow validation script (G14/G15 companion)
