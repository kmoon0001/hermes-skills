# memory.jsonl seeder + verified patterns

## Seed a shared graph (Python, runs anywhere)

```python
import json, os

MPATH = "C:/Users/kevin/.kiro/memory/memory.jsonl"   # MUST be .jsonl, absolute
os.makedirs(os.path.dirname(MPATH), exist_ok=True)

entities = [
    {"name": "PacificCoastCaseHistorian", "entityType": "copilot_agent",
     "observations": [
        "Bot ID: ad635500-cf47-f111-bec5-70a8a5b1c3a3",
        "Env ID: a944fdf0-0d2e-e14d-8a73-0f5ffae23315 (orgbd048f00)",
        "Agent instructions component: 5dc9bc35-a81d-4515-a74d-c577731285c7 (Dataverse type 15)",
        "Model: Sonnet 4.6",
        "25 topics, 11 knowledge sources, 4 connected discipline sub-agents",
     ]},
    {"name": "PowerVAGateway", "entityType": "integration",
     "observations": [
        "Gateway base: https://powervamg.us-il107.gateway.prod.island.powerapps.com/api/botmanagement/v2",
        "Eval needs X-CCI headers + gateway host (direct ppapi = InvalidAudience).",
        "SingleTurn(SR)=c1f6dd5f-2360-48a2-b525-0fc733667644 (100); MultiTurn(Conv)=73635479-2ceb-44f2-9709-8fae06588924 (20)",
     ]},
    {"name": "EvalForensicsPattern", "entityType": "failure_mode",
     "observations": [
        "Grader is LITERAL-EXTRACTION-GROUNDED: wants exact value pulled from inline-pasted text.",
        "Dominant SR fail: completeness=No. Agent KB-searches pasted text instead of reading it.",
        "17/28 no-topic fails = bot-level generative (GPT fallback); instructions type-15 governs those.",
     ]},
    {"name": "LiveUITruthRule", "entityType": "convention",
     "observations": [
        "Live Dataverse = source of truth; local clone read-only this session.",
        "Additive-only fixes; live PATCH botcomponents({id}) data field.",
     ]},
]
relations = [
    {"from": "PacificCoastCaseHistorian", "to": "PowerVAGateway", "relationType": "evaluated_via"},
    {"from": "PacificCoastCaseHistorian", "to": "EvalForensicsPattern", "relationType": "exhibits_failure"},
    {"from": "PacificCoastCaseHistorian", "to": "LiveUITruthRule", "relationType": "governed_by"},
]

lines = []
for e in entities:
    lines.append(json.dumps({"type": "entity", "name": e["name"],
                             "entityType": e["entityType"], "observations": e["observations"]}))
for r in relations:
    lines.append(json.dumps({"type": "relation", "from": r["from"], "to": r["to"],
                             "relationType": r["relationType"]}))
open(MPATH, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("seeded", len(lines), "lines ->", MPATH)
```

## Verify server reads it (Node, MSYS-safe)

```js
// run from cmd.exe /c so npx resolves; pass full path or use 'cmd','/c','npx'
const { spawn } = require('child_process');
const child = spawn('cmd.exe', ['/c', 'npx', '-y', '@modelcontextprotocol/server-memory'],
  { env: { ...process.env, MEMORY_FILE_PATH: 'C:/Users/kevin/.kiro/memory/memory.jsonl' } });
// JSON-RPC: initialize -> notifications/initialized -> tools/list -> tools/call read_graph
// Frame parser: split on complete {} (brace-depth counter); server also prints a non-JSON stdio log line.
```

## Format facts (server v2026.7.4, dist/index.js)

- `defaultMemoryPath = path.join(dirname(import.meta.url), 'memory.jsonl')` — `.jsonl`, not `.json`.
- `ensureMemoryFilePath()`: if `process.env.MEMORY_FILE_PATH` set AND absolute → use as-is; else relative to import.meta.url (npx cache dir). Unset env = ISOLATED cache graph.
- `loadGraph()`: `readFile` → `split("\n")` → `JSON.parse` each line. Single-object `.json` throws `Expected property name or '}' at position 1`.
- Migration: if legacy `memory.json` exists beside the default and `memory.jsonl` does not, it renames `.json`→`.jsonl` (does NOT convert format — only works if the old file was already JSONL).
