# Copilot Studio Official Tooling Landscape

Research scan (2026-07-13) of Microsoft-official CLI tools, SDKs, VS Code extensions, APIs, and GitHub kits for Copilot Studio. Items marked **NOT INSTALLED** are confirmed absent from this environment and are candidates for setup.

## Already Installed (no action needed)

| Tool | Installed Via | Purpose |
|------|--------------|---------|
| `pac` CLI | dotnet global (v2.7.4) | Power Platform CLI — `pac copilot` commands |
| `atk` CLI | npm global (v1.1.6) | Microsoft 365 Agents Toolkit (scaffold, validate, deploy M365 apps) |
| `@microsoft/m365agentstoolkit-mcp` | npm global (v0.2.2) | MCP server for Agents Toolkit |
| `skills-for-copilot-studio` | Git clone | Copilot Studio skills, patterns, eval scripts |
| Hermes copilot-studio-* skills (40) | Hermes profile | Full dev workflow, pipeline, evals, patterns |

## NOT Installed — High Value

### 1. Agent 365 CLI (`a365`)
**Install:** `dotnet tool install --global Microsoft.Agents.A365.DevTools.Cli`
**Docs:** learn.microsoft.com/en-us/microsoft-agent-365/developer/agent-365-cli

Full agent lifecycle CLI for enterprise Agent 365 deployments. Key commands:
- `a365 setup all` — validate prerequisites, create blueprint, configure permissions
- `a365 setup permissions copilotstudio` — OAuth2 grants so your blueprint can invoke Copilot Studio agents via Power Platform API
- `a365 develop-mcp evaluate` — evaluate your MCP servers against best practices (scores + action items)
- `a365 develop-mcp list-environments` / `add-mcp-servers` — manage MCP servers in Dataverse environments
- `a365 develop add-mcp-servers` / `remove-mcp-servers` — manage local agent MCP config
- `a365 provision` / `deploy` — Azure resource provisioning and code deployment
- `a365 publish` — publish agent package to Microsoft admin center
- `a365 cleanup` — tear down all resources (blueprint, instance, Azure) cleanly

Prerequisites: .NET 8.0+, Azure subscription, Entra roles (Agent ID Developer, Contributor)

### 2. Copilot Studio VS Code Extension
**Install:** `code --install-extension ms-CopilotStudio.vscode-copilotstudio`
**Marketplace:** marketplace.visualstudio.com/items?itemName=ms-CopilotStudio.vscode-copilotstudio
**Stars/Installs:** 78K+ installs, 3★ (7 ratings)
**Repo:** github.com/microsoft/vscode-copilotstudio

What it does:
- Clone any Copilot Studio agent into VS Code as editable YAML files
- IntelliSense, syntax highlighting, guided tips for topic YAML
- Preview changes — diff view between local and live agent before applying
- Apply changes — one-click sync back to Copilot Studio (live editing)
- Get changes — pull latest from Copilot Studio into local workspace
- From the changelog: version 1.6.54 (Jul 2026), actively maintained with weekly releases

This directly addresses "streamlining topic building" — you edit in a real IDE with code assistance.

