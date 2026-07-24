---
name: agent-architect
description: Requirements elicitation and topic architecture design for Copilot Studio agents. Takes a natural language description, asks structured clarifying questions, and produces a complete structured spec (topic map, routing matrix, KB requirements, settings, instructions outline). Output is consumed by agent-crafter for YAML generation and agent-qa-gate for verification. The "design" phase of the end-to-end agent builder.
version: 1.0.0
tags: [copilot-studio, architect, design, intake]
---

# Agent Architect

## When to Use
- User says "I need an agent that does [X]" — turn that into a buildable spec
- Before running agent-crafter (YAML generation)
- Before running agent-builder (topic creation)
- Before running agent-optimizer (eval improvement loop)

## How to Use
1. Load this skill
2. Ask the **Interview Questions** below — one at a time, synthesize the answers
3. Produce the **Structured Spec** (the output)
4. Save spec to a file for agent-crafter + agent-qa-gate to consume

---

## Interview Questions (ask in order, synthesize between each)

### Q1: Core Purpose
*Ask:* "What should this agent do? One sentence — what's its core job?"

**Good:** "Audit PT daily notes for Medicare compliance and flag documentation gaps."
**Bad:** "Help with paperwork."

**Synthesize into:**
- `purpose` — one-sentence mission
- `action_verb` — review/audit/generate/extract/route/synthesize
- `discipline` — PT / OT / SLP / multi / general
- `workflow_type` — audit (check for compliance) / generate (write notes) / extract (pull data) / route (classify and forward) / hybrid

### Q2: Input Method
*Ask:* "How do users interact with this agent? Do they upload files, paste text, click buttons, describe sessions in free text, or all of the above?"

**If files + text:** dual-input pattern (Pattern F from agent-audit-protocol)
**If files only:** dual-input still recommended (text path needed for eval)
**If buttons (AdaptiveCards):** card-based intake pattern
**If text only:** SASC with `=System.Activity.Text`
**If free-form session description ("braindump"):** AdaptiveCard with narrative text field + CPT/discipline dropdowns → SASC generates structured note

**Synthesize into:**
- `input_pattern` — file_text_dual / card_intake / text_only / braindump / hybrid
- `needs_upload` — true/false
- `needs_adaptivecards` — true/false

### Q3: Scope & Scale
*Ask:* "What topics/domains does this agent need to cover? List them. (e.g., 'PT daily notes, PT evaluations, PT progress notes, Medicare compliance questions')"

