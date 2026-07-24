# Copilot Studio SPA Navigation Patterns

## Topics Page Access
`/topics` URL redirects to `/overview`. Topics tab is hidden behind the "+N" overflow tab.

**Sequence:**
1. Navigate to agent overview, wait for body > 5000 chars
2. Click the "+N" overflow tab (e.g., "+8") at top of agent nav
3. Wait 2-3s for dropdown
4. Click "Topics" from dropdown items (vertical list at x≈601, starting y≈130)
5. Wait 8s for Topics table to render

Dropdown shows: Knowledge, Tools, Agents, Topics, Activity, Evaluation, Analytics, Channels.

## Web Search Toggle
Checkbox INPUT with `role="switch"` on Overview page, near "Web Search" text label.

**Sequence:**
1. Navigate to Overview, wait for "Web Search" text
2. Find `input[role=switch]` within 200px vertical of "Web Search" text
3. CDP mouse click (typically x≈602, y≈601)
4. No confirmation dialog — toggle activates immediately
5. Verify: text after "Web Search" should say "Enabled"

**Pitfall:** `aria-checked` may be null. Check page text ("Enabled"/"Disabled") to verify.

## Evaluation Page
Direct `/evaluation` URL works but takes 20-30s. Heavy eval detail pages (100 cases) can hang Chrome.

## Chrome Stability
Use `--disable-background-timer-throttling --disable-renderer-backgrounding` flags. If Chrome hangs (CDP 30s timeout but `curl` health check still works), kill and restart — the curl success is deceptive since it's HTTP not WebSocket.
