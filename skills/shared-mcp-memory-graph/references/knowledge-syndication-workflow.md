# Knowledge syndication: Hermes memory → shared graph

Add validated Hermes-memory knowledge to the shared `.jsonl` graph so Kiro (and any other bridge-connected agent) sees it on next startup.

## When to run this

- User asks to share something into the graph explicitly
- You discover validated knowledge in Hermes memory that doesn't exist in the graph
- After resolving a significant gotcha, failure pattern, or design pattern that future agent sessions should know
- **PROACTIVELY after completing any major task** — knowledge source creation, agent build/deploy, audit, fix sweep, or any session where durable facts were discovered. If the user has to prompt you to save context, you missed the trigger.

## Prerequisites

- The shared `.jsonl` file exists at a known absolute path (typically `C:/Users/kevin/.kiro/memory/memory.jsonl`)
- You can read both Hermes memory (injected every turn) and the graph file
- For the full three-tier archive (memory + graph + Notion): the Notion page must be shared with the integration. Verify with `GET /v1/pages/{page_id}` — must return 200. If 404, tell the user to share the page (page `...` → Connections → add integration). Do NOT attempt Notion writes against a 404.

## Workflow

### 0. Verify Notion access (if writing to Notion)

Before attempting Notion writes, verify the integration can actually see the target page:

```bash
curl -s -o /dev/null -w "HTTP %{http_code}" \
  "https://api.notion.com/v1/pages/PAGE_UUID" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

- HTTP 200 = shared, proceed
- HTTP 404 = NOT shared. Tell the user: open page in Notion → `...` → Connections → add the integration. Do not proceed with Notion writes.
- If the API key itself is invalid: `GET /v1/users` will return "API token is invalid." Ask for a new key.

### 1. Read current state of the shared graph

Read the `.jsonl` file directly — it's just newline-delimited JSON:

```bash
cd /c/Users/kevin/.kiro/memory
python3 -c "
import json
with open('memory.jsonl') as f:
    for l in f:
        if l.strip():
            d = json.loads(l)
            if d['type']=='entity':
                print(f\"ENTITY {d['name']} ({d['entityType']}) — {len(d.get('observations',[]))} obs\")
            elif d['type']=='relation':
                print(f\"  REL: {d['from']} --{d['relationType']}--> {d['to']}\")
"
```

### 2. Audit Hermes memory for candidates

Hermes memory is injected at the start of each conversation under `MEMORY (your personal notes)`. Look for candidates that are:

- **gotchas** — things that silently break (DNS quirks, token confusion, publish display vs reality, response-override behavior)
- **design_patterns** — reusable architectures (extraction topic patterns, inspection protocols)
- **conventions** — how things should be done (additive-only, source-of-truth rules)

Exclude from syndication:
- Environment-specific failures (missing binaries, unconfigured keys, fresh-install errors)
- Session-specific transient errors that resolved mid-conversation
- One-off task narratives (individual PR numbers, individual bug titles)
- Instructions to yourself about how to respond or format output (belongs in skills, not the graph)

### 3. Cross-reference against existing graph

Check if the candidate knowledge is already represented:

```bash
grep -c "CandidateName" memory.jsonl
```

Three cases per candidate:
- **Already present** → skip (no duplicate entities)
- **Partially present** → update existing entity observations (or leave it for the next agent to decide)
- **Not present** → add as a new entity (step 4)

### 4. Construct entities and relations

Graph schema:
- **entity**: `{"type":"entity", "name":"<PascalCaseName>", "entityType":"<type>", "observations":["fact 1","fact 2"]}`
- **relation**: `{"type":"relation", "from":"<EntityName>", "to":"<TargetEntity>", "relationType":"<kebab-case-verb>"}`

Choose the right entityType:
| Type | Use for |
|---|---|
| `gotcha` | Quirks, pitfalls, silent failures, endpoint limitations, confusing CLI output |
| `design_pattern` | Reusable architectures, extraction logic, inspection frameworks |
| `failure_mode` | Grader/grader behavior, dominant failure classes, root causes |
| `convention` | Team rules, source-of-truth rules, additive-only policy |
| `copilot_agent` | Bot identities with env/org/tenant IDs, model, topic counts |
| `integration` | Gateway URLs, auth recipes, test set IDs |
| `copilot_topic` | Individual topics created live, their IDs and schemanames |

Observations should be:
- Factual and self-contained (standalone without context from other observations)
- Concise — one discrete fact per observation string
- Non-instructional — describe reality, not "you should X"

### 5. Write the consolidated file (atomic replace)

**Do NOT append incrementally** — a `read_graph` call that fires between your appends sees an incomplete graph. Instead, read → modify → write the whole file atomically:

```python
import json

MPATH = "C:/Users/kevin/.kiro/memory/memory.jsonl"

# 1. Read existing
with open(MPATH) as f:
    lines = [json.loads(l) for l in f if l.strip()]

# 2. Append new entities
entities = [
    {"type":"entity", "name":"MyNewGotcha", "entityType":"gotcha",
     "observations":["thing to remember"]},
]
relations = [
    {"type":"relation", "from":"MyNewGotcha", "to":"ExistingEntity",
     "relationType":"related_to"},
]

lines.extend(entities)
lines.extend(relations)

# 3. Write
with open(MPATH, "w") as f:
    for line in lines:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
```

### 6. Verify

```bash
cd /c/Users/kevin/.kiro/memory
python3 -c "
import json
with open('memory.jsonl') as f:
    lines = [l.strip() for l in f if l.strip()]
for i, l in enumerate(lines, 1):
    try:
        json.loads(l)
    except:
        print(f'LINE {i} FAILED: {l[:80]}')
        break
else:
    print(f'All {len(lines)} lines valid JSON')
"
```

## Pitfalls

- **Do not write duplicates.** Check the existing graph for a matching name before adding an entity.
- **Observation order matters** within an entity — make the most useful fact first (it's what the LLM sees when summarizing).
- **entityType is not free-form** — stick to the table in step 4 so cross-entity queries work (e.g. filtering by type across the graph).
- **relationType should be a short kebab-case verb** — `evaluated_via`, `exhibits_failure`, `governed_by`, `affects_convention`, `impedes`, `related_to`, `fixed_by`, `applies_pattern`, `created_via`, `resolved_by`, `has_gotcha`, `limits`, `includes_pattern`. Keep the list consistent — new relationTypes expand it; an existing one should be reused when it fits.
- **No trailing-newline conventions** matter to some editors — the JSONL server splits on `\n` and ignores empty trailing lines, so either is fine.
- **JSON backslash escaping in observations.** Backslashes in path strings inside observations (e.g. `C:\Users\.dotnet\tools\`) are interpreted as JSON escape sequences — `\.` fails, `\t` becomes a tab character. Always use forward slashes for paths inside JSON strings: `C:/Users/.dotnet/tools/`. If backslashes are unavoidable, double-escape them: `C:\\Users\\.dotnet\\tools\\`. The safer rule: always forward-slash inside JSON, even on Windows.
- **Shell heredocs vs JSON backslashes.** When appending via `cat >> file << 'EOF'` (single-quoted heredoc delimiter), raw backslashes pass through untouched — no shell interpolation. But `python3 -c "..."` or double-quoted heredocs (`<< EOF`) DO interpret backslashes, so paths like `C:\Users` become `C:Users`. Use single-quoted heredoc delimiters (`<< 'EOF'`) or verify raw output when writing JSONL from shell.
