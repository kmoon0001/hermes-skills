# Persistent Auth & Agent Verification (June 2026)

## Persistent Playwright Auth

The old `connectOverCDP('http://127.0.0.1:9223')` approach is fragile:
- Frequently times out (>30s)
- Returns stale/empty page targets
- Requires Chrome restart with `--remote-debugging-port`

**New approach:** Launch a fresh Playwright Chromium, sign in once, save auth state.

```javascript
const browser = await chromium.launch({
  headless: false,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const ctx = await browser.newContext({
  storageState: 'D:/my agents copilot studio/.playwright-auth/state.json'
});
const page = await ctx.newPage();
// Already signed in — navigate directly
await page.goto('https://copilotstudio.microsoft.com/...');
```

Setup script: `scripts/setup-persistent-auth.cjs`

Auth file location: `D:/my agents copilot studio/.playwright-auth/state.json`

## Write-Then-Run Discipline

**Pitfall:** Writing a script file without running it. User frustration signal:
"You just executed tool calls but returned an empty response."

**Rule:** After `write_file`, immediately `terminal` run the script. Never end a
turn on a file write. If the write is for the user (Notepad), that's fine —
but any `.cjs`/`.ps1`/`.py` script meant for execution MUST be run in the
same response.

## Copilot Studio SPA Navigation (current as of June 2026)

### Tabs that work via CDP
- Agent sidebar: `[role="tab"]` with `.includes('Topics')` (text is doubled: "TopicsTopics")
- System tab: same selector, `.includes('System')`
- CB grid cell: `[role="gridcell"]` containing "Conversational boosting" → get `<a>` link
- More button: `button[aria-label="More"]`
- Menu items: `[role="menuitem"]`

### Tabs that are unreliable
- "+5" overflow button — may or may not be present depending on page state
- Topics tab when "+5" is present — hidden, getBoundingClientRect() returns zero
- `/topics` URL — always redirects to `/overview` via SPA

### Reliable approach
1. Navigate to Overview: `page.goto(overviewUrl)` — works with persistent auth
2. Dump all visible `[role="tab"]` elements to see current state
3. Click the correct tab via CDP `Input.dispatchMouseEvent` coordinates
4. If tab is hidden behind "+5", click "+5" first, then the target tab
5. Wait 8-10s between each navigation step

### When tabs are completely broken
Fall back to manual visual verification. Ask the user to check the UI directly
rather than fighting SPA navigation for 30+ minutes.

---

## Related Reference

`references/dl-write-publish-publish-blockers.md` — Covers:
- Instructions `conversationStarters` Title/Text casing requirement
- SPA Publish button disabled after Dataverse API PATCH
- `pac CLI` cached publish failures
- MSAL cache recovery from browser network capture