**Each topic needs:**
- A clear scope boundary (what it handles vs. what it doesn't)
- 5-10 trigger phrases (what users will say)
- A processing pattern: SASC-based generative answer vs. structured intake + AI

**Synthesize into:**
- `topics` — array of {name, purpose, trigger_phrases, pattern}
- `is_generative_answer` — true if mostly answering from KBs
- `is_structured_intake` — true if collecting data then processing

### Q4: Orchestration
*Ask:* "Is this a standalone agent that handles everything on its own, or does it route to other agents (hub-and-spoke)? If routing, what are the child agents?"

**Standalone:** Single agent, no connected agents. All topics in one agent.
**Orchestrator (hub):** Routes to specialist child agents. Has intake/classify topic + routing matrix.
**Specialist (spoke):** Receives routed requests from hub. Has specific topics for its domain.

**Synthesize into:**
- `mode` — standalone / orchestrator / specialist
- `connected_agents` — array of {name, bot_id, schema_name} if applicable
- `has_routing_topic` — true/false

### Q5: Knowledge Sources
*Ask:* "What authoritative sources should this agent reference? (CMS manuals, ASHA guidelines, internal protocols, etc.)"

**Each KB:**
- Name (descriptive, e.g., "CMS Medicare Benefit Policy Manual Ch.15")
- Description (1-2 sentences on what it covers — critical for generative routing)
- Source type (SharePoint folder, uploaded file, public URL)
- Official toggle (yes for regulatory sources)

**Synthesize into:**
- `knowledge_sources` — array of {name, description, type, official}

### Q6: Settings
*Ask:* "Is this a clinical/healthcare agent? Does it need high safety guardrails or more flexibility?"

**If clinical/healthcare:** Content Moderation = Medium (High false-positives on clinical terms), Model Knowledge = ON, Latency Messages = OFF
**If general:** Content Moderation = High, Model Knowledge = ON
**All agents:** Web search = OFF, Semantic search = ON, File analysis = ON, Generative actions = ON

**Synthesize into:**
- `is_healthcare` — true/false
- `settings` — moderation, model_knowledge, latency_messages, web_search

### Q7: Model
*Ask:* "Any model preference? If not, I'll recommend."

**Recommendation logic:**
- Healthcare/compliance agents → GPT-5 Chat (proven, stable)
- Creative/general agents → Sonnet 4.6 (more creative)
- Cost-sensitive → GPT-5 Chat
- No strong preference → GPT-5 Chat (safest default)

**Synthesize into:**
- `recommended_model` — string
- `reasoning` — why this model

### Q8: Exit Criteria
*Ask:* "What score threshold is acceptable? 95% is our fleet standard. Lower means faster but riskier."

**Synthesize into:**
- `sr_target` — default 95
- `conv_target` — default 95
- `min_acceptable` — default 80

---

## Structured Spec Output Template

After all questions answered, produce this YAML block and save to `_agent_spec.yaml`:

```yaml
# Agent Spec — generated by agent-architect
spec_version: 1.0
agent:
  name: "[From user — short, descriptive]"
  purpose: "[From Q1 — one sentence]"
  action_verb: audit        # review / audit / generate / extract / route / hybrid
  discipline: ot             # pt / ot / slp / multi / general
  workflow_type: audit       # audit / generate / extract / route / hybrid
  mode: standalone           # standalone / orchestrator / specialist
  is_healthcare: true
  recommended_model: "GPT-5 Chat"
  model_reasoning: "Stable for healthcare compliance workflows"

topics:
  - name: "[Topic Display Name]"
    modelDescription: "[What this topic does — 1 sentence]"
    trigger_phrases:
      - "[Natural language phrase 1]"
      - "[Natural language phrase 2]"
      - "[at least 5 total]"
    pattern: file_text_dual   # file_text_dual / card_intake / text_only / classify_and_route / extraction
    has_search: true          # uses SASC
    has_question: false       # has Question node (intake)
    needs_upload: true
    notes: "[Any design decisions, edge cases, or caveats]"
  - name: "..."
    # ... repeat per topic

routing:
  has_routing_topic: false
  connected_agents: []
  # If orchestrator:
  # - agent_name: "[name]"
  #   bot_id: "[guid]"
  #   schema_name: "[copilots_header_xxx.agentName]"
  #   topics_routed: ["[topic1]", "[topic2]"]
  fallback_scope: "[Broad description of what Fallback should offer — prevents too-narrow Fallback]"
  generative_boosting_instructions: "[Brief instructions for the boosting catch-all SASC]"

knowledge_sources:
  - name: "[Descriptive KB name]"
    description: "[1-2 sentences on content scope — critical for routing]"
    type: sharepoint          # sharepoint / upload / public_url
    official: true            # toggle for regulatory sources

settings:
  content_moderation: Medium  # Medium for healthcare, High for general
  model_knowledge: true
  semantic_search: true
  file_analysis: true
  latency_messages: false
  web_search: false
  conversation_starters:
    - "[How can I help you today? Specific 1]"
    - "[Specific 2]"
    - "[5-10 total, matching core workflow]"

instructions_outline:
  - "# Role Identity"            — "1-2 sentence what agent IS and IS NOT"
  - "# Scope & Boundaries"       — "What it handles, what it routes/escalates"
  - "# Constraints"              — "HIPAA, HITL, safety, no PHI in outputs"
  - "# Response Format"          — "Conditional: structured for audits, plain for general"
  - "# Knowledge Sources"        — "List what KBs are available (reference only, not restrictive)"
  - "# Handling Edge Cases"      — "What to do when info is missing, ambiguous, or out of scope"
  - "## EVALUATION CONTEXT"      — "**CONDITIONAL PRIMARY DIRECTIVE.** Two subsections REQUIRED:
    - WHEN THE USER PROVIDES CLINICAL TEXT: 'Extract from provided text only. DO NOT search KBs.'
    - WHEN THE USER ASKS A GENERAL QUESTION WITHOUT TEXT: 'DO search KBs and answer from standards.'
    This pattern alone adds +12pp on eval scores (proven: 36%→43% on Case History agent)."
  - "## Swarm Membership"        — "If part of fleet: role, handoff protocol, inter-agent contract"

qa_gates:
  - "All topics have EndDialog + clearTopicQueue:true"
  - "All SASC nodes have responseCaptureType: FullResponse"
  - "No FilePrebuiltEntity — use StringPrebuiltEntity + 3-branch ConditionGroup"
  - "No file[] / turn.uploadedFiles"
  - "Fallback has SASC + EndDialog + broad offer"
  - "Conversational boosting has additionalInstructions"
  - "responseInstructions has NO unconditional format bans"
  - "EVALUATION CONTEXT block present in instructions"
  - "At least 5 trigger phrases per topic"
  - "No duplicate triggers across topics"
  - "Connected agents active (statecode=0)"
  - "ConversationStart has EndDialog(clearTopicQueue:true)"
```

---

## Pattern Selection Logic

Based on the answers, determine which `copilot-studio-patterns` to apply:

| Input Pattern | Topics Need | Applied Pattern |
|---------------|-------------|-----------------|
| File+text upload + audit | Question(StringPrebuiltEntity) → ConditionGroup(file/text/none) → SASC → SendActivity → EndDialog | File+Text dual-input + Document Intake |
| Card-based intake + generate | AdaptiveCardPrompt → SASC → SendActivity(Note DRAFT) → BeginDialog(Audit) → EndDialog | Card-based documentation |
| Classify-then-route | Question(ClosedListEntity) → ConditionGroup → BeginDialog(per option) | Classify-and-route |
| Text-only Q&A | SASC with =System.Activity.Text → SendActivity(=Topic.Answer) → EndDialog | Direct Q&A |
| Orchestrator with children | Intake → BeginDialog(specialist) per discipline | Hub-and-spoke routing |
| Extraction from pasted text | SASC with =Concatenate("extract…", Char(10), System.Activity.Text), applyModelKnowledgeSetting:false | Inline extraction |
| Braindump-to-note (free-text narrative) | AdaptiveCardPrompt (narrative text + CPT dropdown + discipline selector) → SetVariable → SASC (SOAP note generation) → SendActivity → EndDialog | Braindump-to-note |

---

## Architecture Rules (non-negotiable from how-to)

1. Every audit/review topic ends with a decisive output — no "maybe" or "ask someone else"
2. Every topic's flow is linear: intake → process → output → end — no branching back to intake
3. No topic needs both FilePrebuiltEntity and a text-path elseAction — use StringPrebuiltEntity always
4. Every branch in a ConditionGroup ends in an action, never silently drops
5. The routing topic (if any) is the ONLY topic that should have multiple BeginDialog options — leaf topics go straight to SASC
6. If any topic needs file upload, ALL topics that share its domain also get dual-input (test consistency)
7. Empty elseActions = bug. Every elseAction must either SASC, GotoAction, or EndDialog
8. avoid over-segmentation (e.g., separate topics for 'analyze PT daily note' and 'analyze OT daily note' → same anatomy, difference is discipline context, so either one topic with variable discipline or two lean ones)

---

## References
- `copilot-studio-patterns` — 16 design patterns for topic architecture
- `agent-audit-protocol` Pattern F — File+Text dual-input
- `agent-qa-gate` — runs after this spec to verify the built agent matches the spec
- `agent-crafter` — consumes this spec to generate YAML
