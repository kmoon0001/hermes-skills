# Windows Environment & Multi-Agent Context

## Browser Binary Paths

| Tool | Path | On PATH? |
|------|------|----------|
| Google Chrome | `C:\Program Files\Google\Chrome\Application\chrome.exe` | No |
| Kiro (Electron) | `C:\Users\kevin\AppData\Local\Programs\Kiro\Kiro.exe` | No |

Chrome is auto-discovered by `playwright-cli` even though it's not on the MSYS PATH.

## Auth State Export + Reuse

### Process (verified working)

1. Export from Kiro:
   ```
   NODE_PATH=$(npm root -g) node scripts/export_kiro_auth.cjs
   ```
   This launches Chrome with Kiro's `.playwright-auth` profile via CDP on port 9223,
   calls `Network.getAllCookies` for 243+ cookies AND `DOMStorage.getDOMStorageItems`
   for MSAL localStorage tokens.

2. Output: `C:\Users\kevin\.hermes-browser-session\auth.json` (393KB, ~285 cookies + 65 localStorage items)

3. Load into playwright-cli session:
   ```
   npx playwright-cli --session cs open https://example.com
   npx playwright-cli --session cs state-load 'C:\Users\kevin\.hermes-browser-session\auth.json'
   npx playwright-cli --session cs goto https://copilotstudio.microsoft.com
   ```

**Critical:** Both cookies AND localStorage are needed for Copilot Studio SSO.
The MSAL.js token cache lives in localStorage (not IndexedDB in this setup).
Cookies alone redirect to login page.

### --session flag behavior on MSYS/Windows

- `--session <name>` expects a plain session name, NOT a path
- Simple names like `cs`, `pw-session`, `test123` work
- Path arguments cause a concatenation bug:  
  `--session ~/.hermes-browser-session` → tries to create file at  
  `.../daemon/6a3d3b5cb89f0427/C:\Users\kevin\...\.hermes-browser-session.err`
- Use `state-load` + `state-save` with full Windows paths for persistent auth
- Pipeline sessions: use `npx playwright-cli kill-all` to clear stale daemon pipes

## Session Auth State Locations

| Tool | Auth Storage |
|------|-------------|
| Kiro Playwright auth | `C:\Users\kevin\AppData\Local\Programs\Kiro\.playwright-auth\Default\` |
| Kiro MCP profile | `C:\Users\kevin\AppData\Local\Programs\Kiro\.playwright-mcp\` |
| Hermes (this skill) | `~/.hermes-browser-session/` (configurable via `--session`) |
| Codex Playwright | Uses `npx playwright-cli` without persistent session dir |

## Codex Playwright Skills Reference

- **playwright skill:** `~/.codex/skills/playwright/SKILL.md` — CLI wrapper via `scripts/playwright_cli.sh`
- **playwright-interactive skill:** `~/.codex/skills/playwright-interactive/SKILL.md` — js_repl-based persistent browser
- **screenshot skill:** `~/.codex/skills/screenshot/SKILL.md` — OS-level screen capture

The Codex wrapper script (`playwright_cli.sh`) invokes:
```bash
npx --yes --package @playwright/cli playwright-cli [args]
```
with optional `--session` injection from `$PLAYWRIGHT_CLI_SESSION`.

## Kiro Skills Reference

Key skill files discovered in Codex project directories:

- `playwright-topic-editor.md` — Playwright pattern for Copilot Studio topic code editor
- `copilot-studio-topic-injection.md` — Topic injection workflow
- `dataverse-bot-management.md` — Bot CRUD via Dataverse API
- `clinical-swarm-deployment.md` — Multi-agent clinical deployment
- `config-consolidation.md` — Config consolidation workflow

## MCP Servers Configured in Codex

From `~/.codex/config.toml`:

```
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest"]

[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest"]
```

## Copilot Studio Topic Editing — Known Pitfalls

1. Use `button:has-text("More")` NOT `button[aria-label="More"]` — aria-label unreliable
2. Code editor needs 3-4s to open after clicking menu item
3. Monaco editor paste may need retry logic; large YAML should use `.fill()` not clipboard
4. After Ctrl+S, wait 3-4 seconds for server round-trip
5. 3-7 JS errors on every page load are platform noise, NOT topic errors
6. Topic validation errors show as numbers in the Topics grid Errors column, NOT in console
7. Navigate back to topics list before opening each new topic (prevents stale state)

## MSYS/Bash Path Notes

- Use `/c/Users/kevin/...` or `C:\Users\kevin\...` interchangeably in MSYS
- `which` won't find Windows-installed binaries (Chrome, Kiro, etc.)
- `$HOME` resolves to `/c/Users/kevin`
- The Hermes terminal tool runs bash (git-bash/MSYS), NOT PowerShell
