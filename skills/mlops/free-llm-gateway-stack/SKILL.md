---
name: free-llm-gateway-stack
description: Evaluate, install, and configure a local free LLM gateway/router (OmniRoute-class) to pool free API providers with auto-fallback and token compression — so coding agents run on the most powerful free models without paying. Use when the user wants free model access, rate-limit avoidance, key fallback, or token savings; or asks to "stack free models" / "never stop coding" / use a free AI gateway as primary; or names a tool (OmniRoute, LiteLLM, etc.) and asks if it's usable/installable.
---

# Free LLM Gateway Stack

## When to use
- User wants free model access for coding agents (Claude Code, Codex, Cursor, Cline, Copilot) without paying.
- User asks to pool free API keys, add fallback providers, avoid rate limits, or save tokens.
- User says "stack free models", "never stop coding", "free AI gateway", or names a tool and asks if it's usable/installable.
- Recurring user pattern observed: "research a free tool, install it, tell me if it's usable for our stack."

## When NOT to use
- Copilot Studio AGENT EVALUATION. That goes through the PowerVA gateway (X-CCI headers + MSAL eval token). A local model gateway is for model access / coding-agent plumbing only — keep the eval boundary intact. Do not point production eval at it.

## Workflow (research → install → verify → assess)
1. RESEARCH (authoritative only): GitHub repo + official site + `llm.txt` if present. Confirm: license (MIT = safe), what it actually does (key pooling, fallback tiers, rate-limit handling, token compression, eval). Don't trust marketing copy — verify the feature list against repo docs.
2. INSTALL: for node tools `npm install -g <pkg>` (check `node -v` ≥ required, e.g. ≥22). Note the binary path (`which <pkg>` / `%APPDATA%\npm`). Don't reinstall what already exists.
3. RUNTIME VERIFY (the part people skip — do it):
   - Launch the server in background.
   - Probe loopback with `curl -s -m 8 --noproxy '*' http://127.0.0.1:<port>/v1/models` OR `python3 -c "urllib.request.urlopen(...)"`. `--noproxy '*'` matters on Windows.
   - Confirm the model catalog responds (HTTP 200 + JSON). Count models.
   - If it hangs, see Pitfalls before concluding it's broken.
4. CONNECT FREE PROVIDERS: open the dashboard, sign in via OAuth or paste a free API key. Without ≥1 provider, chat completion will hang (nothing to route to).
5. MAP BEST FREE MODELS: see references/free-model-map.md for the per-service table. Pick by purpose (coding / reasoning / fast / vision).
6. CONFIGURE ROUTING: set `auto/best-*` combos, fallback chain (Subscription→API Key→Cheap→Free), and turn ON token compression (RTK + Caveman) — this is the real "run longest free" lever.
7. ASSESS & REPORT: state clearly (a) is it usable, (b) is it installed, (c) what's needed to make it route, (d) which models you'd point at it. Lead bottom-line-first (user preference: no verbose preamble).

## Pitfalls
- OmniRoute FIRST-LAUNCH CRASH: a fresh `omniroute` launch can throw `uncaughtException: file data stream has unexpected number of bytes` and the Next.js front-end routes (everything except /health, which 404s) time out — even though netstat shows LISTENING. The WS port (20129) may still respond (404), confirming the core is up. FIX: kill the process and relaunch; the second launch serves `/v1/models` with HTTP 200. Always retry a launch before concluding it's broken.
- `/v1/chat` hangs with no provider key — not a crash, just no route. Connect a provider first.
- MCP endpoint (`/api/mcp/stream`) returns 401 until you pass the dashboard API key — expected, not a bug.
- `.env` management password defaults to `CHANGEME` — fine for localhost, change before any remote/network exposure.
- Free models have rate limits and can be pulled without notice (OpenRouter states this). Auto-fallback + token compression is the mitigation; do NOT point production Copilot Studio eval at this.
- Windows loopback: `curl` without `--noproxy '*'` and some node `fetch` calls can fail even when the server is up. Use python `urllib` or `curl --noproxy '*'`.

## Verification checklist
- [ ] `GET /v1/models` returns HTTP 200 with a non-empty model array
- [ ] `auto/best-coding`, `auto/best-reasoning`, `auto/best-fast` present (1M ctx)
- [ ] At least one provider connected (chat returns non-empty)
- [ ] Dashboard reachable at configured port
- [ ] Token compression enabled

## Support files
- references/free-model-map.md — condensed install/port/endpoint facts + best-free-model-per-service table (researched July 2026).
