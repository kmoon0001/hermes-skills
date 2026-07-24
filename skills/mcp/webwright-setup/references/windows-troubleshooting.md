# Webwright on Windows — Setup Troubleshooting

## Issue: Browser Not Found
```
FileNotFoundError: [WinError 2] The system cannot find the file specified
FileNotFoundError: Could not find Chrome/Chromium...
```

**Cause:** `local_browser.yaml` defaults to `browser_mode: local_cdp` which searches Mac/Linux paths only.

**Fix:** Stack `ww_win_local.yaml` AFTER `local_browser.yaml` to override to `local_launch` mode:
`-c base.yaml -c local_browser.yaml -c ww_win_local.yaml -c model_openrouter_free.yaml`

## Issue: OpenRouter 401 Unauthorized
**Fix:** Set `OPENROUTER_API_KEY` env var. Use `set -a && source .env` to load from `.env` file.

## Issue: OpenRouter 404 Not Found
**Fix:** Free models need `provider_require_parameters: false`. Use `model_openrouter_free.yaml`.

## Issue: Config Stacking Order
Correct order: `base.yaml` > `local_browser.yaml` > `ww_win_local.yaml` > `model_openrouter_free.yaml`
Each overrides the previous at the same key path (recursive merge).

## Issue: Async Event Loop
Webwright manages its own async loop. Run in a fresh Python process — do not import inside existing asyncio applications.
