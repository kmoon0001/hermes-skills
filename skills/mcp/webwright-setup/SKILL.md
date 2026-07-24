---
name: webwright-setup
description: "Webwright (Microsoft Research) browser agent setup on Windows with OpenRouter free models — install, configure, and run Copilot Studio automation tasks via code-as-action framework"
version: 1.0.0
author: Hermes Agent
platforms: [windows]
---

# Webwright Setup (Windows + OpenRouter)

Webwright is a Microsoft Research open-source browser agent framework (github.com/microsoft/webwright) that uses code-as-action — an LLM writes Playwright Python scripts to interact with web pages. Achieves 86.7% on real-website benchmarks.

## Prerequisites

- Python 3.10+
- Git
- An OpenRouter API key (free models available)

## Installation

```bash
cd /d/my\ agents\ copilot\ studio
git clone https://github.com/microsoft/webwright.git
cd webwright
python3 -m venv ww_venv
source ww_venv/Scripts/activate
pip install -e .
playwright install chromium
```

## Configuration Files

All configs go in `webwright/src/webwright/config/`.

### 1. OpenRouter Free Model Config (`model_openrouter_free.yaml`)

```yaml
model:
  model_class: openrouter
  model_name: openrouter/free
  openrouter_endpoint: https://openrouter.ai/api/v1/chat/completions
  provider_require_parameters: false
```

Note: `provider_require_parameters: false` is required for free models (they don't support strict JSON schema).

### 2. Windows Local Browser Override (`ww_win_local.yaml`)

```yaml
environment:
  browser_mode: local_launch
  headless: true
  launch_args: ["--no-sandbox", "--disable-gpu"]
```

This overrides `local_browser.yaml`'s default CDP mode (port 9222) to use Playwright's bundled Chromium.

## Running

```bash
set -a && source /path/to/.env  # provides OPENROUTER_API_KEY
cd /d/my\ agents\ copilot\ studio/webwright
source ww_venv/Scripts/activate
python -m webwright.run.cli main \
  -c base.yaml -c local_browser.yaml -c ww_win_local.yaml -c model_openrouter_free.yaml \
  -t "Your task description" \
  --task-id task_name \
  -o outputs
```

### Key Flags

| Flag | Description |
|------|-------------|
| `-c` | Config file(s) from `src/webwright/config/` (stackable). Order matters — later files override earlier. |
| `-t` | Natural language task instruction |
| `--task-id` | Output subfolder name |
| `--start-url` | Optional starting URL |
| `-o` | Output directory |
| `--debug` | Launch headed local Playwright with devtools |

## Output

Each run creates a folder under `outputs/` with:
- `trajectory.json` — step-by-step actions and results
- `final_script.py` — generated reusable Playwright script
- `step_<NNNN>.png` — screenshots at each step (in live browser mode)
- `plan.md` — the agent's plan for the task

## Available Free Models on OpenRouter

| Model | ID | Best For |
|-------|-----|----------|
| Auto-router | `openrouter/free` | Picks best available free model |
| Qwen3 Coder 480B | `qwen/qwen3-coder:free` | Code-generating tasks |
| Owl Alpha | `openrouter/owl-alpha` | Agentic browsing |
| Nemotron 3 Super 120B | `nvidia/nemotron-3-super-120b-a12b:free` | Reasoning |
| Nemotron 3 Ultra 550B | `nvidia/nemotron-3-ultra-550b-a55b:free` | Large reasoning |
| Poolside Laguna M.1 | `poolside/laguna-m.1:free` | Code tasks |
| GPT-OSS-120B | `openai/gpt-oss-120b:free` | General |
| Hermes 3 405B | `nousresearch/hermes-3-llama-3.1-405b:free` | General |

## Pitfalls

1. **Windows browser path** — `local_browser.yaml` defaults to CDP mode (port 9222). On Windows without a running Chrome CDP session, use `ww_win_local.yaml` to switch to `local_launch` mode with Playwright's bundled Chromium.
2. **`provider_require_parameters`** — Must be `false` for free models. Default OpenRouter config sets it `true` which causes 404 errors from free model providers.
3. **Config stacking** — `ww_win_local.yaml` MUST be stacked AFTER `local_browser.yaml`: `-c base.yaml -c local_browser.yaml -c ww_win_local.yaml -c model_openrouter_free.yaml`
4. **.env file** — Webwright reads `OPENROUTER_API_KEY` from environment. Use `set -a && source .env` to load from a `.env` file.
5. **Async event loop** — Webwright fails with "no running event loop" if run inside an active asyncio event loop. Always run fresh.
6. **CDP integration with existing Chrome** — Use `local_browser.yaml` (sets `browser_mode: local_cdp`) with `LOCAL_BROWSER_CDP_URL=http://127.0.0.1:9223`. This connects to the same authenticated Chrome that Playwright uses. The `.env` file is at `/d/my agents copilot studio/.env` (parent of webwright dir).
7. **Copilot Studio SPA timing** — The SPA needs 15-20s to render. Webwright's LLM may timeout before the SPA loads. Consider using `await page.wait_for_timeout(20000)` in the generated scripts.
8. **Slower than direct Playwright** — Webwright generates Playwright scripts via LLM at each step, adding ~5-10s per step. For repeatable tasks (like topic injection), use the direct Playwright skill (`cdp-instructions-injection`) instead.
