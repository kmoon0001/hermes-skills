# Notion ↔ Knowledge Graph Bridge

Cross-store architecture pattern for using Notion (structured document database) alongside the MCP knowledge graph (entity/relation graph). Three-tier design with Hermes memory as the operational layer.

## Architecture

```
Hermes Memory (session)        Knowledge Graph (entities)         Notion (records)
┌───────────────────────┐     ┌──────────────────────┐     ┌────────────────────────┐
│ Prefs, IDs, pointers  │     │ Cycle6Strategy      │     │ Status Log DB          │
│ (2,200 chars)         │     │ StockTSMOMStrategy  │     │ Agent Memory DB        │
│                       │     │ FreqtradeRepo       │     │ Bot Config DB          │
│ Session-essential     │     │ StorageRules        │     │                        │
│ only                  │     │ FullTransparencyRule│     │ Universal — all agents │
└───────────────────────┘     └──────────────────────┘     └────────────────────────┘
       │                              │                            │
       └────── Hermes writes ─────────┴──────────── Hermes writes ──┘
                    Codex/Kiro read both stores, write graph only
```

## Principles

| Principle | Rule |
|-----------|------|
| **One source of truth per fact** | Each fact lives in exactly one canonical store. Other stores get derived pointers. |
| **One writer per domain** | Hermes writes trading bot. Kiro writes Copilot Studio. No domain has multiple writers. |
| **Notion = canonical records** | Time-series, rich text, config history. Full detail. |
| **Graph = cross-agent summaries** | Compact observations readable by all agents. Pointers to Notion for detail. |
| **Hermes memory = operational** | Session-essentials only — prefs, IDs, tool quirks. Pointers to larger stores. |
| **No duplicates** | Cross-store pointers only. Never the same value in two stores. |

## Implementation

### Notion databases (under "Agent Memory -- All Agents" page)

| Database | Row = | Key properties |
|----------|-------|----------------|
| **Status Log** | One run/event | Name, Date, Status (OK/Alert/Error), Equity, Agent (Hermes/Codex/Kiro), Summary, Duration |
| **Agent Memory** | One session/decision | Title, Date, Category (Fix/Audit/Config/Research/Observation/Decision/Incident), Detail (markdown), Tags (multi-select), Commit |
| **Bot Config** | One parameter | Key, Value, Category (Pipeline/Strategy/Risk/Script/Integration/Copilot-Studio), Agent, LastUpdated, Notes |

### Graph entities

Related: Cycle6Strategy, StockTSMOMStrategy, FreqtradeRepo, Cycle6DailyPipeline, StorageRules, FullTransparencyRule, NotionMemoryBridge.

### Cron sync bridge (scripts/notion_log.py)

```
log_run()           -> Notion Status Log
sync_graph_status() -> graph entity observation (same run)
```

Best-effort: Notion and graph are independent writes. One can fail without blocking the other.

## Failure modes

| Failure | Effect | Recovery |
|---------|--------|----------|
| Notion API key missing | Notion skipped, graph still syncs | Set NOTION_API_KEY |
| Graph file corrupt | Graph sync fails | Repair JSONL |
| Notion rate limited | Write delayed (3 req/s) | Retries next cycle |
| Both unavailable | Pipeline runs, no logging | Advisory only |

## CRITICAL GOTCHA — Page sharing with integration

**Symptom:** Notion API returns HTTP 404 for every endpoint (pages, blocks, data_sources, search). Even `POST /v1/search` returns 0 results for all queries. The integration is connected to the user account (verified via `GET /v1/users`), but sees nothing.

**Root cause:** The Notion page/database has NOT been shared with the integration. Connecting an integration to a workspace grants access to the USER, but each individual page must be explicitly shared.

**How to share:** In the Notion UI, open the target page → click `...` top-right → **Connections** → search for the integration name → click to add it. The integration name is the bot name shown in `GET /v1/users` (e.g. "Hemres", "hermes", "Notion MCP").

**Verification (ALWAYS do this before attempting writes):**
```bash
# Check that the API key works
curl -s "https://api.notion.com/v1/users" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | python3 -c "import json,sys;d=json.load(sys.stdin);print([u['name'] for u in d.get('results',[])])"

# Check that the integration can see the shared page
curl -s -o /dev/null -w "HTTP %{http_code}" \
  "https://api.notion.com/v1/pages/YOUR_PAGE_UUID" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
# 200 = shared, 404 = NOT shared (even if integration is connected to account)
```

**Integration name mismatch:** Multiple bots can exist under one API key. The page must be shared with the SPECIFIC integration whose token you're using. "Hemres" and "hermes" are different integrations — sharing with one does NOT grant access to the other. Always verify with `GET /v1/users` to confirm which integration the key belongs to.

**Do NOT attempt writes against a 404 page** — all operations will fail silently. Fix the sharing first, then retry.

## Setup

1. Create Notion integration → copy key
2. `hermes config set NOTION_API_KEY ntn_your_key_here`
3. Create parent page in Notion → **share with integration** (page `...` → Connections → add integration) → give Hermes the page ID
4. **Verify sharing** — test the page ID with `GET /v1/pages/{id}` — must return 200, not 404
5. Run `scripts/setup_notion_memory.py`
6. DB IDs stored in config — cron uses them automatically
