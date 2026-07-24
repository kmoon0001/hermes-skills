# Moon Bridge + Codex MCP Conflict

## Error Message
```
unexpected status 502 Bad Gateway: upstream stream error: Invalid 'tools[192].function.name': empty string. Expected a string with minimum length 1, but got an empty string instead., url: http://127.0.0.1:38440/v1/responses
```

## Context
- User was configuring OpenAI Codex CLI to use DeepSeek model via Moon Bridge (local endpoint at http://127.0.0.1:38440/v1)
- Codex config.toml had MCP servers configured (including chrome-devtools-mcp and @playwright/mcp from Kiro IDE)
- When using a custom model provider like Moon Bridge, Codex's MCP server configuration can cause tool definition errors

## Root Cause
The MCP server configuration (specifically the `[mcp_servers.node_repl]` section in this case) was causing Codex to send tool definitions with empty function names to the Moon Bridge endpoint, which validates that tool.function.name must be a non-empty string.

## Fix
1. Comment out ALL MCP server sections in `~/.codex/config.toml` (or `%USERPROFILE%\.codex\config.toml` on Windows)
   ```toml
   # [mcp_servers.node_repl]
   # args = []
   # command = '...'
   # ...
   
   # [mcp_servers.node_repl.env]
   # NODE_REPL_NATIVE_PIPE_CONNECT_TIMEOUT_MS = "1000"
   # ...
   ```
2. Save the config.toml file
3. **Completely restart the Codex desktop application** (config changes require restart)
4. Verify the error is resolved

## Verification
After restarting Codex:
- The "Reconnecting... 5/5" loop should stop
- Codex should successfully connect to http://127.0.0.1:38440/v1/responses
- Normal operation with DeepSeek via Moon Bridge should resume

## Notes
- This fix is temporary for using custom model providers that don't support MCP tool discovery
- To restore MCP functionality (e.g., for Browser Plugin with default OpenAI provider), uncomment the MCP sections and restart Codex
- The specific MCP server causing the issue may vary - in this case it was node_repl, but others like chrome-devtools-mcp or @playwright/mcp could cause similar symptoms
- Moon Bridge appears to be a local proxy/adapter for DeepSeek API that expects standard OpenAI-compatible tool definitions

## Related
- See codex skill's "Custom Model Providers and Troubleshooting" section for general guidance
- MCP servers in Codex config enable local tool usage (like browser automation) but can conflict with custom providers