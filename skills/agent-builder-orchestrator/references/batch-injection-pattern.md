# Batch Botcomponent Injection Pattern (from Kiro rebuild-populate skill)

## Problem
PATCHing individual botcomponents one-at-a-time via Dataverse API is slow and error-prone — especially for agents with 20+ topics. Each PATCH requires a separate `curl` call and the instructions component (type 15) needs coordinated updates.

## Solution
Create a single PowerShell script (`inject-agent.ps1`) that reads all YAML files from a scratch directory and batch-creates/updates all botcomponents.

## Directory Structure
```
scratch/{agent-name}/
├── README.md                    # Package manifest
├── gpt-instructions.yml         # Full GPT component YAML
├── 01-{topic-name}.yml          # Topic YAML files (numbered for ordering)
├── 02-{topic-name}.yml
├── ...
└── inject-agent.ps1             # Single script to inject everything
```

## Script Flow
1. Authenticate via `az account get-access-token` to get Dataverse token
2. For each topic YAML file:
   - Construct PATCH URL: `PATCH /botcomponents({id})` with `{"data": "<yaml_content>"}`
   - If botcomponent doesn't exist yet, change to POST to create it
3. For instructions:
   - PATCH /botcomponents({instructions_id})/data with `{"value": "<instructions_text>"}`
4. Publish: `pac copilot publish --bot <id> --environment <url>`

## Key Details
- Topic YAML must start with `# {topic_name}` comment line (Dataverse requirement)
- Instructions are a SEPARATE componenttype 15 record — identified via `botcomponents?$filter=componenttype eq 15`
- Use `#` prefix for topic data to avoid YAML root conflicts
- Always verify each PATCH returned 204 before proceeding to next

## When to Use
- Populating a brand-new agent shell with 10+ topics for the first time
- Rebuilding an agent from YAML after a publish failure
- Moving topic sets between environments (prefer surgical solution packaging for full migration)

## Alternatives
- **Microsoft manage-agent CLI:** `node manage-agent.bundle.js push` — uses VS Code LSP protocol, handles auth and batch operations. Requires VS Code extension installed.
- **Surgical solution packaging:** Export → scrub → re-import. Full environment migration.
- **Individual PATCH:** One-at-a-time via Dataverse API. Fine for 1-3 topic changes.

## Pitfalls
- Token expires ~15min — for large batches, refresh before each PATCH or use a loop that re-authenticates every 5 topics
- YAML escaping: the `data` field uses `\r\n` CRLF line endings. Normalize to `\n` before editing, convert back to `\r\n` after
- Instructions component may NOT have a `kind:` line — it's raw text content, not YAML. Wrap as `{"value": "<text>"}` not `{"data": "<yaml>"}`
