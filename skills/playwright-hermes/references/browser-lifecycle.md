# Browser Lifecycle Management

## The Core Problem

Terminal timeout kills the Node.js process, which Playwright propagates to kill Chrome.
Even without calling `browser.close()`, the Chrome window disappears when the terminal
command times out (default 180s, foreground max 600s).

## Root Cause

Terminal timeout → Node process killed → Child Chrome process killed → Window disappears

## Solutions

### Good: Headless mode (best for data collection)

```javascript
const browser = await chromium.launch({ headless: true });
// Works in foreground terminal. No window to close. Survives normal timeouts.
// Use for: token capture, scraping, screenshots, automation that doesn't need user eyes.
```

### Fragile: Headed mode via background (when user must see the window)

On Git Bash (MSYS), background processes with terminal(background=true) get orphaned
at shell exit. Chrome launched by Playwright inside a background terminal command may
survive or die depending on timing.

### Best for headed mode with CDP persistence

Launch Chrome independently, then connect via CDP:

```bash
# Terminal: Launch Chrome with remote debugging (survives terminal timeout)
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9223 \
  --user-data-dir="D:/my agents copilot studio/.playwright-auth" \
  --no-first-run --no-default-browser-check \
  about:blank &
```

```javascript
// Then connect via connectOverCDP
const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
```

This decouples the Chrome lifecycle from the Node.js script lifecycle.

### Never: Calling browser.close() without user permission

The user has repeatedly expressed frustration with this pattern. The browser window
is their working environment for Copilot Studio. Never close it unless asked.

### MSYS/Git Bash limitations

- headless: false inside a terminal(background=true) job fails with "stdin is not a tty".
  Git Bash PTY can't serve as a display.
- Use headless: true for automated tasks, or launch Chrome independently for visual tasks.
- nohup doesn't reliably detach child processes from the shell on Windows/MSYS.
