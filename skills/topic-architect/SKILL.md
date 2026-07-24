---
name: topic-architect
description: "Design complete minimal topic sets for any Copilot Studio agent. Takes agent function, domains, and knowledge sources as input. Outputs YAML topic files optimized for 95%+ SR and Conv eval scores."
category: copilot-studio
---

# Topic Architect

**Purpose:** Given an agent's purpose, domains, and knowledge sources, produce a minimal-complete topic set that achieves 95%+ on both SR and Conversation evaluations.

**Authoritative sources:** Microsoft Learn — [Defining agent topics](https://learn.microsoft.com/microsoft-copilot-studio/guidance/defining-chatbot-topics), [Topic authoring best practices](https://learn.microsoft.com/microsoft-copilot-studio/guidance/topic-authoring-best-practices), [Trigger phrase design](https://learn.microsoft.com/microsoft-copilot-studio/guidance/trigger-phrases-best-practices), plus empirical data from 4 therapy audit agents scoring 97-99%.

---

## Phase 1: Agent Analysis

Collect these inputs before designing topics:

| Input | Example |
|-------|---------|
| **Agent purpose** | "Audit SLP documentation for Medicare compliance" |
| **Domains/subdomains** | dysphagia, aphasia, voice, cognitive-communication, AAC |
| **Knowledge sources** | CMS Chapter 15, ASHA guidelines, Jimmo FAQ, IDDSI framework |
| **Document types** | evaluation, daily note, progress note, recertification, discharge |
| **Model** | GPT5Chat or Sonnet46 |
| **Target eval type** | Single Response (SR), Conversation (Conv), or both |

---

## Phase 2: Topic Set Architecture

### The Golden Rule: Minimal topics, maximal knowledge

The agent's instructions handle format and behavior. Topics handle triggering and knowledge routing. **Do not create a topic for every document type.** One catch-all topic with knowledge sources covers 90% of queries.

### Required topics (every agent):

```
1. Conversational boosting (catch-all) — OnUnknownIntent
   - SearchAndSummarizeContent with knowledgeSources + additionalInstructions
   - No Question nodes. userInput: =System.Activity.Text
   - EndDialog with clearTopicQueue: true

2. Greeting (optional, deactivate if it has Question nodes)
   - Simple SendActivity greeting + EndDialog
   - Trigger phrases: "hello", "hi", "what can you do"
```

### Domain-specific topics (add ONLY if needed):

Only add a topic when:
- It needs specific `knowledgeSources` different from the catch-all
- It needs specific `additionalInstructions` beyond what's in agent instructions
- It has unique trigger phrases not covered by the catch-all

Maximum: 3-5 custom topics. Each uses the template below.

### Standard topic template (eval-optimized):

```yaml
kind: AdaptiveDialog
modelDescription: <one-line purpose>
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: <TopicName>
    triggerQueries:
      - <phrase 1>
      - <phrase 2>
      - <phrase 3>
  actions:
    - kind: SearchAndSummarizeContent
      id: search
      userInput: =System.Activity.Text
      additionalInstructions: |-
        <Specific instructions for this domain>
      knowledgeSources:
        - schemaname: <exact schemaname from Dataverse>
      applyModelKnowledgeSetting: true
    - kind: EndDialog
      id: done
      clearTopicQueue: true
```

---

## Phase 3: Anti-Patterns (DO NOT CREATE)

Based on Microsoft Learn + empirical eval data:

| Pattern | Why it fails | Source |
|---------|-------------|--------|
| `kind: Question` nodes | Returns interactive content, not text — breaks SR eval | AGENTS.md #4 |
| Shell topics (`intent: {}`) | No trigger phrases — never fires | AGENTS.md |
| `SearchAndSummarizeContent` without `knowledgeSources` | KB not engaged — scores 0-4% | AGENTS.md #1 |
| `SearchAndSummarizeContent` without `additionalInstructions` | Generic answers fail Groundedness | AGENTS.md #6 |
| Topics without `EndDialog` | Conversation bleed across test cases | AGENTS.md |
| Duplicate trigger phrases | Causes "Multiple Topics Matched" — eval noise | Microsoft Learn |
| Topic per document type | Bloat. Instructions + catch-all handles this | Empirical 97-99% data |
| `Conversation Start` with Question nodes | Blocks every SR test case with "What can I help with?" | AGENTS.md #3 |

---

## Phase 4: Trigger Phrase Design

Per Microsoft Learn [trigger phrase best practices](https://learn.microsoft.com/microsoft-copilot-studio/guidance/trigger-phrases-best-practices):

1. **3-10 phrases per topic** — enough for NLU to match, not so many they overlap
2. **Include variations** — question form ("what is X"), command form ("audit X"), keyword form ("X compliance")
3. **Avoid overlap** — no shared key terms between topics unless intentional disambiguation
4. **More specific first** — specific topics should have narrower triggers that match before broad catch-all

Example for a dysphagia topic:
```yaml
triggerQueries:
  - audit my dysphagia assessment
  - check swallowing documentation
  - is my dysphagia note compliant
  - review aspiration risk documentation
  - dysphagia diet consistency audit
```

---

## Phase 5: Topic YAML Generation

Generate topics as individual `.yml` files. Use `copilot-studio-author-topic` skill for the YAML template. Validate with `schema-lookup.bundle.js validate <file>`.

### Checklist before delivery:

- [ ] Catch-all topic has `knowledgeSources` with exact schemanames
- [ ] Catch-all has `additionalInstructions` with citation requirements
- [ ] No Question nodes in any topic
- [ ] Every leaf topic has `EndDialog` with `clearTopicQueue: true`
- [ ] `userInput: =System.Activity.Text` on all SearchAndSummarizeContent
- [ ] Trigger phrases are unique across all topics
- [ ] `applyModelKnowledgeSetting: true` on all SearchAndSummarizeContent
- [ ] Deactivate Conversation Start if it has Question nodes (`statecode: 1`)
- [ ] Total custom topics ≤ 5 (excluding system topics)

---

## Phase 6: Instruction Design (paired output)

Topics alone won't score 95%+. Instructions must include:

1. **RESPONSE FORMAT** — 6 numbered sections with emoji-driven risk tiers
2. **NO-CAVEAT STANDARDS CHECK** — never ask for documents, audit directly
3. **RESPONSE BEHAVIOR** — "never defer, never ask, just audit"
4. **SCORING STRICTNESS** — domain-specific auto-deductions
5. **SAFETY** — Non-Device CDS, no PHI, clinical review required
6. **modelNameHint** — Sonnet46 or GPT5Chat (both proven at 97%+)

---

## Reference: Proven Topic Set (Therapy Audit Agents)

All four agents (OT, PT, SLP, TDA) score 97-99% with this architecture:

- **~5000 topics total per agent** (mostly system-generated — only 2-5 are custom)
- **Conversational boosting** (OnUnknownIntent) handles all unmatched queries
- **0-2 domain-specific topics** with SearchAndSummarizeContent
- **Conversation Start DEACTIVATED**
- **Instructions** carry the response format and behavior rules
- **Knowledge sources** are explicit in every topic's SearchAndSummarizeContent

## Key Scripts

| Script | Purpose |
|--------|---------|
| `dump_agent_full.cjs <botId>` | Inspect current topics and instructions |
| `schema-lookup.bundle.js validate <file>` | Validate topic YAML before push |
| `manage-agent.bundle.js push` | Push validated topics to agent |
| `copilot-studio-run-eval` skill | Test DRAFT agent before publishing |

## Pitfalls

- `knowledgeSources` schemanames must match EXACTLY what's in Dataverse — verify with `componenttype in (14,16)` query
- `data` field patchable via API, `content` is NOT (400 error) — use manage-agent.bundle.js for content
- Regex-based YAML removal destroys adjacent blocks — use line-by-line iteration instead (AGENTS.md #2)
- PAC publish may report "Failed" but actually succeed — check timestamp in Copilot Studio UI (AGENTS.md #9)
- **Missing no-caveat = eval failure:** Agents without a NO-CAVEAT STANDARDS CHECK block stall on SR eval ("please provide the note"). This single block can raise scores from 69% to 97%. See `copilot-studio-pipeline` references/no-caveat-and-merge-patterns.md.
- **Question nodes kill SR eval:** Interactive prompts (Question, AdaptiveCardPrompt) return non-text responses. Graders score these as Abstention. Use `SearchAndSummarizeContent` + `userInput: =System.Activity.Text` + `EndDialog` instead.
- **Contradictory instructions confuse models:** If instructions say both "never audit yourself" and "always provide audit," the model picks randomly. Merge non-contradictory pieces, preserve the stronger directive.
