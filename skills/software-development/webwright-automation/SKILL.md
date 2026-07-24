---
name: webwright-automation
description: >-
  Install, configure, and run Microsoft Webwright (github.com/microsoft/webwright)
  for AI-driven browser automation tasks on Windows. Uses code-as-action paradigm:
  the LLM writes Playwright Python scripts to interact with web pages instead of
  fragile coordinate-clicking. Supports OpenRouter free models.
platforms: [windows]
---

# Webwright Automation

## What it is
Microsoft Research's open-source (~1.5k LoC) browser agent framework. Gives an LLM a terminal + Playwright to write and execute Python scripts for web tasks. MIT license. [github.com/microsoft/webwright](https://github.com/microsoft/webwright)

## Installation (Windows)

```bash
cd /d/project/dir
git clone https://github.com/microsoft/webwright.git
cd webwright

# Create venv (Windows: Scripts/, not bin/)
python3 -m venv ww_venv
source ww_venv/Scripts/activate

# Install package and browser
pip install -e .
playwright install chromium

# Verify
python -m webwright.run.cli doctor
```

Expected: 5/6 pass (OpenAI key check fails — ignored when using OpenRouter).

## Configuration

### OpenRouter free model config
Create `src/webwright/config/model_openrouter_free.yaml`:
```yaml
model:
  model_class: openrouter
  model_name: openrouter/free
  openrouter_endpoint: https://openrouter.ai/api/v1/chat/completions
  provider_require_parameters: false
```

Key detail: `provider_require_parameters: false` is required for free models (they don't support JSON schema output).

### Available free models
The `openrouter/free` model auto-routes. For specific models:
- `qwen/qwen3-coder:free` — code-specialized (480B)
- `openrouter/owl-alpha` — agentic browsing
- `nvidia/nemotron-3-super-120b-a12b:free` — 120B reasoning

### Free vision models (for CAPTCHA reading)
- `google/gemma-4-26b-a4b-it:free` — tested, works for simple images but struggles with distorted CAPTCHAs
- `nvidia/nemotron-nano-12b-v2-vl:free` — smaller, less accurate
- Note: free models get ~0% accuracy on distorted BotDetect CAPTCHAs. For production CAPTCHA solving, use paid models (GPT-4o) or semi_auto.py approach.

To use vision, set `attach_observation_screenshot: true` in config so Webwright sends screenshots to the model. The model sees the CAPTCHA and can type the answer.

## Running tasks

### Live browser mode (required on Windows)
```bash
export OPENROUTER_API_KEY=***
source ww_venv/Scripts/activate

python -m webwright.run.cli main \
  -c base.yaml -c local_browser.yaml -c model_openrouter_free.yaml \
  -t "Natural language task description" \
  --task-id task_name \
  -o outputs
```

**IMPORTANT:** The `-c local_browser.yaml` flag is REQUIRED on Windows. Without it, the agent tries to generate a standalone Playwright script that spawns the browser via subprocess, which fails with `FileNotFoundError` on Windows because the binary search paths are Mac/Linux-only.

### What local_browser.yaml mode does
- Runs a live Playwright session the agent drives directly each turn
- ARIA snapshot of page body (text) is the primary view
- Screenshots saved to disk each step (step_<NNNN>.png) but not sent visually unless `attach_observation_screenshot: true`
- Final answer reported in `final_response` when agent decides it's done
- Browser is disposable: launches, does task, closes

### Output artifacts
Each run creates a timestamped folder under `-o <dir>`:
- `trajectory.json` — full action log
- `step_<NNNN>.png` — screenshots
- `raw_responses.jsonl` — model response traces

## Use cases for Copilot Studio
- Navigate to agent pages, read/write toggles
- Verify KB descriptions are populated
- Click topic More menus, delete topics
- Open code editor and verify YAML content
- Read evaluation results

## Pitfalls
- **Windows browser path:** Webwright's default `_CHROMIUM_EXECUTABLE_CANDIDATES` has only Mac/Linux paths. Must use `local_browser.yaml` mode which uses Playwright Python API directly (finds the installed Playwright Chromium correctly).
- **Free model limitations:** `openrouter/free` routes to different providers. May hit rate limits. The `provider_require_parameters: false` is essential — without it, OpenRouter returns 404 because free models don't support `response_format: json_schema`.
- **Live mode vs script mode:** `local_browser.yaml` (live) operates on current page state. `base.yaml` (script) generates reusable `.py` files. On Windows only live mode works. For repeatable tasks, use script mode on Mac/Linux.
- **Screenshot tokens:** `attach_observation_screenshot: true` adds significant image token cost per step. Only enable when structure/text parsing fails. Default is `false` (ARIA text only).
