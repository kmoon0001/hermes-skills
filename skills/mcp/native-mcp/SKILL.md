---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxx...xxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Microsoft Learn MCP Server

Microsoft Learn provides an official remote Streamable HTTP MCP endpoint with no authentication required:

```yaml
mcp_servers:
  microsoft-learn:
    url: "https://learn.microsoft.com/api/mcp"
```

Hermes CLI setup pattern:

```bash
# Microsoft Learn docs say this endpoint requires no auth.
printf 'n\nY\n' | hermes mcp add microsoft-learn --url https://learn.microsoft.com/api/mcp
hermes mcp test microsoft-learn
```

Expected discovered tools include:

- `microsoft_docs_search`
- `microsoft_docs_fetch`
- `microsoft_code_sample_search`

After adding/reconfiguring, run `/reload-mcp` or start a fresh Hermes session before expecting the MCP tools to appear in the conversation tool list.

### NotebookLM MCP Server

[notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli) exposes 39 tools (notebook CRUD, source add/query, studio artifacts, research, batch ops) via Google NotebookLM's internal APIs.

#### Install

```bash
uv tool install notebooklm-mcp-cli
```

Installs two executables: `nlm` (CLI) and `notebooklm-mcp` (MCP server).

#### Add to Hermes (Windows)

**Critical: use Windows-native paths**, not MSYS paths:

```bash
hermes mcp add notebooklm-mcp --command "C:\Users\kevin\.local\bin\notebooklm-mcp.exe"
```

MSYS paths like `/c/Users/kevin/.local/bin/notebooklm-mcp` will fail with `WinError 2 (file not found)` because the Hermes MCP client's subprocess runner uses Windows PATH resolution, not MSYS.

On success, expect 39 tools to auto-discover (notebook_query, source_add, studio_create, research_start, etc.). Enable all with `Y` when prompted. For non-interactive install, pipe it:

```bash
printf "Y\n" | hermes mcp add notebooklm-mcp --command "C:\\Users\\kevin\\.local\\bin\\notebooklm-mcp.exe"
```

#### Authentication (Cookie-Based)

NotebookLM uses undocumented internal APIs that require browser cookies from an authenticated session:

**Automated flow (recommended):**
```bash
nlm login
```
This launches Chrome via CDP and waits 300s for you to sign in to your Google account. After sign-in completes in the browser window, the cookies are saved and the MCP tools become operational.

**Manual flow (when automated Chrome launch fails):**
1. Open Chrome, navigate to `https://notebooklm.google.com` and sign in
2. Open DevTools (F12) → Application → Cookies → `notebooklm.google.com`
3. Copy the Cookie header value
4. Save via: `nlm login --manual --file <cookie_file>`

#### Windows Chrome Caveat

When driving Chrome programmatically (e.g. launching `notebooklm.google.com` from the MCP setup), Chrome's `Chrome_WidgetWin_1` window class drops background PostMessage for keyboard combos. Use `delivery_mode:"foreground"` for `hotkey` and `type_text` actions on Chrome address bars. The UIA ValuePattern `set_value` works for the address bar text but does NOT trigger navigation — you need a pixel-level click → type → Enter sequence.

#### Generate JSON config for other tools

To get the MCP server JSON snippet for Claude Code, Cursor, or other MCP clients:

```bash
printf "1\n1\n" | nlm setup add json
```

This prints the `{"notebooklm-mcp": {"command": "uvx", "args": ["--from", "notebooklm-mcp-cli", "notebooklm-mcp"]}}` config without needing to parse it from the interactive menu.

#### Windows Chrome Address Bar Navigation (Pitfall)

When `nlm login` opens Chrome, the UIA ValuePattern `set_value` on the address bar sets the text but does NOT trigger navigation — Chrome's `Chrome_WidgetWin_1` class drops background PostMessage for keyboard combos. The working workaround:

1. Click on the address bar via **pixel coordinates** with `delivery_mode: "foreground"`
2. Use `hotkey` with `delivery_mode: "foreground"` for `ctrl+a` (select all)
3. Type the URL with `type_text` and `delivery_mode: "foreground"`
4. Press `enter` with `delivery_mode: "foreground"`

This ensures the keystrokes reach Chrome's input handler.

#### Notebook Creation & Research Workflow

Once authenticated, you can create notebooks and populate them with sources:

```bash
# Create notebook
nlm notebook create "My Topic"

# Add direct URLs (repeatable -u flag, max ~7 per call)
nlm source add <notebook-id> -u "https://example.com" -u "https://other.com" --wait

# Deep web research (finds ~90 sources in ~5 min)
nlm research start "research query" -n <notebook-id> --mode deep --auto-import

# Check sources
nlm notebook get <notebook-id>

# Delete broken sources (404s, etc.)
nlm source delete <notebook-id> <source-id-1> <source-id-2> --confirm
```

The `--auto-import` flag on `research start` waits for completion and imports automatically. Without it, run `nlm research import <notebook-id> <task-id>` separately.

#### Slide Deck Generation

Generate a presentation from notebook sources:

