# MCP Server Setup on Windows

The built-in MCP client spawns subprocesses with a **filtered environment** — only safe baseline variables (PATH, HOME, USER, LANG, etc.) are inherited. API keys and PATH additions from your shell profile are NOT passed through. This causes two common Windows failures.

## Symptom

```bash
hermes mcp add notebooklm-mcp --command "uvx --from notebooklm-mcp-cli notebooklm-mcp"
# → ✗ Failed to connect: [WinError 2] The system cannot find the file specified
```

Even though `uvx` and the server binary are on your interactive shell's PATH, the MCP subprocess doesn't see those directories.

## Fix: use the full Windows-style path (not MSYS)

MSYS paths like `/c/Users/kevin/.local/bin/notebooklm-mcp` also fail because the subprocess doesn't use MSYS path translation. Use the native Windows path:

```bash
hermes mcp add notebooklm-mcp --command "C:\Users\kevin\.local\bin\notebooklm-mcp.exe"
```

This works because:
- The native Windows path is resolved directly by CreateProcess
- The filtered PATH doesn't need to include `.local/bin` — we're passing the absolute binary path
- The `.exe` extension is required (no PATH-based lookup happens)

## Finding the correct binary path

After installing with `uv tool install <package>`, find the actual binary:

```bash
# uv tools go to ~/.local/bin/ on Windows
ls -la "$HOME/.local/bin/<tool>"
# or
which <tool-name>
```

Then convert to Windows path format:
- `/c/Users/kevin/.local/bin/tool.exe` → `C:\Users\kevin\.local\bin\tool.exe`

## Example: NotebookLM MCP

```bash
# 1. Install
uv tool install notebooklm-mcp-cli

# 2. Register with Hermes (use full Windows path)
hermes mcp add notebooklm-mcp --command "C:\Users\kevin\.local\bin\notebooklm-mcp.exe"

# 3. Accept all 39 tools when prompted (or select interactively)
#    The output shows available tools: notebook_query, source_add, studio_create, etc.

# 4. Authenticate (interactive — opens Chrome for Google OAuth)
nlm login
# Chrome opens; sign in to Google → NotebookLM cookies are saved automatically

# 5. Verify
hermes mcp list
# Should show notebooklm-mcp as ✓ enabled

# 6. Start a new Hermes session to use the tools
#    Tools appear as mcp_notebooklm_mcp_* in the tool list
```

## For npx-based servers

When adding npx-based MCP servers, use the full path to `npx.cmd` or `node.exe`:

```bash
# Find npx path
which npx.cmd  # or: cmd.exe /c where npx

# Add with full path
hermes mcp add my-server --command "C:\Program Files\nodejs\npx.cmd" --args "-y,@package-name"
```

## For uvx-based servers

`uvx` is a better approach than `uvx --from` — but on Windows, use the direct binary path of the installed tool instead of uvx, since uvx needs to resolve the package name and may fail in the filtered environment.

## Auth flows that need a browser

Some MCP servers (NotebookLM, Google services) need OAuth via browser. The MCP server may:
1. Open a Chrome window automatically (NotebookLM does this via `nlm login`)
2. Provide a URL for you to visit and a code to enter

In both cases, the server handles the credential storage — you only need to complete the login flow once.

### NotebookLM auth flow (nlm login)

```bash
nlm login
```

This launches Chrome with its own managed profile (not your default Chrome), navigates to Google sign-in, and waits. Steps:
1. **Google sign-in** appears with your known Google account shown
2. Click your account — if you have a **Windows Hello passkey** set up, it prompts PIN/fingerprint
3. After authentication completes, cookies are extracted and saved to `~/.notebooklm-mcp-cli/profiles/default/`
4. The terminal output confirms: `Cookies: ~32 extracted`, `CSRF Token: Yes`, `Account: your@email.com`

Verify success:
```bash
nlm login --check
# → ✓ Authentication valid! Notebooks found: N
```

### Non-interactive MCP registration

When adding an MCP server that has an interactive "accept tools" prompt, pipe `Y` to auto-accept all tools:

```bash
printf "Y\n" | hermes mcp add notebooklm-mcp --command "C:\Users\kevin\.local\bin\notebooklm-mcp.exe"
```

For selective tool enablement, omit the pipe and use the interactive selector instead.
