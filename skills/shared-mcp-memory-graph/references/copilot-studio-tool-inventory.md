# Copilot Studio Tool Inventory (shared graph entity map)

Every tool/resource here has a corresponding entity in the shared graph at `C:/Users/kevin/.kiro/memory/memory.jsonl`. When you find a new free/authoritative Copilot Studio tool, add it to both places.

## CLI Tools

### Agent 365 CLI — `a365`
- **Entity:** `Agent365CLI` (entityType `tool`)
- **Install:** `dotnet tool install --global Microsoft.Agents.A365.DevTools.Cli`
- **Version installed:** v1.1.214
- **Path:** `%USERPROFILE%/.dotnet/tools/a365.cmd`
- **Key commands:**
  - `a365 setup all` — full Agent 365 setup (blueprint, Entra app, permissions, Azure deploy)
  - `a365 setup permissions copilotstudio` — OAuth2 grants for Copilot Studio API access
  - `a365 develop-mcp evaluate` — evaluate MCP servers for production readiness
  - `a365 develop-mcp list-environments` — list Dataverse environments for MCP management
- **Requires:** .NET 8.0+, Azure subscription
- **Use when:** Setting up enterprise agent lifecycle, managing MCP servers in Dataverse, deploying agents to Azure

### Microsoft 365 Agents Toolkit CLI — `atk`
- **Entity:** Not added to shared graph (no entity yet) — already installed before this session
- **Install:** `npm install -g @microsoft/m365agentstoolkit-cli`
- **Version installed:** v1.1.6
- **Key commands:** `atk new`, `atk add`, `atk provision`, `atk deploy`, `atk publish`, `atk validate`
- **Requires:** Node.js
- **Use when:** Scaffolding, validating, and deploying M365 Copilot extensions and agents

### Power Platform CLI — `pac`
- **Entity:** Not added to shared graph (too generic)
- **Install:** `dotnet tool install --global microsoft.powerapps.cli.tool`
- **Key Copilot commands:** `pac copilot publish`, `pac copilot list`, `pac copilot extract-template`
- **Use when:** Publishing agents from CLI

## Repositories (cloned locally)

### Power CAT Copilot Studio Kit
- **Entity:** `PowerCATCopilotStudioKit` (entityType `repository`)
- **Path:** `C:/Users/kevin/Power-CAT-Copilot-Studio-Kit/`
- **URL:** https://github.com/microsoft/Power-CAT-Copilot-Studio-Kit
- **Contents:** AgentReviewTool (governance dashboard + pipelines), CopilotStudioAccelerator (deployment accelerator, compliance hub, agent inventory schema, conversation KPI reporting)
- **Use when:** Need governance/audit tooling, agent inventory, compliance tracking across multiple agents

### M365 Agent Templates
- **Entity:** `M365AgentTemplates` (entityType `repository`)
- **Path:** `C:/Users/kevin/m365-agent-templates/`
- **URL:** https://github.com/microsoft/m365-agent-templates
- **Contents:** Ready-to-deploy agent templates (HR, IT, Sales, Service, Finance)
- **Also at:** https://microsoft.github.io/m365-agent-templates/ (web viewer)
- **Use when:** Need reference implementations for common agent scenarios, or don't know what to build

### skills-for-copilot-studio (Microsoft's open-source plugin)
- **Path:** `C:/Users/kevin/skills-for-copilot-studio/`
- **URL:** https://github.com/microsoft/skills-for-copilot-studio
- **Key scripts:** `refresh_eval_token.cjs`, `manage-agent.bundle.js`, `eval-api.bundle.js`, `schema-lookup.bundle.js`
- **See also:** `copilot-studio-pipeline/references/ms-skills-for-copilot-studio-repo.md`

## API Surfaces

### Power Platform API (official eval API)
- **Entity:** `PowerPlatformEvalAPI` (entityType `integration`)
- **Base:** `https://api.powerplatform.com/copilotstudio/` (api-version 2024-10-01)
- **Separate from** the PowerVA gateway we use for gateway-based eval
- **Key ops:**
  - `GET /environments/{env}/bots/{bot}/api/makerevaluation/testsets` — list test sets
  - `POST .../testsets/{testSetId}/evaluate` — start evaluation
  - `GET .../runs/{runId}` — get results
- **Auth:** Standard Entra ID OAuth2 app registration (NOT the MSAL `refresh_eval_token.cjs` script)
- **Use when:** Building CI/CD eval pipelines; this is the official Microsoft API surface

