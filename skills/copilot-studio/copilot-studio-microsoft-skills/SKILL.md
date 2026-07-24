---
name: copilot-studio-microsoft-skills
description: "References to Microsoft's official Copilot Studio GitHub repos cloned locally. Contains YAML schemas, design patterns, evaluation tools, and agent templates from microsoft/skills-for-copilot-studio, microsoft/cat-agent-skills, and microsoft/agent-academy."
version: 1.0.0
---

# Microsoft Copilot Studio GitHub Resources (Local Clones)

## Cloned Repos (C:\Users\kevin\)

| Repo | Path | Contents | Stars |
|------|------|----------|-------|
| skills-for-copilot-studio | `C:\Users\kevin\skills-for-copilot-studio\` | 20 skills, 15 patterns, YAML schema | Microsoft official |
| cat-agent-skills | `C:\Users\kevin\cat-agent-skills\` | Copilot Studio community gallery | Microsoft official |
| agent-academy | `C:\Users\kevin\agent-academy\` | 3-part training (prompts, cards, flows) | Microsoft official |
| awesome-copilot-studio-agents | `C:\Users\kevin\awesome-copilot-studio-agents\` | 89 paste-ready M365 agent instructions | ★ 425 |
| awesome-copilot | `C:\Users\kevin\awesome-copilot\` | Community agents, instructions, hooks | GitHub community |
| awesome-harness-engineering | `C:\Users\kevin\awesome-harness-engineering\` | AI agent scaffolding meta-patterns | Community |
| mcscatblog | `C:\Users\kevin\mcscatblog\` | Microsoft CAT blog + resource pages | Microsoft CAT |
| powerplatform-mcp | `C:\Users\kevin\powerplatform-mcp\` | MCP server for Dataverse/PowerPlatform | Public |

## Key Files

### YAML Schema (validate any topic)
`C:\Users\kevin\skills-for-copilot-studio\reference\bot.schema.yaml-authoring.json`

### Design Patterns (skills-for-copilot-studio/patterns/)
- `chain-of-thought-logging.md` — RAI logging for multi-step reasoning
- `dynamic-topic-redirect.md` — Redirect between topics at runtime
- `conversation-history-variable.md` — Maintain multi-turn state
- `orchestrator-variables.md` — Variables across child agents
- `knowledge-hold-message.md` — Latency handling for knowledge calls
- `teams-production-hardening.md` — Production readiness for Teams
- `rai-error-handling.md` — Responsible AI error handling

## CAT Agent Gallery (C:\Users\kevin\cat-agent-skills\)

Community agent gallery with 17 submissions: campaign-deck-builder, customer-sentiment-triage, expense-report-filler, incident-triage-assistant, knowledge-source-router, legal-toolkit, meeting-summarizer, onboarding-buddy, pdf-form-extractor, redlining-content, release-notes-writer, sql-query-helper, translation-helper, web-research-assistant. Each has a full agent definition with instructions, trigger phrases, and topic structure. Located at `C:\Users\kevin\cat-agent-skills\submissions\`.

## Design Patterns (skills-for-copilot-studio/patterns/)
Complete inventory (15 patterns):

### Kiro Resources (D:\my agents copilot studio\.kiro\)

Local Kiro workspace with complementary Copilot Studio tools — hooks, skills, specs, and steering docs. These are user-authored (not Microsoft official) but contain proven patterns for the therapy agent fleet.

### Structure
```
D:\my agents copilot studio\.kiro\
  ├── hooks/          # 19 pipeline hooks (JSON — trigger on tool use / file events)
  │   ├── pre-publish-check.kiro.hook          # Validates before publish (duplicates, null content, flows)
  │   ├── orphan-flow-detector.kiro.hook       # Catches stale flow references (#1 publish blocker)
  │   ├── post-publish-verify.kiro.hook        # Queries sync status after publish (don't trust CLI)
  │   ├── text-corruption-detector.kiro.hook   # CRLF, duplicated sections, mid-word splices
  │   ├── topic-structure-check.kiro.hook      # Validates topic count, triggers, architecture
  │   ├── topic-yaml-lint.kiro.hook            # YAML structure validation
  │   ├── phi-audit-check.kiro.hook            # PHI/PII detection before PATCH
  │   ├── eval-result-triage.kiro.hook         # Eval failure routing
  │   ├── solution-pack-check.kiro.hook        # Surgical solution validation
  │   ├── fleet-health-check.kiro.hook         # Cross-agent health monitoring
  │   └── 9 more (work-iq-kill, verify-routing, etc.)
  ├── skills/         # 13 skill files (markdown — process descriptions)
  │   ├── agent-rebuild-and-populate.md        # Full rebuild: context→design→build→populate
  │   ├── clinical-swarm-deployment.md         # Multi-agent deployment patterns
  │   ├── copilot-agent-auditor.md             # Agent auditing workflow
  │   ├── copilot-fix-with-subagents.md        # Subagent-based fix workflow
  │   ├── copilot-studio-topic-injection.md    # Topic injection via API
  │   ├── copilot-testdebug-deep-audit.md      # Deep debugging workflow
  │   ├── dataverse-bot-management.md          # Bot management via Dataverse API
  │   ├── eval-failure-analyzer.md             # Eval failure analysis (before vs after)
  │   ├── surgical-solution-packaging.md       # Minimal solution zips for cross-env deploy
  │   └── 4 more (powerautomate-scripts, config-consolidation, etc.)
  ├── specs/          # 19 agent-specific configuration specs
  │   ├── copilot-agent-factory/               # Generic agent builder spec
  │   ├── fleet-agent-audit/                   # Fleet-wide audit config
  │   ├── therapy-doc-audit-agent-optimization/ # TheraDoc optimization spec
  │   └── 16 more agent specs
  └── steering/       # Steering/routing documents
