# Interactive Alibaba / Qwen API-key setup notes

Session-derived workflow for helping a user create and install a DashScope / Model Studio key without exposing secrets in chat.

## Browser handoff

1. Open the Model Studio API-key page:
   `https://bailian.console.alibabacloud.com/?tab=model#/api-key`
2. If the page is at Alibaba sign-in, stop and ask the user to sign in directly in the browser window. Do not request password or MFA codes in chat.
3. After login, guide the user to create/copy a **Model Studio / DashScope API key**. Re-emphasize that Alibaba Cloud AccessKey ID/secret is not the inference key Hermes needs.

## Secure local setup script pattern

When the user needs help installing the key, prefer writing a small local script that uses `getpass.getpass()` so the secret is typed into the terminal, not chat. The script should:

- read/write the active Hermes profile `.env`, usually `C:/Users/<user>/AppData/Local/hermes/profiles/<profile>/.env` on Windows;
- upsert `DASHSCOPE_API_KEY=...`;
- test both likely endpoint families when region is unclear:
  - international: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
  - China: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- if China endpoint works, also set `DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`;
- configure Hermes with `hermes config set model.provider alibaba` and a known-working model;
- tell the user to restart Hermes or use `/reload`.

## Verification pitfall

A helper script that prompts for a key can hang automated verification. Include an offline verification path such as `--self-test` that checks deterministic pieces without requiring the secret:

- `python -m py_compile setup_qwen_alibaba.py`
- `python setup_qwen_alibaba.py --self-test`

Do not use `npm run test` as the primary verification for a standalone Python helper. If an external verifier asks for it and it is only a placeholder (`Error: no test specified`), report that as not applicable and provide the Python verification evidence instead.

## Error interpretation

- `401 invalid_api_key` after direct probe means credential problem: wrong/expired key or wrong region/account. It is not caused by Anthropic-vs-OpenAI message format.
- `429` means the key/provider connected but quota/credits/rate limit are exhausted.
