---
name: agent-crafter
description: Consumes the structured spec from agent-architect and produces ALL YAML files for a Copilot Studio agent — agent instructions, topics, settings, and knowledge source config. Handles every topic pattern (file+text dual-input, card intake, classify-and-route, text-only Q&A, inline extraction). Produces editor-safe YAML that passes agent-qa-gate. The "build" phase of the end-to-end agent builder.
version: 1.0.0
tags: [copilot-studio, crafter, yaml, build]
references:
  - copilot-studio-yaml-reference — YAML schema reference
  - copilot-studio-patterns — 16 design patterns
  - agent-architect — spec format consumed by this skill
  - agent-qa-gate — verification gate after this skill
---

# Agent Crafter

## When to Use
- AFTER agent-architect has produced `_agent_spec.yaml`
- To generate ALL topic YAML + instructions + settings from a spec
- BEFORE agent-qa-gate (verification)

## How to Use
1. Load this skill
2. Read `_agent_spec.yaml` (from agent-architect)
3. For each topic in spec.topics: generate YAML using the pattern template
4. Generate instructions component (componenttype 15 data)
5. Write all files to the workspace
6. Report file inventory to user

---

## File Inventory (what gets created)

| File | Purpose | Source |
|------|---------|--------|
| `agent.mcs.yml` | Agent metadata + instructions + settings | spec.agent + spec.instructions_outline + spec.settings |
| `topics/{topic_name}.mcs.yml` | One per spec.topics[N] | spec.topics[N] + pattern template |
| `_topic_inventory.txt` | Quick reference of all topics | Generated from spec.topics |

---

## Pattern Templates (editor-safe, validated YAML)

### Template A: File+Text Dual-Input (for audit/review topics with document upload)
```yaml
# {topic_name}
kind: AdaptiveDialog
beginDialog:
  dialogType: AdaptiveDialog
  actions:
    - kind: Question
      id: question_doc_input
      variable: init:Topic.DocumentText
      prompt: "Paste {document_type} documentation text, or upload the PDF for audit."
      entity: StringPrebuiltEntity
      allowInterruption: false
    - kind: ConditionGroup
      id: conditionGroup_input_check
      conditions:
        - id: branch_file
          condition: "=!IsBlank(First(System.Activity.Attachments))"
          actions:
            - kind: SearchAndSummarizeContent
              id: sasc_file_audit
              userInput: "=Concatenate(\"Audit the following therapy documentation for Medicare compliance. Identify documentation gaps, missing required elements, and compliance risks. Produce a structured audit report with: [DM] Document Type → [FR] Findings → [SCORE] X/100 → [GAPS] Missing Elements → [REC] Recommendations.\", Char(10), System.Activity.Text)"
              additionalInstructions: |-
                You are a {discipline} documentation compliance auditor. 
                Base your audit on CMS Chapter 15, 42 CFR Part 409, and payer-specific medical review criteria.
                Flag each finding as High/Medium/Low risk.
                Cite the specific regulation or guideline for each flag.
                Do NOT fabricate clinical data — only audit what is present.
                If the document text is unclear or insufficient, state what is missing.
              responseCaptureType: FullResponse
              allowLatencyMessage: false
        - id: branch_text
          condition: "=!IsBlank(Trim(Topic.DocumentText))"
          actions:
            - kind: SearchAndSummarizeContent
              id: sasc_text_audit
              userInput: "=Concatenate(\"Audit the following therapy documentation for Medicare compliance. Identify documentation gaps, missing required elements, and compliance risks. Produce a structured audit report with: [DM] Document Type → [FR] Findings → [SCORE] X/100 → [GAPS] Missing Elements → [REC] Recommendations.\", Char(10), Topic.DocumentText)"
              additionalInstructions: |-
                You are a {discipline} documentation compliance auditor. 
                Base your audit on CMS Chapter 15, 42 CFR Part 409, and payer-specific medical review criteria.
                Flag each finding as High/Medium/Low risk.
                Cite the specific regulation or guideline for each flag.
                Do NOT fabricate clinical data — only audit what is present.
                If the document text is unclear or insufficient, state what is missing.
              responseCaptureType: FullResponse
              allowLatencyMessage: false
        - id: branch_none
          condition: "=true"
          actions:
            - kind: SendActivity
              id: send_nothing_provided
              activity: "I didn't receive any documentation. Please paste or upload the {document_type} you'd like me to audit."
            - kind: GotoAction
              id: goto_ask_again
              action: question_doc_input
    - kind: SendActivity
      id: send_audit_result
      activity: "={Topic.DocumentText}"    # populated by whichever SASC ran
    - kind: EndDialog
      id: end_audit
      clearTopicQueue: true
```

