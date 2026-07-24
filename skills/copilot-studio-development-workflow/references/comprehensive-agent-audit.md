# Comprehensive Agent Audit Checklist

A pre-deployment or pre-publish audit that checks every layer of a Copilot Studio agent against all available skill standards. Run this before publishing to catch the full set of issues.

## How to Use

1. Load all relevant skills (see References below).
2. For each section, check the agent's topics, settings, and instructions against the listed criteria.
3. Compile findings into a priority-ordered action list (P0, P1, P2).
4. Execute fixes starting from P0.

## References (Skills to Load)

- `copilot-studio-yaml-reference` — YAML pitfalls, Power Fx rules, SearchAndSummarizeContent output
- `copilot-studio-topic-assessment` — Topic necessity, shell topics, eval regression
- `clinical-swarm-guardrails` — Healthcare AI settings (contentModeration, useModelKnowledge, etc.)
- `copilot-studio-edit-agent` — Agent instructions, EVALUATION CONTEXT block, Button-First UX anti-pattern
- `copilot-studio-patterns` — 15 proven patterns (RAI handling, auto-poll, tool call leaks, etc.)
- `copilot-studio-validate` — Schema and LSP validation workflow
- `evaluation-driven-agent-optimization` — Eval score optimization loop
- `copilot-studio-development-workflow` — This umbrella (CDP workflow, publish diagnostics)

## Audit Sections

### Section 1 — Agent Instructions (`instructions-component.yml` / `agent.mcs.yml`)

| Check | Standard |
|-------|----------|
| EVALUATION CONTEXT block present (not old no-caveat style) | copilot-studio-edit-agent |
| No "Button-First UX" anti-pattern (reject-free-text) | copilot-studio-edit-agent |
| No template boilerplate comments (e.g., "HARDENING VERIFIED") | copilot-studio-edit-agent |
| Instructions cover: ROLE, CORE REVIEW STANDARD, APPROVED KNOWLEDGE SOURCES, KNOWLEDGE HIERARCHY, GUARDRAILS, ROUTING LOGIC, CITATION RULES, OUTPUT FORMAT | clinical-swarm-guardrails |
| conversationStarters exist and link to distinct topics | MS Learn |
| modelNameHint matches agent's deployment model | copilot-studio-edit-agent |

### Section 2 — Agent Settings (live UI or `settings.mcs.yml`)

| Setting | Required Value | Source |
|---------|---------------|--------|
| contentModeration | High | clinical-swarm-guardrails |
| useModelKnowledge | false | clinical-swarm-guardrails |
| optInUseLatestModels | false | clinical-swarm-guardrails |
| webBrowsing | false | clinical-swarm-guardrails |
| codeInterpreter | false | clinical-swarm-guardrails |
| authenticationTrigger | Always | clinical-swarm-guardrails |
| accessControlPolicy | GroupMembership | clinical-swarm-guardrails |
| isAgentConnectable | true (if hub-and-spoke) | clinical-swarm-guardrails |

### Section 3 — Per-Topic Checklist

For each topic file (`*.yml`):

**Structure:**
- [ ] Has exactly one trigger (OnRecognizedIntent, etc.)
- [ ] Has `modelDescription` on the trigger (generative) or `triggerQueries` (classic)
- [ ] If `triggerQueries` present: no duplicate phrases across topics
- [ ] `clearTopicQueue: true` on all `EndDialog` nodes

**SearchAndSummarizeContent / AnswerQuestionWithAI nodes:**
- [ ] `knowledgeSources:` block present (not empty)
- [ ] `responseCaptureType: FullResponse` set
- [ ] `additionalInstructions` present (not blank)
- [ ] All `SendActivity` references to this node's variable use `.Text.Content`
- [ ] Blank/null guard before `.Text.Content` output (prevent silent blank message)

**Power Fx / Conditions:**
- [ ] All `condition:` values use quoted strings (not `|-` block scalars)
- [ ] `in` operator always wraps topic variable in `Text()`: `"X" in Text(Topic.var)`
- [ ] All `activity:` / `value:` / `condition:` using multi-line Power Fx with colons use `|-` block scalars
- [ ] No duplicate YAML properties (detect with `sort | uniq -d`)

**Knowledge:**
- [ ] Topic-level `modelDescription` and SearchAndSummarizeContent `modelDescription` are aligned
- [ ] If topic accepts file uploads: FilePrebuiltEntity used correctly
- [ ] If topic produces an audit report: no raw record output

### Section 4 — Patterns Check

| Pattern | Check |
|---------|-------|
| RAI Error Handling | On_Error has category-specific subcode handling? |
| Prevent Tool Call Leaks | All SearchAndSummarizeContent outputs use `.Text.Content`? |
| Auto-Poll Async Status | If topic submits an async job, does it auto-poll (vs. manual "check status" command)? |
| Knowledge Hold Message | Is there a "processing..." message during knowledge search latency? |
| Chain of Thought Logging | Are there "Thinking..." messages during multi-step flows? |
| Conversation History | Is conversation captured for escalation/traceability? |
| Line Breaks | Uses `<br /><br />` not `\n` for paragraph spacing? |
| Action Execution Order | Guardrail SendActivity precedes SearchAndSummarizeContent? |

### Section 5 — System Topics

| Topic | Check |
|-------|-------|
| Fallback | Has `additionalInstructions` that don't conflict with agent guidelines; no `in` operator pitfalls |
| On_Error | Has RAI content-filter subcode handling; logs errors gracefully |
| Multiple_Topics_Matched | Standard disambiguation, no custom edits breaking it |
| Escalate | Has correct routing/handoff info |
| Conversation_Start / Greeting | Welcome message sent, no conversation blockers |

### Section 6 — YAML Validation

- [ ] Schema validation: `schema-lookup.bundle.js validate <path>` (fast, local)
- [ ] LSP validation: `manage-agent.bundle.js validate --workspace <path>` (comprehensive, needs .mcs/conn.json)
- [ ] Quick parse: `js-yaml` or `PyYAML` check on all topic files
- [ ] Content cleanliness: mojibake scan (emoji double-encoding, C1 control chars)
- [ ] Publish diagnostic query if publish fails: `synchronizationstatus.lastFinishedPublishOperation.diagnosticDetails`

### Section 7 — Pre-Commit / CI Gates

- [ ] Pre-commit hook installed (global via `core.hooksPath` or per-repo)
- [ ] Hook checks: `knowledgeSources:` presence, `.Text.Content` on all SearchAndSummarizeContent outputs
- [ ] YAML parse gate before publish

## Priority Rules

| Priority | Criteria | Example |
|----------|----------|---------|
| P0 | Runtime failure or user-facing data leak | Missing `.Text.Content` (leaks AI metadata); `in` operator without `Text()` (silent failure); missing `knowledgeSources:` (ungrounded answers) |
| P1 | Eval failure or UX degradation | Duplicate triggers (random routing); Button-First UX (rejects text input); Dead retry loops |
| P2 | Best-practice gap, no immediate failing | Missing Chain of Thought logging; No RAI error handling; Long `modelDescription` |
| P3 | Cosmetic / maintainability | Aligned modelDescription length; Template comment cleanup |
