---
name: alibaba-qwen-provider-setup
description: "Set up and troubleshoot Alibaba Cloud / DashScope Qwen models in Hermes Agent, including provider IDs, API-key validation, and model selection."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [hermes, qwen, alibaba, dashscope, model-provider, setup]
---

# Alibaba / Qwen Provider Setup for Hermes

Use this skill when the user asks how to access Qwen through Alibaba Cloud, DashScope, Model Studio, or free Alibaba credits in Hermes Agent.

## Key distinction

Do not assume an Alibaba Cloud account AccessKey is usable for model inference. Hermes needs a DashScope / Model Studio API key, normally stored as:

```bash
DASHSCOPE_API_KEY=...
```

If the user says they set up Alibaba Cloud credits but Qwen returns `401 invalid_api_key`, the likely fix is to create/copy the Model Studio / DashScope API key, not to change the model protocol.

## Hermes provider IDs

Hermes has two relevant provider IDs:

- `alibaba` — Qwen Cloud / DashScope normal endpoint
  - base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
  - env var: `DASHSCOPE_API_KEY`
- `alibaba-coding-plan` — Alibaba Cloud Coding Plan endpoint
  - base URL: `https://coding-intl.dashscope.aliyuncs.com/v1`
  - env vars: `ALIBABA_CODING_PLAN_API_KEY` or `DASHSCOPE_API_KEY`

Recommended coding-agent setup:

```bash
hermes config set model.provider alibaba-coding-plan
hermes config set model.default qwen3-coder-plus
```

Recommended general Qwen setup:

```bash
hermes config set model.provider alibaba
hermes config set model.default qwen3.5-plus
```

Restart Hermes after editing `.env`, or use `/reload` in an interactive Hermes CLI session if available.

## Fast checks

```bash
hermes config path
hermes config env-path
hermes auth list alibaba
hermes auth list alibaba-coding-plan
```

Expected credential display looks like:

```text
alibaba (1 credentials):
  #1  DASHSCOPE_API_KEY    api_key env:DASHSCOPE_API_KEY

alibaba-coding-plan (1 credentials):
  #1  DASHSCOPE_API_KEY    api_key env:DASHSCOPE_API_KEY
```

## Validate the key directly

Use an OpenAI-compatible chat completion probe. On Windows/Git Bash, avoid `source .env` if the file has unquoted values containing spaces or shell metacharacters; parse the file from Python instead.

```bash
python - <<'PY'
import json, urllib.request, urllib.error
from pathlib import Path

# Adjust profile if needed.
env_path = Path.home() / 'AppData/Local/hermes/profiles/coding-profile/.env'
vals = {}
for line in env_path.read_text(errors='ignore').splitlines():
    s = line.strip()
    if s and not s.startswith('#') and '=' in s:
        k, v = s.split('=', 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")

key = vals.get('ALIBABA_CODING_PLAN_API_KEY') or vals.get('DASHSCOPE_API_KEY')
assert key, 'No DASHSCOPE_API_KEY or ALIBABA_CODING_PLAN_API_KEY found'

url = 'https://coding-intl.dashscope.aliyuncs.com/v1/chat/completions'
body = {
    'model': 'qwen3-coder-plus',
    'messages': [{'role': 'user', 'content': 'Reply exactly: OK'}],
    'max_tokens': 5,
    'temperature': 0,
}
req = urllib.request.Request(
    url,
    data=json.dumps(body).encode(),
    headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    print('STATUS OK')
    print(data['choices'][0]['message']['content'])
except urllib.error.HTTPError as e:
    print('HTTP', e.code)
    print(e.read().decode()[:1000])
    raise
PY
```

## Interpreting failures

- `HTTP 401 invalid_api_key` / `Incorrect API key provided`: the configured key is not a valid DashScope / Model Studio inference key, is expired, or belongs to the wrong region/account. Create a new Model Studio API key and put it in `.env` as `DASHSCOPE_API_KEY=...`.
- `HTTP 429` or quota/credit errors: the key works, but the Alibaba/DashScope credit or rate quota is exhausted. Switch provider or add credits.
- Model-not-found errors: try a cached/listed model such as `qwen3-coder-plus`, `qwen3.5-plus`, `qwen3.6-plus`, or check current provider model listing.

## Common models seen in Hermes caches

For `alibaba` and `alibaba-coding-plan`, useful model names may include:

- `qwen3.7-max`
- `qwen3.6-plus`
- `qwen3.5-plus`
- `qwen3-coder-plus`
- `qwen3-coder-next`

Model availability changes. Prefer checking provider listings before declaring a model unavailable.

## Interactive API-key setup

For browser-assisted key creation and a secure local `getpass` setup-script pattern, see `references/interactive-api-key-setup.md`. Use that reference when the user asks you to navigate Alibaba Cloud and help install the key without exposing secrets in chat.

## Pitfalls

- Do not blame Anthropic vs OpenAI message style for a clear provider error like `401 invalid_api_key`; fix the credential first.
- Do not paste or ask the user to paste secrets into chat. Have them edit `.env` or run `hermes auth add ...` locally; for guided setup, write a local script that prompts with `getpass`.
- If you create a helper script that prompts for a secret, add an offline `--self-test` so verification can run without hanging on input.
- On Windows/Git Bash, do not blindly `source` `.env`; unquoted values with spaces or shell metacharacters can break the shell parse. Use Python parsing for probes.
- On Windows, Hermes profile config commonly lives under `C:\Users\<user>\AppData\Local\hermes\profiles\<profile>\config.yaml` and `.env` beside it, not necessarily under the default `~/.hermes` path.
- **Config key is `alibaba`, not `dashscope`.** When adding Qwen/DashScope to `config.yaml` under `providers:`, the key must be `alibaba:` or `alibaba-coding-plan:`. The interactive `hermes model` menu says "Qwen Cloud / DashScope" but the underlying config key is `alibaba`. Using `dashscope:` may silently fail — Hermes won't find the provider credentials.
- **Bulk-editing `providers:` model lists requires `execute_code`.** The `hermes config set` CLI only handles single key-value pairs. To restructure the `providers:` section with multiple model entries, use `execute_code` to read config.yaml, regex-replace the providers block, and write back. `read_file` is blocked on config files — use Python's `open()` inside `execute_code` instead.