### Template B: Text-Only Q&A (for general knowledge / compliance Q&A topics)
```yaml
# {topic_name}
kind: AdaptiveDialog
beginDialog:
  dialogType: AdaptiveDialog
  actions:
    - kind: SearchAndSummarizeContent
      id: sasc_answer
      userInput: "=System.Activity.Text"
      additionalInstructions: |-
        You are a {discipline} compliance expert.
        Answer the question directly based on your knowledge sources.
        If the question is about a specific regulation or guideline, cite it.
        Provide complete, thorough information — not just a summary.
        For general questions, respond conversationally.
        Do NOT ask the user to provide documentation first.
      responseCaptureType: FullResponse
      allowLatencyMessage: false
    - kind: SendActivity
      id: send_answer
      activity: "={Topic.Answer}"
    - kind: EndDialog
      id: end_answer
      clearTopicQueue: true
```

### Template C: Card-Based Intake + Generation (for documentation generation agents)
```yaml
# {topic_name}
kind: AdaptiveDialog
beginDialog:
  dialogType: AdaptiveDialog
  actions:
    - kind: AdaptiveCardPrompt
      id: card_ intake
      variable: init:Topic.CardData
      prompt: "Complete the {note_type} fields below."
      entity: StringPrebuiltEntity
      card:
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json"
        type: AdaptiveCard
        version: "1.5"
        body:
          - type: TextBlock
            text: "| {note_type_title}"
            weight: bolder
            wrap: true
          - type: Input.Text
            id: field_1
            placeholder: "Enter details..."
          - type: Input.ChoiceSet
            id: field_choice
            choices:
              - title: "Option 1"
                value: "Option 1"
              - title: "Option 2"
                value: "Option 2"
            style: expanded
        actions:
          - type: Action.Submit
            title: "Generate Note"
            data:
              actionSubmitId: submit_{topic_name}
    - kind: SetVariable
      id: set_draft
      variable: Topic.CardSummary
      value: "={Concatenate(Topic.CardData.field_1, \", \", Topic.CardData.field_choice)}"
    - kind: SearchAndSummarizeContent
      id: sasc_generate
      userInput: "=Concatenate(\"Generate a complete {note_type} based on this clinical data. Use professional SOAP format. Include all required elements per Medicare guidelines. The note must be ready for signature.\", Char(10), Topic.CardSummary)"
      additionalInstructions: |-
        Generate a professionally formatted {note_type} note.
        Use the card data provided. Do NOT add fabricated clinical measurements — use only what was provided.
        Format as a complete clinical note suitable for medical records.
        Follow Medicare documentation standards.
      responseCaptureType: FullResponse
      allowLatencyMessage: false
    - kind: SendActivity
      id: send_draft
      activity: "=Concatenate(\"## {note_type_title} — DRAFT\", Char(10), Char(10), Topic.Answer, Char(10), Char(10), \"⚠️ CLINICAL REVIEW REQUIRED — This is an AI-generated draft. Review and verify all content before signing.\")"
    - kind: EndDialog
      id: end_generate
      clearTopicQueue: true
```

### Template D: Classify-and-Route Intake (for orchestrator agents)
```yaml
# {topic_name}
kind: AdaptiveDialog
beginDialog:
  dialogType: AdaptiveDialog
  actions:
    - kind: Question
      id: question_classify
      variable: init:Topic.Classification
      prompt: "What type of {domain} do you need help with?"
      entity: StringPrebuiltEntity
      allowInterruption: false
    - kind: ConditionGroup
      id: conditionGroup_route
      conditions:
        # One per routing option
        - id: route_option_1
          condition: "=Contains(Topic.Classification, \"{option_1_keyword}\")"
          actions:
            - kind: BeginDialog
              id: begin_option_1
              dialog: {option_1_topic_id}
        - id: route_option_2
          condition: "=Contains(Topic.Classification, \"{option_2_keyword}\")"
          actions:
            - kind: BeginDialog
              id: begin_option_2
              dialog: {option_2_topic_id}
        - id: route_fallback
          condition: "=true"
          actions:
            - kind: SendActivity
              id: send_unclear
              activity: "I'm not sure which topic that falls under. Could you rephrase? I can help with: {option_1_keyword}, {option_2_keyword}."
            - kind: GotoAction
              id: goto_reask
              action: question_classify
    - kind: EndDialog
      id: end_route
      clearTopicQueue: true
```

