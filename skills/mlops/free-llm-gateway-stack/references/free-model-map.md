# Free LLM Gateway — Reference (researched Jul 2026)

## OmniRoute (diegosouzapw/OmniRoute) — verified instance
- License: MIT. Install: `npm install -g omniroute` (node ≥22). Binary: `%APPDATA%\npm\omniroute`.
- Runs locally on **port 20128** (dashboard + OpenAI-compatible `/v1` API). Config dir: `~/.omniroute/` (storage.sqlite, .env, logs/application/app.log).
- Verified live: `GET /v1/models` → 99 models incl `auto/best-coding`, `auto/best-reasoning`, `auto/best-fast`, `auto/best-vision`, `auto/best-chat` (all 1M ctx).
- 236 providers catalogued, 90+ with a free tier, 11 free-forever.
- Features: 4-tier auto-fallback (Subscription→API Key→Cheap→Free), 18 routing strategies, RTK+Caveman token compression (15–95%), MCP server (/api/mcp/stream, 94 tools/30 scopes, 401 without key), A2A, eval framework, circuit-breaker.
- FIRST-LAUNCH CRASH quirk: fresh launch can throw `uncaughtException: file data stream has unexpected number of bytes`; Next.js routes time out while core WS (20129) still answers 404. Relaunch fixes it.

## Best free model → service map (for our coding/clinical-dev work)
| Purpose | Best free model | Service |
|---|---|---|
| Heavy agentic coding | Qwen3 Coder 480B (1M ctx) | OpenRouter |
| Reasoning codegen | DeepSeek V4 Flash (1M ctx) | OmniRoute native (opencode node) |
| | Nemotron 3 Super 120B (1M) | OpenRouter + opencode |
| Reasoning/research/orchestration | Nemotron 3 Ultra 550B (1M, frontier) | OpenRouter |
| | Tencent Hy3 295B (256K, strong agentic) | OpenRouter (Hermes's current model) |
| | Poolside Laguna M.1 (256K, coding agent) | OpenRouter |
| Fast / high-volume chatter | Gemma 4 31B (262K, vision, quality 65) | OpenRouter |
| | Llama 4 Scout | OmniRoute native (duckduckgo-web) |
| Free-forever fallback | GPT-5-class via Pollinations | OmniRoute native (no key) |
| Vision / doc OCR | Nemotron Nano 12B VL | NVIDIA build.nvidia.com |
| | Gemma 4 31B | OpenRouter |

## Free nodes to keep in the stack
- OmniRoute native free-forever (no key): Pollinations (GPT-5-class), LongCat (50M tok/day), opencode (DeepSeek V4 Flash, Nemotron 3 Super, Qwen3.6 Plus), duckduckgo-web (Llama 4 Scout), auggie / theoldllm / veoaifree.
- OpenRouter free (one free key unlocks all): nvidia/nemotron-3-ultra-550b:free, tencent/hy3:free, qwen/qwen3-coder:free, poolside/laguna-m.1:free, google/gemma-4-31b-it:free, openai/gpt-oss-120b:free.
- NVIDIA build.nvidia.com free (separate key, user explicitly keeps): Llama Nemotron Ultra / Nemotron 3 family (70+ models free forever), Nemotron Nano 12B VL.

## Stacking recipe for longest free run
1. Primary = OmniRoute gateway (pools all free quotas into one endpoint).
2. Inside it: keep OpenRouter + NVIDIA as separate nodes (OmniRoute spills between them on rate-limit).
3. Routing combos: best-coding → Qwen3-Coder→DeepSeek V4 Flash→Nemotron 3 Super→Pollinations; best-reasoning → Nemotron 3 Ultra→Hy3→Laguna M.1; best-fast → Gemma 4→Llama 4 Scout.
4. Fallback chain = Subscription→API Key→Cheap→Free (all free here → loops free lanes forever).
5. Token compression (RTK + Caveman) ON — multiplies every free quota's effective length.