```bash
nlm slides create <notebook-id> --confirm
```

Returns an `artifact_id` (e.g., `48e1a537-...`). Check generation status:

```bash
nlm studio status <notebook-id> --artifact-id <artifact-id>
```

Status goes from `"unknown"` (processing) to `"completed"` with a download URL.

#### Download Artifacts

Download completed slide decks (or any studio artifact) to a file:

```bash
nlm download slide_deck <notebook-id> <artifact-id> --output "C:\Users\kevin\Desktop\my-deck.pptx"
```

Supported artifact types: `audio`, `video`, `report`, `mind_map`, `slide_deck`, `infographic`, `data_table`, `quiz`, `flashcards`.

For quizzes and flashcards, optionally specify output format:
```bash
nlm download quiz <notebook-id> <artifact-id> --output-format markdown
```

For slide decks, optionally specify format:
```bash
nlm download slide_deck <notebook-id> <artifact-id> --slide-deck-format pptx
```

#### Quick verification

```bash
# Check auth status
nlm login --check

# List notebooks
nlm notebook list
```

#### Research Knowledge Base Workflow

For the end-to-end pattern of building topic-specific research notebooks with curated + auto-discovered sources, deep research, and parallel queries for grounded answers, see `references/notebooklm-research-workflow.md` under this skill.

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  notebooklm-mcp:
    command: "C:\\Users\\kevin\\.local\\bin\\notebooklm-mcp.exe"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Cross-Agent Shared Memory Graph (the `@modelcontextprotocol/server-memory` server)

You can make TWO agents (e.g. Hermes + Kiro) share ONE knowledge graph by pointing both of their `memory` MCP servers at the same file via `MEMORY_FILE_PATH`. This was verified end-to-end on Windows (2026-07-12). Gotchas that will bite without warning:

**GOTCHA 1 — modern server version uses JSONL, not `memory.json`.** Server versions ~2025+ read `MEMORY_FILE_PATH` and do `readFile` → `data.split("\n")` → `JSON.parse` **per line** (it expects `memory.jsonl`). A legacy single-object `memory.json` (`{"entities":[...],"relations":[...]}`) fails with:
```
Expected property name or '}' in JSON at position 1 (line 1 column 2)
```
That error is the server's *internal read failing*, not the file being unreadable. Fix: store the graph as **JSONL** — one JSON object per line, each line tagged `{"type":"entity",...}` or `{"type":"relation",...}`. Seed recipe:
```python
import json
ents=[{"name":"BotX","entityType":"copilot_agent","observations":["Bot ID: ...","Env: ..."]}]
rels=[{"from":"BotX","to":"GatewayY","relationType":"evaluated_via"}]
lines=[json.dumps({"type":"entity",**e}) for e in ents]+[json.dumps({"type":"relation",**r}) for r in rels]
open("C:/Users/kevin/.kiro/memory/memory.jsonl","w").write("\n".join(lines)+"\n")
```
Verify valid JSONL: `python3 -c "import json;[json.loads(l) for l in open(path) if l.strip()]"`.

**GOTCHA 2 — `env: {}` means the WRONG file.** If a config declares `"memory": {"env": {}}` (or omits `MEMORY_FILE_PATH`), the server falls back to `join(dirname(serverEntryPoint), 'memory.jsonl')` — i.e. a file **inside the npx cache dir** (`...\npm-cache\_npx\...\server-memory\memory.jsonl`), NOT your intended shared path. Both agents then write to *different* cache files → no sharing. Always set `MEMORY_FILE_PATH` explicitly and to the **same absolute path** on both sides.

**GOTCHA 3 — absolute path + forward slashes work.** Use `MEMORY_FILE_PATH: "C:/Users/kevin/.kiro/memory/memory.jsonl"` (forward slashes are fine on Windows for this server's `path.isAbsolute` check). Backslashes also worked in testing; either is accepted.

**Verified setup recipe (Hermes + Kiro, both reading/writing one graph):**
```yaml
# Hermes: append to ~/.hermes/config.yaml
mcp_servers:
  shared_memory:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-memory"]
    env:
      MEMORY_FILE_PATH: "C:/Users/kevin/.kiro/memory/memory.jsonl"
    timeout: 120
```
```json
// Kiro: ~/.kiro/settings/mcp.json  (set the SAME path; do NOT leave env: {})
"memory": { "env": { "MEMORY_FILE_PATH": "C:/Users/kevin/.kiro/memory/memory.jsonl" }, "disabled": false, ... }
```
After editing, **restart both agents** (MCP servers load at startup) for the new `mcp_shared_memory_*` tools to appear.

**End-to-end proof (do this once to confirm wiring):** spawn the server via `cmd.exe /c npx -y @modelcontextprotocol/server-memory` with the env var set, then `initialize` → `tools/list` (expect 9 tools: read_graph, create_entities, create_relations, add_observations, …) → `read_graph` (should return your seeded entities) → `create_relations` (should persist to the file). If `read_graph` returns `isError:true` with "Expected property name…", you seeded `memory.json` not `memory.jsonl` (GOTCHA 1).

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)
