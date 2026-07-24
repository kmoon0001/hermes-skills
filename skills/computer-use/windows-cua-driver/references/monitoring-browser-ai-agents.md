# Monitoring Browser-Based AI Agents

Pattern for polling and verifying completion of AI agents (Gemini, Copilot, etc.)
working in the user's Chrome browser on Power Automate, Copilot Studio, or similar web apps.

Uses `computer_use(action="capture", app="Chrome")` for all monitoring — no MCP tools needed.

## Poll: Is the Agent Still Working?

Capture Chrome and check these signals:

```
computer_use(action="capture", app="Chrome")
```

**Working signals (still running):**
- Tab title contains `"Gemini is working on your task…"` (or similar LLM-agent text)
- A `"Stop response"` / `"Stop"` button (role=Button with that label) is present
- The agent's input field shows progress text, not `"Enter a prompt"`

**Completed signals (done):**
- Tab title no longer says `"Gemini is working…"`
- `"Stop response"` button is gone
- Input field shows `"Enter a prompt for Gemini"` or `"Type / to use skills"`
- A submit/chat button is visible instead of a stop button

Look at the element list for these. The Power Automate tab title will say
`"Edit your flow | Power Automate"` (no "working" suffix) when done.

## Polling Cadence

Wait 15-30s between polls. Power Automate flows take 30s-5min depending on
complexity. Typical loop:

1. Capture Chrome
2. Check tab title or element list for completion signals
3. If still working, `computer_use(action="wait", seconds=15)` then repeat
4. If done, proceed to verify

Don't hammer <10s intervals — captures are non-trivial (screenshot + AX tree).

## Verifying Save in Power Automate

After the agent finishes, the flow may auto-save but always verify:

1. Capture Chrome (the Power Automate tab)
2. Look for a `"Save draft"` button (role=Button) in the toolbar
3. If present AND ENABLED (not greyed), the flow has unsaved changes — click it
4. If missing or disabled, the flow is already saved

## Verifying Publish Status

1. Look for `"Publish"` button in the toolbar
2. If enabled: highlighted blue/active — published state differs from draft
3. If disabled/greyed: draft matches published state

## Chrome Tab Switching via UIA TabItem

When the browser window shows the wrong tab (user switched tabs, page navigated away),
switch back to the desired Chrome tab using UIA TabItem elements:

1. Run `get_window_state(pid, window_id)` on the Chrome window
2. Look for elements with `role='TabItem'` whose `label` contains your target title
   (e.g. `"Edit your flow | Power Automate"`)
3. Select it: `mcp_cua_driver_click(pid, window_id, element_index=N)` on the TabItem
4. The browser switches to that tab — verify with a follow-up capture

**TabItem elements** are typically found at the top of the UIA tree (depth ~8),
in the same window as the current active tab. They remain accessible even when
another tab is active. Look for elements like:
- `role=TabItem, label="Edit your flow | Power Automate"` — the target tab
- `role=TabItem, label="DeepSeek Platform - Memory usage - 64.5 MB"` — may also be present

The `role="TabItem"` pattern works because the UIA tree exposes ALL tabs in the
window as siblings, regardless of which one is active. This is more reliable than
pixel-coordinate clicking on the tab strip.

## Tab Restore After Chrome Crash

Chrome's "Restore pages?" dialog (shown after an unclean shutdown) has buttons:

2. **Gemini conversation may show "New Conversation" at first** — this is a cosmetic
   issue. After getting the full `get_window_state`, the actual Gemini tab title
   reveals the real conversation (e.g. "Gemini Chrome :: Invalid Character in Dataverse Field").
   Check `elements` for the `Document` with `value="chrome://glic/"` — its child
   `Document` will have the real title.

3. **If "Open Gemini in Chrome" button is visible** instead of the side panel,
   click it (element 42 on Power Automate pages) to reopen the Gemini side panel
   on the shared tab.

