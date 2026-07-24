---
name: copilot-studio-agent-builder
description: UNIFIED entry point for end-to-end Copilot Studio agent creation and building — blank agent → instructions → topics → knowledge sources → publish → evals. Consolidates 41 Copilot Studio skills into one loadable workflow. Use for any agent build, edit, or lifecycle task.
category: copilot-studio
version: 1.0.0
author: Hermes + Kevin McEuen
---

# Copilot Studio Agent Builder — Unified Entry Point

One skill to load for ANY Copilot Studio agent task. Consolidates 41 fragmented skills into a single workflow. Load this first, then load specific phase references as needed.

## 🚀 PRIMARY EXECUTION PATH: One-Shot Pipeline

For building a complete agent from scratch, load **`agent-builder-pipeline`** instead. It executes the full 8-phase pipeline (Research → Preflight → Shell → Topics/GPT → Deploy → QA → Publish/Test → Optimize) with visual verification at every checkpoint. Say: **"Build me an agent for [domain/purpose]"**

This skill (`copilot-studio-agent-builder`) remains the reference hub for individual operations and deep dives.

## When to Load This

- Creating a new agent from scratch
- Editing an existing agent (instructions, topics, KBs, settings)
- Adding knowledge sources programmatically
- Publishing and verifying agents
- Running and analyzing evals
- Debugging any Copilot Studio issue
- Building knowledge source content for agents

## Architecture Overview

```
Copilot Studio Agent
├── bot record (Dataverse `bots` table)
│   ├── name, publishedon, configuration, synchronizationstatus
│   └── applicationmanifestinformation (Teams/M365 config)
├── botcomponents (Dataverse `botcomponents` table)
│   ├── type 9:  Topics (AdaptiveDialog, TaskDialog)
│   ├── type 14: Uploaded files (PDFs, DOCX — UI only)
│   ├── type 15: Agent instructions (GptComponentMetadata)
│   ├── type 16: Web knowledge sources (PublicSiteSearchSource)
│   ├── type 18: Settings (Feedback, Content Moderation)
│   └── type 19: Conversation starters / eval markers
└── Eval sets (Gateway API — separate from Dataverse)
    ├── Single-turn (SR — Success Rate)
    └── Multi-turn (Conv — Conversational)
```

## Auth Tokens — NEVER Mix These

| Token | Command | Used For | Expires |
|-------|---------|----------|---------|
| **Azure CLI (Dataverse)** | `az account get-access-token --resource https://{org}.crm.dynamics.com/` | PATCH/POST botcomponents, bots table | ~1 hr |
| **MSAL PPAPI (Gateway)** | `node refresh_tda_eval_token.cjs` | Eval API (start/poll/analyze) | ~15 min |
| **PAC auth** | `pac auth create --environment ...` | `pac copilot publish` | Long-lived |

**NEVER use the Dataverse token for Gateway calls or vice versa.** Wrong token = HTTP 403.

## Environments

| Name | Env ID | Dataverse Org |
|------|--------|---------------|
| Therapy AI Agents Dev | `a944fdf0-0d2e-e14d-8a73-0f5ffae23315` | `orgbd048f00.crm.dynamics.com` |
| PCCA Package | (varies) | `pccapackage.crm.dynamics.com` |

## Phase Reference — Load by Need

| Phase | Reference File | When |
|-------|---------------|------|
| 1 — Create | `references/phase-1-create.md` | Creating blank agents, discovering bots/envs |
| 2 — Knowledge | `references/phase-2-knowledge.md` | Adding KS via API/UI, web-crawl vs uploaded files |
| 3 — Topics | `references/phase-3-topics.md` | Authoring topics, YAML patterns, trigger phrases |
| 4 — Instructions | `references/phase-4-instructions.md` | Agent instructions, description, displayName injection |
| 5 — Publish | `references/phase-5-publish.md` | Gateway/pac publish, verification, troubleshooting |
| 6 — Evals | `references/phase-6-evals.md` | Eval creation, analysis, triage, optimization loop |
| ALL — Gotchas | `references/gotchas.md` | Compiled pitfalls from all 41 skills |

## Quick Start: Build an Agent in 6 Steps

