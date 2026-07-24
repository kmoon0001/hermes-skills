# Gatekeeper Protocol — Multi-Agent Conflict Prevention

With 3 agents (Hermes, Codex, Kiro) writing to the same stores (Knowledge Graph, Notion, Hermes Memory), conflicts are inevitable without enforcement. This protocol prevents silent overwrites, duplication, and contradictory facts.

## Principle: Append > Overwrite > Delete

| Action | Safe? | Where |
|--------|-------|-------|
| **Append** (new row/page) | ✅ Always safe | Status Log, Agent Memory |
| **Overwrite** (update existing) | ⚠️ Only with read-before-write check | Bot Config |
| **Delete** | ❌ Never by agents | All stores |

## Notion Gatekeeper Rules

### Status Log — Append-Only
Each run/event is a new row. Never modify existing rows.

### Agent Memory — Append-Only
Each session/decision is a new row. Never modify existing entries. If you have a correction, write a new entry linking back to the original.

### Bot Config — The Only Store Where Overwrites Happen

Before updating ANY config value:

```
1. READ the current value from Bot Config (query by Key)
2. COMPARE: does the new value differ from what's stored?
   - If SAME → skip (no change needed)
   - If DIFFERENT → read the LastUpdated date, Agent, and Notes fields
3. APPLY staleness gate:
   → If human-set (no Agent field OR notes say "by human") AND < 7 days old
     → BLOCK the write. Print ⛔ GATEKEEPER message.
     → Write an Incident entry to Agent Memory documenting the blocked change.
   → If > 30 days since last update (stale) → ALLOW with annotation
   → Otherwise → FLAG for approval
4. WRITE only after check passes
5. TAG every write with the Agent field
```

**Conflict resolution order when two agents wrote contradictory configs:**
1. Human-set values beat agent-set values (no Agent field = human-set)
2. Most recent timestamp wins
3. Most specific scope wins (agent-specific beats general)

**Override:** Use `force=True` to skip all checks (for human-approved changes).

## Knowledge Graph Gatekeeper Rules

### Before Creating ANY New Entity

```
1. SEARCH the graph for existing entities matching your concept
   → Use read_graph and filter by name/entityType
2. IF EXISTS → add an observation instead of creating a duplicate
   → Tag your observation with "Source: <your_name>"
3. IF NOT EXISTS → create, but check again within 24h for conflicts
```

### Before Deleting ANY Observation/Entity/Relation
- DON'T. Append corrections. The graph is append-only by convention.
- If an entity has stale info, add a new observation saying "Deprecated as of YYYY-MM-DD: reason"
- Never remove observations made by another agent — tag yours with source so readers can weigh them

### Concurrent Write Prevention
- The MCP memory server rewrites the entire JSONL on each mutation.
- Two agents writing simultaneously = last write wins, first write lost.
- If you detect the graph was modified since you last read it (check file mtime), re-read before writing.
- Preferred: serialize writes through the primary agent during normal sessions.

## Hermes Memory Gatekeeper Rules
- Single writer (Hermes only). No conflict possible.
- Cleanup: when usage hits 80%, audit for stale entries. Move to Notion or Graph.

## The Golden Test

For every write, ask:

*"If another agent reads this tomorrow, will they know whether it's still current, who wrote it, and whether a conflicting fact exists?"*

If the answer is no for any of those three, add more context before writing.

## Implementation

The gatekeeper logic is implemented in `scripts/notion_log.py`:

- `_notion_prop_val()` — extracts plain text from any Notion property type
- `update_config()` — reads before writing, applies staleness check, supports `force=True`
- On block: prints ⛔ warning and writes Incident entry to Agent Memory

Notion API version: 2025-09-03. See `references/notion-api-2025-09-03.md` for API quirks.