4. **Gemini task progress is lost** even when the conversation is restored — the
   step-by-step action list is preserved but the agent won't resume. You need to
   take over manually or re-prompt.

## Power Automate Flow Testing

Flows with `"When Copilot Studio calls a flow"` trigger:
- **Manual mode** shows "This flow cannot be triggered for testing."
- **Automatically mode** must be selected, then "With a recently used trigger."
- Click **Test** to run with cached trigger data

After saving a draft, the flow status changes from "Published" to "Draft" and
shows "We saved your draft flow. You can test and run it after you publish."
You must publish before it can be tested again with a new trigger.

## Flow Node Search

Instead of scrolling the canvas to find specific actions:

1. Click **"Search workflow actions"** (left toolbar, element ~76-83)
2. Type the action name in the "Search for operation" input
3. Click the result to navigate directly to that action in the canvas
4. The properties panel opens for the selected action

## Power Automate Flow Definition via API

When the Power Automate UI is too slow to navigate, fetch the full flow
definition via the management API:

```bash
# Get token
token=$(az account get-access-token --resource https://service.powerapps.com/ --query accessToken -o tsv)

# Fetch flow definition
env="<environment-id>"
flow_id="<flow-id>"
curl -s -H "Authorization: Bearer $token" \
  "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/$env/flows/$flow_id?api-version=2016-11-01"
```

The response contains `properties.definition` with the full JSON workflow
definition including all triggers, actions, branches, and expressions.

**PATCH limitation:** The management API is read-only for flow definitions.
PUT/PATCH fails with:
> *"unpublished active row"*

To update a flow, use the UI Code view tab (paste modified `properties.definition`
JSON) or the Dataverse API against the workflow entity directly.

**Dataverse API (when DNS resolves):**
```bash
token=$(az account get-access-token --resource https://<org>.crm.dynamics.com --query accessToken -o tsv)
curl -s -X PATCH \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"clientdata": "<escaped workflow definition JSON>"}' \
  "https://<org>.crm.dynamics.com/api/data/v9.2/workflows(<workflow-unique-id>)"
```

Note: Corporate Dataverse instances (e.g. `powervamg.*.crm.dynamics.com`)
use internal DNS that may not resolve from git-bash terminal. Only the
browser can reach them. Use PowerShell as an alternative terminal, or
work through the Power Automate UI directly.

## Dataverse Entity Mapping (Notes/annotations)

Power Automate's Dataverse connector entity names:
- **`annotations`** = Notes table (file attachments)
  - `item/subject` = Title/Subject
  - `item/notetext` = Description/Note text
  - `item/documentbody` = File content (base64-encoded)
  - `item/filename` = Original file name
  - `item/mimetype` = MIME type (e.g. `application/pdf`)

## Dataverse "Invalid Character" Fix

When a Power Automate "Create a new row" action on the Dataverse `annotations`
(Notes) table fails with "Invalid Character in Dataverse Field":

**Root cause:** The `documentbody` field (nvarchar) rejects certain control
characters found in PDF/document binary converted to base64. Common offenders:
- `%00` (0x00) — null byte
- `%12` (0x12) — Data Link Escape
- `%01`-`%08`, `%0B`, `%0C`, `%0E`-`%1F` — other control chars

**Comprehensive sanitization (strips 0x00-0x1F except tab/LF/CR):**

```
@replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(outputs('Resolve_file_content_base64'), decodeUriComponent('%00'), ''), decodeUriComponent('%01'), ''), decodeUriComponent('%02'), ''), decodeUriComponent('%03'), ''), decodeUriComponent('%04'), ''), decodeUriComponent('%05'), ''), decodeUriComponent('%06'), ''), decodeUriComponent('%07'), ''), decodeUriComponent('%08'), ''), decodeUriComponent('%0B'), ''), decodeUriComponent('%0C'), ''), decodeUriComponent('%0E'), ''), decodeUriComponent('%0F'), ''), decodeUriComponent('%10'), ''), decodeUriComponent('%11'), ''), decodeUriComponent('%12'), ''), decodeUriComponent('%13'), ''), decodeUriComponent('%14'), ''), decodeUriComponent('%15'), ''), decodeUriComponent('%16'), ''), decodeUriComponent('%17'), ''), decodeUriComponent('%18'), ''), decodeUriComponent('%19'), ''), decodeUriComponent('%1A'), ''), decodeUriComponent('%1B'), ''), decodeUriComponent('%1C'), ''), decodeUriComponent('%1D'), ''), decodeUriComponent('%1E'), ''), decodeUriComponent('%1F'), '')
```

