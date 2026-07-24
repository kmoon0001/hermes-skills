# Codex Desktop App Diagnostics

When the Codex desktop app fails to start, connect, or respond, follow this decision tree before diving into config changes.

## Decision Tree

```
Codex app not working?
  ↓
Open config.toml → check model_provider
  ↓
Custom provider (moonbridge, custom endpoint)?
  ├─ YES → Check if local proxy/endpoint is actually running:
  │         curl http://127.0.0.1:<port>/v1/models
  │         If connection refused → the proxy server is down.
  │         Fix: Start the proxy server (Moon Bridge, etc.)
  │         If 200 OK → see MCP conflict path (codex/references/moonbridge-mcp-conflict.md)
  └─ NO  → Check OpenAI auth:
            cat ~/.codex/auth.json  (valid?)
            codex login  (re-authenticate)
```

## Primary Check: Is the Proxy Running?

If Codex uses a custom model provider pointing to `127.0.0.1` or `localhost`, the local
proxy/adapter MUST be running for Codex to function at all.

```bash
# Check if the port is listening
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:38440/v1/models
# Returns "000" means connection refused — proxy is DOWN
# Returns 200+ means proxy is running (but may still have issues)
```

The most common symptom when the proxy is down: Codex opens but sits at a
"Connecting..." or "Reconnecting..." screen indefinitely.

## Secondary Check: MCP Server Conflicts

If the proxy IS running but Codex shows errors, the MCP server sections in
config.toml may be interfering. See `references/moonbridge-mcp-conflict.md`
for the full fix (comment out [mcp_servers.*] sections).

## Config Locations

| Component | Path |
|-----------|------|
| Codex config | `%USERPROFILE%\.codex\config.toml` |
| Codex auth | `%USERPROFILE%\.codex\auth.json` |
| CLI binary | `%APPDATA%\npm\codex` or `%USERPROFILE%\.codex\...\codex.exe` |

## Common config.toml patterns for custom providers

```toml
model = "deepseek-v4-flash"
model_provider = "moonbridge"

[model_providers.moonbridge]
name = "Moon Bridge"
base_url = "http://127.0.0.1:38440/v1"
env_key = "DEEPSEEK_API_KEY"
```

The `env_key` field tells Codex which environment variable to read for the API
key. If the server is running, also verify the key exists in the environment:

```bash
echo ${DEEPSEEK_API_KEY:0:8}...  # Should show a real key, not empty
```