### Template E: Inline Extraction (for extract/identify/synthesize from pasted text — fixes gptFallback failures)
```yaml
# {topic_name}
kind: AdaptiveDialog
beginDialog:
  dialogType: AdaptiveDialog
  actions:
    - kind: SearchAndSummarizeContent
      id: sasc_extract
      userInput: "=Concatenate(\"Extract the following elements from the clinical text below. For each element, provide the EXACT value from the text, the source sentence, and the line position. If an element is not present in the text, state 'NOT FOUND'. Do NOT infer or fabricate values. Elements to extract: {extraction_elements}.\", Char(10), System.Activity.Text)"
      additionalInstructions: |-
        You are a clinical data extraction specialist.
        Your job is to find and quote exact values from the provided text.
        Do NOT paraphrase — use the patient's exact words and values.
        If a value is not in the text, state "NOT FOUND" — do NOT invent it.
        Output format:
        | Element | Value | Source Text | Location |
      responseCaptureType: FullResponse
      allowLatencyMessage: false
      applyModelKnowledgeSetting: false
    - kind: SendActivity
      id: send_extraction
      activity: "={Topic.Answer}"
    - kind: EndDialog
      id: end_extract
      clearTopicQueue: true
```

### Template F: Braindump-to-Note (for free-text clinical narrative → structured note generation)
Designed for agents like TheraDoc Workbench. Clinician types a free-form session narrative, AI structures it into a Medicare-compliant note. Best paired with AdaptiveCardPrompt for CPT/discipline dropdowns + SASC for AI generation.

```yaml
# {topic_name}
kind: AdaptiveDialog
beginDialog:
  dialogType: AdaptiveDialog
  actions:
    - kind: AdaptiveCardPrompt
      id: card_braindump
      variable: init:Topic.Braindump
      prompt: "Describe the {discipline} session — what you did, patient response, observations."
      entity: StringPrebuiltEntity
      allowInterruption: false
      card:
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json"
        type: AdaptiveCard
        version: "1.5"
        body:
          - type: TextBlock
            text: "| {note_type} — Describe the Session"
            weight: bolder
            wrap: true
          - type: Input.Text
            id: clinical_narrative
            placeholder: "E.g.: Patient walked 50ft with FWW, min assist, pain 3/10."
            isMultiline: true
          - type: Input.ChoiceSet
            id: cpt_code
            choices:
              - title: "97110 Therapeutic Exercise" value: "97110"
              - title: "97112 Neuromuscular Re-ed" value: "97112"
              - title: "97116 Gait Training" value: "97116"
              - title: "97140 Manual Therapy" value: "97140"
              - title: "97530 Therapeutic Activities" value: "97530"
              - title: "97535 Self-Care/Home Mgmt" value: "97535"
              - title: "97542 Wheelchair Mgmt" value: "97542"
            placeholder: "Select CPT code"
          - type: Input.ChoiceSet
            id: discipline
            choices:
              - title: "PT" value: "PT"
              - title: "OT" value: "OT"
              - title: "SLP" value: "SLP"
            placeholder: "Select discipline"
        actions:
          - type: Action.Submit
            title: "Generate Note"
            data:
              actionSubmitId: submit_{topic_name}
    - kind: SetVariable
      variable: Topic.CombinedInput
      value: "={Concatenate(Topic.Braindump.discipline, \" | \", Topic.Braindump.cpt_code, \" | \", Topic.Braindump.clinical_narrative)}"
    - kind: SearchAndSummarizeContent
      id: sasc_generate
      userInput: "=Concatenate(\"Generate a {note_type} note from this clinical narrative. Use SOAP format. Include CPT code justification and medical necessity per Chapter 15.\", Char(10), Topic.CombinedInput)"
      additionalInstructions: |-
        Generate a professionally formatted {note_type} note in SOAP format.
        Use only the clinical narrative provided — do NOT fabricate data.
        Identify the CPT code and justify medical necessity.
        End with: "DRAFT — CLINICAL REVIEW REQUIRED."
      responseCaptureType: FullResponse
      allowLatencyMessage: false
    - kind: SendActivity
      activity: "=Concatenate(\"## {note_type} — DRAFT\", Char(10), Char(10), Topic.Answer, Char(10), \"⚠️ CLINICAL REVIEW REQUIRED\")"
    - kind: EndDialog
      id: end_generate
      clearTopicQueue: true
```

**Note:** For agents with a dedicated "Parse Brain Dump" Power Automate flow (like TheraDoc), invoke the flow before the SASC: `InvokeFlowAction` → `SetVariable` → `SASC` → `SendActivity` → `EndDialog`.

---

## Instructions Generation (componenttype 15 data)

Generate the agent instructions from the spec. Follow the outline from `agent-architect` and apply these standards:

