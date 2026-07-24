---
name: agent-audit-protocol
description: "Unified agent audit protocol — merged best of agent-comprehensive-inspection (12-domain deep dive, fix patterns A-F) and therapy-fleet-agent-audit (P0/P1 severity, workspace investigation, parallel fleet sweep, environment registries). End-to-end audit and remediation for any Copilot Studio agent. Targets 95%+ SR/Conv. Use BEFORE deployment, after major changes, or for persistent eval failures. Supersedes agent-comprehensive-inspection and therapy-fleet-agent-audit."
version: 2.0.0
tags: [copilot-studio, audit, inspection, pre-flight, evaluation, optimization]
---

# Agent Audit Protocol (unified)

## When to Use
- Inspect/audit/evaluate ANY Copilot Studio agent
- Pre-deployment readiness checks
- Start a new optimization cycle
- After major topic/instruction changes
- Debug persistent eval failures
- Full **fleet sweep** across N agents

## Auth (unified — pac primary, az fallback)
Primary: `pac auth create --environment https://<org>.crm.dynamics.com/`
Fallback: `az login --tenant 03cc92c3-986c-4cf4-ae27-1478cf99d17f`
Full auth reference: copilot-studio-common-reference §Auth Patterns.
**Rule:** `az` 401s on this machine for pccapackage. Use `pac auth create`.

## Hard Rules (non-negotiable)
1. **Auth = `pac auth create` not `az`** — see above.
2. **Never ship `inputType: file[]` / `turn.uploadedFiles`** — breaks editor (blank canvas freeze, confirmed 2026-07-16). Use File+Text 3-branch dual-input pattern instead.
3. **Commit before any PATCH** — on dirty multi-agent repos commit ONLY this bot's audit/fix artifacts (not `git add -A`).
4. **Live UI = source of truth** — API 204 means write landed, NOT that editor renders. Verify via cua-driver. After publish, verify `synchronizationstatus` + `publishedon` (Pacific), not `pac copilot publish` CLI text alone.
5. **Additive-only fixes** unless user approves removal.
6. **Audit live `data` only** for new-experience topics — never treat `content` as live truth (may look better and still be dead/stale).

## Environment Definitions
| Env | Org URL | Env ID | Purpose |
|-----|---------|--------|---------|
| PCCA Package | `pccapackage.crm.dynamics.com` | `077422cf-...` | Pacific Coast Doc Defense Agent |
| Therapy AI Dev | `orgbd048f00.crm.dynamics.com` | | Therapy fleet (hub, specialists) |
| Therapy AI Prod | `org532ca94a.crm.dynamics.com` | `6951ccc2-...` | Prod — explicit direction only |
| Ensign Default | `org3353a370.crm.dynamics.com` | `Default-03cc92c3-...` | PT/OT/SLP/TDA — explicit direction only |

## Severity Classification
Every finding must be tagged:
- **P0 — Must Fix:** Breaks core function, blocks publish, causes data loss, runtime failures (missing EndDialog, placeholder flow IDs, broken YAML, missing SendActivity after SASC)
- **P1 — Should Fix:** Degrades quality, limits eval scores, inconsistency, maintenance debt (multi-Question flows failing SR, empty topics by BeginDialog, duplicate triggers, cosmetic config mismatch)

---

## Pre-Inspection Discovery

### Locate the agent
1. Find `agent.mcs.yml` in workspace — displayName may NOT match directory name.
2. `pac copilot list` or Dataverse `GET /bots?$filter=name eq '<name>'&$select=botid,name,statecode`
3. The bot GUID from Copilot Studio URL IS the Dataverse bot ID. Match by name, not directory.

### Inventory all components
```bash
# pac org fetch XML:
<fetch><entity name="botcomponent"><attribute name="botcomponentid"/><attribute name="name"/><attribute name="componenttype"/><attribute name="statecode"/><attribute name="schemaname"/><attribute name="data"/><filter><condition attribute="parentbotid" operator="eq" value="<botId>"/></filter></entity></fetch>
> pac org fetch -xf query.xml > components.xml
```
| Type | Meaning |
|------|---------|
| 9 | Topic / AdaptiveDialog |
| 10 | System component |
| 14 | File KB (uploaded PDF) |
| 15 | Instructions (GptComponentMetadata) |
| 16 | Web/SharePoint KB |
| 19 | Trigger phrases OR Evaluation data — sample `data` field to distinguish |

### Workspace classification (before reading YAML)
Check for: `agent.mcs.yml` (cloned agent), `solution_unpacked/` (solution archive), `DO-NOT-APPLY-CHANGES.md` (read-only), `conn.json.DISABLED-*` (disconnected). Also detect dual-agent workspaces (recursive `agent.mcs.yml` search), empty `.mcs.yml` files (0-byte stubs — P0 if referenced by BeginDialog, P1 otherwise).
**No workspace on disk?** Some agents are live-only (no local YAML). Use pure live-Dataverse workflow — see `references/live-only-agent-fix-workflow.md`.

