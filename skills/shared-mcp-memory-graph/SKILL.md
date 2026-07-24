---
name: shared-mcp-memory-graph
description: "Cross-agent shared memory architecture: MCP knowledge graph + Notion bridge + Hermes memory. Three-tier storage for entity relations, structured records, and session context. Covers server setup, JSONL format, Notion 2025-09-03 API quirks, cross-store pointer conventions, and storage rules."
version: 1.3.1
author: Copilot Studio Pipeline + Hermes
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [mcp, knowledge-graph, multi-agent, kiro, notion, memory, cross-store, storage-architecture]
---

# Shared MCP Knowledge Graph (cross-agent)

Make two or more AI agents share ONE knowledge graph so each reads what the other writes. The canonical server is `@modelcontextprotocol/server-memory` (the official MCP "memory" / knowledge-graph server).

## When to use

- User says "let Kiro and Hermes share the same knowledge / memory graph"
- You need agent-to-agent knowledge transfer (bot IDs, architecture decisions, failure modes, PATCH patterns)
- Any ask to "wire agent X and agent Y to the same graph / brain"

## CRITICAL FORMAT GOTCHA (verified 2026-07-12, server v2026.7.4)

**This server reads/writes JSONL (`memory.jsonl`), NOT the legacy `memory.json` array.** Its loader does `fs.readFile` then `split("\\n")` and `JSON.parse` **each line** (see `dist/index.js` `loadGraph()`). A single JSON object → `JSON.parse` on the first line fails with `Expected property name or '}' at position 1 (line 1 column 2)`.