For maintainability, add a **Compose action** after the base64 resolution that
does the sanitization, then reference `@outputs('Sanitize_document_body')` in
the `item/documentbody` field. This separates concerns and keeps the expression
readable.

**Diagnostic approach:**
1. Look at test history (Test > Automatically > With a recently used trigger)
   for "Succeeded" vs "Failed" entries
2. Click a "Failed" entry to inspect the error
3. Check the Code view tab on the failing action for the current expression

## The Draft → Publish → Test Cycle

Power Automate flows must be **Published** before they can be tested with new trigger data:

1. **Save draft** — Click the "Save draft" button. Shows "We saved your draft flow. You can test and run it after you publish."
2. **Publish** — Click "Publish" to promote the draft to the active version
3. **Test** — Only after publishing can you run the "Automatically" test with "With a recently used trigger."

The flow name subtitle changes:
- `•Published` = has been published, testable
- `•Draft` = has unsaved changes, must publish before testing

You cannot test a draft flow that has never been published.

## Deep-Nested Flow Navigation

Actions inside Switch/If branches and their sub-branches are deeply nested in the
UIA tree and often off-screen. The **Node Search panel** is the only reliable way
to reach them:

1. Click **"Search workflow actions"** (left toolbar)
2. The search panel opens showing ALL flow actions in a flat scrollable list —
   including actions nested inside Switch cases, If/Else branches, For-each loops,
   and sub-branches at any depth
3. Type a partial action name in the **"Search for operation"** input to filter
4. Click the result to navigate directly to that action in the canvas AND open
   its properties panel
5. The canvas auto-scrolls and selects the action

**Why this works:** The search panel scans the full `properties.definition.actions`
tree recursively, not just the visible canvas DOM. Deeply nested actions that
would require multiple Expand clicks + scrolling are all exposed as flat results.

**Tree expansion via UIA (fallback when search panel is unreliable):**
1. Collapsed Switch/If nodes show only the node header — look for an "Expand" button
2. Click it to reveal branch headers ("True condition", "False condition")
3. Each branch header has its own Expand/Collapse button
4. Expand the target branch to see its child actions
5. If branches contain nested If/Switch nodes, repeat recursively
6. Each expansion shifts viewport — the canvas may need scrolling between clicks

## Code View Editing via UIA set_value (BEST APPROACH)

Power Automate's Code view editor exposes its content via UIA ValuePattern,
making `mcp_cua_driver_set_value` the most reliable way to replace the full
action JSON in one shot.

**Recipe:**
1. Navigate to the target action (using Node Search panel or expanding branches)
2. Switch to the **Code view** tab (click TabItem "Code view", typically element ~106)
3. Find the editor element — look for an `Edit` with label `"Editor content"`
   (typically at `element_index` ~111, under a `Text` container, inside the
   Operation details panel)
4. Call `mcp_cua_driver_set_value(pid, window_id, element_index=N, value="<full JSON>")`
5. The editor accepts the full JSON string via UIA ValuePattern.SetValue — no
   type-char-by-char needed, works with content up to at least ~5KB
6. Click **Save draft** to persist

**Why this works:** The Monaco editor (used by Power Automate) implements
UI Automation ValuePattern on its textarea peer. `set_value` calls
`IUIAutomationValuePattern::SetValue` which replaces the entire document
content atomically. The `value` attribute visible in `get_window_state`
output is truncated (~200 chars) but the actual write accepts much larger
content.