---

## 12-Domain Audit (per agent)

### Domain 1: Instructions (GPT — componenttype 15)
| Check | Criteria | How |
|-------|----------|-----|
| Size | 2000-6000 chars | Query data, count chars |
| No BOM | No uFEFF | `grep -c $'\xef\xbb\xbf'` |
| No mid-word splices | No word fragments before caps | Visual scan first 200 chars |
| No duplicated headers | Each heading appears once | Count occurrences |
| No contradictory caps | "prioritize completeness" NOT next to "under 800 chars" | Visual scan |
| EVALUATION CONTEXT present | DATA-SPARSE + DATA-RICH subsections | Grep |
| No abstention directives | No "I cannot find" / "the sources do not address" | Grep |
| Conditional RESPONSE FORMAT | Structured for audits, plain for general | Visual scan |
| Mission clarity | Agent says WHAT it IS and IS NOT (review vs write) | First 200 chars |
| Model hint correct | GPT5Chat, Sonnet46 — no typos (GPT55Chat is WRONG) | Query componenttype 15 |
| responseInstructions | NO "No headers/markdown/tables" — use conditional formatting | Settings field |
| Model knowledge | ON (true or absent) | Settings |
| Web browsing | OFF for PHI agents | Settings |
| Source restriction trap | "Use ONLY these N sources" → abstention failures. Fix: soften to "primary reference, use model knowledge when unaddressed" | Grep for "only" |

### Domain 2: Knowledge Sources
| Check | Criteria |
|-------|----------|
| KB name | Descriptive, unique — "CMS MDS 3.0 Manual" NOT "Doc1" |
| KB description | 1-2 sentences per source — critical for generative routing |
| Official toggle | On for authoritative sources (CMS, ASHA, APTA, AOTA, CFR) |
| No duplicates | Same doc in KB + SharePoint = double retrieval |
| Files under 5MB | MS Learn limit for eval test set gen |
| **SearchSpecificFiles** | **REMOVE from ALL topics** — restricts search to hardcoded files |
| **SearchSpecificKnowledgeSources** | **REMOVE** — separate restriction from SearchSpecificFiles. Check BOTH. |
| Cross-discipline parity | All specialist agents share CMS CFR, Ch 15, PI Ch 3, Claims Ch 5, etc. |
| Instructions-vs-KB cross-ref | Every numbered source in instructions must have a corresponding uploaded file |