1. **Create blank agent** in Copilot Studio UI → "Skip to create blank"
2. **Write instructions** → PATCH type 15 component (2000-6000 chars)
3. **Add knowledge sources** → web-crawl via API (type 16), files via UI (type 14)
4. **Author topics** → POST type 9 components with triggers + SASC nodes
5. **Publish** → gateway `us-il106` publishv2
6. **Eval** → Conv (20 cases) then SR (100 cases), iterate to 95%+

## Skill Map — For Deep Dives

This unified skill covers the essentials. When you need deep detail on one area:

| Area | Detailed Skill |
|------|---------------|
| KS API operations | `copilot-studio-knowledge-api` |
| **🚀 One-Shot Pipeline** | **`agent-builder-pipeline`** |
| Live PATCH patterns | `copilot-studio-live-patch` |
| Eval optimization loop | `eval-optimization-loop` |
| Eval triage framework | `eval-triage-framework` |
| Topic YAML reference | `copilot-studio-int-reference` |
| KS content building | `knowledge-source-builder` |
| Agent instructions v9 template | `copilot-studio-instructions-v9` |
| Conversational booster fix | `conversational-booster-fix` |
| Multi-agent orchestration | `copilot-studio-add-other-agents` |
| Design review + troubleshooting | `copilot-studio-advisor` |
| Debug + optimization loop | `copilot-debug` |
| Full fleet audit | `agent-audit-protocol` |
| Single-bot env transport | `surgical-solution-packaging` |
| Solution migration (ALM) | `copilot-studio-agent-solution-migration` |
| Session retrospective | `session-retrospective` |
| Clinical swarm deployment | `clinical-swarm-deployment` |
| Clinical swarm guardrails | `clinical-swarm-guardrails` |

## Discovery Workflow (Before Any API Call)

```bash
# 1. Find Dataverse org from environment ID
TOKEN=$(az account get-access-token --resource 'https://service.powerapps.com/' --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.powerapps.com/providers/Microsoft.PowerApps/environments/{envId}?api-version=2023-06-01"
# → properties.linkedEnvironmentMetadata.instanceUrl

# 2. Find bot by name (Copilot Studio UI GUID ≠ Dataverse botid)
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/bots?\$filter=contains(name,'Agent Name')&\$select=name,botid" -o json

# 3. Find customization prefix (needed for schemaname on new components)
az rest --resource "$ORG/" --method GET \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '{botId}' and componenttype eq 9&\$select=schemaname&\$top=1" -o json
# → prefix = schemaname.split('.')[0:2] joined, e.g. "cr917_CompetencyCheckGamerAgent"
```

## Publishing: Gateway publishv2 (Primary Method)

```bash
# Auth — different scope than Dataverse
TOKEN=$(az account get-access-token --resource '96ff4394-9197-43aa-b393-6a41652e21f8' --query accessToken -o tsv)
TENANT=$(az account show --query tenantId -o tsv)  # FULL GUID required

# Find region (try us-il106 through us-il110)
for REGION in us-il106 us-il107 us-il108 us-il109 us-il110; do
  GATEWAY="https://powervamg.${REGION}.gateway.prod.island.powerapps.com"
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "${GATEWAY}/api/botmanagement/v1/environments/${ENV}/bots/${BOT}/publishv2-operations" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-CCI-TenantId: $TENANT" \
    -H "x-cci-applicationsource: Web" \
    -d '{}')
  [ "$HTTP" != "404" ] && break
done

# Poll until isInFinalState=true (10-30s typical)
# state="Finished" = success | state="FinishedWithUserErrors" = check exceptionType
```

## Fix: Empty Conversation Starters Block Publish

If publish fails with `MissingRequiredProperty: Title` / `MissingRequiredProperty: Text`:
```python
# GET current instructions data
# Replace: "conversationStarters:\r\n  - {}" 
# With:    "conversationStarters:\r\n  - title: Get Started\r\n    text: ..."
# PATCH back to botcomponents({id}) with {"data": fixed_data}
```

## THE GOLDEN RULE: Data Field != Content Field

- `data` = patchable via API (YAML)
- `content` = UI-only (different representation)
- PATCHing `content` returns HTTP 400
- Only `data` works for programmatic edits

## THE HARD STOP: File Uploads Are UI-Only

API can create PublicSiteSearchSource (type 16 — web crawl) and SharePoint sources. CANNOT upload binary files (.md, .pdf, .docx). For file uploads, use Copilot Studio UI → Knowledge → Add knowledge → Upload files. Do not attempt programmatic file uploads.
