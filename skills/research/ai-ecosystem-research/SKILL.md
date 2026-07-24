---
name: ai-ecosystem-research
description: "Research AI ecosystem developments (models, protocols, tools) for digests and summaries. Primary approach: programmatic APIs over web search."
version: 1.0.0
author: hermes-agent
metadata:
  hermes:
    tags: [research, AI, models, MCP, OpenRouter, digest, news]
---

# AI Ecosystem Research

Gather AI ecosystem news (new models, protocol updates, tool releases, pricing changes) for digests, summaries, or weekly reports. Designed for recurring use — not one-off searches.

## Core Principle: Hermes Managed Tools First, APIs Second

**Primary path: use Hermes managed web tools (`web_search`, `web_extract`).** These route through Firecrawl or similar backends that handle CAPTCHAs, JS rendering, and bot detection automatically. Batch all independent searches into a single turn for concurrent execution. Reserve raw curl for structured data endpoints (APIs).

**Use programmatic APIs for structured data** — GitHub API for releases, OpenRouter API for model catalogs, provider APIs for versioned changelogs. APIs return cleaner data than HTML when you need machine-readable output.

**Fallback order:**
1. Hermes `web_search` + `web_extract` — for general multi-domain research (works in cron contexts, no CAPTCHA fighting)
2. Direct API calls (GitHub API, OpenRouter API) — for structured data: releases, model catalogs, pricing
3. `curl` + `grep` on target websites — for blogs without APIs
4. Browser automation — only when interaction is required (forms, JS-rendered content, or web_extract fails)
5. Raw search engines — last resort. These still get blocked by CAPTCHAs; prefer (1) through (4)

## API Reference

### OpenRouter

**Model catalog** — all models with timestamps, pricing, capabilities:
```bash
curl -sL "https://openrouter.ai/api/v1/models" | python3 -c "
import json, sys, time
data = json.load(sys.stdin)
for m in data['data']:
    created = time.strftime('%Y-%m-%d', time.gmtime(m.get('created', 0)))
    print(f'{m[\"name\"]} | {m[\"id\"]} | {created}')
"
```

**Filter recent models** (past N days):
```python
import time
cutoff = int(time.time()) - (N * 86400)
recent = [m for m in models if m.get('created', 0) >= cutoff]
```

**Find free models:**
```python
free = [m for m in models if ':free' in m.get('id', '')]
```

**Blog** — https://openrouter.ai/blog (no API; use curl + grep or browser)

### GitHub API (no auth needed for public repos)

**New repos by topic + date:**
```bash
curl -sL "https://api.github.com/search/repositories?q=topic:MODEL_CONTEXT_PROTOCOL+created:>YYYY-MM-DD&sort=stars&order=desc&per_page=10"
```

**Spec/protocol issues and PRs:**
```bash
curl -sL "https://api.github.com/search/issues?q=repo:OWNER/REPO+created:>YYYY-MM-DD&sort=created&order=desc&per_page=10"
```

**SDK releases:**
```bash
curl -sL "https://api.github.com/repos/OWNER/REPO/releases?per_page=5"
```

**Recent commits:**
```bash
curl -sL "https://api.github.com/repos/OWNER/REPO/commits?since=YYYY-MM-DDTHH:MM:SSZ&per_page=10"
```

### MCP-Specific Endpoints

| What | Endpoint |
|------|----------|
| MCP org repos | `https://github.com/modelcontextprotocol` |
| MCP spec issues | `repo:modelcontextprotocol/modelcontextprotocol` |
| MCP server registry | `repo:modelcontextprotocol/registry` |
| MCP official servers | `repo:modelcontextprotocol/servers` |
| Python SDK releases | `repo:modelcontextprotocol/python-sdk` |
| TypeScript SDK releases | `repo:modelcontextprotocol/typescript-sdk` |

## Workflow

1. **Parallel data gathering** — fire off all API calls simultaneously (they're independent)
2. **Timestamp filtering** — convert Unix timestamps to dates, filter to target window
3. **Deduplicate** — same story may appear in multiple sources
4. **Categorize** — group by theme (new models, free tier changes, protocol updates, tool releases)
5. **Format** — bullet list with URLs, concise descriptions, dates

## Output Format (for digests)

```markdown
## Category Name (Date Range)

### Item Title (Date)
- One-line description
- https://url-to-source
```

## Pitfalls

- **CAPTCHAs on search engines**: Don't retry. Switch to Hermes managed tools or APIs immediately.
- **GitHub API rate limits**: 60 req/hr unauthenticated. Batch parallel calls, don't loop.
- **Unix timestamp conversion**: Use `time.gmtime()` not `time.localtime()` for consistency.
- **OpenRouter API `created` field**: Unix timestamp, not ISO string. Convert explicitly.
- **Blog content**: No API; use `curl -sL URL | grep -oiP 'pattern'` for quick extraction, or browser for JS-rendered content.