### Domain 3: Topics — Structural Integrity
| Element | Required | System Topic Exempt? |
|---------|----------|---------------------|
| EndDialog with clearTopicQueue:true | YES | Yes (OnConversationStart MUST have it — #1 Conv eval fix) |
| SendActivity before EndDialog (outputs =Topic.Answer) | YES | No |
| No BOM chars | YES | Yes |
| Valid YAML | YES | Yes |
| No duplicate node IDs | Each ID unique within topic | Yes |
| No empty SASC nodes (id only) | Must have userInput + additionalInstructions + fileSearchDataSource + responseCaptureType + allowLatencyMessage | N/A |
| responseCaptureType: FullResponse | YES on every SASC | N/A |
| allowLatencyMessage: false | YES on every SASC | N/A |
| applyModelKnowledgeSetting | true or omit | N/A |
| OnError handler | YES every custom topic | N/A |
| ≥5 trigger phrases | YES custom topics | N/A |
| No duplicate triggers across topics | Jaccard < 60% | N/A |

**Special patterns to detect (from fleet audits):**
- **Hollow topics:** Match via triggers but produce zero output (single "AI can't give medical advice" SendActivity, no search, no EndDialog). Flag P0.
- **Hollow Search handoff (Pattern P):** Custom leaves = Question → BeginDialog `*.topic.Search` → EndConversation/static "Analysis complete". Resolve schemaname: `topic.Search` is frequently **Conversational boosting**. If boosting is silent (SASC → EndDialog without SendActivity), the whole agent is eval-hollow. Flag P0.
- **Dual OnUnknownIntent:** Conversational boosting (priority -1) + Fallback (priority -2) both OnUnknownIntent. Boosting wins first. Audit BOTH. Fix boosting to Pattern L; still rewrite Fallback (Pattern J) for when boosting blanks.
- **Structured-Intake-Only anti-pattern:** All topics = Question→Question→SendActivity("stays in structured intake mode..."), no SASC, no EndDialog, empty connectionreferences. Entire architecture is a shell. Flag P0.
- **Duplicate topic representations:** NLU-triggered `.mcs.yml` vs compiled `content.yaml` from solution export — they diverge. The NLU `.mcs.yml` is the authority.
- **Connected agent routing gap:** Declared connected agents but zero InvokeConnectedAgent calls across all topics. Report-only (platform orchestration may handle it).
- **Orphan topics:** Unreachable via triggers OR BeginDialog OR routing matrix. Flag P1.

**Question Node Guard:** No Question nodes in audit/answer topics. If Question exists (intake), must end with EndDialog and `allowInterruption: false`.

### Domain 4: Topic Names & Triggers
| Check | Criteria |
|-------|----------|
| Display name | No periods (breaks export), no trailing spaces, <50 chars, PascalCase/snake_case consistent |
| modelDescription | Present on every topic, describes WHAT it does (not implementation), unique, matches trigger intent |
| Trigger phrases | 5-10 per topic, natural language variety (questions + commands + statements), no exact/near duplicates, no misspellings |

### Domain 5: Connected Agents & Tools
| Check | Criteria |
|-------|----------|
| Connected agent provisioned | Verify in Copilot Studio → Agents |
| Schema name matches live agent | Query Dataverse for actual schema name |
| Topic is ACTIVE | `statecode=0` — deactivated (1) = silent no-op |
| No stale connections | Remove unused agents |
| Flow deployed | InvokeFlowAction flows must exist in env |
| Flow **active** | `GET /workflows({flowId})` → `statecode=0` (Inactive while still invoked is P0) |
| Flow connection refs populated | Not empty |
| Placeholder flow IDs | GUIDs like `11111111-...` or `66666666-...` are template stubs → crash at runtime. P0. |
| BeginDialog target real | Resolve `dialog: <schemaname>` against live `botcomponents.schemaname` — `topic.Search` is often **Conversational boosting** |

### Domain 6: Settings & Configuration
| Check | Criteria |
|-------|----------|
| Content Moderation | Medium for healthcare (High false-positives on clinical language) |
| Model knowledge | ON |
| Semantic search | ON |
| File analysis | ON |
| Latency messages | OFF (confuses grader) |
| Generative actions | ON |
| Conversation starters | 5-10 varied, matching core workflows. Also check componenttype 19 for extras. |
| Web search / code interpreter | OFF for PHI agents |

### Domain 7: YAML Anti-Corruption
- UTF-8 without BOM
- CRLF consistent (Dataverse uses \r\n — always convert to \n before editing, back to \r\n after)
- Valid YAML (pyyaml safe_load)
- No duplicated sections (check for duplicate beginDialog blocks)
- No mid-word splices at line boundaries
- No text concatenation (`"for official guidance."ide active knowledge sources` = cursor paste corruption)
- No extra root `kind` entries
- `activity:` strings with colons MUST be quoted: `activity: "I need: SBAR handoff"` NOT `activity: I need: SBAR handoff`

### Domain 8: Silent Failures & Loop Prevention
- No GotoAction infinite loops (every GotoAction needs exit condition)
- No dead-end BeginDialog (targets must exist)
- ConditionGroup empty elseActions = silent stop
- OnError topic: configured, not blank
- Fallback topic: HAS SearchAndSummarizeContent + EndDialog — NOT "I am not sure how to help"
- Fallback SendActivity lists what the agent CAN do (prevents abstention failures)
- OCR polling has max retries (retry_count_num sentinel)
- **Question-First anti-pattern:** Agent opens with "What type of document?" + buttons → Conv eval <20%. Fix: remove greeting gate from Conversation Starter topic, NOT instructions.

### Domain 9: Knowledge Source Optimization
- No duplicate or deprecated KBs
- KB ordering: most specific → least specific
- Every KB has unique, specific description stating content scope
- No generic descriptions ("PDF file")

### Domain 10: Testing Window Verification
| Test | Expected |
|------|----------|
| Welcome flow | Welcome card, no error |
| Topic routing | Routes to correct topic, gets answer |
| Follow-up | Maintains context, adds to existing output |
| Sparse query | Useful framework, not "please provide document" |
| Out of scope | Graceful redirect, not error |
| Connected agent | Routes correctly |
| No errors | All text/card responses, no error text |

### Domain 11: Deployment Readiness
Pre-flight checklist — ALL must pass:
- [ ] Domains 1-10 at 100%
- [ ] Instructions 2000-6000 chars, no corruption
- [ ] All CUSTOM/QM leaf topics (OnRecognizedIntent) EndDialog + clearTopicQueue:true (system topics use CancelAllDialogs — NOT a defect)
- [ ] No Question nodes in audit topics
- [ ] No SearchSpecificFiles or SearchSpecificKnowledgeSources
- [ ] Every SASC has userInput: =System.Activity.Text, responseCaptureType: FullResponse
- [ ] Flows exist and deploy (no placeholder IDs)
- [ ] KBs named + described properly
- [ ] Trigger phrases 5-10/topic, no duplicates
- [ ] Connected agents: keep active **only if** target bot publishes + chaining works; if runtime/eval shows `ConnectedAgentBotNotPublished` / `ChainingNotSupported`, DISABLE (`statecode=1`) — Pattern R
- [ ] responseInstructions has NO "No headers/markdown"
- [ ] EVALUATION CONTEXT block present in instructions
- [ ] YAML validates clean
- [ ] No deactivated **leaf** custom topics (dup files / crashy connected agents disabled intentionally OK)
- [ ] No managed Power Automate flows with stale output bindings blocking publish
- [ ] **Tier 1 live without external data** (when asked): publish Succeeded + channels synced + Pattern L + user paste SOP — `references/live-ready-without-integrations.md`

### Domain 12: Post-Eval Analysis & Iteration
After eval run, classify EVERY failure:
```python
classifications = {
  "abstention": "Agent refused — grader marked abstention=Yes",
  "incomplete": "Missing elements or truncated",
  "groundedness": "Not supported by KBs",
  "relevance": "Wrong topic matched",
  "format": "Wrong output format",
  "error": "Runtime error (ExecutionFailed, notextresponse)"
}
```
Cross-reference Conv and SR failures. If same category dominates both → systemic fix.
4. **Connected-agent crashes:** `ConnectedAgentBotNotPublished` / `ConnectedAgentChainingNotSupported` → DISABLE (`statecode=1`) InvokeConnectedAgent TaskDialogs.
5. **Eval-setup remainder:** reword facility-export tests (eval Pattern E5) if plateau — not another architecture rewrite.

**User preference:** mid scores after solid structural pass → surgical failure-analysis-first, not full rebuild. See `references/report-prep-v2-safe-fix-post-baseline-2026-07-17.md`.

### Pattern S: Three-mode leaf instructions (data-sparse SASC fix)

When global anti-abstention instructions exist in GPT metadata, Conversational boosting, and Fallback — but a specialized leaf topic says only "Extract only from user-provided text when present" — the leaf wins on direct-intent routing. Symptoms: record IDs → "no notes found", partial metrics → "no prior quarter found", IDT agenda → "what type of document?"

**Fix:** Replace leaf SASC `additionalInstructions:` with three explicit modes:
1. **DATA RICH** — Full clinical text: extract only from what was provided. Never invent.
2. **DATA SPARSE** — Only record IDs/dates: deliver CMS compliance checklist, placeholder fields, "To complete from your facility data". Never claim EHR was searched or notes absent.
3. **PARTIAL DATA** — Partial metrics: format provided values, create blank comparator columns, mark missing as "To complete from your facility data".

**Post-fix signature:** Failures shift from "abstention-routing" to "groundedness/completeness" — agent delivers CMS policy content but grader expects facility data the test didn't supply. This confirms the fix is working; remaining failures are eval-setup issues (Pattern E5).

**Template + leaf IDs:** `copilot-studio-report-prep-v2` skill, `references/data-sparse-leaf-patch-pattern.md`.

---

---

## New-Experience Agent Recognition & Audit

Classic vs new Copilot Studio:
- **New (Topic V2):** Topics as hyperlinked cards on Overview, Model selector inline, KBs show "Ready" badges, URL uses `environments/<guid>/bots/<botId>/`. Component labels are readable (`Topic (V2)`, `Custom GPT`, `Knowledge Source`, `Copilot Settings`) instead of bare numbers. Web API STILL returns componenttype 9/14/15/16/19 — do NOT assume "0 results"; this agent returned all of them cleanly via the Web API.
- **Classic:** Topic grid, botcomponents queryable via Dataverse.
- **Audit implications:** New-experience agents ARE fully queryable via the Dataverse Web API (see "Live Dataverse Pull" below). The SPA UI is only required for APPLYING fixes to managed/new-exp topics that reject API PATCH (content=null / sync bypass). Pure audit + eval reading is API-friendly.

### NEW-EXPERIENCE STRUCTURAL FACTS (audit-critical)
1. **DUAL-FIELD TOPICS — audit the `data` field, not `content`.** Every topic
   (ct=9) carries BOTH `data` AND `content`. They DIVERGE. `data` is the
   AUTHORITATIVE generative version (has `SearchAndSummarizeContent` +
   `userInput: =System.Activity.Text` + `EndDialog`). `content` is frequently a
   SEPARATE hardcoded/legacy version (e.g. a static SendActivity with EndDialog
   but NO clearTopicQueue). Reading/patching `content` does NOT change live
   behavior. Always key structural checks off `data`.
2. **System topics legitimately have NO EndDialog — FALSE POSITIVE if flagged.**
   Conversation Start / Greeting / Goodbye / Fallback / On Error / Escalate /
   Sign in / Reset Conversation / End of Conversation / Multiple Topics Matched
   use `OnConversationStart` / `CancelAllDialogs` / `OnUnknownIntent` / `OnError`
   / `OnSignIn` / `OnSystemRedirect` / `OnSelectIntent` triggers and do NOT close
   with `kind: EndDialog`. The Domain 3 "EndDialog required" row applies ONLY to
   custom/QM leaf topics (`OnRecognizedIntent`). Do not report "NO EndDialog" on
   system topics.
3. **Instructions corruption signature (ct=15, one `data` blob):**
   `kind: GptComponentMetadata` + `instructions: |-` + `responseInstructions:` +
   `aISettings` + `conversationStarters`. Watch for: mid-word splice artifacts
   ("analy## ROLE AND SCOPE"), DUPLICATE section sets (same content under plain
   headers AND under `## ` prefixed headers), orphan fragments spliced mid-section,
   and the "No headers/markdown/tables" ban repeated 3-4x. These are merge/paste
   corruption — rewrite as ONE clean version (Pattern H + K).

### Live Dataverse Pull — clean JSON via Web API (preferred over `pac org fetch`)
`pac org fetch` emits a FIXED-WIDTH TEXT TABLE, not JSON — it garbles multi-line
`data`/`content` (topic YAML, instructions) and is unusable for real audit. Use
the Web API:
```bash
# 1. token (az handles claims challenges az rest can't)
az account get-access-token --resource "https://<org>.crm.dynamics.com/" \
   --tenant 03cc92c3-986c-4cf4-ae27-1478cf99d17f
# 2. GET — URL-ENCODE filter; use NAVIGATION VALUE not logical attr:
#      WRONG: $filter=parentbotid eq <guid>        (400 incompatible types)
#      RIGHT: $filter=_parentbotid_value eq <guid>
GET /api/data/v9.2/botcomponents?$filter=_parentbotid_value eq <botId>
   &$select=botcomponentid,name,componenttype,schemaname,statecode,statuscode,data,content,category
# 3. json.loads in Python. componenttype: 9=Topic(V2) 15=Instr 16=KB
#    14=BotFile 19=Eval/Trigger 11=Entity 12=Var 18=Settings
```
WSL note: `pac.exe` works via interop, but the execute_code sandbox is a
separate Windows-Python env — write the token to a Windows path
(`C:\Users\...\tok.txt`), NOT `/tmp`, or the sandbox can't read it.

---

## Parallel Fleet Sweep (5+ agents)

1. **Parallel analysis** — Up to 3 subagents × 2-4 agents each. Each counts P0/P1.
2. **Priority queue** — Write to file: worst-first (most P0s).
3. **Fix + QA** — Work through queue. Multiple fix subagents in parallel (per-agent).
4. **Systemic bulk** — For 20+ same-root-cause P0s (missing EndDialog across all topics): fix in one batch per agent.

---

## Scope Cleanup

1. Classify every topic: ALIGNED / PARTIALLY ALIGNED / MISALIGNED / ORPHAN
2. Create removal manifest listing topics to disable/remove, grouped by reason
3. **Prefer DISABLE over DELETE** — `statecode: 1, statuscode: 2` on Dataverse. Preserves GUIDs, prevents publish crashes on cross-references.
4. Don't delete local YAML files — manifest is guide for live agent cleanup.
5. Update router before removing topics.

---

## Publish Diagnostics

`pac copilot list` shows stale "Published" even when last publish failed. Verify:
```bash
# FetchXML for bot:
<fetch><entity name="bot"><attribute name="synchronizationstatus"/><filter><condition attribute="botid" operator="eq" value="<botId>/</filter></entity></fetch>
> pac org fetch -xf query.xml
```
Parse `lastFinishedPublishOperation.status` — MUST be "Succeeded". If "Failed", check `diagnosticDetails[].diagnosticList[].errorMessage`.

### Iterative Publish Masking Pattern

Errors mask each other. Fix one layer, publish, and the REAL error set emerges. **Do NOT try to fix all errors at once — you can't see them all until earlier layers are resolved.**

Common masking sequence in card-based agents (TheraDoc Workbench confirmed):
1. **Layer 1 — Missing dialog references:** `Dialog with id 'AuditExistingNote' not found` → fix: redirect to correct topic name or activate the inactive topic
2. **Layer 2 — Variable scope:** `Identifier not recognized: Topic.Answer` (19+ occurrences) → fix: add `variable: Topic.Answer` to all SASC nodes at CORRECT indent
3. **Layer 3 — Schema validation:** `Missing OutputType` (13) + `errorMessage` (89) → fix: these are often **phantom errors** masking REAL issues. Publish after layers 1-2 and check if they persist
4. **Layer 4 — Flow bindings:** `Output binding 'X' is not found` (50+ fields) → fix: delete orphaned flow from Copilot Studio Actions. NOT a topic YAML issue.

**Each publish resolves the masked errors and reveals the true next layer. Always publish after each fix round, don't batch everything.**

## Comparative Agent Assessment

When asked to compare two agents (e.g., "which is more mature?", "which has better CPT coverage?"), use this structured comparison:

### Comparison Dimensions
| Dimension | What to Measure | Data Source |
|-----------|----------------|-------------|
| **Architecture pattern** | Card-based (AdaptiveCards) vs free-text (Questions) vs hybrid | Count AdaptiveCardPrompt vs Question nodes across all topics |
| **CPT code coverage** | Which specific codes (97110, 97112, 97116, 97140, 97530, 97535, 97542, 92521-92526) are embedded | Grep topic data for each code. Note whether codes are in dropdowns (user selects) vs free text prompts (user types) |
| **Regulatory grounding** | CMS references, Chapter 15, Jimmo, 42 CFR, APTA/AOTA/ASHA | Grep instructions + topic data for each reference |
| **Discipline coverage** | PT/OT/SLP/ST — does each have dedicated workflows? | Topic displayNames per discipline; per-discipline AdaptiveCards/ChoiceSets |
| **Input method** | Buttons/clicks vs free-text typing | Count AdaptiveCardPrompt (card-based) vs Question nodes (type-based) vs SASC with =System.Activity.Text (braindump) |
| **Automation** | InvokeFlowAction, InvokeConnectedAgent | Count flow/connected-agent references |
| **Ease of use** | Structured choices vs free-text responses | ChoiceSet + Toggle + Action.Submit counts vs Input.Text + Question counts |
| **Braindump support** | Can user type free-form and get structured output? | Check for Parse Brain Dump flows, "brain dump" in instructions, SASC with =System.Activity.Text |
| **Test coverage** | Eval test set count and type | Count EvaluationData components; check SingleTurn vs MultiTurn |
| **Publish health** | Does it publish cleanly? | Run pac copilot publish or check synchronizationstatus diagnosticDetails |

### Maturity Heuristics
- **Card-based > free-text** — AdaptiveCards with dropdowns require less effort than 85+ free-text Questions
- **Structured CPT > mentioned CPT** — CPT codes in dropdowns (click) is better than in prose prompts (memorize/type)
- **Braindump pipeline > Questions-only** — a "Parse Brain Dump" flow + AI structuring beats rigid Question sequences
- **Deeper regulatory grounding** — more CMS/Chapter 15/Jimmo refs in content = more compliant output
- **Full episode coverage** — topics for eval + treatment + progress + recert + discharge = complete patient cycle

## Score Variance
- ±5% between runs is normal (MS Learn)
- For 20-case Conv: 1 case = 5%. For 100-case SR: 5 cases = 1%
- Run 3x and average for baseline

## Common Failure Patterns
| Pattern | Impact | Fix |
|---------|--------|-----|
| abstention=Yes, rel=NA | -5 to -20pts | Add EVALUATION CONTEXT "NEVER abstain" |
| abstention persists despite NEVER abstain | -5 to -20pts | **Platform limitation** — enrich KB, modify test set, or document |
| completeness=No, rel=Yes, gnd=Yes | -10 to -25pts | Remove "No headers/markdown/under N sentences" from responseInstructions |
| completeness=No, rel=Yes, gnd=No | -10 to -15pts | Add/improve KBs, ensure SASC is used |
| rel=NA, comp=undefined, abs=Yes | -5 to -20pts | Strengthen SPARSE PROMPTS directive |
| Agent writes/analyzes wrong output type | -10 to -30pts | Fix mission clarity — instructions say "review" but test expects "draft" |
| FilePrebuiltEntity Question → never completes on text | -20 to -35pts | Change to StringPrebuiltEntity + 3-branch ConditionGroup |
| Question node in audit topic | -5 to -15pts (SR) | Replace with SASC + userInput: =System.Activity.Text |
| Missing responseCaptureType: FullResponse | -5 to -10pts | Add to every SASC |
| Empty SASC (id only) | -20 to -30pts | Restore full pipeline |
| Missing EndDialog on ConversationStart | 0% Conv | Add EndDialog(clearTopicQueue:true) |
| Source restriction "use ONLY" | ~24/100 abstention | Soften to "use as primary reference; may use model knowledge" |
| Use of file[] / turn.uploadedFiles | **BLANK EDITOR** | Revert, use Pattern F instead |

## Agent Registries

### Therapy AI Dev (`orgbd048f00.crm.dynamics.com`)
| Agent | Bot ID | Role |
|-------|--------|------|
| SNF Command Center V2 | `9f3e370c-a747-f111-bec6-0022480b6bd9` | Orchestrator Hub |
| SNF AI Dashboard V2 | `bd570423-cf47-f111-bec5-70a8a5b1c3a3` | Data Viz |
| TheraDoc Workbench | `e09954e1-4af8-47c6-8ef4-d1d9335bf2e6` | Doc Assistant |
| Pacific Coast Case Historian | `ad635500-cf47-f111-bec5-70a8a5b1c3a3` | Longitudinal Analysis |
| Pacific Coast QM Coach V2 | `ea52ad9c-8233-f111-88b3-6045bd09a824` | Quality Measures |
| Pacific Coast Denial Defense V2 | `6d7815b4-ce47-f111-bec5-70a8a5b1c3a3` | Denial Management |
| Therapy Report Prep V2 | `fd1bce12-cf47-f111-bec5-70a8a5b1c3a3` | Report Gen |
| Pacific Coast Compliance Analyzer | `19779839-7b6e-4362-925b-8ddf03979f7d` | Compliance Audit |
| Pacific Coast Regulatory Hub V2 | `ea901efc-d043-4023-88a6-8ac4c561a4d5` | Regulatory |
| PacCoast Daily+Weekly Meeting | `ee72fe1a-0882-4dec-9959-ace1fbb74280` | Meeting Support |
| Clinical Synthesis Lab V2 | `89c7415d-df73-490c-9d78-4829cfbc2f84` | Clinical Synthesis |
| POSTette Compliance Agent | `03b08692-aa24-4159-986b-cfad8fed6865` | Compliance |
| Pacific Coast Documentation Defense Agent | `2e08ac68-bdef-481e-9c04-6a349c79d6c0` | Doc Defense (migrated from PCCA; source `9e7b871d-...`) |
| Pacific Coast Case History Reviewing Agent | `f19e1c40-f07e-f111-ab0e-70a8a5b24e56` | Acute-to-SNF eval prep (live-only; type-15 `cc349f24-...`) |
| Copy Therapy Doc Feedback | `b0346795-4876-f111-ab0e-70a8a5b1b8cc` | Feedback (new-exp) |

### Ensign Default (`org3353a370.crm.dynamics.com`)— explicit direction only
| Agent | Bot ID |
|-------|--------|
| OT_Specialist | `73b45e98-af7a-443a-aa12-6d8a05118530` |
| PT_Specialist | `593407f3-539b-490f-84ac-d74e13216c81` |
| SLP_Specialist | `6e437a77-a5dc-4984-90eb-4924eab10006` |
| Therapy Doc Audit Agent | `4d0ed0d3-30f6-f011-8406-000d3a37eba2` |
| Therapy Report Prep Asst | `c030a53a-4839-f111-88b4-000d3a37eba2` |

### PCCA (`pccapackage.crm.dynamics.com`)
| Agent | Bot ID |
|-------|--------|
| Pacific Coast Documentation Defense | `9e7b871d-1d80-f111-ab0f-000d3a5b0d6c` |

---

## Pitfalls (real incidents)
- **FetchXML `pac org fetch` filter attribute:** Use LOGICAL name `parentbotid` in FetchXML (works). But the Web API OData filter needs the NAVIGATION VALUE `_parentbotid_value eq <guid>` — using `parentbotid eq <guid>` returns HTTP 400 "incompatible types 'bot' and 'Edm.Guid'". Two different query paths, two different attribute names.
- **`pac org fetch` returns a TEXT TABLE, not JSON** — multi-line `data`/`content` (topic YAML, instructions) is garbled/unparseable. For real audit work use the Web API GET (see "Live Dataverse Pull") and `json.loads`.
- **New-experience topics have TWO fields (`data` + `content`) that DIVERGE.** `data` is authoritative (generative SASC version); `content` is often a separate hardcoded legacy version. Audit/patch `data`; ignore `content` for live behavior.
- **System-topic "NO EndDialog" is a FALSE POSITIVE** in new-experience agents — they end via `CancelAllDialogs`/`OnConversationStart` etc. Only `OnRecognizedIntent` (custom/QM) leaf topics need `EndDialog` + `clearTopicQueue: true`.
- **Instructions merge-corruption signature:** mid-word splice (`analy## ROLE AND SCOPE`), duplicate plain + `## `-prefixed section sets, and "No headers/markdown" ban repeated 3-4x. Rewrite as ONE clean version.
- **file[] → blank editor freeze.** Dual-input pattern F instead.
- **az 401 → pac auth create** (cached identity, no MFA).
- **pac copilot list stale** → check `synchronizationstatus`, not the list.
- **CRLF vs LF.** Dataverse uses \r\n. Convert to \n before editing, back to \r\n after.
- **Minimized Chrome** → cua-driver can't screenshot. Restore tab first.
- **File dialog fragile under UIA** → self-closes on wrong input.
- **Never trust subagent self-reports** — count actual .bak files, not claimed numbers.
- **Trailing slash on az resource.** `--resource "https://org3353a370.crm.dynamics.com/"` (WITH slash) — without it returns 401.
- **`az rest` handles claims challenges** that bare `az account get-access-token` doesn't.
- **PATCH:** Entity-level `PATCH /botcomponents({id})` uses `{"data":"<yaml>"}`. Property-specific `PATCH /botcomponents({id})/data` uses `{"value":"<yaml>"}`. Mixing them up causes HTTP 400 "property does not exist on type botcomponent".
- **CRLF regex trap:** When using `re.sub` on Dataverse YAML, ALWAYS normalize `\r\n` → `\n` first. The pattern `(allowLatencyMessage: false\s*)` consumed by `\s*` eats the `\r\n` line endings AND the next line's whitespace when `\r\n` isn't normalized first. Replacement with `\n`-only then produces mixed line endings → broken indentation → publish fails with `Missing required property 'UserInput'`. Fix: `data.replace('\r\n', '\n')` → edit → `fixed.replace('\n', '\r\n')`.
- **Managed/locked topics:** Create new component with `_v2` schema name instead of PATCHing locked ones.
- **Managed flow blocker:** `Output binding 'X' is not found, refresh this flow` errors come from managed Power Automate flows (`ismanaged=True`). Cannot be deleted via REST API. Must: (a) uninstall the managed solution, or (b) add matching `outputType` properties to the topic the flow binds to. Workflow entity deletion: `DELETE /workflows({id})`, deactivation: `PATCH /workflows({id}) {"statecode": 1}` works for non-managed flows.
- **New-experience agent fixes:** Prefer Dataverse API PATCH of the `data` field (validated QM Coach V2 2026-07-17: instructions, Fallback, 6 SASC topics, Conversation Start, settings, KBs, On Error — all 204 + publish Succeeded). Fall back to SPA only when API returns content=null / sync bypass / system-topic lock. Always re-GET `data` after PATCH and verify `synchronizationstatus` after publish.
- **`pac copilot publish` can print a STALE Succeeded date** (e.g. old June timestamp while today's publish actually landed). Always `GET /bots({id})?$select=publishedon,synchronizationstatus` and require `lastFinishedPublishOperation.status==Succeeded` with today's `publishedon`. Report times in **Pacific**.
- **KB description empty-check:** Use YAML `description:` in ct=16 `data`, NOT JSON `"description":`. Several KBs already had good descriptions while 1–2 incomplete ones did not — do not flag the whole set.
- **Commit scope on dirty repos:** When the workspace has unrelated agent churn, commit ONLY the audit/fix artifacts for this bot (not `git add -A`) so the pre-PATCH baseline stays revertible without bundling foreign deletions.
- **Eval data does NOT survive environment transport.** After migrating an agent (export/import solution to another env), all eval history — runs, test sets, definitions — is lost. The new env starts empty. Old eval scores from the source env are noise and should be ignored. Must create fresh test sets and establish a new baseline. See `references/post-migration-eval-gap.md` for details.

## References (from merged skills)
- `copilot-studio-pipeline` — deploy/validate scripts
- `eval-optimization-loop` — run, analyze, fix evals (merged from 7 prior skills)
- `eval-triage-framework` — failure triage (SHIP/ITERATE/BLOCK)
- `copilot-studio-yaml-reference` — YAML schema
- `agent-builder-orchestrator` — full end-to-end build pipeline (architect → crafter → QA → deploy → eval)
- `agent-qa-gate` — 12-gate verification (run BEFORE deploy)
- `copilot-studio-common-reference` — canonical auth, generation rules, patterns, pitfalls
- Linked: `references/live-only-dataverse-workflow.md` (agents with no local workspace)
- Linked: `references/theradoc-vs-tda-comparison.md` (structure comparison — which agent is more mature, CPT code coverage, CMS grounding)
- Linked: `references/doc-defense-post-migrate-fix-2026-07-16.md` (post-migrate Pattern J fix pass)
- Linked: `references/solution-transport-focused-bot.md` (DocDefenseTransport; migration skill is pinned)
- Linked: `references/qm-coach-v2-new-exp-audit-fix-2026-07-17.md` — full new-exp audit/fix recipe (Web API pull, dual data/content, Patterns L–O, publish verify)
- Linked: `references/report-prep-v2-audit-2026-07-17.md` — hollow Search/boosting handoff (Patterns P–Q)
- Linked: `references/report-prep-v2-safe-fix-post-baseline-2026-07-17.md` — Pattern R surgical pass
- Report publish times in **Pacific local** for Kevin (convert UTC).
