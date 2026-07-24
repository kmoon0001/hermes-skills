# OmniRoute Quick Reference (verified 2026-07-13, v3.8.46)

## Install
```bash
npm install -g omniroute        # node >=22; takes ~6 min (large, native deps). BE PATIENT.
which omniroute                 # ~/AppData/Roaming/npm/omniroute on Windows
omniroute --version             # 3.8.46
```

## Run (background)
```bash
omniroute                       # dashboard + API on :20128; Ctrl+C to stop
# Dashboard: http://localhost:20128   API: http://localhost:20128/v1
```

## VERIFY — prove the API serves (banner lies if Next.js crashed)
```bash
curl -s --noproxy '*' -w "\nHTTP %{http_code}\n" http://127.0.0.1:20128/v1/models
# HTTP 200 + JSON list (99 models: auto/best-coding, auto/best-reasoning, auto/best-fast, ...)
```
- `--noproxy '*'` from git-bash (proxy env => HTTP 000).
- If still `000`: `netstat -an | grep 20128` (expect LISTENING); tail
  `~/.omniroute/logs/application/app.log` for `uncaughtException`. A startup crash there
  kills the front-end but the WS ports (20129/20131) survive — restart clean.

## ROUTE — completion needs a provider
```bash
curl -s --noproxy '*' -X POST http://127.0.0.1:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"hi"}]}'
```
- **HANGS with zero providers configured** — no route target. Fix: dashboard → connect a
  free provider (OAuth) or paste an API key. Catalog lists without keys; completion does not.

## MCP server
```bash
claude mcp add omniroute --type http --url http://localhost:20128/api/mcp/stream
# 94 tools / 30 scopes. 401 without dashboard API key (set OMNIROUTE_API_KEY).
```

## Security
- `~/.omniroute/.env` ships `INITIAL_PASSWORD=CHANGEME` (log warns). Change before remote use.
- Config dir is a credential store (holds provider keys). Don't read `.env`; use `.env.example`.

## Point a coding tool at it
Set the tool's base URL to `http://localhost:20128/v1` and any key from the dashboard.
Works with Claude Code, Codex, Cursor, Cline, Copilot, Antigravity, OpenCode, etc.
