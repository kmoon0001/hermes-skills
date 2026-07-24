# API Endpoints & Patterns — June 2026 Session

## OpenRouter API

### Base URL
`https://openrouter.ai/api/v1/`

### /models endpoint
Returns full model catalog. Key fields:
- `id` — model identifier (e.g. `openrouter/fusion`)
- `name` — display name
- `created` — Unix timestamp (seconds since epoch)
- `pricing.prompt` — cost per token (string, e.g. "0.000005")
- `pricing.completion` — cost per output token
- `:free` suffix in `id` indicates free tier

### Notable models discovered (June 2026)
| Model | ID | Date | Free? |
|-------|-----|------|-------|
| Sakana: Fugu Ultra | sakana/fugu-ultra | Jun 24 | No |
| Google: Nano Banana 2 | google/gemini-3.1-flash-image | Jun 18 | No |
| Google: Nano Banana Pro | google/gemini-3-pro-image | Jun 18 | No |
| Cohere: North Mini Code | cohere/north-mini-code:free | Jun 17 | Yes |
| Z.ai: GLM 5.2 | z-ai/glm-5.2 | Jun 16 | No |
| OpenRouter: Fusion | openrouter/fusion | Jun 12 | Custom |

### Fusion model
Multi-model deliberation system. 1M context window. Pricing = "-1" (custom routing).
Expert models analyze in parallel with web search/fetch, then a synthesizer combines results.

## GitHub API — MCP Ecosystem

### Key repositories
| Repo | Purpose |
|------|---------|
| modelcontextprotocol/modelcontextprotocol | Core spec, issues, PRs |
| modelcontextprotocol/servers | Official MCP servers |
| modelcontextprotocol/registry | MCP server registry |
| modelcontextprotocol/python-sdk | Python SDK |
| modelcontextprotocol/typescript-sdk | TypeScript SDK |

### Search pattern for new MCP servers
```
GET /search/repositories?q=topic:model-context-protocol+created:>YYYY-MM-DD&sort=stars&order=desc
```

### Search pattern for spec changes
```
GET /search/issues?q=repo:modelcontextprotocol/modelcontextprotocol+created:>YYYY-MM-DD&sort=created&order=desc
```

### Notable MCP developments (June 2026)
- **2026-07-28 RC** — Stateless HTTP protocol (no initialize handshake)
- **Python SDK v2.0.0a3** — Third alpha, stateless negotiation
- **TS SDK server-legacy v2.0.0-alpha.3** — Frozen v1 SSE + OAuth helpers
- **Financial Services Interest Group** — New working group charter
- **MCP conformance runner** — Standardized compliance testing

### Notable new MCP servers (by stars)
| Repo | Stars | Description |
|------|-------|-------------|
| aresyn/codex-control-plane-mcp | 203 | Durable control plane for Codex Desktop |
| PerfectXM/mcp-db-server | 96 | Multi-DB stateless server |
| badchars/darknet-mcp-server | 67 | 66-tool dark web intelligence |
| abluva-research/mcp-trust-plane | 60 | Data security plane |

## Curl Patterns

### Quick blog content extraction
```bash
curl -sL "https://openrouter.ai/blog" | grep -oiP '<h[23][^>]*>[^<]+|<time[^>]*>[^<]+'
```

### GitHub release parsing
```bash
curl -sL "https://api.github.com/repos/OWNER/REPO/releases?per_page=5" | \
  python3 -c "import json,sys; [print(f'{r[\"tag_name\"]} | {r[\"published_at\"][:10]}') for r in json.load(sys.stdin)]"
```