```

### Key Differences from Microsoft Official
| Aspect | Microsoft skills-for-copilot-studio | Kiro .kiro |
|--------|-------------------------------------|------------|
| Format | Claude Code / GitHub Copilot CLI plugins | JSON hooks + markdown skills |
| Scope | Generic Copilot Studio patterns | Therapy agent fleet (Ensign-specific) |
| Pre-publish | Schema validation only | Flow validation, orphan detection, corruption check |
| Post-publish | None | Sync status verification |
| Auth | VS Code extension LSP binary | pac + az + MSAL |
| Deployment | manage-agent CLI clone/push/pull | Surgical solution packaging |
| Eval analysis | CSV analysis (analyze-evals) | Failure classification (setup vs agent) |

### Integration with Hermes Pipeline
The Kiro hooks have been integrated into `agent-qa-gate` as G15-G18. The eval failure analysis is in `eval-optimization-loop`. The surgical solution packaging and manage-agent CLI are in `agent-builder-orchestrator`.

## Copilot Studio Skills (skills-for-copilot-studio/skills/)
Complete inventory (34 skills as of v1.0.11):
- `add-action/` — Add connector actions
- `add-adaptive-card/` — AdaptiveCardPrompt nodes
- `add-generative-answers/` — SearchAndSummarizeContent nodes
- `add-global-variable/` — Bot-level persistent variables
- `add-knowledge/` — Knowledge source configuration
- `add-node/` — Generic node insertion
- `add-other-agents/` — Multi-agent (InvokeConnectedAction)
- `analyze-evals/` — CSV eval analysis
- `chat-directline/` — DirectLine v3 chat testing
- `chat-sdk/` — M365 SDK chat testing
- `chat-with-agent/` — Bundled LSP chat testing
- `clone-agent/` — Clone agents between environments
- `create-eval/` — Single eval creation
- `create-eval-set/` — CSV test set creation
- `detect-mode/` — Detect agent auth mode
- `directline-chat/` — DirectLine chat (standalone)
- `edit-action/` — Edit existing actions
- `edit-agent/` — Agent metadata editing
- `edit-triggers/` — Trigger phrase management
- `int-patterns/` — Internal pattern library (Advisor agent)
- `int-project-context/` — Project context scanner
- `int-reference/` — Internal YAML reference (Author agent)
- `list-kinds/` — List all kind discriminators
- `list-topics/` — List agent topics
- `lookup-schema/` — Schema lookup LSP query
- `manage-agent/` — Clone/push/pull/validate via LSP binary
- `new-topic/` — Create new topic YAML
- `run-eval/` — Start and poll evaluations
- `run-tests-kit/` — Run test suite
- `test-auth/` — Test authentication
- `validate/` — Schema/LSP validation

## Kiro Resources (D:\my agents copilot studio\.kiro\)

### 89 M365 Agent Templates (awesome-copilot-studio-agents/)
All at `C:\Users\kevin\awesome-copilot-studio-agents\agents\`:
| Category | Agents | Path |
|----------|--------|------|
| Writing & Communication | 7 | `writing-communication/` |
| Project Management | 12 | `project-management/` |
| HR & People | 3 | `hr-people/` |
| Finance | 5 | `finance/` |
| Sales & Business Dev | 5 | `sales/` |
| Commercial & Legal | 4 | `commercial-legal/` |
| Data Analytics | 4 | `data-analytics/` |
| IT & Operations | 6 | `it-ops/` |
| Learning & Dev | 4 | `learning-development/` |
| Productivity | 8 | `productivity/` |
| Strategy & Executive | 5 | `strategy-executive/` |
| Customer Success | 3 | `customer-success/` |
| Procurement | 3 | `procurement/` |
| ESG & Sustainability | 4 | `esg/` |
| Data Privacy | 4 | `data-privacy/` |
| Trade Compliance | 4 | `trade-compliance/` |
| Industry (Energy) | 3 | `industry/epc-energy/` |

## Remixing M365 Agent Instructions → Copilot Studio Topics

The 89 agents are **declarative agent instructions** (for M365 Copilot Agent Builder). But their instruction patterns directly map to Copilot Studio's **GPT instructions** (componenttype 15). 

### Direct Remix Path
1. Read the agent's `instructions` block (under `## Instructions`)
2. That block can be pasted into Copilot Studio's **Instructions** field (Settings → General → Instructions)
3. The `## Conversation Starters` become trigger phrase ideas for topics
4. The `## WHAT YOU DO NOT DO` section becomes guardrails in the instructions

