# Browser Automation Timeout Survival Guide

## The Problem

When automating Copilot Studio via Playwright/Chrome:
- `terminal(timeout=60)` kills the Node.js process at 60 seconds
- The Node.js process owns the Playwright browser — killing Node = killing Chrome
- Result: Chrome window disappears, user frustration

## Solution: Timeout by Mode

### Headless Mode (No Browser Window)
- Works reliably within `terminal(timeout=120)`
- Use `terminal(timeout=120)` for scripts that navigate 1-2 pages
- For 4-agent batch scans, use `terminal(timeout=180)`
- The SPA may not fully render in headless mode (especially Knowledge and Evaluation pages)

### Headless: false (Visible Browser)
- Needs longer timeout: `terminal(timeout=180)`
- The browser stays alive for the full 180 seconds
- After timeout, the process IS killed (browser closes) but you get your data first
- Use for debugging SPA rendering issues

### Background True (Long-Running Keepalive)
- `terminal(background=true, notify_on_complete=true)` — process still gets killed
- `cmd.exe /c start /B "" node script.cjs` — on Windows Git Bash, this also gets killed when the shell session ends
- **No reliable way to keep a GUI Chrome alive across terminal calls** — the shell kills child processes on exit

### Best Practice

For a single comprehensive scan:
1. Write one `.cjs` script that does EVERYTHING (KB extraction → SP navigation → eval token capture → score query)
2. Launch with `terminal(timeout=180)` — enough time for most workflows
3. Script writes all output to console before the timeout kills it
4. Do NOT call `browser.close()` — let the timeout handle cleanup (or the user may keep the window)

### Popup Dismissal Order

When navigating to any Copilot Studio page:
1. Navigate
2. Wait 8-12s for SPA to initialize
3. Escape x 5 (300ms delay each) — dismisses modals and tooltips
4. Button hunt: click buttons labeled "Got it", "Skip", "Dismiss", "Close", "OK"
5. Wait 3s for UI to settle
6. Then read body.innerText or interact

Without this sequence, the Knowledge page shows test chat panel instead of source list, and the Evaluation page shows empty.

## SharePoint Auth Limitation

The Playwright persistent auth (`storageState`) captures **Power Platform cookies** only — not SharePoint cookies. SharePoint requires separate auth (FedAuth, rtFa cookies). When navigating to SharePoint from a Playwright session:

- If the auth cookie cache includes Microsoft Online session (ESTSAUTH, ESTSAUTHPERSISTENT), SharePoint may auto-redirect through SSO
- If not, SharePoint redirects to login page → body.innerText shows "Sign in" or the tenant login
- Workaround: navigate via Copilot Studio's knowledge source details panel (it opens SharePoint in the authenticated context)

## Token Capture Timeout

When waiting for eval API token:
- The SPA may not trigger `makerevaluation` API calls if the evaluation section doesn't render
- Try navigating to the **Overview** or **Knowledge** page first (these render reliably), then navigate to Evaluation
- If no eval token after 25s, the page probably didn't trigger the API — proceed without scores and report manually