- Store the graph as **one JSON object per line**: `{"type":"entity","name":...,"entityType":...,"observations":[...]}` then `{"type":"relation","from":...,"to":...,"relationType":...}` per line.
- File extension MUST be `.jsonl` (the server's `defaultMemoryPath` is `memory.jsonl`). A `.json` file is silently misread even if valid.
- Convert a seeded `memory.json` array to JSONL: emit one line per `entities[]` entry (as `type:"entity"`) and one per `relations[]` entry (as `type:"relation"`).

## CRITICAL FILE CORRUPTION GOTCHA — Two JSON Objects on One Line (verified 2026-07-20)

**Symptom:** `read_graph` (or any MCP tool that reads the graph) fails with `"Unexpected non-whitespace character after JSON at position N (line 1 column M)"`. Every other tool that reads the file also fails. The `.jsonl` file appears valid at a glance (no missing braces, no syntax error inside each object), but the parser fails anyway.

**Cause:** Two or more complete JSON objects got written to the SAME line without a newline separator:

```
{"type":"relation","from":"A","to":"B","relationType":"links"}{"type":"entity","name":"C",...}
```

The server's `split("\\n")` reads this as ONE line, then `JSON.parse` processes only the first object. The remaining characters (`{...second object...}`) trigger the "Unexpected non-whitespace character" error because the parser finished a complete JSON object but found more data on the same line.

**How this happens:** A write process (agent, script, or tool) that appends or rewrites the graph file must guarantee exactly one JSON object per line. Any code that does `file.write(json.dumps(obj))` followed by `file.write(json.dumps(obj2))` without inserting `"\\n"` between produces this corruption. The most common cause is a `writelines()` with a missing newline character or a manual concatenation that joins two objects.

**Detection:**
```bash
python3 -c "
import json
with open('memory.jsonl') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not stripped: continue
    objs = 0; depth = 0
    for ch in stripped:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
        if depth == 0 and ch == '}': objs += 1
    if objs > 1:
        print(f'CORRUPTED line {i}: {objs} objects on one line')
"
```
**PITFALL — naive `}{` splitting corrupts files with `}{` inside strings:** Do NOT use `line.replace('}{', '}\n{')` — it splits every `}{` literally, including ones inside JSON string values like `\"Fixed: SendActivity from '{Topic.Answer}{System.Activity.Text}'\"`. This produces broken JSON fragments. Always use a brace-count parser that respects string boundaries.

**Fix — repair the file (brace-count approach, string-aware):** Use a state-machine splitter that tracks brace depth while respecting JSON string/escape context:

```python
import json

def split_jsonl_objects(text):
    """Split concatenated JSON objects on one line, respecting string boundaries."""
    objs = []
    depth = 0
    start = 0
    in_string = False
    escape = False
    
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    objs.append(text[start:i+1])
    return objs if objs else [text]

# Usage:
with open('memory.jsonl') as f:
    lines = f.readlines()

fixed = []
for line in lines:
    stripped = line.rstrip('\n')
    if not stripped:
        fixed.append('\n')
        continue
    for obj in split_jsonl_objects(stripped):
        fixed.append(obj + '\n')

with open('memory.jsonl', 'w') as f:
    f.writelines(fixed)

# Verify
with open('memory.jsonl') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if line:
            json.loads(line)
print(f'Repaired: all {i} lines valid')
```

**Prevention — atomic write pattern:** Any code that modifies the graph should use a read-modify-write cycle that guarantees one object per line. When appending a single object, ensure the last line of the file ends with `\\n` before appending. The safest approach is to always rewrite the entire file via `writelines` with each line terminated by `\\n`.

**Why it matters more than a syntax error:** This corruption silently blocks ALL tools that read the graph — `read_graph`, `create_entities`, `create_relations`, `add_observations`, `delete_*`. No graph operations work until the file is repaired.

## CRITICAL FRAGMENTATION GOTCHA (verified 2026-07-12)

If `MEMORY_FILE_PATH` is NOT set on a server, it **falls back to a local default** (`path.join(dirname(import.meta.url), 'memory.jsonl')` — i.e. inside the npx cache dir), NOT a shared location. Two agents with `env: {}` on the memory server will each get their OWN isolated graph in their own npx cache. The shared graph only exists if BOTH agents explicitly point `MEMORY_FILE_PATH` at the **same absolute path**.

- Step 1: pick ONE absolute path, e.g. `C:/Users/kevin/.kiro/memory/memory.jsonl` (Windows) or `/home/kevin/.kiro/memory/memory.jsonl` (linux).
- Step 2: set `MEMORY_FILE_PATH` in BOTH agents' MCP configs to that exact path.
- Step 3: create + seed the file (see `references/memory-jsonl-seed.md` for a ready seeder).

## Hermes config (native MCP client)

Add under `mcp_servers` in `~/.hermes/config.yaml` (global) or the profile config (`AppData/Local/hermes/profiles/<profile>/config.yaml`):

```yaml
mcp_servers:
  shared_memory:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-memory"]
    env:
      MEMORY_FILE_PATH: "C:/Users/kevin/.kiro/memory/memory.jsonl"
    timeout: 120
```

Tools register as `mcp_shared_memory_read_graph`, `mcp_shared_memory_create_entities`, `mcp_shared_memory_create_relations`, `mcp_shared_memory_add_observations`, etc. **Requires restart** — MCP servers load at agent startup, no hot-reload.

## Kiro config

In `~/.kiro/settings/mcp.json` (the `memory` server entry):

```json
"memory": {
  "env": { "MEMORY_FILE_PATH": "C:/Users/kevin/.kiro/memory/memory.jsonl" },
  "disabled": false,
  "autoApprove": ["read_graph", "create_entities", "add_observations"]
  // ...args: ["-y", "@modelcontextprotocol/server-memory"], command: "npx"
}
```

Note: Kiro's default memory server ships with `"env": {}` — you MUST add the `MEMORY_FILE_PATH` or it fragments to the npx cache.

## Verify the wiring (end-to-end, do NOT skip)

Don't assume it works from config alone. Prove the server reads AND writes the shared file:

1. Spawn the server with `cmd.exe /c npx -y @modelcontextprotocol/server-memory` and `MEMORY_FILE_PATH` set (node's bare `spawn('npx')` fails under MSYS — use `cmd.exe` + `/c`, or pass the full npx path `C:/Program Files/nodejs/npx`).
2. Send JSON-RPC: `initialize` → `notifications/initialized` → `tools/list` (expect 9 tools) → `tools/call read_graph` → `tools/call create_relations` with a test relation.
3. Confirm the test relation now appears in the `.jsonl` file on disk. Then remove the test relation to keep the graph clean.

The server emits a non-JSON logging line (`Knowledge Graph MCP Server running on stdio`) mixed into stdout — frame parser must split on complete `{}` objects (brace-depth counter), NOT on newlines only, or `JSON.parse` of a partial frame throws.

## Seed content pattern

Seed entity types that pay off across sessions:
- `<AgentName>` (entityType `copilot_agent`): bot/env/org IDs, model, topic/KB counts.
- `<Integration>` (entityType `integration`): gateway URL, auth recipe, test-set IDs.
- `<FailurePattern>` (entityType `failure_mode`): grader behavior, dominant failure subscore, where per-case reasons live.
- `<Convention>` (entityType `convention`): source-of-truth rule, additivity, live-PATCH path.
- `<Tool>` (entityType `tool`): installed CLIs, SDKs, version, install command, disk path.
- `<Repository>` (entityType `repository`): cloned repos, URL, key contents, when to use.
- `<Configuration>` (entityType `configuration`): extension paths, binary locations, launcher notes.

Then `relations` linking them (e.g. `<Agent> evaluated_via <Integration>`, `<Agent> exhibits_failure <FailurePattern>`, `<Tool> can_configure <Integration>`).

See `references/copilot-studio-tool-inventory.md` for the current tool/repository/API inventory already seeded in the graph.

## Knowledge syndication workflow (operational: adding content)

**Trigger this workflow PROACTIVELY after completing any major task** — not just on `/new`. Major task = knowledge source creation, agent build/deploy, audit, fix sweep, or any session where durable facts were discovered. If the user has to prompt you to save context, you missed the trigger.

The setup above creates the **pipeline**. Use `references/knowledge-syndication-workflow.md` when you need to **run it** — specifically:

1. **Audit** — scan three vectors for candidates:
   - Hermes memory (gotchas, design patterns, conventions injected at session start)
   - External research (deep web searches for official Microsoft tooling, CLIs, SDKs, APIs — find tools we don't have)
   - Session resolutions (fixes, workarounds, architecture decisions durable enough to cross sessions)
2. **Cross-reference** existing entities to avoid duplicates.
3. **Construct entities + relations** using the right entityType for the class of knowledge.
4. **Write atomically** — prefer **full file rewrite** (read → modify → write entire `.jsonl`) when adding 3+ entities; incremental appends accepted for 1-2 entries. Full rewrite is the clean, safe approach — no risk of the server reading an incomplete graph between writes.
5. **Verify** every line parses as valid JSON.

Each qualified item triggers this workflow. Do NOT syndicate environment-specific failures, transient middleware errors, or session-specific task narratives — those waste graph capacity and misdirect other agents.

Full reference: `references/knowledge-syndication-workflow.md`

## Syndicate the bridge into each tool's guidance files (REQUIRED, easy to miss)

Wiring the MCP server makes the graph *technically* shared, but each tool (Hermes, Kiro, Claude
Code, Cursor, Codex) only looks in its OWN guidance files for "what do I know about this project."
If you don't also drop a pointer line in those files, a future session in tool X will NOT know the
bridge exists and will re-derive or duplicate knowledge. This is the most common gap after setup.

For a project repo, add a one-line "Shared memory bridge" note to each guidance/steering file the
tools read:

- `AGENTS.md` and `CLAUDE.md` (project root) — add under the relevant section:
  `**Shared memory bridge (Hermes ↔ Kiro):** both read/write C:/Users/kevin/.kiro/memory/memory.jsonl — write cross-tool facts there once, do not duplicate into separate stores.`
- `.kiro/steering/*.md` — if a steering file already summarizes cross-tool rules, append the same pointer.
- `.kiro/hooks/` — no change needed (hooks fire at commit, not knowledge discovery), but verify none
  of them hardcode a *separate* memory path that would fragment knowledge.
- Project `lessons-learned.md` — this is the human-readable knowledge base; the JSONL graph is the
  machine-readable twin. Keep them in sync: update `lessons-learned.md` for durable patterns AND
  write the structured entity/relation to the shared `.jsonl`.

After editing, grep each file to confirm the pointer line is present (the bridge is only useful if
every future session visibly sees it).

## Gatekeeper Protocol — Multi-Agent Conflict Prevention

When 3+ agents (Hermes, Codex, Kiro) write to the same stores, silent overwrites and duplication are inevitable without enforcement. See `references/gatekeeper-protocol.md` for the full protocol.

### Quick Rules

| Store | Write rule | Conflict prevention |
|-------|------------|-------------------|
| **Knowledge Graph** | Append-only (add observations, never delete) | Search before creating entities. Tag source. Deprecate stale info. |
| **Notion Status Log** | Append-only (new rows only) | None needed — no overwrite possible |
| **Notion Agent Memory** | Append-only (new rows only) | None needed — no overwrite possible |
| **Notion Bot Config** | Overwrite with read-before-write check | Staleness gate: if human-set <7d ago, FLAG. Override with force=True. |
| **Hermes Memory** | Hermes-only writer | None needed — single writer |

### The Golden Test

Before every write: *"If another agent reads this tomorrow, will they know if it's still current, who wrote it, and whether a conflicting fact exists?"*

## Limitations / scope

- This shares GRAPH KNOWLEDGE between agents. It does NOT bridge one agent into another's runtime/toolset. For that, wrap the target's scripts as an MCP server (stdio) exposing them as tools — a different task.
- The memory server is a flat entity/relation graph, not a document store. Keep observations short and factual.
- Server version drift: future `@modelcontextprotocol/server-memory` releases may change the default path or re-introduce `memory.json`. Always verify the loader format against the installed `dist/index.js` before seeding.

## Three-Tier Storage Architecture

The graph is ONE tier in a three-tier architecture. Each tier serves a different purpose:

| Tier | Capacity | Best for | Avoid |
|------|----------|----------|-------|
| **Hermes Memory** | ~2,200 chars | Session essentials: prefs, IDs, tool quirks, pointers | Long text, time-series, narrative |
| **Knowledge Graph** | Unlimited (JSONL) | Entity relationships, cross-agent facts, tool inventories | Paragraphs, timestamps, secrets |
| **Notion** | Unlimited (API) | Run logs, session notes, config history, audit docs | Cross-agent instant lookup |

### Decision Tree — Where to Store

```
Is this needed every session start?
  ├── YES -> Hermes Memory (keep under 1,500 chars)
  |
  +-- NO -> Is it a relationship or semantic fact?
            +-- YES -> Knowledge Graph (entity + observations)
            +-- NO -> Does it have a time dimension or need rich text?
                      +-- YES -> Notion
                      +-- NO  -> Short pointer in Hermes Memory (last resort)
```

### Entity Convention (Knowledge Graph)

- **Entity name:** PascalCase, descriptive (`Cycle6Strategy`, not `c6` or `MyEntity`)
- **Entity type:** lowercase, one of: strategy, repository, tool, integration, pipeline, convention, gotcha, observation, feature, copilot_agent, failure_mode, design_pattern
- **Observations:** one sentence each, atomic facts. Not paragraphs.
- **Source tag:** last observation = `"Source: <agent_name>"` so others know provenance
- **Relations:** active voice verbs (`runs_on`, `logs_to`, `syncs_from`, `lives_in`, `documents`)

### Cross-Store Pointers (NOT Duplicates)

When one store references another, use a pointer -- not a copy:

- Hermes Memory: `"Trading metrics -> Notion Agent Memory"` (pointer, not the values)
- Graph observation: `"Notion Status Log DB: 118bf11a"` (pointer, not the log contents)
- Notion entry: `"Sharpe formula corrected Jul 20 -- see audit/security_and_accuracy.md"` (pointer to git file)

**The test:** If you change the source value, do you need to update the pointer? If yes, the pointer is good. If you have the same value in two stores, one is wrong.

## Cross-store bridge with Notion (structured data supplement)

The graph works well for semantic entity/relation knowledge, but it's NOT a document store — time-series data (run logs), rich-text notes, and config history with update tracking don't fit in observations. See `references/notion-graph-bridge.md` for a pattern that pairs the MCP graph with Notion databases:

- **Notion** = canonical structured records (Status Log, Agent Memory, Bot Config)
- **Graph** = short cross-agent summaries derived from Notion records
- **One writer per domain** — Hermes writes both for trading-bot data; no duplication
- **Cron sync bridge** — daily pipeline logs to Notion then updates graph observations

This pattern keeps the graph fast and focused while pushing rich data to Notion where it belongs. The bridge reference covers setup, architecture, failure modes, and the three database schemas. Requires `NOTION_API_KEY` and a parent page shared with the integration.

## Companion MCP Stack Reference

Kiro runs a full 8-server MCP stack alongside this shared graph. For comparing Hermes MCP coverage against Kiro's production setup, see `references/kiro-full-mcp-stack.md` — a snapshot of every server, its purpose, and which ones Hermes would benefit from adding (sequential-thinking, git, github) vs. skipping (filesystem, playwright).

## Related

- `native-mcp` skill — Hermes native MCP client config reference.
- `copilot-studio-analyze-evals` / `copilot-studio-run-eval` — the agents this was stood up to connect.
