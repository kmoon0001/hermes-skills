---
name: codex-setup
description: "Configure Codex CLI with custom model providers, troubleshoot MCP server integration, and set up proxy/bridge services (e.g. Moon Bridge)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [codex, moonbridge, model-provider, mcp, configuration, troubleshooting]
    related_skills: [systematic-debugging, native-mcp]
---

# Codex CLI Setup

## Overview

Configure OpenAI's Codex CLI to work with non-OpenAI models via proxy/bridge services like Moon Bridge. Covers the full setup lifecycle: provider registration, environment variables, MCP server compatibility, sandbox configuration, and verification.

## When to Use

- User wants to run Codex with a model other than OpenAI (DeepSeek, Claude, local LLM)
- Codex throws 502/400 errors with tool-related messages
- MCP server configurations conflict with custom model providers
- Setting up Moon Bridge, LiteLLM, or similar proxy endpoints for Codex
- Debugging "empty string" or "invalid function" errors in tool definitions

## Configuration

### Minimal Provider Config

The `config.toml` (`~/.codex/config.toml`) needs these sections:

```toml
model = "your-model-name"
model_provider = "your-provider-name"

[model_providers.your-provider-name]
name = "Human-readable Name"
base_url = "http://127.0.0.1:PORT/v1"
env_key = "YOUR_API_KEY_ENV_VAR"
```

### Required Fields

- **`model`** — The model name string (e.g. `"deepseek-v4-flash"`, `"gpt-4o"`). Must match what the provider's `/v1/models` endpoint lists.
- **`model_provider`** — A key matching one of the `[model_providers.*]` sections.
- **`[model_providers.*]`**
  - `name` — Display name for the provider
  - `base_url` — API endpoint (must include `/v1` suffix)
  - `env_key` — OS environment variable name containing the API key

### Environment Variable

The API key must be set as a **system-level** environment variable for the Codex desktop app:

**Windows:**
```
System Properties → Environment Variables → User variables → New
Variable name: DEEPSEEK_API_KEY
Variable value: sk-...
```

**Linux/macOS (for CLI usage):**
```bash
export DEEPSEEK_API_KEY="sk-..."
# Add to ~/.bashrc or ~/.zshrc for persistence
```

> **Note:** Terminal `export` only affects that session. GUI apps like Codex Desktop require system-level env vars or launching Codex from the terminal.

## MCP Server Troubleshooting

### The Empty Tool Name Bug

Codex sends tool definitions to the model provider in the `/v1/responses` request body. If any MCP server definition injects a tool with an empty `function.name`, the provider returns:

```
unexpected status 502 Bad Gateway: upstream stream error:
Invalid 'tools[N].function.name': empty string. Expected a string with minimum length 1
```

**Root Cause:** An `[mcp_servers.*]` section in `config.toml` defines a server that either:
- Starts but fails to return valid tool definitions
- Returns tool schemas with empty/malformed function names
- Has been removed/uninstalled but its config entry remains

### Fix

**Temporarily:** Comment out the `[mcp_servers.*]` section(s) in `config.toml`:

```toml
# [mcp_servers.node_repl]
# command = '...'
# args = []
#
# [mcp_servers.node_repl.env]
# KEY = "VALUE"
```

**Permanently:** Investigate the MCP server integration — the issue is in how the server advertises its tools. Use `native-mcp` skill to test MCP server tool listings independently.

### Sandbox Considerations

If MCP-related errors persist after commenting out MCP config, try:

```toml
[windows]
sandbox = "danger-full-access"
```

This eliminates any sandbox-level filtering of tool schemas during debugging. Revert to a stricter sandbox after the root cause is fixed.

## Project Trust

Codex requires a `trusted` project entry for workspaces outside the home directory:

```toml
[projects.'d:\\path\\to\\project']
trust_level = "trusted"
```

## Verification

### 1. Test the Provider Endpoint

```bash
curl -X POST http://127.0.0.1:PORT/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $YOUR_API_KEY" \
  -d '{"model":"your-model","tools":[],"input":"say hello"}'
```

### 2. Test the Provider Model List

```bash
curl http://127.0.0.1:PORT/v1/models
```

### 3. Run a Codex Command

```bash
codex exec --json --skip-git-repo-check "say hello"
```

Use `--json` to see the full response stream. Use `--skip-git-repo-check` if the workspace is not a git repo.

## Common Providers

### Moon Bridge

Moon Bridge is a lightweight proxy that adapts various model APIs (DeepSeek, Claude, etc.) to the OpenAI-compatible format Codex expects.

```toml
model = "deepseek-v4-flash"
model_provider = "moonbridge"

[model_providers.moonbridge]
name = "Moon Bridge"
base_url = "http://127.0.0.1:38440/v1"
env_key = "DEEPSEEK_API_KEY"
```

**Known issues:**
- Model name must match exactly what `/v1/models` returns (case-sensitive)
- MCP server config must be disabled or it will inject empty tool names
- Sandbox should be permissive during initial setup

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| MCP server enabled with custom provider | 502 Bad Gateway: empty tool name | Comment out `[mcp_servers.*]` |
| Wrong model name | 400/404, model not found | Check `/v1/models` for exact string |
| Missing API key env var | 401/403 auth failure | Set as system env var, restart Codex |
| Sandbox too restrictive | Tool schemas rejected | Use `danger-full-access` temporarily |
| Provider URL missing `/v1` suffix | 404 Not Found | Append `/v1` to `base_url` |
| Moon Bridge server not running | Model refresh fails, `Failed to refresh available models` | Check port: `curl http://127.0.0.1:38440/v1/models`. If dead, switch to native OpenAI with ChatGPT OAuth (see Switching to Native OpenAI below). |
| ChatGPT OAuth + gpt-5.6-sol model | `The 'gpt-5.6-sol' model is not supported when using Codex with a ChatGPT account.` | Set `model = "gpt-5.5"` in config.toml or pass `--model gpt-5.5` on CLI |
| Windows sandbox: logon session missing | `CreateProcessAsUserW failed: 1312` on `exec` | Use `--yolo` flag to bypass sandbox; error is Windows session token issue, not auth failure |
| Model name from CLI not persisted | Error reappears after restart | Set `model` in `config.toml`, not just via flag |
| **OpenRouter as Codex provider** | 404 on `/v1/responses`, `No endpoints found` | Codex uses OpenAI's Responses API (`/v1/responses`) — OpenRouter only supports Chat Completions (`/v1/chat/completions`). OpenRouter CANNOT work as a Codex provider. Use a real OpenAI key, ChatGPT OAuth, or a local proxy (Moon Bridge) that translates Responses ↔ Chat Completions |
