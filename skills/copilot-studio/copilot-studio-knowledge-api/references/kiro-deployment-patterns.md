# Kiro Power Lessons — Operational Deployment Patterns

Source: Kiro's `copilot-studio-agent-builder-steering` power (1,765-line unified-pipeline.md, built July 2026). Field-validated patterns for Copilot Studio agent deployment via Dataverse REST API.

## Deployment Method Hierarchy (Proven)

| Method | What It Handles | Priority |
|--------|----------------|----------|
| Dataverse REST API (az token) | GPT PATCH, topic POST/PATCH, knowledge PATCH, bot entity PATCH, Teams activation | PRIMARY |
| Playwright MCP | Knowledge source FILE UPLOAD (binary chunking) | UI-ONLY fallback |

**Single-token flow (VALIDATED):** Get token once → deploy ALL components via API → publish once.

## Critical API Patterns

### Topic POST — use `parentbotid@odata.bind`
`"_parentbotid_value"` causes 0x80060888. Always use `"parentbotid@odata.bind": "/bots($botId)"`.

### Knowledge source descriptions — JSON in `data` field
Type 14 `data` field uses JSON not YAML: `{"description": "...", "isOfficialSource": true}`.

### Agent description in GPT component
The `description:` field in GptComponentMetadata (type 15) populates BOTH Overview UI and orchestrator routing. Deploy via same PATCH as instructions — NOT UI-only.

### Knowledge source WEB URLs — API, not Playwright
Type 16 (PublicSiteSearchSource) is standard Dataverse POST with YAML `data`. Fully automatable.

## Playwright — When Actually Needed
Only for: knowledge file UPLOAD (binary chunking), Work IQ toggle verification, Test Chat verification.
NOT needed for: topics, GPT, knowledge names/descriptions, web URLs, description, Teams, Response Formatting, conversation starters.

## Fleet Constraints (Non-Negotiable)
webBrowsing:false, clearTopicQueue:true, allowLatencyMessage:false, applyModelKnowledgeSetting:true, ≤10 topics, ≤4 bullets/topic, ≤5,500 GPT chars, ≥5 triggers/topic, `"{Topic.Answer}"` not `=Topic.Answer`.
