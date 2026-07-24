# Live-Only Dataverse Workflow

Some agents exist ONLY in Dataverse with no local workspace on disk
(no `agent.mcs.yml`, no `topics/` directory). Discovered 2026-07-16 with
Case History Reviewing Agent (`f19e1c40`) in Therapy AI Dev.

## Detection
- `agent.mcs.yml` does not exist anywhere on disk
- `conn.json` may point at a deprovisioned/migrated bot ID
- Agent appears in `pac copilot list` but workspace is empty
- `pac org fetch` with `parentbotid` filter returns components

## Workflow
1. **Pull live state** via `pac org fetch -xf query.xml` (componenttype filter).
2. **Read topic YAML** from the `data` field of each type-9 component.
3. **PATCH** via Dataverse API when `az` token works:
   - `PATCH /api/data/v9.2/botcomponents(<id>)` with `{"value":"<yaml>"}`
   - System topics: PATCH via API causes SynchronizationSystemError — use UI only.
4. **Publish** via `pac copilot publish --bot <id> --environment <url>`
5. **Verify** via `pac org fetch` for synchronizationstatus.

## No Workspace Implications
- No local backup — always dump live state to file before PATCHing.
- No `manage-agent.bundle.js push/pull` — only live API operations.
- Topic inventory must be reconstructed from Dataverse each session.