### Full Remix: Agent Instructions → Topic YAML
To convert an M365 declarative agent into a full Copilot Studio topic with proper triggers, YAML nodes, and actions:

1. **Topic header**: Use `kind: AdaptiveDialog` with `OnRecognizedIntent`
2. **ModelDescription**: Extract from the agent's `description` frontmatter
3. **Trigger phrases**: Adapt from `## Conversation Starters`
4. **Actions**:
   - `SendActivity` for the output (using the agent's output format)
   - `SearchAndSummarizeContent` if knowledge sources are referenced
   - `ConditionGroup` for branching review criteria
5. **Instructions**: The agent's full instruction block becomes the GPT-level instructions

See `templates/m365-to-cs-remix.yaml` for the complete conversion template.

## CAT Resources (mcscatblog)
`C:\Users\kevin\mcscatblog\` — Microsoft Customer Architecture Team blog, agent patterns, implementation guides. Browse `src/content/` for articles.

## Supporting Files

### References
- `references/official-tooling-landscape.md` — Complete scan of all Microsoft-official Copilot Studio CLIs, SDKs, VS Code extensions, APIs, and GitHub kits. Documents what's installed vs what's available but not yet set up. Check this before making tool recommendations.
- `references/dot-cache-cleanup.md` — Tool `.cache` directory sizes and safe-delete mapping (puppeteer, codex, huggingface, webwright, etc.)

### Templates
- `templates/m365-to-cs-remix.md` — Guide: converting M365 declarative agent instructions → Copilot Studio topic YAML
- `templates/document-reviewer-topic.yaml` — Worked example: Document Reviewer agent converted to full Copilot Studio topic
- `templates/README.md` — Index of all cloned Microsoft Copilot Studio GitHub repos
