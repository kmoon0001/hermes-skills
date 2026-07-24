---
name: clinical-swarm-deployment
description: >-
  Deployment standards and fleet management for the Pacific Coast Clinical AI Swarm.
  Auto-synced from .kiro/steering/deployment-standards.md and .kiro/hooks/.
  Covers schema conventions, topic standards, pre-publish validation, and agent connections.
---

# Clinical Swarm Deployment Standards

Source: `.kiro/steering/deployment-standards.md` and `.kiro/hooks/` from the codex-sharepoint-bridge-hardening-fix-all repository.

## Schema Name Conventions

| Bot | Schema | Topic Pattern |
|-----|--------|--------------|
| Command Center V2 | `auto_agent_v_5Bm` | `auto_agent_v_5Bm.topic.{Name}` |
| SNF Dashboard V2 | `auto_agent_GZ3k3` | `auto_agent_GZ3k3.topic.{Name}` |
| TheraDoc Workbench | `pcca_theradocworkbench` | `pcca_theradocworkbench.topic.{Name}` |
| Case Historian V2 | `auto_agent_XRF5I` | `auto_agent_XRF5I.topic.{Name}` |
| QM Coach V2 | `cr917_agent` | `cr917_agent.topic.{Name}` |
| Denial Defense V2 | `auto_agent_6Wt3Y` | `auto_agent_6Wt3Y.topic.{Name}` |
| Report Prep V2 | `auto_agent_aaamq` | `auto_agent_aaamq.topic.{Name}` |
| Regulatory Hub V2 | `pacific_coast_regulatory_hub_v2` | `pacific_coast_regulatory_hub_v2.topic.{Name}` |

Action schema: `{botSchema}.action.{FlowName}`
Connection schema: `{botSchema}.InvokeConnectedAgentTaskAction.{TargetName}`

## Topic Standards (Microsoft Learn)

- **Descriptions:** "Use this topic when [user intent]. It [what it does]."
- **triggerQueries:** Min 5 phrases per custom topic
- **No blocked patterns:** No triple backticks, no empty `{}` stubs, no `inputType: {}` / `outputType: {}` at root
- **No undefined variables** — `=Topic.X` without prior `init:Topic.X`

## Pre-Publish Checklist

1. No duplicate topics (query by name, flag if count > 1)
2. All BeginDialog targets exist (cross-reference dialog references)
3. All InvokeAction flows connected (flowId exists in workflows entity)
4. No NULL content topics (statecode=0 and content is null)
5. Topic count matches manifest
6. Connection references valid
7. Tools/actions enabled — no critical tools toggled OFF

## Agent Connection Standards

Hub-and-spoke architecture:
- **Command Center V2** = Orchestrator Hub (routes to all agents)
- **Dashboard V2** = Data Visualization (connects to specialists for data, CC for escalation)
- **All others** = Specialists (connect to CC + Dashboard + relevant peers)

Required for connections:
1. Both agents in same environment
2. Target agent published
3. Target has `isAgentConnectable: true`
4. `modelDescription` is REQUIRED — tells AI WHEN to route
5. After creating, publish the SOURCE agent

## Dataverse API Patterns

### Component Types
| Type | What |
|------|------|
| 9 | Topic / Agent Connection |
| 11 | Entity (ClosedList) |
| 12 | Global Variable |
| 14 | Knowledge source (file) |
| 15 | GptComponentMetadata (agent.mcs.yml) |
| 16 | Knowledge source (web) |
| 18 | Variable |
| 19 | Trigger phrase |

### Patching Locked Components
- If `iscustomizable.Value = false`, PATCH is refused
- Fix: Create new component with `_v2` schema name suffix
- Or use Playwright Code Editor (has elevated UI permissions)

### Content Format Rules
- Content starting with `#` → rejected on PATCH but works on POST
- Content starting with `m` (mcs.metadata) → rejected
- Content starting with `k` (kind:) → rejected
- **Only PATCH works on components where `iscustomizable.Value = true`**
- **POST bypasses format restrictions**

## Fleet Health Check

Run a diagnostic across all agents in the environment to check topic counts, duplicate detection, NULL content, and publish status in one pass.

### Manual Run (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/Fleet_Health_Check.ps1
```
The script at `scripts/Fleet_Health_Check.ps1` (in the codex-sharepoint-bridge-hardening-fix-all repo) queries all agents via `pac copilot list`, then checks each agent's topic components for duplicates and NULL content.

### Programmatic Run (Python — More Reliable)
The PowerShell output is garbled in some terminals. Use this Python pattern instead:
```python
from hermes_tools import terminal
for name, bot_id in [("Agent Name", "bot-guid")]:
    r = terminal(f'pac org fetch --environment {env} --xml "..." 2>&1')
    topics = [l for l in r["output"].split("\\n") if len(l.strip().split()) >= 2 and "-" in l.strip().split()[0]]
    print(f"{name}: {len(topics)} topics")
```
See the `copilot-studio-development-workflow` skill for the complete fleet health check implementation pattern.

### What It Checks Per Agent
1. Topic count (query `botcomponent` where `componenttype=9`)
2. Duplicate topic names (same name appearing multiple times → non-deterministic routing)
3. NULL content topics (active topics with empty YAML content)
4. Publish status (StateCode = Provisioned)
5. Deactivated agents flagged separately

## Related Hermes Skills

- `clinical-swarm-guardrails` — Do/Don't/Never rules and compliance
- `copilot-studio-development-workflow` — YAML-first dev pipeline
- `copilot-debug` — Debugging and evaluation repair