### 3. Power Platform API for Agent Evaluation
**Docs:** learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-agent-evaluation-rest-api
**Base:** `api.powerplatform.com/copilotstudio/` (NOT the PowerVA gateway we've been using)

Official REST API for programmatic evaluation:
- `GET /environments/{env}/bots/{bot}/api/makerevaluation/testsets` — list test sets with IDs, names, case counts
- `POST /environments/{env}/bots/{bot}/api/makerevaluation/start` — start an evaluation run
- `GET /environments/{env}/bots/{bot}/api/makerevaluation/runs/{runId}` — get results
- `GET /environments/{env}/bots/{bot}/api/makerevaluation/runs/{runId}/details` — per-case breakdown (HTTP 405 issues on some endpoints — see shared graph EvalEndpointLimitations entity)

Auth: OAuth 2.0 via Entra ID app registration with Power Platform API scope. Different token from the CRM Dataverse token and from the PowerVA gateway MSAL token.

### 4. Power CAT Copilot Studio Kit
**Repo:** github.com/microsoft/Power-CAT-Copilot-Studio-Kit
**Stars:** 415★, actively maintained (commits hours ago as of Jul 2026)
**Languages:** TypeScript (73%), C# (27%)

Two major components:
- **AgentReviewTool** — governance dashboard for reviewing Copilot Studio agents at scale. Pipelines included. TypeScript-based.
- **CopilotStudioAccelerator** — deployment accelerator with compliance hub, agent inventory schema, conversation KPI reporting, environment variable management. C#-based Power Platform solution.

Key feature: **Agent inventory schema** — discover and audit ALL Copilot Studio agents in your org from admin center, API, or Azure.

### 5. NLU Topic Authoring ("Create from Description")
**Docs:** learn.microsoft.com/en-us/microsoft-copilot-studio/nlu-authoring

Built into Copilot Studio UI: describe a topic in plain English and AI builds it. Currently UI-only (no API/CLI path). Directly solves the "streamline topic building when you don't know the agent's functionality" use case — just describe what you want.

### 6. Custom Knowledge Sources (OnKnowledgeRequested trigger)
**Docs:** learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/custom-knowledge-sources

YAML-only trigger for building your own knowledge retrieval. Key system variables:
- `System.SearchQuery` — context-aware rewritten query for semantic search
- `System.KeywordSearchQuery` — rewritten query for keyword engines
- `System.SearchResults` — where you store formatted knowledge snippets

Works with: Azure AI Search, custom APIs, enterprise search systems, custom connectors, Power Automate flows.

## NOT Installed — Medium Value

### 7. Agent Library / M365 Agent Templates
**Web:** microsoft.github.io/m365-agent-templates/
**App:** Agent Library marketplace app (aka.ms/agentlibrarymarketplace)
**Repo:** github.com/microsoft/m365-agent-templates

Ready-to-deploy agent templates by category (HR, IT, Sales, Finance, etc.). Can browse and deploy from the Agent Library app. Helpful starting point when you don't know what to build.

### 8. Microsoft 365 Agents SDK
**Docs:** learn.microsoft.com/en-us/microsoft-365/agents-sdk/
**Samples:** github.com/microsoft/Agents

Pro-code SDK for building agents in C#, JavaScript, or Python. Deploy to Azure Bot Service. Separate from low-code Copilot Studio. Relevant if building pro-code agents that Copilot Studio invokes as connected agents.

### 9. Evaluation-Driven Triage Framework
**Docs:** learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/evaluation-triage-overview

Microsoft's official 4-stage framework: (1) Define foundational set, (2) Set baseline + iterate, (3) Expand coverage, (4) Operationalize. Categorizes failures by quality signal (policy accuracy, source attribution, personalization, action enablement, privacy protection). Complements our existing `copilot-studio-eval-loop` and `eval-triage-framework` skills.

### 10. Copilot Studio Agent Academy
**URL:** aka.ms/agent-academy
Curated lessons walking through Copilot Studio agent building concepts and practices. Microsoft CAT-maintained.

### 11. Copilot Studio MCP Integration
**Docs:** learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-mcp

Native MCP server support within Copilot Studio UI:
- Connect to existing MCP servers (stdio only, SSE removed after Aug 2025)
- Create new MCP servers directly from Copilot Studio
- Tools/resources auto-discovered and reflected dynamically
- Requires generative orchestration to be on

### 12. Copilot Studio Connector for Power Automate
**Docs:** learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-agent-evaluation-automate-tools

Trigger agent evaluations from Power Automate flows using the Copilot Studio Connector. Connect via `mcsConnectionId` (found in Power Automate > Connections > Microsoft Copilot Studio > URL). Supports using a connection as a user profile for evaluations.

## Related Shared Graph Entities

The following entities in the Kiro/Hermes shared graph track related knowledge:
- `PowerVAGateway` — the gateway-based eval API (in use)
- `EvalEndpointLimitations` — which PowerVA eval endpoints actually work
- `EvalTokenGotcha` — MSAL vs CRM token confusion
- `PacPublishBehavior` — pac publish "Failed" display quirk
- `Copilot Studio research` tag on entity observations
