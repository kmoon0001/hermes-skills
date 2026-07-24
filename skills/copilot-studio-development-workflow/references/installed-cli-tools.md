# Installed CLI Tools & Resources (added 2026-07-13)

These tools were identified via deep research (Microsoft Learn, GitHub, npm, NuGet, VS Code Marketplace) and installed to extend the Copilot Studio development workflow. 

See `shared-mcp-memory-graph/references/copilot-studio-tool-inventory.md` for full inventory and `shared-mcp-memory-graph` skill for the shared graph entity definitions.

## Tools

| Tool | Install | Key Use | Shared Graph Entity |
|------|---------|---------|---------------------|
| `a365` (Agent 365 CLI) | `dotnet tool install -g Microsoft.Agents.A365.DevTools.Cli` | Full agent lifecycle: blueprint, MCP servers in Dataverse, Azure deploy, admin center publish. `setup permissions copilotstudio` for Copilot Studio API auth. | `Agent365CLI` |
| Power Platform Eval API | (REST API, no install) | Official eval API at `api.powerplatform.com/copilotstudio/` — separate from PowerVA gateway. CI/CD pipelinable with Entra OAuth2. | `PowerPlatformEvalAPI` |
| Power CAT Copilot Studio Kit | `git clone https://github.com/microsoft/Power-CAT-Copilot-Studio-Kit` | Governance dashboard (AgentReviewTool w/ pipelines), deployment accelerator (CopilotStudioAccelerator), agent inventory schema, compliance hub. | `PowerCATCopilotStudioKit` |
| M365 Agent Templates | `git clone https://github.com/microsoft/m365-agent-templates` | Ready-to-deploy agent templates for reference implementations (HR, IT, Sales, Service, Finance). Web viewer at microsoft.github.io/m365-agent-templates/. | `M365AgentTemplates` |
| CS VS Code Extension (background automation) | VS Code marketplace `ms-CopilotStudio.vscode-copilotstudio` | Drive via cua-driver when Dataverse PATCH fails. Clone, preview diff, apply changes. VS Code binary at VS Code/bin/code.cmd (not PATH — Cursor's binary shadows it). | `CSVSLauncherConfig` |

## CS VS Code Extension as Background Automation Path

v1.5.57 installed. When Dataverse API PATCH fails (DNS quirk, auth issues, permission errors), drive the extension via cua-driver:
1. `launch_app(path="C:/Program Files/Microsoft VS Code/bin/code.cmd", start_minimized=true)`
2. Navigate to Copilot Studio panel via UIA tree (sidebar icon)
3. Clone agent → preview changes (diff view) → apply changes
The extension's sync mechanism may handle edge cases the raw API can't.

## Research Pattern (how to find more tools)

1. Search Microsoft Learn SDK/CLI/API docs
2. Check VS Code Marketplace for Copilot Studio extensions
3. Search GitHub `microsoft/` repos for "copilot studio", "agent", "m365-agent"
4. Check npm (`@microsoft/*agent*`, `@microsoft/*copilot*`) and NuGet (`Microsoft.Agents.*`, `Microsoft.PowerApps.*`) for CLI packages
5. Check community: Reddit r/copilotstudio, Tech Community, Stack Overflow
6. Cross-reference against Hermes skills, installed tools, and shared graph to identify gaps
7. Install free tools, clone repos, seed shared graph entities with `tool`/`repository`/`configuration` entityTypes
