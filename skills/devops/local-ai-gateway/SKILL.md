---
name: local-ai-gateway
description: "Local AI gateway / universal LLM proxy for coding-agent token & quota plumbing — pool free API keys, auto-fallback across providers, compress tokens, expose one OpenAI-compatible endpoint. Covers OmniRoute install/run/verify and the class of tools it represents."
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [ai-gateway, llm-proxy, omniroute, token-savings, rate-limit, free-api, coding-agent]
    category: devops
---

# Local AI Gateway (class: OmniRoute and peers)

A **local AI gateway** sits between your coding tools (Claude Code, Codex, Cursor, Cline,
Copilot) and the model providers. Its job: pool free/paid API keys across many providers,
auto-fallback when one hits a quota or rate limit, compress tokens, and expose ONE
OpenAI-compatible endpoint (`/v1`). Point every tool at that endpoint and stop fighting
per-tool quota exhaustion.

This skill documents the class and the concrete OmniRoute instance we run. It is NOT a
replacement for the PowerVA / Power Platform eval path — different purpose (model access
plumbing, not agent evaluation).

## When to use

- User wants to avoid API rate limits / quota exhaustion across coding tools
- User wants to "find free API keys / lanes" and pool them so builds never stall
- User wants token-saving / compression on heavy agent chatter
- User mentions OmniRoute, "omni route", or a "free AI gateway"
- You need one endpoint for many tools instead of per-tool API config

## OmniRoute — install & run (verified v3.8.46, 2026-07-13)

```bash
npm install -g omniroute          # node >=22; binary at ~/AppData/Roaming/npm/omniroute (Win)
omniroute                         # launches dashboard + API on :20128
```
- Dashboard: http://localhost:20128
- API base: http://localhost:20128/v1  (OpenAI-compatible: /v1/models, /v1/chat/completions)
- Config dir: ~/.omniroute/ (storage.sqlite, .env, logs/)
- MCP server: http://localhost:20128/api/mcp/stream — 94 tools / 30 scopes. Returns **401
  without** the dashboard API key (expected). Pass `OMNIROUTE_API_KEY` / `--api-key`.

### Verify it actually serves (don't trust the banner)

The "OmniRoute is running!" banner appears even if the Next.js front-end crashes. **Prove
the API responds before declaring success:**

```bash
curl -s --noproxy '*' -w "\nHTTP %{http_code}\n" http://127.0.0.1:20128/v1/models
# Expect HTTP 200 and a JSON model list (99 models incl. auto/best-coding, auto/best-reasoning)
```
Use `--noproxy '*'` from git-bash (proxy env can cause HTTP 000). If `curl` still returns
`000`, confirm the port is listening with `netstat -an | grep 20128` and check
`~/.omniroute/logs/application/app.log` for `uncaughtException`.

### Gotcha: provider required before routing works

With **zero providers configured**, `/v1/chat/completions` **hangs** (no route target).
You MUST connect at least one provider in the dashboard first:
- OAuth sign-in to a free provider (Pollinations, Groq, etc.), or
- paste an API key (provider settings → add key).

The catalog (`/v1/models`) lists models without any key — but completion needs a live route.

### Gotcha: default management password

`~/.omniroute/.env` ships `INITIAL_PASSWORD=CHANGEME` (the log warns about it). Fine for
localhost-only. **Change before any remote/exposed use.** The `.env` is secret-guarded — read
`.env.example` instead of `.env` for structure.

## Class characteristics (what to expect from any gateway in this class)

- **Multi-provider catalog** (100s of providers, many free tiers) exposed as one model list
- **Auto-fallback tiers**: Subscription → API Key → Cheap → Free; switches in ms on quota-out
- **Token compression**: RTK + Caveman stacks cut 15–95% of eligible tokens on tool-heavy traffic
- **Routing strategies**: `auto/best-coding`, `auto/best-reasoning`, `auto/best-fast`, etc.
- **Resilience**: per-provider circuit breaker, cooldown, lockout; semantic cache
- **Protocols**: MCP server, A2A, built-in eval framework
- **Self-hostable**: npm / Docker / Electron desktop (Win/Mac/Linux)

## Security notes

- Localhost-only by default. Never expose :20128 to the network with the default password.
- Gateway holds your provider API keys — treat its config dir as credential store.
- This is a *local model-access layer*; it does not touch Copilot Studio agents or their eval.

## Reference Files

- `references/omniroute-quickref.md` — OmniRoute install/verify/route recipe + the exact
  verification curl and the no-provider-hang gotcha.