### Dataverse Web API (live topic PATCH)
- **Entity:** Covered by `LiveUITruthRule` (entityType `convention`)
- **Base:** `https://{org}.crm.dynamics.com/api/data/v9.2/`
- **Key ops:** `GET/PATCH botcomponents`, `GET bots`
- **PITFALL:** Only `data` field is writable via API — `content` field rejects PATCH
- **PITFALL:** DNS quirk — `{org}.api.crm.dynamics.com` intermittently fails; `api.crm.dynamics.com` always resolves

## VS Code Extension (background automation path)

### Copilot Studio VS Code Extension
- **Entity:** `CSVSLauncherConfig` (entityType `configuration`)
- **Installed version:** v1.5.57
- **Path:** `.vscode/extensions/ms-copilotstudio.vscode-copilotstudio-1.5.57-win32-x64/`
- **VS Code binary:** `C:/Users/kevin/AppData/Local/Programs/Microsoft VS Code/bin/code` (NOT `code` in PATH — Cursor's binary shadows it)
- **Extension capabilities:** Clone agent, preview changes (diff view), apply changes (live sync), get changes from Copilot Studio
- **Use when:** Dataverse API PATCH fails (DNS quirk, auth issues), or you need a diff preview before pushing changes
- **Background driving (cua-driver):**
  - `launch_app(path="C:/Program Files/Microsoft VS Code/bin/code.cmd", start_minimized=true)` — launches minimized, no foreground disruption
  - **Activity bar navigation works minimized.** UIA `SelectionItem.Select` on sidebar TabItems (Explorer, Copilot Studio, Extensions, etc.) routes through the accessibility tree even when the window is minimized — no `raise_window` needed for tab switching
  - **Extension panel content needs the window visible.** The Copilot Studio extension panel (Clone agent button, agent list, Preview/Apply/Sync buttons) renders inside an Electron webview that only exposes content when the window is on screen. For panel interaction, restore the window via `bring_to_front(pid=..., window_id=...)` briefly, take a screenshot, then click the required element
  - **Verified:** click on TabItem element index by element_index works via UIA Invoke pattern from background. The screenshot/capture limitation is the Electron webview, not the UIA tree

## Built-in Copilot Studio Features (no install)

### NLU Topic Authoring
- **Docs:** `learn.microsoft.com/en-us/microsoft-copilot-studio/nlu-authoring`
- **What:** Describe a topic in plain English → AI builds the topic nodes for you
- **Use when:** Streamlining topic building, especially when you don't know the agent's full functionality

### Custom Knowledge Sources (OnKnowledgeRequested)
- **Docs:** `learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/custom-knowledge-sources`
- **What:** YAML-only trigger that connects your own search API as a knowledge source
- **System variables:** `System.SearchQuery` (semantic), `System.KeywordSearchQuery` (keyword), `System.SearchResults`
- **Use when:** Built-in knowledge sources (SharePoint, Dataverse) don't cover your use case

### Agent Library / M365 Agent Templates
- **Docs:** `learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/agent-library-overview`
- **Web:** `microsoft.github.io/m365-agent-templates/`
- **What:** Pre-built agents you can deploy with one click
- **Use when:** Exploring what's possible or need a starting point

### Evaluation Triage Framework
- **Docs:** `learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/evaluation-triage-overview`
- **What:** 4-stage framework: (1) Define, (2) Baseline + Iterate, (3) Expand, (4) Operationalize
- **Use when:** Turning eval failures into prioritized fixes

## Research Pattern (how this inventory was built)

When asked to find Copilot Studio tools/CLIs/SDKs/resources:

1. **Search Microsoft Learn** via `mcp__microsoft_learn__microsoft_docs_search` for official SDK, CLI, API docs
2. **Search VS Code Marketplace** for Copilot Studio extensions (`marketplace.visualstudio.com`)
3. **Search GitHub** for `microsoft/` repos matching "copilot studio", "copilot-agent", "agents", "m365-agent"
4. **Search community** — Reddit, Tech Community, Stack Overflow for tools people actually use
5. **Check npmjs.com** for official Microsoft packages (`@microsoft/*copilot*`, `@microsoft/*agent*`)
6. **Check NuGet** for `dotnet tool` packages (`Microsoft.Agents.*`, `Microsoft.PowerApps.*`)
7. **Cross-reference** against Hermes skills, installed tools, and the shared graph to identify gaps
8. **Install free tools** via their canonical package manager; clone open-source repos to `~/`
9. **Seed shared graph** with entities for every installed/found tool so both agents discover them