**Example pattern (Power Automate flow action JSON):**
```python
mcp_cua_driver_set_value(
    pid=<pid>,
    window_id=<window_id>,
    element_index=111,  # "Editor content" element after Code view tab selected
    value='{"type": "OpenApiConnection", "inputs": {"parameters": {...}}}'
)
```

**Always verify by re-snapshotting the editor's `value` attribute after write,**
then clicking **Save draft** (look for "Save draft" button in toolbar). If
the save succeeds, the flow can be published.

## Alternative Approaches (when set_value fails or isn't available)

1. **Use the Parameters tab instead** — For simple single-field edits (changing
   one expression), stay on the Parameters tab and edit the field directly.
2. **API fetch → edit → paste via set_value** — Fetch via management API,
   edit locally, then use `set_value` on the Code view editor (above).
3. **UIA post-click into editor** — Click into the editor by element index.
   Does NOT give you write access but does focus the editor.

## API Paths — Working vs Non-Working

**WORKING — Power Automate management API (read-only, external DNS):**
```bash
# Get token
token=$(az account get-access-token --resource https://service.powerapps.com/ --query accessToken -o tsv)
# Fetch flow definition
curl -s -H "Authorization: Bearer $token" \
  "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/$env/flows/$flow_id?api-version=2016-11-01"
```
This resolves from any network and returns the full flow definition JSON.
Use for diagnostics and offline editing.

**NON-WORKING — PUT/PATCH to same endpoint:**
The management API is read-only. PUT/PATCH fails with "unpublished active row" error.
Cannot update flows through this API.

**WORKING — Dataverse API (write, internal DNS only):**
```bash
token=$(az account get-access-token --resource https://<org>.crm.dynamics.com --query accessToken -o tsv)
curl -s -X PATCH -H "Authorization: Bearer $token" -H "Content-Type: application/json" \
  -d '{"clientdata": "..."}' \
  "https://<org>.crm.dynamics.com/api/data/v9.2/workflows(<workflow-unique-id>)"
```
Only works from environments where the corporate DNS resolves. Git-bash terminal
often cannot resolve `powervamg.*.crm.dynamics.com`. PowerShell may have different
DNS resolution behavior. The browser can always reach these URLs.

**BEST PRACTICE:** Fetch via management API (read), edit the JSON offline, then
paste the modified `properties.definition` into the Power Automate UI's Code view
tab. This avoids both the API write limitation and the DNS resolution issue.

## Pitfalls

- **Tab navigated away:** If Gemini isn't responding, the user may have switched tabs.
  Check the tab bar for the title — the current capture window may be a different tab.
- **Hidden side panel:** Gemini's side panel can be collapsed or closed. Refresh the
  Power Automate page if you don't see it but expect it.
- **"Take over task" button:** If present, Gemini hit a wall and needs human input
  (CAPTCHA, confirmation dialog, etc.). Report this to the user — don't click it.
- **Flow checker warnings:** After Gemini modifies a flow, the "Flow checker" icon
  may show warnings (yellow/red). These don't block save but may block publish.
- **Multiple Chrome windows:** Use `app="Chrome"` — it captures whichever Chrome window
  is most recently used. If the user has multiple Chrome windows, the wrong one may
  be captured. Check the `window_title` in the capture result.
- **Element cache expires after dialog close:** When you close a modal dialog
  (e.g. "Test Flow"), the element cache for that window is invalidated. Always
  call `get_window_state` again before the next click on the same window.
- **Scroll doesn't work via background delivery on Chromium:** Chromium
  `Chrome_WidgetWin_1` windows don't accept background scroll events. Use
  `query_dom` or `execute_javascript` to navigate, or foreground scroll.
- **get_text captures incomplete content:** On complex SPAs like Power Automate,
  `get_text()` only returns visible/rendered text, not the full page content.
  Use Code view tab for action JSON, or `query_dom` for structured reads.
