---
name: agent-builder-pipeline
displayName: One-Shot Agent Builder Pipeline
description: Build a complete Copilot Studio agent in one shot — from domain research through published, verified, and tested. Operaional pipeline with visual verification at every checkpoint. Say "Build me an agent for [domain]" to start.
category: copilot-studio
keywords:
  - build a Copilot Studio agent
  - create agent
  - one-shot agent builder
  - agent pipeline
  - build agent from scratch
  - deploy agent
  - QA agent
  - publish agent
---

# One-Shot Agent Builder Pipeline

Build a complete Microsoft Copilot Studio agent end-to-end in one shot. This is an OPERATIONAL guide — read sequentially, execute each phase, verify at checkpoints.

Trigger: **"Build me an agent for [domain/purpose]"**

## Architecture

Pure-steering skill. No TypeScript runtime, no build step. Hermes reads this guide and calls tools directly. All operational content is inline.

**Tool mapping (Hermes equivalents of Kiro's MCP tools):**

| Kiro Tool | Hermes Tool | Used For |
|-----------|------------|----------|
| `az account get-access-token` | `terminal` (az CLI) | Dataverse REST API auth |
| pac CLI | `terminal` (pac) | FetchXML queries, publish |
| Playwright MCP | `browser` tool | UI verification, Test Chat, file upload |
| copilot-studio MCP | `terminal` (az rest) | Bot queries, component ops |
| execute_pwsh | `terminal` (bash) | PowerShell commands |
| Screenshot verification | `computer_use` or `browser_vision` | Visual checkpoints |
| **MS Learn MCP** 🆕 | **`mcp__microsoft_learn__microsoft_docs_search`** | Authoritative MS documentation |
| **MS Learn fetch** 🆕 | **`mcp__microsoft_learn__microsoft_docs_fetch`** | Full article content |
| **MS Learn code** 🆕 | **`mcp__microsoft_learn__microsoft_code_sample_search`** | Code samples + patterns |

**MS Learn MCP is pre-configured.** URL: `https://learn.microsoft.com/api/mcp` — free, no auth, 3 tools. Available via `tool_call` with name `mcp__microsoft_learn__microsoft_docs_search` (and `_fetch`, `_code_sample_search`).

---

---

## 🆕 MS Learn MCP Integration

This pipeline is **Kiro-equivalent PLUS Microsoft Learn MCP** — an advantage Kiro doesn't have:

| Phase | Without MS Learn | With MS Learn |
|-------|-----------------|---------------|
| 0 — Research | Web searches only (3rd-party interpretations) | +2 MS Learn searches for authoritative Microsoft patterns |
| 3 — Generate | Manual YAML validation | +MS Learn schema cross-reference (catches invalid fields) |
| 5 — QA | Static 12-section checklist | +MS Learn compliance cross-reference (always current) |

**How to use:** MS Learn tools are available as `mcp__microsoft_learn__microsoft_docs_search`, `_fetch`, and `_code_sample_search`. Call them via `tool_call` at the marked 🆕 checkpoints.

## Pipeline Overview

```
Phase 0: Architect Research  →  Domain deep-dive, fleet analysis, self-critique
Phase 1: Preflight           →  Auth check, mode determination
Phase 2: Agent Shell          →  User creates in UI, capture Bot ID + Schema
Phase 3: Topic + GPT Gen      →  Generate YAML topics + GPT instructions
Phase 4: Cascade Deploy       →  Dataverse API (single token) deploy everything
Phase 5: QA Verification      →  12-section checklist
Phase 6: Publish + Test       →  Publish, 90s wait, Test Chat verify
Phase 7: Optimization         →  Only if scores < 90%
```

Each phase has entry/exit criteria. Never skip ahead.

## Automation Modes

| Mode | When | What Happens |
|------|------|-------------|
| **Full Auto** | `az account get-access-token` succeeds | Deploy ALL via Dataverse REST API. Browser only for file upload + Test Chat. |
| **Generate + Instruct** | No API token available | Generate all files to `scratch/[agent-name]/`. Give user paste instructions. |

Both produce identical results.

---

## Phase 0: Architect Research

**Entry:** User says "Build me an agent for [domain]"
**Exit:** Complete Agent Spec produced

### 0.1 Web Research (MANDATORY)

Search the domain deeply before designing anything. Even if you "know" the domain, verify with current sources.

**Research methodology (7 searches, in order — 5 web + 2 MS Learn):**

1. **Broad (web):** "[domain] requirements and best practices" — establishes knowledge landscape
2. **Deep (web):** "[specific regulation] requirements checklist" — detailed rules for GPT instructions
3. **User language (web):** "how do [users] ask about [topic]" — natural trigger phrases
4. **Failure modes (web):** "common mistakes in [domain]" — safety guardrails
5. **Knowledge sources (web):** "[domain] official guidelines PDF" — identify documents for upload
6. **🆕 MS Learn — Architecture:** `mcp__microsoft_learn__microsoft_docs_search` with "Copilot Studio agent architecture best practices topic design" — authoritative Microsoft guidance on topic count, naming patterns, orchestrator routing
7. **🆕 MS Learn — GPT Instructions:** `mcp__microsoft_learn__microsoft_docs_search` with "Copilot Studio agent instructions best practices GPT system prompt" — Microsoft's official guidance on instruction structure, length limits, and priority ordering

**After MS Learn searches, fetch key articles for deep reference:**
- `mcp__microsoft_learn__microsoft_docs_fetch` on the most relevant article URLs from search results
- This gives you exact Microsoft-validated patterns for topic design, trigger phrases, and GPT structure

**Why MS Learn matters:** Web searches find third-party interpretations. MS Learn gives you the SOURCE — exact patterns that Microsoft's own evaluation grader expects. An agent built to MS Learn patterns scores higher on evals because the grader is calibrated to those standards.

**Research output structure:**

```
domainResearch:
  regulations: [list with citations]
  terminology: {term: domain-specific definition}
  userQuestionPatterns: [15-30 real phrasings]
  edgeCases: [known exceptions, failure modes]
  recommendedSources:
    - name: Source Name
      url: https://...
      description: 50-300 char retrieval-focused description
```

**What makes researched instructions better:**
- Generic: "Answer payroll questions concisely"
- Researched: "Explain pay stub sections (gross, deductions, net, YTD). FICA = Social Security (6.2%) + Medicare (1.45%). Refer to payroll team for specific calculations — never estimate amounts."

### 0.2 Fleet Analysis

Query the target environment to understand existing agents:

```bash
# List all bots
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/bots?\$select=name,schemaname,statecode,publishedon" -o json

# Check for domain overlap with existing agents
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/bots?\$filter=contains(name,'[keyword]')&\$select=name,botid" -o json
```

**Analysis output:**
- existingBots: all bots with names + schemas
- workingPatterns: topic counts, GPT lengths, knowledge types from high-scoring agents
- gaps: what's missing that new agent fills
- conflicts: existing agents that overlap

### 0.3 Self-Critique Pass

Attack your own design:
- Too many topics? (>10 = orchestrator confusion)
- Overlapping intent between topics?
- Under 5,500 chars GPT? (count explicitly)
- Any conflicting guidance in GPT? (e.g. "be concise" vs "be comprehensive")
- Enough knowledge sources for all topics?
- Trigger phrases diverse and natural?

### 0.4 Specification Output

Produce the Agent Spec containing:

**Agent identity:** name, description, orchestration mode (Generative)

**Topics** (each with):
- name: "Action/Domain Specific Scope" pattern
- triggerPhrases: ≥5 from REAL user language (never YAML syntax)
- additionalInstructions: ≤4 bullets, specific to this topic, "Close with:" on final bullet
- description: 30-50 words with domain terms + 3-5 sub-topics listed

**GPT instructions structure:**
```
SCOPE → ROLE → RESPONSE FORMAT → RESPONSE BEHAVIOR (≤6 rules) → DOMAIN-SPECIFIC → CONVERSATION CONTINUITY → SAFETY
```

**Knowledge sources** (each with): type, name, 50-300 char retrieval-focused description

**Conversation starters:** EXACTLY 10. First 3 = most common use cases. Cover every topic. Include 1-2 scope boundary starters.

**Length limits:**
- Specialist GPT: ≤5,500 chars
- Orchestrator GPT: ≤7,000 chars
- Topics: 3-10 (sweet spot: 5-7)

📸 **VISUAL CHECKPOINT** — Save Agent Spec to `scratch/[agent-name-kebab]/AGENT-SPEC.md`. Confirm with user before proceeding.

---

## Phase 1: Preflight

**Entry:** Agent Spec approved
**Exit:** Mode determined, environment confirmed

### 1.1 Azure CLI Auth Check

```bash
az account get-access-token --resource "https://orgbd048f00.crm.dynamics.com/" --query accessToken -o tsv 2>/dev/null
```

- Token returned → Full Auto mode ✅
- No token → try `az login --tenant 03cc92c3-986c-4cf4-ae27-1478cf99d17f`
- Still fails → Generate + Instruct mode

### 1.2 pac CLI Auth Check

```bash
pac auth who 2>/dev/null
```

- Shows correct environment → ✅
- Expired → `pac auth create --environment https://orgbd048f00.crm.dynamics.com`

### 1.3 Environment Confirmation

```bash
# Get Dataverse org URL from environment ID
TOKEN=$(az account get-access-token --resource 'https://service.powerapps.com/' --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.powerapps.com/providers/Microsoft.PowerApps/environments/a944fdf0-0d2e-e14d-8a73-0f5ffae23315?api-version=2023-06-01"
```

### Mode Determination

| Check | Full Auto | Generate + Instruct |
|-------|-----------|---------------------|
| az token | ✅ Valid | ❌ Unavailable |
| pac CLI | ✅ Authenticated | May work independently |
| Deploy method | Dataverse API (single token) | Generate files + user pastes |

📸 **VISUAL CHECKPOINT** — Report mode and environment to user. Confirm before Phase 2.

---

## Phase 2: Agent Shell Creation

**Entry:** Preflight passed
**Exit:** Bot ID + Schema Name captured

### Step 1: Instruct User

> **Create the agent in Copilot Studio:**
> 1. Open https://copilotstudio.microsoft.com → select "Therapy AI Agents Dev"
> 2. Click **Create** → **New agent**
> 3. Name: "[name from Phase 0 spec]"
> 4. Description: "[description from spec]"
> 5. Save (don't publish yet)
> 6. Tell me once created

### Step 2: Capture Bot ID + Schema Name

```bash
# Query for the new bot
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/bots?\$filter=contains(name,'[AgentName]')&\$select=name,botid,schemaname&$orderby=createdon desc&\$top=1" -o json
```

**Capture:** `botid` (GUID) and `schemaname` (e.g. `cr917_AgentName`). Store both.

📸 **VISUAL CHECKPOINT** — Query bot record. Confirm it exists with name, botid, and schemaname.

---

## Phase 3: Topic and GPT Generation

**Entry:** Bot ID + Schema captured
**Exit:** All artifacts generated + validated, saved to `scratch/[agent-name-kebab]/`

### 3.1 GPT Instructions

Generate using the researched content from Phase 0. Structure:

```
SCOPE — What agent covers and doesn't. Clear in-scope/out-of-scope.
ROLE — Professional role with correct terminology from research.
RESPONSE FORMAT — How responses structured (bullets, length, citations).
RESPONSE BEHAVIOR — ≤6 actionable, non-redundant rules.
DOMAIN-SPECIFIC — Key domain rules from Phase 0 research.
CONVERSATION CONTINUITY — Multi-turn handling.
SAFETY — Domain guardrails. MUST include anti-fabrication rule.
```

**Critical rule:** Anti-fabrication MUST be in SAFETY section: "Never invent facts, statistics, citations, or claims. If unsure, say so."

**modelDescription (description: field):** "[Domain] specialist that [primary function]. Handles [key topics]. Provides [output type] grounded in [knowledge sources]." Max 1024 chars.

Save to: `scratch/[agent-name-kebab]/GPT-INSTRUCTIONS.txt`

### 3.2 Topic YAML Generation

Use this EXACT template for every topic (fill values from Agent Spec):

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: [Topic Name — Action/Domain Specific Scope]
    triggerQueries:
      - [phrase 1 — from real user language]
      - [phrase 2 — different phrasing]
      - [phrase 3 — diverse variant]
      - [phrase 4 — natural conversational style]
      - [phrase 5 — another approach]
    description: [1 sentence — orchestrator routing signal, 30-50 words, domain terms + 3-5 sub-topics]
  actions:
    - kind: SearchAndSummarizeContent
      id: search-[kebab-name]
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        [Instruction 1 — from Phase 0 research, specific to THIS topic]
        [Instruction 2 — domain-specific guidance]
        [Instruction 3 — what to include]
        [Instruction 4 — max 4 bullets. Final: "Close with: [action]"]
      applyModelKnowledgeSetting: true
    - kind: SendActivity
      id: send-answer
      activity: "{Topic.Answer}"
    - kind: EndDialog
      id: end-topic
      clearTopicQueue: true
inputType: {}
outputType: {}
```

**⚠️ CRITICAL — SendActivity Format:**
- ✅ CORRECT: `activity: "{Topic.Answer}"` — string interpolation
- ❌ WRONG: `activity: =Topic.Answer` — Power Fx pill, outputs NOTHING

Save each topic to: `scratch/[agent-name-kebab]/topics/[NN]-[topic-kebab].yaml`

### 3.3 Conversation Starters

Exactly 10. Format:
```yaml
conversationStarters:
  - title: [3-5 words]
    text: [Full natural prompt]
```

Rules:
- First 3 = most common/important use cases
- Cover every custom topic with ≥1 starter
- Include 1-2 scope boundary starters
- Each starter triggers a DIFFERENT topic

### 3.4 Pre-Deploy Validation

ALL checks MUST pass before Phase 4:

| # | Check | Requirement |
|---|-------|-------------|
| 1 | Trigger phrases | ≥5 per topic, ALL natural language, NO YAML syntax |
| 2 | Latency message | `allowLatencyMessage: false` on all topics |
| 3 | Model knowledge | `applyModelKnowledgeSetting: true` on all topics |
| 4 | Topic queue | `clearTopicQueue: true` on all EndDialog |
| 5 | Instructions | ≤4 additionalInstructions per topic, "Close with:" on final |
| 6 | SendActivity | ALL topics use `"{Topic.Answer}"` format |
| 7 | IDs | Unique across all topics |
| 8 | Topic count | ≤10 custom topics |
| 9 | GPT length | ≤5,500 chars specialist / ≤7,000 orchestrator |
| 10 | Starters | Exactly 10, diverse |
| 11 | webBrowsing | `false` in GPT capabilities |
| 12 | Topic descriptions | 30-50 words, domain terms, 3-5 sub-topics |
| 13 | additionalInstructions | Specific + actionable + "Close with:" pattern |

**Trigger phrase overlap detection:** Compare triggers across topics. If >80% word overlap between DIFFERENT topics → merge or rename. Exact duplicate → hard fail.

**If any check fails:** Fix and re-validate. Do NOT proceed to Phase 4 with failures.

**🆕 MS Learn Schema Validation:** Before deploying, fetch the latest topic YAML schema and GPT instruction guidance from Microsoft:
```
tool_call: mcp__microsoft_learn__microsoft_docs_search
  query: "Copilot Studio topic YAML schema AdaptiveDialog SearchAndSummarizeContent"
→ Fetch the top result article for exact YAML structure
→ Validate all generated topics against the official schema
→ Validate GPT structure against Microsoft's recommended format
```
This catches YAML issues that aren't obvious in manual review — missing fields, wrong indentation, invalid node types.

📸 **VISUAL CHECKPOINT** — List all generated files with sizes. Confirm validation pass/fail per topic.

---

## Phase 4: Cascade Deployment

**Entry:** All validated (Phase 3 passed)
**Exit:** All components deployed (topics, GPT, knowledge, formatting, starters)

**Single-Token Flow:** Get token ONCE, execute ALL API operations sequentially, publish ONCE at end.

### 4.0 Get Authentication Token

```bash
ORG="https://orgbd048f00.crm.dynamics.com"
TENANT="03cc92c3-986c-4cf4-ae27-1478cf99d17f"
TOKEN=$(az account get-access-token --resource "$ORG/" --tenant "$TENANT" --query accessToken -o tsv)
BOT_ID="[from Phase 2]"
echo "Token: ${#TOKEN} chars"
```

### 4.1 GPT Instructions (Type 15)

**Find the type 15 component:**
```bash
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '$BOT_ID' and componenttype eq 15&\$select=botcomponentid,data,name" -o json
```

**Build the GPT YAML:**
```yaml
kind: GptComponentMetadata
displayName: [Agent Name]
description: [Orchestrator-facing description from Phase 3.1]
instructions: |-
  [FULL GPT INSTRUCTIONS from GPT-INSTRUCTIONS.txt]
responseInstructions: [Conciseness directive, ≤500 chars]
gptCapabilities:
  webBrowsing: false
conversationStarters:
  - title: [Starter 1]
    text: [Starter 1 text]
  - title: [Starter 2]
    text: [Starter 2 text]
  # ... all 10
```

**PATCH the component:**
```bash
# Read GPT YAML from file, escape for JSON, PATCH
GPT_YAML=$(cat scratch/[agent-name]/GPT-YAML.txt | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
COMPONENT_ID="[from query above]"

az rest --resource "$ORG/" --method PATCH \
  --url "$ORG/api/data/v9.2/botcomponents($COMPONENT_ID)" \
  --body "{\"data\": $GPT_YAML}" \
  --headers "Content-Type=application/json" "If-Match=*" -o json
```

**Validation before PATCH:**
- YAML starts with `kind: GptComponentMetadata` (not `kind:` alone)
- Only ONE `kind:` declaration
- `description:` field present (max 1024 chars)
- `webBrowsing: false` in gptCapabilities
- `responseInstructions:` present
- `conversationStarters:` has exactly 10 entries

⚠️ ALWAYS full replacement — never append. The `data` field is the COMPLETE GPT component.

### 4.2 Topic Deployment (Type 9)

**🆕 Parallel Deployment:** POST all topics concurrently (up to 5 at a time) rather than sequentially:

```python
# Execute in parallel via execute_code or multiple terminal calls
# Post 5 topics at once, wait for all, verify all succeeded
topics = [...]  # list of (name, yaml_content, schema_name)
results = []
for topic in topics:
    # POST each topic
    # Collect component IDs
# Verify count matches expected
```

**POST each topic (with retry):**
```bash
# For each topic YAML file — retry up to 3 times with backoff
TOPIC_NAME="[Topic Display Name]"
TOPIC_YAML=$(cat "scratch/[agent-name]/topics/[NN]-[topic].yaml" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
SCHEMA_NAME="cr917_$(echo "$TOPIC_NAME" | sed 's/[^a-zA-Z0-9]//g')"

for attempt in 1 2 3; do
  RESULT=$(az rest --resource "$ORG/" --method POST \
    --url "$ORG/api/data/v9.2/botcomponents" \
    --body "{
      \"componenttype\": 9,
      \"parentbotid@odata.bind\": \"/bots($BOT_ID)\",
      \"name\": \"$TOPIC_NAME\",
      \"data\": $TOPIC_YAML,
      \"schemaname\": \"$SCHEMA_NAME\"
    }" \
    --headers "Content-Type=application/json" -o json 2>&1)
  
  if echo "$RESULT" | grep -q "botcomponentid"; then
    echo "✅ Topic '$TOPIC_NAME' created (attempt $attempt)"
    break
  else
    echo "⚠️ Attempt $attempt failed, retrying in $((attempt * 2))s..."
    sleep $((attempt * 2))
  fi
done
```

**⚠️ CRITICAL — Navigation Property:**
- ✅ CORRECT: `"parentbotid@odata.bind": "/bots($BOT_ID)"`
- ❌ WRONG: `"_parentbotid_value": "$BOT_ID"` — causes `0x80060888`

**Pre-POST validation per topic:**
1. Must start with `kind: AdaptiveDialog`
2. `clearTopicQueue: true` present
3. `SendActivity` present
4. No `applyModelKnowledgeSetting: false`
5. Strip BOM if present

### 4.3 Knowledge Sources

**Upload files (browser — UI only for binary content):**
```
1. browser_navigate → https://copilotstudio.microsoft.com/environments/[ENV_ID]/bots/[BOT_ID]/knowledge
2. Wait for SPA render (~10s)
3. Click "Add knowledge"
4. Find file input → setInputFiles([file_paths])
5. Click "Add to agent"
6. Wait for "Ready" status (~30-60s)
```

**Create web URL sources (API):**
```bash
az rest --resource "$ORG/" --method POST \
  --url "$ORG/api/data/v9.2/botcomponents" \
  --body "{
    \"name\": \"[Source Display Name]\",
    \"componenttype\": 16,
    \"parentbotid@odata.bind\": \"/bots($BOT_ID)\",
    \"data\": \"{\\\"url\\\":\\\"https://github.com/user/repo/blob/main/file.md\\\",\\\"description\\\":\\\"[retrieval-focused description]\\\",\\\"isOfficialSource\\\":true,\\\"sourceType\\\":\\\"PublicSiteSearchSource\\\"}\"
  }" \
  --headers "Content-Type=application/json" -o json
```

**After upload/creation — PATCH name + description + Official Source:**
```bash
# Query all knowledge sources
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '$BOT_ID' and (componenttype eq 14 or componenttype eq 16)&\$select=botcomponentid,name,data,componenttype" -o json

# For each source, PATCH name + description
az rest --resource "$ORG/" --method PATCH \
  --url "$ORG/api/data/v9.2/botcomponents([COMPONENT_ID])" \
  --body "{
    \"name\": \"[Display Name — Authority/Source Type]\",
    \"data\": \"{\\\"description\\\":\\\"[50-300 char retrieval-focused description with domain keywords]\\\",\\\"isOfficialSource\\\":true}\"
  }" \
  --headers "Content-Type=application/json" "If-Match=*" -o json
```

**When to use web URL vs file upload:**
- Web URL: Stable public content (GitHub .md, gov docs), less eval-sensitive agents
- File upload: Deterministic retrieval needed for eval, private/not web-accessible
- Therapy audit agents: Always file uploads
- Game/utility agents: Web URLs acceptable

**Duplicate detection (run BEFORE adding):**
```bash
# Query all, group by name, delete extras
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '$BOT_ID' and (componenttype eq 14 or componenttype eq 16)&\$select=name,botcomponentid" -o json
```

### 4.4 Teams/M365 Activation (skip if not needed)

Only if agent needs Teams/M365 Copilot availability:

PATCH bot entity with `applicationmanifestinformation` + `configuration.channels` including MsTeams.

⚠️ Re-publish REQUIRED after Teams activation.

### 4.5 Work IQ Disable (MANDATORY)

Work IQ MUST be disabled. It uses per-user OAuth that blocks eval channel → causes 0-15% eval scores.

Check: query type 9 components for `InvokeExternalAgentTaskAction`. If found → deactivate.

For new agents (no built-in Work IQ topics): this is auto-disabled.

Verify post-publish: Agent → Overview → Tools → Work IQ = Disabled.

📸 **VISUAL CHECKPOINT** — After deployment:
1. Query all botcomponents — confirm type 15 (GPT), type 9 (topics), type 14/16 (knowledge) present
2. Count topics deployed = expected count
3. Verify GPT component has `description:` field
4. Verify knowledge sources have descriptions + isOfficialSource

**🆕 Post-Deploy Diff Verification:** Query back what was actually deployed and diff against local files:
```bash
# Pull all deployed topics
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '$BOT_ID' and componenttype eq 9&\$select=name,data" -o json

# Compare: for each deployed topic name, verify YAML contains all required fields
# Flag any topics where: clearTopicQueue is missing, allowLatencyMessage is true, 
# or applyModelKnowledgeSetting is false
```
This catches deployment corruption that wouldn't surface until eval runs.

---

## Phase 5: QA Verification

**Entry:** Deployment complete
**Exit:** All 12 sections pass

Run ALL checks. If ANY section fails, fix before publishing. After fixing, re-run FULL QA (not partial).

### Checklist

| # | Section | Key Checks |
|---|---------|------------|
| 5.1 | Agent Overview | Name descriptive, description set in GPT YAML |
| 5.2 | Knowledge Sources | Named + described + Official, "Ready" status, no duplicates |
| 5.3 | Tools/Agents | Skip if no tools; Work IQ disabled if therapy agent |
| 5.4 | Topics | ≤10, ≥5 triggers each, natural language only, descriptions 30-50 words |
| 5.5 | Generative Nodes | allowLatencyMessage:false, applyModelKnowledgeSetting:true, ≤4 additionalInstructions |
| 5.6 | SendActivity | ALL use `"{Topic.Answer}"` format, NOT `=Topic.Answer` |
| 5.7 | EndDialog | clearTopicQueue:true on ALL |
| 5.8 | Starters | Exactly 10, diverse, cover all topics, include scope boundaries |
| 5.9 | GPT | Structured (7 sections), ≤5,500 chars, webBrowsing:false, anti-fabrication rule present |
| 5.10 | Response Formatting | responseInstructions set, ≤500 chars |
| 5.11 | Model | Default, not unnecessarily changed |
| 5.12 | Fleet Constraints | ALL constraints pass |

### Trigger Phrase Overlap Detection

```python
# Run against all topic trigger phrases
# Compare word-level Jaccard similarity
# >80% similarity across DIFFERENT topics → merge warning
# Exact duplicate → hard fail
```

### Duplicate Knowledge Source Detection

```bash
# Query all, group by name, flag duplicates
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '$BOT_ID' and (componenttype eq 14 or componenttype eq 16)&\$select=name,botcomponentid" -o json
# If duplicates: keep oldest, DELETE extras
```

📸 **VISUAL CHECKPOINT** — Produce pass/fail per section:
```
✅ 5.1 Agent Overview: PASS
✅ 5.2 Knowledge Sources: PASS — [N] sources, all Ready
✅ 5.3 Tools/Agents: SKIPPED
✅ 5.4 Topics: PASS — [N] topics, ≥5 triggers each
...
OVERALL: PASS — proceed to Phase 6
```

**🆕 MS Learn Compliance Cross-Reference:** Before finalizing QA, cross-reference against Microsoft's latest published standards:
```
tool_call: mcp__microsoft_learn__microsoft_docs_search
  query: "Copilot Studio agent evaluation readiness checklist best practices 2025 2026"
→ Verify our 12-section checklist still aligns with Microsoft's current recommendations
→ Flag any new requirements Microsoft has added since the pipeline was authored
→ Update fleet constraints if Microsoft's standards have changed
```

---

## Phase 6: Publish and Test Chat

**Entry:** QA passed
**Exit:** Published + Test Chat verified

### 6.1 Publish

```bash
# Publish via pac CLI
pac copilot publish --bot $BOT_ID --environment $ORG

# OR via gateway publishv2 (more reliable)
TOKEN_GW=$(az account get-access-token --resource '96ff4394-9197-43aa-b393-6a41652e21f8' --query accessToken -o tsv)
TENANT=$(az account show --query tenantId -o tsv)

# Find region (try us-il106 through us-il110)
for REGION in us-il106 us-il107 us-il108 us-il109 us-il110; do
  GATEWAY="https://powervamg.${REGION}.gateway.prod.island.powerapps.com"
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "${GATEWAY}/api/botmanagement/v1/environments/a944fdf0-0d2e-e14d-8a73-0f5ffae23315/bots/${BOT_ID}/publishv2-operations" \
    -H "Authorization: Bearer $TOKEN_GW" \
    -H "X-CCI-TenantId: $TENANT" \
    -H "x-cci-applicationsource: Web" \
    -d '{}')
  [ "$HTTP" != "404" ] && break
done
```

**Verify publish succeeded:**
```bash
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/bots($BOT_ID)?\$select=synchronizationstatus" -o json
# Parse: lastFinishedPublishOperation.status must = "Succeeded"
```

### 6.2 Post-Publish Checks

**Wait 90 seconds** after publish before testing.

Then verify:
1. Work IQ = Disabled (Agent → Overview → Tools)
2. Response Formatting still set
3. All topics visible

### 6.3 Test Chat Verification

Use browser tool to test the agent:

1. Navigate to agent overview
2. Click "Test your copilot"
3. Test all 10 conversation starters
4. Test 1 out-of-scope question
5. Test 1 follow-up question

**Pass criteria:**
- All 10 starters → relevant, formatted responses ✅
- Out-of-scope → graceful decline ✅
- No Work IQ auth blocking ✅
- No empty responses or errors ✅
- Follow-up maintains context ✅

📸 **VISUAL CHECKPOINT** — Screenshot Test Chat results. Show publish status + first 3 starter responses.

---

## Phase 7: Optimization

**Entry:** Published + Test Chat verified
**Exit:** Scores ≥90% OR optimization complete + documented

**Only enter Phase 7 if:**
- Test Chat reveals issues
- Eval scores < 90%
- Agent works but could be better

**Skip Phase 7 if** Test Chat passes cleanly AND initial eval ≥ 90%.

### Proven Fix Sequence (Apply in Order)

1. **Deactivate Work IQ** → +49 pts validated
2. **Set Response Formatting** → +33-47 pts validated
3. **Trim GPT if >5,500 chars** → reduces budget overflow
4. **Fix topic architecture** → ≤10 topics, EndDialog+clearTopicQueue:true, ≤4 bullet additionalInstructions
5. **Publish + wait 90s** → verify synchronizationstatus
6. **Eval 3x** → stable measurement (±5% variance expected)

### Hard Rules

- **NEVER rewrite GPT on agents scoring >50%** unless confirmed corrupted
- **NEVER change AI model** unless testing proves current model ineffective
- **NEVER add OnGeneratedResponse** triggers (platform bug)
- **NEVER delete clinical/compliance/regulatory content** during optimization

### Optimization Complete When:
1. All eval sets ≥ 90%
2. Scores consistent across 3 runs (<5% variance)
3. Known gaps documented
4. No blocking issues

---

## Pipeline Summary Output

```
✅ Agent "[Name]" built successfully

Pipeline Results:
- Mode: [Full Auto / Generate + Instruct]
- Topics: [N] created
- GPT: [N] chars
- Starters: 10
- Knowledge: [N] sources
- Response Formatting: Set ✅
- Work IQ: Disabled ✅

Fleet Constraints: ALL PASS
- webBrowsing: false ✅
- clearTopicQueue: true (all topics) ✅
- allowLatencyMessage: false (all topics) ✅
- applyModelKnowledgeSetting: true (all topics) ✅
- Topic count: [N] (≤10) ✅
- GPT length: [N] (≤5,500) ✅

Publish: Succeeded ✅
Test Chat: [N/10] starters passed ✅

Pipeline Status: COMPLETE
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `az account get-access-token` fails | Token expired | `az login --tenant 03cc92c3-986c-4cf4-ae27-1478cf99d17f` |
| Topic POST: `0x80060888` | Using `_parentbotid_value` | Use `parentbotid@odata.bind` navigation property |
| All responses are auth prompts | Work IQ enabled | Disable Work IQ → re-publish |
| 0% eval scores | Corrupted triggers (YAML syntax) | Full topic replacement, never partial edit |
| Empty responses from agent | `activity: =Topic.Answer` format | Change to `activity: "{Topic.Answer}"` |
| Publish fails: `MissingRequiredProperty` | Empty conversation starter `{}` | Replace with valid title+text |
| Bot not found in query | Agent not saved in UI | Verify user saved (not just named) the agent |
| Knowledge duplicates | Same file uploaded multiple times | Query by name, DELETE extras |

---

## File Structure After Build

```
scratch/[agent-name-kebab]/
├── AGENT-SPEC.md              ← Phase 0 spec
├── GPT-INSTRUCTIONS.txt       ← Phase 3 GPT (clean text)
├── GPT-YAML.txt               ← Phase 4 GPT (full YAML with metadata)
├── topics/
│   ├── 01-[topic].yaml
│   ├── 02-[topic].yaml
│   └── ...
└── knowledge/
    └── manifest.md            ← Knowledge source manifest
```

## References

- **Kiro unified-pipeline.md** — Source: `D:\my agents copilot studio\.kiro\powers\copilot-studio-agent-builder-steering\steering\unified-pipeline.md`
- **copilot-studio-knowledge-api** — KS API patterns (loaded automatically)
- **copilot-studio-advisor** — Troubleshooting + design review
- **eval-triage-framework** — Eval interpretation
- **clinical-swarm-guardrails** — Fleet standards + compliance
