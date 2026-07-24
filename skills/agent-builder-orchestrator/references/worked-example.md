# Worked Example: Building a PT Compliance Auditor

This example walks through the full orchestrator pipeline for a concrete agent.
Use as a template — replace the specifics for your agent.

## User Prompt
"Build an agent that audits PT daily notes for Medicare compliance and flags
documentation gaps."

## Phase 0 — Architect Interview

**Q1: Core Purpose**
User: "Audit PT daily notes for Medicare compliance and flag documentation gaps."
→ purpose: "Audits PT daily notes for Medicare compliance and flags gaps"
→ action_verb: audit, discipline: pt, workflow_type: audit

**Q2: Input Method**
User: "Users paste text or upload PDFs of their PT daily notes."
→ input_pattern: file_text_dual, needs_upload: true

**Q3: Scope & Scale**
User: "Just PT daily notes. Maybe general Medicare compliance Q&A too."
→ 2 topics:
  - "PT Daily Note Audit" — audit pattern
  - "Medicare Compliance Q&A" — text-only Q&A

**Q4: Orchestration**
User: "Standalone. Just this agent."
→ mode: standalone, connected_agents: []

**Q5: Knowledge Sources**
User: "CMS Chapter 15, 42 CFR Part 409, the MSCA Audit Worksheet."
→ 3 KBs: CMS Ch.15 (sharepoint), 42 CFR 409 (sharepoint), MSCA worksheet (upload)

**Q6: Settings**
User: "Yes, clinical/healthcare."
→ is_healthcare: true, moderation: Medium, latency: OFF

**Q7: Model**
User: "Whatever you recommend."
→ recommended_model: GPT-5 Chat

**Q8: Exit Criteria**
User: "95% is fine."
→ sr_target: 95, conv_target: 95

## Phase 0 Output (_agent_spec.yaml)

```yaml
agent:
  name: PT Compliance Auditor
  purpose: Audit PT daily notes for Medicare compliance and flag documentation gaps
  action_verb: audit
  discipline: pt
  workflow_type: audit
  mode: standalone
  is_healthcare: true
  recommended_model: GPT-5 Chat
topics:
  - name: PT Daily Note Audit
    pattern: file_text_dual
    trigger_phrases:
      - "Audit this PT daily note"
      - "Check my PT note for compliance"
      - "Review this PT documentation"
      - "Are there gaps in my PT note?"
      - "Does this PT note meet Medicare requirements?"
      - "Flag issues in this PT daily note"
  - name: Medicare Compliance Q&A
    pattern: text_only
    trigger_phrases:
      - "What are Medicare requirements for PT notes"
      - "Tell me about PT documentation standards"
      - "What needs to be in a PT daily note"
      - "Medicare compliance rules for PT"
      - "PT documentation requirements"
knowledge_sources:
  - name: CMS Medicare Benefit Policy Manual Ch.15
    description: Covers coverage of outpatient therapy services, plan of care, certification requirements
    type: sharepoint
    official: true
  - name: 42 CFR Part 409
    description: Medicare regulations for therapy services including supervision, documentation, medical necessity
    type: sharepoint
    official: true
  - name: MSCA Audit Worksheet
    description: Therapy documentation audit framework used by Medicare contractors
    type: upload
    official: true
settings:
  content_moderation: Medium
  model_knowledge: true
  semantic_search: true
  latency_messages: false
  web_search: false
```

## Phase 1 — Crafter Output

Generated files:
- `agent.mcs.yml` — instructions + settings + conversation starters
- `topics/pt_daily_note_audit.mcs.yml` — Template A (dual-input audit)
- `topics/medicare_compliance_qa.mcs.yml` — Template B (text-only Q&A)

Instructions text (6000 chars):
```
# PT COMPLIANCE AUDITOR — Audits PT daily notes for Medicare compliance

## Role Identity
You audit PT daily notes for Medicare compliance. You are a documentation
AUDIT tool — NOT a documentation writer or generator.

## Constraints
...
## EVALUATION CONTEXT - DIRECT ANSWER REQUIRED
## DATA-SPARSE PROMPTS
...
```

## Phase 2 — QA Gate

Result: PASS (12/12)
- G1 spec alignment: All 2 topics present, patterns match
- G2 structural: Valid YAML, no file[], no BOM
- G3 termination: Both have EndDialog+clearTopicQueue
- G4 SASC: Both have responseCaptureType, allowLatencyMessage:false
- G5 Question: StringPrebuiltEntity, 3-branch ConditionGroup
- G6 Triggers: 6+ per topic, no duplicates
- G7 modelDescription: Both present, unique
- G8 Connected agents: N/A (standalone)
- G9 Instructions: 4500 chars, EVAL CONTEXT present
- G10 Settings: Medium moderation, latency OFF, web OFF
- G11 KBs: Named, described, official toggled
- G12 Editor render: CONFIRMED (canvas shows both topics)

## Phase 3 — Deploy

`pac copilot publish` → Succeeded
synchronizationstatus → lastFinishedPublishOperation.status: "Succeeded"

## Phase 4 — Live UI Verify

flow-editor-container: child nodes visible ✓
Test message: "Audit this PT note" → structured audit response ✓

## Phase 5 — Eval

Conv: 80% → fix (Fallback scope too narrow) → 95%
SR: 88% → fix (add EVALUATION CONTEXT to instructions) → 97%
Both ≥ target after 2 iteration cycles.

## Phase 6 — Report

```
=== Agent Builder Report: PT Compliance Auditor ===
Spec: Audit PT daily notes for Medicare compliance and flag gaps
Topics created: 2
  - PT Daily Note Audit — file_text_dual
  - Medicare Compliance Q&A — text_only
QA Gate: PASS (12/12)
Deploy: 2026-07-16T12:00:00Z
Publish: Succeeded 2026-07-16T12:05:00Z
Editor render: CONFIRMED
Eval: SR = 97%  Conv = 95%  (target ≥ 95%)
Status: READY
Remaining P1: 0 (non-blocking)
```
