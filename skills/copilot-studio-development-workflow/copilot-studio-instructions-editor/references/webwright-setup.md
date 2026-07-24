# Webwright setup for Copilot Studio automation

## Overview

[Webwright](https://github.com/microsoft/webwright) is Microsoft Research's open-source browser agent framework (MIT license, ~1.5k LoC) that gives an LLM a terminal + Playwright to write reusable Python scripts for web tasks. It uses code-as-action instead of coordinate-clicking.

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

## OpenRouter config (free models)

Config at `src/webwright/config/model_openrouter_free.yaml`:
```yaml
model:
  model_class: openrouter
  model_name: qwen/qwen3-coder:free
  openrouter_endpoint: https://openrouter.ai/api/v1/chat/completions
```

## Usage

```bash
export OPENROUTER_API_KEY=<your-key>
python -m webwright.run.cli main \
  -c base.yaml -c model_openrouter_free.yaml \
  -t "Task description" \
  --task-id my_task \
  -o outputs/default
```

## Proven free models for agentic tasks

- `qwen/qwen3-coder:free` (480B) — best for code generation (Playwright scripts)\n- `openrouter/owl-alpha` — designed for agentic browsing\n- `nvidia/nemotron-3-super-120b-a12b:free` — 120B active params, good reasoning\n- `poolside/laguna-m.1:free` — code-focused\n- `qwen/qwen3-next-80b-a3b-instruct:free` — good reasoning\n\n## Windows + local_launch fix\n\nOn Windows, the default `local_browser.yaml` uses `browser_mode: local_cdp` which\nlooks for Chrome at `http://127.0.0.1:9222`. To use Playwright's bundled Chromium instead,\ncreate `src/webwright/config/ww_win_local.yaml`:\n\n```yaml\nenvironment:\n  browser_mode: local_launch\n  headless: true\n  launch_args: [\"--no-sandbox\", \"--disable-gpu\"]\n```\n\nStack it in this ORDER (local_browser.yaml before the Win override):\n\n```bash\nexport OPENROUTER_API_KEY=<your-key>\npython -m webwright.run.cli main \\\n  -c base.yaml -c local_browser.yaml -c ww_win_local.yaml -c model_openrouter_free.yaml \\\n  -t \"Task description\" \\\n  --task-id my_task \\\n  -o outputs/default\n```\n\nKey: `local_browser.yaml` must come BEFORE the Win override so its `environment:`\nsection exists for the override to merge into.\n\n## Provider requirement flag\n\nFree models on OpenRouter rarely support `response_format: json_schema`. The\nOpenRouter config must set `provider_require_parameters: false`:\n\n```yaml\nmodel:\n  model_class: openrouter\n  model_name: openrouter/free\n  openrouter_endpoint: https://openrouter.ai/api/v1/chat/completions\n  provider_require_parameters: false\n```\n\nWithout this, the 404 error means the router skipped free providers.

## How it differs from coordinate-clicking

| Approach | Our current method | Webwright |
|----------|-------------------|-----------|
| Action space | Hardcoded mouse clicks | Free-form Python scripts |
| State | Persistent browser session | Workspace (scripts + screenshots + logs) |
| Robustness | Fragile (coords change) | Reusable (code targets elements) |
| Verification | Manual polling | Screenshot capture + self-reflection |
| Learning | Sessions produce disposable scripts | Sessions produce reusable tools |

## Cost

With OpenRouter free models: $0. Agentic tasks via Qwen3 Coder cost $0/task on OpenRouter's free tier.

## Status (June 14, 2026)

Installed at `D:/my agents copilot studio/webwright/`. Doctor passes 5/6 (fails OPENAI_API_KEY check — expected when using OpenRouter). Tested with 401 (needs API key export). Ready for use once OPENROUTER_API_KEY is set.