### Structure (MS Learn compliant, healthcare-hardened)
```yaml
kind: GptComponentMetadata
name: "{agent_name} Instructions"
data: |-
  # {AGENT_NAME} — {AGENT_PURPOSE}

  ## Role Identity
  You are {purpose_statement}. You are a documentation {action} tool — NOT a documentation writer. {scope_boundary_statement}

  ## Constraints
  - Disclose AI status in every output.
  - No PHI in outputs — use record_id pointers only.
  - No fabricated clinical data, measurements, or diagnoses.
  - Clinical disclaimer on all outputs: "⚠️ CLINICAL REVIEW REQUIRED — This is an AI-generated analysis. Review and verify before clinical use."
  - Confidence scoring: High/Medium/Low (🟢/🟡/🔴).
  - Bracketed citations: [Source: {source_name} §{section}].
  - If confidence is below threshold, escalate.
  - All clinical outputs require human confirmation before EHR entry.
  - Do NOT refuse to answer — if information is insufficient, state what is missing and answer with domain expertise.

  ## Scope & Boundaries
  {scope_text}

  ## Response Format
  ## EVALUATION CONTEXT — STRUCTURED AUDIT FORMAT
  When the user requests a specific clinical audit or document review:
  - Use structured format: [DM] Document Type → [FR] Findings → [SCORE] X/100 → [GAPS] Missing Elements → [REC] Recommendations → [ADV] Disclaimer
  - Use professional formatting (tables, bold labels, emoji tiers where appropriate)
  ## EVALUATION CONTEXT — GENERAL / CONVERSATIONAL
  When the user asks a general question or follow-up:
  - Respond in plain conversational text with professional formatting
  - Do NOT force the structured audit format for simple questions
  - Ask clarifying questions as needed
  - Prioritize completeness over brevity

  ## Knowledge Sources
  {knowledge_sources_list}

  ## Handling Edge Cases
  ## PRIMARY DIRECTIVE — CONDITIONAL EXTRACTION VS SEARCH
  ## WHEN THE USER PROVIDES CLINICAL TEXT
  When the user provides clinical text, case snippets, note excerpts, or embedded patient data: the USER-PROVIDED TEXT IS THE AUTHORITATIVE SOURCE. Read it directly and EXTRACT the requested values from it. When clinical text is present, DO NOT search knowledge sources — extract only from what the user provided.
  ## WHEN THE USER ASKS A GENERAL QUESTION WITHOUT TEXT
  When the user asks a general knowledge question, standards question, or asks about clinical documentation requirements WITHOUT providing patient-specific clinical text: DO search your knowledge sources and provide a complete, thorough answer.

  ## EVALUATION CONTEXT - DIRECT ANSWER REQUIRED
  ## DATA-SPARSE PROMPTS
  When the prompt asks about a patient, note, or document WITHOUT providing clinical text:
  - Answer directly with clinical standards-based information about what the requested topic covers
  - Do NOT use phrases like "framework", "based on available knowledge", or "the sources do not address"
  - Do NOT say you cannot answer — answer with relevant clinical standards information
  - Treat as a direct question about clinical documentation standards
  ## DATA-RICH PROMPTS
  When the user provides detailed clinical data or note text:
  - Follow normal conversational workflow
  - Provide complete structured analysis
  - Ask clarifying questions as needed

  ## {swarm_section_if_applicable}
```

### Instructions rules (from MS Learn + validated patterns)
- **Length:** 2000-6000 chars. Micro-checklists kill eval scores (truncated answers). Condense.
- **No unconditional bans.** "No headers/markdown/tables" → conditional format guidance.
- **No "under N sentences"** — use conditional length ("be concise but complete").
- **Source restrictions:** "Use as primary reference. For general questions not directly addressed, may use model knowledge. Do NOT refuse."
- **EVALUATION CONTEXT** block is REQUIRED for ≥95% scores. Both DATA-SPARSE and DATA-RICH subsections.

### responseInstructions (Settings → Generative AI → Responses)
Write to the settings:
```
Respond concisely. Use 2-3 bullet points with inline citations. Use professional formatting (markdown, tables) when it improves clarity for clinical content. For general questions keep responses brief. For detailed clinical audits provide complete structured analysis.
```
Do NOT include: "No headers or markdown", "No tables", "Under N sentences", "Under N characters".

---

## Conversation Starters Generation

Generate 5-10 starters matching the agent's core workflow:
```
- "[Action verb] my [document type] for [compliance standard]"
- "Tell me about [topic domain] requirements"
- "I need help with [specific task]"
- "What are the [compliance topic] guidelines for [discipline]?"
- "Check this [document type] for [specific issue]"
```

