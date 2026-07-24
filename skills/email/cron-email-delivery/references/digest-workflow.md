# Digest Compilation Workflow

## Step-by-Step Pattern

Two approaches, pick based on scope:

### Google News Scanning
For curated news picks, search `news.google.com` via web_search with site-specific operators:

```bash
web_search(query="Google News \"Copilot Studio\" OR \"Power Platform AI\" 2026 July", limit=8)
web_search(query="Google News \"Hermes agent\" OR \"Nous Research\" 2026", limit=5)
web_search(query="Google News \"AI agents\" OR \"MCP protocol\" 2026", limit=8)
```

Google News aggregates are especially useful for the "Google News Picks" section of a digest — they surface stories that may not appear in top web search results. News searches generally return the most interesting results when framed as `Google News "<topic>" OR "<related term>" <date>`.

### Approach A: Direct Parallel Research (fast, ≤10 searches)
Best for single-session cron runs where subagent overhead isn't warranted. Run everything from the parent session:

**Phase 1 — Broad parallel search:**
```
web_search(query="Microsoft Copilot Studio new features 2026", limit=5)
web_search(query="NousResearch Hermes Agent GitHub releases", limit=5)
web_search(query="OpenRouter free models new 2026", limit=5)
web_search(query="MCP Model Context Protocol new servers tools 2026", limit=5)
web_search(query="Google News \"Copilot Studio\" OR \"AI agents Microsoft\"", limit=8)
# ... up to ~7-8 parallel searches
```
Batch all independent searches into a single turn. The runtime executes independent calls concurrently.

**Phase 2 — Tier-2 deep dives:**
After reviewing search results, `web_extract` the 3-5 most promising URLs for full content. Run additional tier-2 searches to fill gaps.

**Phase 3 — Compile & deliver:**
Write digest to temp file, then pipe through send script.

### Approach B: Subagent Delegation (slower, parallel)
Use when research spans many independent domains and you want to keep the parent context uncluttered.

```
delegate_task(tasks=[
    {"goal": "Search for [Topic A] news. Find 3-5 developments with URLs.", "toolsets": ["web", "search"]},
    {"goal": "Search for [Topic B] news. Find 3-5 developments with URLs.", "toolsets": ["web", "search"]},
    {"goal": "Search for [Topic C] news. Find 3-5 developments with URLs.", "toolsets": ["web", "search"]},
])
```

**Pitfall:** `max_concurrent_children` defaults to 3. Subagents work in the background — you don't see results until they finish independently.

### 2. Direct API Research (parent session)
Run these in parallel while subagents work:

**GitHub releases:**
```bash
curl -s "https://api.github.com/repos/{owner}/{repo}/releases?per_page=5" | \
  python3 -c "import sys,json; [print(f'{r[\"tag_name\"]} | {r[\"published_at\"]}') for r in json.load(sys.stdin)[:5]]"
```

**OpenRouter models:**
```bash
curl -s "https://openrouter.ai/api/v1/models" | \
  python3 -c "import sys,json; models=json.load(sys.stdin)['data']; free=[m for m in models if m.get('pricing',{}).get('prompt')=='0']; print(f'{len(free)} free models'); [print(f'  {m[\"name\"]} ({m[\"id\"]})') for m in free[:10]]"
```

**MCP docs search:**
```
mcp_microsoft_learn_microsoft_docs_search(query="Copilot Studio new features 2026")
```

### 3. Compile Digest
- Format: `═══` headers, `##` sections, `•` bullet points
- Every bullet needs a source URL
- No fabricated dates or releases
- Concise and actionable

### 4. Deliver
Option A — pre-built script (preferred):
```bash
cat << 'DIGEST_EOF' | python scripts/send_digest.py
[full digest]
DIGEST_EOF
```

Option B — write_file + pipe redirect (fallback when heredoc gets false-positive errors):
```bash
# Step 1: write digest using the write_file tool (agent session, not shell)
# Step 2: pipe file to send script
python "C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/scripts/send_digest.py" < "C:/path/to/cache/digest_tmp.txt"
```

Option C — inline smtplib (see main SKILL.md email pattern)

### 5. Output
Always output the digest in the final response for conversation visibility.
