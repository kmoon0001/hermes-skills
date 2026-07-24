---
name: clinical-swarm-guardrails
description: >-
  Mirror of the Kiro project steering rules for the Pacific Coast Clinical AI Swarm.
  Auto-synced from .kiro/steering/ in the codex-sharepoint-bridge-hardening-fix-all repo.
  Rules for agent development, compliance, healthcare AI safety, and tooling priority.
---

# Clinical Swarm Guardrails

Source: `.kiro/steering/` from the codex-sharepoint-bridge-hardening-fix-all repository.

## Active Fleet (Therapy AI Agents Dev)

Environment: `orgbd048f00.crm.dynamics.com`
Tenant: `03cc92c3-986c-4cf4-ae27-1478cf99d17f`

| Agent | Bot ID | Role |
|-------|--------|------|
| SNF Command Center V2 | `9f3e370c-a747-f111-bec6-0022480b6bd9` | Orchestrator Hub |
| SNF AI Dashboard V2 | `bd570423-cf47-f111-bec5-70a8a5b1c3a3` | Data Visualization |
| TheraDoc Workbench | `e09954e1-4af8-47c6-8ef4-d1d9335bf2e6` | Therapy Documentation |
| Pacific Coast Case Historian V2 | `ad635500-cf47-f111-bec5-70a8a5b1c3a3` | Longitudinal Analysis |
| SimpleLTC QM Coach V2 | `ea52ad9c-8233-f111-88b3-6045bd09a824` | Quality Measures |
| Denial Defense V2 | `6d7815b4-ce47-f111-bec5-70a8a5b1c3a3` | Denial Management |
| Therapy Report Prep V2 | `fd1bce12-cf47-f111-bec5-70a8a5b1c3a3` | Report Generation |
| PT_Specialist | `c9eb5556-e562-4bf0-9536-6a6f7fe0a0df` | PT Documentation Audit |
| OT_Specialist | `63e468f5-6867-4940-ade7-ff10adeac525` | OT Documentation Audit |
| SLP_Specialist | `5b44ba2e-4c37-4db1-becc-a499d27bd299` | SLP Documentation Audit |
| Pacific Coast Compliance Analyzer | `19779839-7b6e-4362-925b-8ddf03979f7d` | Compliance Audit |
| Pacific-Coast Regulatory Hub V2 | `ea901efc-d043-4023-88a6-8ac4c561a4d5` | Regulatory Reference |
| Daily/Weekly Medicare Meeting Agent | `ee72fe1a-0882-4dec-9959-ace1fbb74280` | Meeting Support |
| Pacific-Coast Clinical Synthesis Lab V2 | `89c7415d-df73-490c-9d78-4829cfbc2f84` | Clinical Synthesis |

## ✅ Do Without Asking

- Read any file in the repo
- Generate topic YAML, flow stubs, schema drafts
- Run lint, typecheck, or validation commands
- Write to `/topics/`, `/flows/`, `/schemas/`
- Query Dataverse API for bot component status
- Run dedup scans and diagnostic checks
- Create/update files in `.kiro/skills/` or `.kiro/steering/`

## ⚠️ Ask Before Doing

- Install or remove any package or CLI tool
- Delete any topic, flow, table, or solution component
- Commit to git or open a pull request
- Rename files or move directory structure
- Modify environment variables or connection references
- Import or export solutions (`pac solution import/export`)
- Trigger `PvaPublish` on any bot

## 🚫 Never Do

- Publish any agent to production — stage only
- Commit .env files, client secrets, or connection strings
- Store or log PHI outside of approved Dataverse tables
- Force push to main or any protected branch
- Skip the HITL confirmation step on any clinical data output
- Assume a flow is working — always validate with a test run
- Use Dataverse API PATCH to update botcomponent content on locked components (use Playwright UI instead)
- Delete system topics (Conversation Start, Fallback, On Error) — only override them

## Compliance Rules (Non-Negotiable)

- **HIPAA:** Any topic or flow that touches patient data must be flagged and include a human-in-the-loop confirmation step
- **CMS/SNF QRP:** Documentation field names must match MDS 3.0 codes
- **Clinical output:** Any output surfacing clinical data needs explicit user confirmation before being saved or sent
- **PHI minimum necessary:** Use record IDs, not full patient identifiers in topic logic
- **Audit trail:** All clinical data operations must be traceable

## Healthcare AI Settings Standards

All clinical agents MUST have:
- `contentModeration: High`
- `useModelKnowledge: false`
- `optInUseLatestModels: false`
- `isAgentConnectable: true` (hub-and-spoke)
- `authenticationTrigger: Always`
- `accessControlPolicy: GroupMembership`
- `webBrowsing: false`
- `codeInterpreter: false`

## Tool Priority Order

1. **Playwright UI code editor** — for creating/editing topics (Microsoft Learn recommended)
2. **Dataverse API** — for querying, deleting, creating agent connections, triggering publish, reading diagnostics
3. **pac CLI** — for solution export/import, auth management, publishing
4. **Playwright UI buttons** — last resort

## Related Hermes Skills

- `clinical-swarm-deployment` — Deployment standards and fleet management
- `copilot-studio-development-workflow` — YAML-first dev pipeline
- `copilot-debug` — Debugging and evaluation repair
- `passagenttesting` — Evaluation score improvement