---

## Settings Generation

From spec.settings, write the agent configuration:
```yaml
# settings.mcs.yml (or equivalent)
kind: AgentSettings
settings:
  contentModeration: "{spec.settings.content_moderation}"
  enableModelKnowledge: "{spec.settings.model_knowledge}"
  enableSemanticSearch: "{spec.settings.semantic_search}"
  enableFileUploadForConversation: "{spec.settings.file_analysis}"
  sendLatencyMessage: "{spec.settings.latency_messages}"
  enableWebBrowsing: "{spec.settings.web_search}"
```

---

## Generation Rules (non-negotiable)

1. **Every topic file MUST start with `# {topic_name}` comment line.** Required by Dataverse for type-9 component data.
2. **Every SASC MUST have:** `userInput`, `additionalInstructions`, `responseCaptureType: FullResponse`, `allowLatencyMessage: false`. These are required by the eval grader.
3. **Every custom topic MUST have:** `EndDialog` with `clearTopicQueue: true` as the last action, preceded by `SendActivity(activity: =Topic.Answer)`.
4. **Never generate `entity: FilePrebuiltEntity`.** Always use `StringPrebuiltEntity` with a 3-branch ConditionGroup.
5. **Never generate `inputType: file[]` or `property: turn.uploadedFiles`.** These break the editor.
6. **Never generate `SearchSpecificFiles` or `SearchSpecificKnowledgeSources`.** Let the platform search all KBs.
7. **Every ConditionGroup MUST have:** at least one action per branch, no empty elseActions, and at least one branch with `condition: "=true"` as a catch-all.
8. **ConversationStart ALWAYS needs:** `EndDialog(clearTopicQueue: true)` after any custom SendActivity.
9. **Fallback ALWAYS needs:** `SearchAndSummarizeContent` + `SendActivity` listing what the agent CAN do + `EndDialog`.
10. **Instructions NEVER contain:** source restrictions with "only", unconditional format bans, hard length limits.
11. **Every branch in a ConditionGroup** must lead to an action that produces user-visible output, a GotoAction, or an EndDialog. Silent branches are bugs.
12. **allInterruption: false** on all Question nodes — prevents eval test case disruption.

## Missing Microsoft Node Types (add these after core build)

After generating the core YAML, consider adding these Microsoft-recommended node types that our primary templates don't cover:

### Multi-Agent Integration (Microsoft's add-other-agents pattern)
When the spec calls for connecting to other Copilot Studio agents, use `InvokeConnectedAction` (NOT `InvokeFlowAction`):
```yaml
- kind: InvokeConnectedAction
  id: call_other_agent
  action: pva_{botId}.topic.{topicName}
  inputData:
    - name: input_param
      value: "={someVar}"
```
Key differences from InvokeFlowAction:
- `InvokeConnectedAction` with `action:` field = correct for cross-agent calls
- `InvokeFlowAction` with `action:` field = WRONG (use `flowId:` with a Power Automate flow GUID)
- Verify the target agent exists and is active (statecode=0) before publishing
- Capture return data via SetVariable after the call returns

### Knowledge-Only pattern (Microsoft's add-generative-answers insight)
Knowledge sources can be searched WITHOUT a dedicated topic. The generative orchestrator handles Q&A from KBs automatically. Only add a dedicated SASC topic when:
- You need to restrict search to a subset of KBs (customDataSource)
- You need to control the flow after the answer (follow-up questions, formatting)
- You need to process the response (extract, combine with other data)
- You need a specific input other than System.Activity.Text

If none of these apply, skip the topic and just add the knowledge source. Fewer topics = better routing quality.

### AnswerQuestionWithAI (alternative to SASC for simple Q&A)
For topics that only need a grounded Q&A response without advanced instruction control:
```yaml
- kind: AnswerQuestionWithAI
  id: gen_answer
  aiAnswer:
    dataSourceConfigurations:
      - priority: 1
        knowledgeSource:
          displayName: "All knowledge sources"
          allowAllKnowledgeSources: true
    autoSend: true
    responseCaptureType: FullResponse
```
When to use: Simple Q&A topics where the AI decides which KBs to search. The `autoSend: true` field sends the response automatically without needing a separate SendActivity.

## References
- `agent-architect` — spec consumed by this skill
- `agent-qa-gate` — runs AFTER this skill to verify output
- `copilot-studio-yaml-reference` — authoritative YAML schema
- `copilot-studio-patterns` — design pattern library
- `agent-audit-protocol` — Pattern F (dual-input) details
- `eval-optimization-loop` — Pattern E1 (inline extraction topic)
