---
name: playwright-hermes
description: >
  Browser automation, web UI testing, and visual verification via Playwright CLI + CDP.
  Persistent sessions with exported Kiro auth. Full Copilot Studio topic edit workflow
  with before/after visual verification.  Use for: navigating web apps, filling forms,
  taking screenshots, scraping data, debugging live web UIs (especially Copilot Studio,
  Power Platform, Power Automate), running visual QA, batch topic updates, or any
  browser-based tool interaction that requires SSO auth persistence.
---

# Playwright Hermes — Browser Automation & Visual Verification

Drive Chrome from the terminal using `playwright-cli`.  This skill covers:
1. **Basic browser automation** (open, click, fill, snapshot, screenshot)
2. **Persistent SSO auth sessions** (export from Kiro, reuse across turns)
3. **Copilot Studio topic editing with visual verification** (before/after screenshots, error checking)
4. **Chrome DevTools Protocol** for deep debugging
5. **Computer-use subagent integration** for complex multi-step workflows

## Tool Map

| Tool | When to use |
|------|-------------|
| `playwright-cli` (npx) | Primary CLI browser automation |
| Hermes `browser_*` tools | Quick one-off page loads (no SSO needed) |
| **Raw CDP via Node.js WebSocket** | Copilot Studio automation when playwright-cli auth fails (expired MSAL tokens, partitionKey errors). Use `references/cdp-copilot-studio-automation.md` for full patterns. |
| `chrome-devtools-mcp` (npx) | CDP: console, network, performance |
| `export_kiro_auth.cjs` | Export Kiro auth → reusable session (CDP-based) |
| `delegate_task` (browser+terminal) | Complex multi-step browser workflows |

## Prerequisites

```bash
# Verify all prerequisites
node --version          # need v18+
command -v npx         # must exist
ls "/c/Program Files/Google/Chrome/Chrome.exe"  # Chrome on PATH (added to .bashrc)
npx playwright-cli --help | head -3
```

Chrome is on PATH at `C:\Program Files\Google\Chrome\Application` (added to `~/.bashrc`).

If `playwright-cli` can't find Chrome:
```bash
export PLAYWRIGHT_CHROME_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe"
```

---

## 1. BASIC BROWSER AUTOMATION

```bash
# Open headed (visible window)
npx playwright-cli open https://example.com --headed

# Snapshot → get element refs (e1, e2, e3...)
npx playwright-cli snapshot

# Interact using refs
npx playwright-cli click e3
npx playwright-cli fill e5 "user@example.com"
npx playwright-cli type "hello world"
npx playwright-cli press Enter

# Screenshot
npx playwright-cli screenshot

# Navigate
npx playwright-cli goto https://example.com/page2

# Select dropdown
npx playwright-cli select e7 "Option A"

# Check/uncheck
npx playwright-cli check e10
npx playwright-cli uncheck e10

# Drag and drop
npx playwright-cli drag e3 e8

# Hover
npx playwright-cli hover e5
```

---

## 2. PERSISTENT AUTH SESSIONS

### 2a. Check for existing auth

```bash
# Check if Kiro auth export already exists
ls 'C:\Users\kevin\.hermes-browser-session\auth.json' 2>/dev/null && echo "Auth export exists" || echo "No auth export — run export_kiro_auth.cjs first"
```

### 2b. Export auth from Kiro (one-time setup)

Kiro's `.playwright-auth/` has ~243 encrypted cookies + MSAL token cache in localStorage.
To export them as reusable storageState JSON:

```bash
# Requires: Chrome, Node.js, ws module (npm install -g ws)
# Launches Chrome with Kiro's profile, exports cookies + localStorage, saves auth.json
NODE_PATH=$(npm root -g) node scripts/export_kiro_auth.cjs
```

This produces `C:\Users\<you>\.hermes-browser-session\auth.json` with:
- **All cookies** — `MC1`, `fpc`, `brcap`, MSAL session cookies from `.login.microsoftonline.com`, `copilotstudio.microsoft.com`, etc.
- **localStorage** — MSAL.js token cache (65+ items) which is critical for SSO

**If the script doesn't work** (Chrome launch issues), manually run:

```bash
# Step 1: Launch Chrome with Kiro profile in background
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9223 \
  --user-data-dir="C:\Users\kevin\AppData\Local\Programs\Kiro\.playwright-auth" \
  --no-first-run --no-default-browser-check \
  --disable-extensions \
  about:blank &

# Step 2: Wait for CDP, then export
NODE_PATH=$(npm root -g) node scripts/export_kiro_auth.cjs
```

### 2c. Use the exported auth

Use `state-load` to inject cookies + localStorage into any playwright-cli session:

```bash
# Start a session (any name works)
npx playwright-cli --session cs-session open https://example.com

# Load the Kiro auth (cookies + MSAL token cache)
npx playwright-cli --session cs-session state-load 'C:\Users\kevin\.hermes-browser-session\auth.json'

# Now navigate to Copilot Studio — already authenticated!
npx playwright-cli --session cs-session goto https://copilotstudio.microsoft.com

# Snapshot to confirm logged-in (should see environments/home page)
npx playwright-cli --session cs-session snapshot

# Take a screenshot for visual verification
npx playwright-cli --session cs-session screenshot
```

**Session naming:** Use simple names like `cs-session`, `pw-session`, etc. (not paths).
The `--session` flag on Windows/MSYS has issues with path arguments, so use **names only**.

**Save auth back** after any new login (e.g., if session expired):
```bash
npx playwright-cli --session cs-session state-save 'C:\Users\kevin\.hermes-browser-session\auth.json'
```

---

## 3. COPILOT STUDIO — FULL WORKFLOW WITH VISUAL VERIFICATION

This is the primary workflow for designing, implementing, troubleshooting, testing,
and refactoring Copilot Studio agents.

### 3a. Start Session + Load Auth

```bash
# Use simple session name (not a path)
npx playwright-cli --session cs open https://example.com

# Load Kiro auth (286 cookies + MSAL localStorage tokens)
npx playwright-cli --session cs state-load 'C:\Users\kevin\.hermes-browser-session\auth.json'

# Navigate to bot topics
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/topics"
sleep 5
npx playwright-cli --session cs screenshot
```

### 3b. BEFORE Screenshot (baseline)

**Always take a before screenshot before making changes:**

```bash
npx playwright-cli --session cs screenshot
# Saves to .playwright-cli/page-<timestamp>.png
# OR specify path:
npx playwright-cli --session cs screenshot ~/before_edit.png
```

Use `vision_analyze` to record the baseline state:
```
vision_analyze("~/before_edit.png",
  "Describe: topic list, any visible errors in the Errors column, topic count, search box state")
```

### 3c. Search and Open a Topic

```bash
# Search for the topic
npx playwright-cli --session cs snapshot
# Find the search input ref, then:
npx playwright-cli --session cs fill <search-ref> "Topic Name"
sleep 2

# Take screenshot of search results (VERIFY visually)
npx playwright-cli --session cs screenshot ~/search_results.png
# → vision_analyze to confirm the right topic appeared

# Click the topic link
npx playwright-cli --session cs click <topic-link-ref>
sleep 5

# Screenshot: topic editor loaded?
npx playwright-cli --session cs screenshot ~/topic_opened.png
# → vision_analyze to confirm topic editor is open and content is visible
```

### 3d. Open Code Editor

```bash
# CRITICAL: Use has-text, NOT aria-label
npx playwright-cli --session cs snapshot
# Find the "More" button ref, then:
npx playwright-cli --session cs click <more-btn-ref>
sleep 1.5

# Screenshot: did the menu open?
npx playwright-cli --session cs screenshot ~/menu_open.png
# → vision_analyze: "Is the dropdown menu visible with 'Code editor' option?"

# Click "Code editor" menu item
npx playwright-cli --session cs click <code-editor-menuitem-ref>
sleep 4

# Screenshot: code editor loaded?
npx playwright-cli --session cs screenshot ~/code_editor_open.png
# → vision_analyze: "Is the Monaco editor visible? Is YAML content displayed?"
```

### 3e. Replace Topic Content

```bash
# Select all existing content
npx playwright-cli --session cs press "Control+A"
sleep 0.5

# Paste new YAML content via clipboard
# For small content (<500 chars), use clipboard:
npx playwright-cli --session cs eval "navigator.clipboard.writeText(\`YOUR_YAML_HERE\`)"
sleep 0.5
npx playwright-cli --session cs press "Control+V"
sleep 1

# Screenshot: content replaced?
npx playwright-cli --session cs screenshot ~/content_pasted.png
# → vision_analyze: "Does the Monaco editor show the new YAML content? Any inline validation errors?"

# For large content (>500 chars), fill the textarea directly:
# npx playwright-cli --session cs eval "
#   const editor = document.querySelector('.monaco-editor textarea');
#   if (editor) { editor.focus(); document.execCommand('insertText', false, \`LARGE_YAML\`); }
# "
```

### 3f. Save

```bash
npx playwright-cli --session cs press "Control+S"
sleep 4

# Screenshot: save confirmed?
npx playwright-cli --session cs screenshot ~/after_save.png
# → vision_analyze: "Any error toasts? Is the page still on the topic editor or did it navigate back?"
```

### 3g. AFTER Screenshot + Visual Comparison

```bash
# Navigate back to topics list to verify
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/topics"
sleep 5

# Screenshot: topics list with error column
npx playwright-cli --session cs screenshot ~/after_edit_topics_list.png
```

**Visual verification checklist** — use `vision_analyze` on each screenshot:

1. **Topics list view:** Are there numbers in the "Errors" column? (0 = good)
2. **Topic row:** Does the topic name match what you edited?
3. **Page state:** Any error toasts, banners, or modal dialogs?
4. **Consistency:** Does the topic count match your expectation?

### 3h. Using the Visual Verify Workflow

The workflow itself is the verification — no automated Python script needed. Use
playwright-cli screenshots + `vision_analyze` at each step:

## 4. KNOWLEDGE SOURCE FILE RENAME & REDESCRIBE

Rename uploaded knowledge source files and rewrite their descriptions in Copilot Studio — critical for moving from raw filenames like `aota-apta-asha-consensus-statement.pdf` to clean names like `AOTA/APTA/ASHA Consensus Statement on Therapy Documentation`.

### 4a. Files Tab — Where Uploaded Files Live

**CRITICAL DISTINCTION:** Uploaded files only appear under the **Files** filter tab on the Knowledge page, NOT the "All" view. The "All" view only shows Public website and SharePoint sources. To see uploaded files, click the **Files** tab (`ref=e190` in the snapshot tab bar) first.

### 4b. Full Rename + Redescribe Workflow

For each file that needs renaming:

```bash
# 1. Navigate to the knowledge page
npx playwright-cli --session <session> goto "https://copilotstudio.microsoft.com/environments/<env>/bots/<botId>/knowledge"
sleep 12

# 2. Click the Files tab to reveal uploaded files
npx playwright-cli --session <session> snapshot
# Find "button \"Files\" [ref=eNNN]" in snapshot output
npx playwright-cli --session <session> click e190
sleep 6

# 3. Click the file link to open its detail page
npx playwright-cli --session <session> snapshot
# Find "link \"filename.pdf\" [ref=eNNN]" in snapshot output
npx playwright-cli --session <session> click eNNN
sleep 6

# 4. SET NAME — use React native value setter (REQUIRED for CS inputs)
npx playwright-cli --session <session> eval "(function(){ var inp = document.querySelector('input[placeholder=\"Enter name\"]'); var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; s.call(inp, 'New Clean Name Here'); inp.dispatchEvent(new Event('input', {bubbles:true})); inp.dispatchEvent(new Event('change', {bubbles:true})); return 'name set'; })()"

# 5. SET DESCRIPTION — use React native value setter for textarea
npx playwright-cli --session <session> eval "(function(){ var ta = document.querySelector('textarea'); var s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set; s.call(ta, 'Provides... Use when... Covers...'); ta.dispatchEvent(new Event('input', {bubbles:true})); ta.dispatchEvent(new Event('change', {bubbles:true})); ta.dispatchEvent(new Event('blur', {bubbles:true})); return 'desc set'; })()"

# 6. SAVE — click the "Save knowledge changes" button (Ctrl+S DOES NOT WORK here)
npx playwright-cli --session <session> snapshot
# Find "button \"Save knowledge changes\" [ref=eNNN]"
npx playwright-cli --session <session> click eNNN
sleep 4
```

**PITFALL: Ctrl+S does NOT persist on the knowledge source detail page.** The "Save knowledge changes" button MUST be clicked directly. This is different from the topic code editor where Ctrl+S works.

### 4c. Using Direct URLs for Known Component IDs

If you know the knowledge source component ID (from Dataverse or a previous navigation), navigate directly:
```
https://copilotstudio.microsoft.com/environments/<env>/bots/<botId>/knowledge/<componentId>/details
```
This avoids the slow Files tab navigation step.

### 4d. Microsoft Learn Description Pattern

Follow this pattern for all knowledge source descriptions:
```
Provides [source content]. Use when [query intent / user scenario]. Covers [key topics].
```
**Good example:** "Provides CMS Medicare Benefit Policy Manual Chapter 15 on covered medical services. Use when auditing skilled therapy documentation for Medicare Part B coverage, determining reasonable and necessary criteria, or verifying qualifying service definitions. Covers skilled PT, OT, and SLP services, outpatient therapy thresholds, the therapy cap exceptions process, and supervision requirements."

**Bad example:** "This knowledge source searches information contained in Medicare Benefits Policy Manual Chapter 15.pdf"

### 4e. Batch Rename Pattern (Multiple Files)

```bash
# For each file:
# 1. Navigate to knowledge page (refreshes the list)
npx playwright-cli --session <session> goto "https://copilotstudio.microsoft.com/environments/<env>/bots/<botId>/knowledge"

# 2. Click Files tab
npx playwright-cli --session <session> click e190
sleep 6

# 3. Click file link (get ref from snapshot)
npx playwright-cli --session <session> click eNNN
sleep 6

# 4. Set name + description
# 5. Click "Save knowledge changes" button
# 6. Repeat for next file
```

### 4f. Knowledge Source Detail Page — Save Pitfall

**CRITICAL:** On the knowledge source detail page (`/knowledge/<componentId>/details`), pressing `Ctrl+S` does NOT persist changes. The **"Save knowledge changes"** button (`button:has-text("Save knowledge changes")`) MUST be clicked. This is different from every other editor in Copilot Studio (topic Monaco editor, instructions contentEditable). Always click the button, not the keyboard shortcut.

### 4g. Files vs All Tab Distinction

Uploaded knowledge source files (PDFs, DOCX) only appear under the **Files** filter tab — NOT the "All" view. The "All" view only shows Public website and SharePoint sources. Always click the Files tab first when you need to see uploaded documents.

---

## 5. VISUAL VERIFICATION PROTOCOL

Since Copilot Studio rejects changes that don't conform to its UI expectations,
always verify visually — not just with snapshots.

### Verification Steps (after EVERY edit)

| Step | Screenshot | What to check |
|------|-----------|---------------|
| 1. Before | `before_edit.png` | Baseline: topic list state, error column |
| 2. Menu open | `menu_open.png` | Dropdown appeared with "Code editor" option |
| 3. Code editor | `code_editor_open.png` | Monaco editor visible, content loaded |
| 4. Content pasted | `content_pasted.png` | New YAML in editor, no inline errors |
| 5. After save | `after_save.png` | No error toast, save succeeded |
| 6. Topics list | `after_edit_topics_list.png` | Errors column shows 0, topic name correct |

### Using vision_analyze for Each Screenshot

```
vision_analyze("~/after_edit_topics_list.png",
  "Check: (1) Numbers in Errors column — should be 0. (2) Topic name visible. (3) No red error banners. (4) Page fully loaded?")
```

**If errors found:**
- Inline validation errors in Monaco → fix YAML syntax before saving
- Numbers in Errors column → topic has validation issues, click into topic to see details
- Error toast → the save was rejected; the UI rejected the change. Re-open and fix.

---

## 6. COPILOT STUDIO NAVIGATION PATTERNS

### 6a. Environment Switching

When an agent is in a different environment than the one currently loaded:

```bash
# 1. Click the environment selector in the top bar
npx playwright-cli --session cs eval "(function(){
  var els = document.querySelectorAll('span, button, div');
  for(var i=0;i<els.length;i++){
    if(els[i].textContent.includes('Ensign Services') || els[i].textContent.includes('Therapy AI Agents')){
      els[i].click(); return 'clicked env selector';
    }
  }
})()"

# 2. Wait for the "Select environment" panel to slide out (right side)
sleep 4

# 3. Click the target environment in the panel
npx playwright-cli --session cs eval "(function(){
  var all = document.querySelectorAll('span, div, button, [role=option]');
  for(var i=0;i<all.length;i++){
    if(all[i].textContent.trim()==='Ensign Services (default)' && all[i].offsetParent!==null){
      all[i].click(); return 'clicked';
    }
  }
})()"

# 4. Wait 8-10s for redirect to new environment
```

### 6e. Conversation Start Topic — Greeting Editing

The **Conversation Start** system topic defines the agent's first message and suggested action buttons. Editing it follows the standard topic code-editor workflow but requires finding the component ID first.

**Finding the component ID:**
```
pac org fetch --environment <env-url> --xml "
<fetch><entity name='botcomponent'>
  <attribute name='botcomponentid'/><attribute name='name'/>
  <filter>
    <condition attribute='componenttype' operator='eq' value='9'/>
    <condition attribute='parentbotid' operator='eq' value='<botId>'/>
    <condition attribute='name' operator='eq' value='Conversation Start'/>
  </filter>
</entity></fetch>"
```

**Navigating and editing:**
```bash
# Navigate to the topic's adaptive editor
npx playwright-cli --session <s> goto \
  "https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/adaptive/<componentId>"
sleep 12

# Click "More" button → "Open code editor"
npx playwright-cli --session <s> snapshot
# Find More button ref (usually first button with text "More")
npx playwright-cli --session <s> click <more-ref>
sleep 2
npx playwright-cli --session <s> snapshot
# Find "Open code editor" menuitem
npx playwright-cli --session <s> click <code-editor-ref>
sleep 5

# Fill with greeting YAML using Monaco textbox
npx playwright-cli --session <s> snapshot
# Look for textbox with placeholder containing "Editor content"
npx playwright-cli --session <s> fill <editor-ref> "$(cat greeting.yaml)"

# Save
npx playwright-cli --session <s> press "Control+S"
sleep 3
```

**PITFALL — Suggested actions not visible in topic page:** The `suggestedActions` values are stored in the YAML but only render as clickable buttons in the test chat pane or published agent — NOT on the topic editor page or in the page text. The only way to see them is to open the test chat and look for buttons beneath the greeting bubble. Do not consider the greeting "broken" just because you can't see suggested actions in the editor.

See the `copilot-studio-development-workflow` skill's `templates/conversation-start-greeting.yaml` for a reusable greeting template.

### 6f. Bot Discovery in an Environment

To find bot IDs and names in an environment:

```bash
# Navigate to agents list
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/environments/<envId>/bots"

# Poll for grid load (can take 30-40s)
npx playwright-cli --session cs eval "(function(){
  return document.body?.innerText?.includes('My agents') ? 'loaded' : 'waiting';
})()"
```

Each agent row has an `<a>` link with empty href (JS-driven). To extract the bot ID, click the agent name and watch for navigation to `/overview` — the URL contains the bot ID. Or use `pac copilot list` after authenticating.

### 6c. Topics Tab Navigation

The `/topics` URL redirects to `/overview` in Copilot Studio. To reach topics:

1. Navigate to `/overview` first
2. Click the Topics tab button in the agent's tab bar
3. The "+8" overflow tab may hide Topics — click it first to expand

```bash
npx playwright-cli --session cs goto ".../overview"
sleep 10

# Click "+8 more" overflow tab, then "Topics"
npx playwright-cli --session cs eval "(function(){
  var tabs = document.querySelectorAll('[role=tab]');
  for(var i=0;i<tabs.length;i++){
    if(tabs[i].textContent.includes('more')){
      tabs[i].click(); return 'clicked +8';
    }
  }
})()"
sleep 3
npx playwright-cli --session cs eval "(function(){
  var all = document.querySelectorAll('[role=tab], [role=menuitem]');
  for(var i=0;i<all.length;i++){
    if(all[i].textContent.trim()==='Topics' && all[i].offsetParent!==null){
      all[i].click(); return 'clicked';
    }
  }
})()"
```

### 6d. Topic Toggle (On/Off)

To toggle a topic ON or OFF in the topics grid:

```bash
# Find the row, then the switch input, then set checked + dispatch events
npx playwright-cli --session cs eval "(function(){
  var sw = document.querySelector('input[aria-label=\"On\"][role=\"switch\"]');
  if(sw){
    sw.checked = true;
    sw.setAttribute('aria-checked', 'true');
    sw.dispatchEvent(new Event('change', {bubbles: true}));
    sw.dispatchEvent(new Event('click', {bubbles: true}));
    return 'toggled';
  }
})()"
```

**Pitfall:** `.click()` on CS toggle switches doesn't toggle them. You MUST set `.checked` + dispatch `change` and `click` events.

### 6d. Agent Instructions Editing — Multiple Edit Buttons Pitfall

The SLP_Specialist, PT_Specialist, OT_Specialist, and similar agents have agent **instructions** on the Overview page. The page has **three** `Edit` buttons. They are NOT the same.

**Which Edit to click:**
1. **Edit [ref=e176/highest-numbered visible]** — Description editor (under "Details" heading). If you see agent description text after clicking, you hit the wrong one.
2. **Edit [disabled]** — Near publish area — not functional.
3. **Edit [ref=e535/lowest-numbered visible]** — Instructions editor — this is the target.

**Problem:** Clicking the first `Edit` (Description) opens a `div[contenteditable]` that becomes `contentEditable=true`, but it's the wrong field. You'll see the agent description, not the instructions.

**How to reliably find and click the Instructions Edit:**
```bash
# In the snapshot, look at what's near each Edit button:
# "Details" heading before Edit → Description editor
# The Instructions section heading before Edit → this is the target
# Click the last visible Edit button
npx playwright-cli --session <session> click e535
```

```javascript
// Via CDP — click all Edit buttons, check which one worked by finding contentEditable
var btns = document.querySelectorAll('button');
for(var i=0;i<btns.length;i++){
  if(btns[i].textContent.trim() === 'Edit' && btns[i].offsetParent !== null){
    btns[i].dispatchEvent(new MouseEvent('click', {bubbles:true}));
  }
}
```

**Pitfall:** After clicking Edit, `contentEditable` may remain `false` for 1-3s while React processes. Wait 3-5s before reading. If it stays `false`, dispatch a `MouseEvent` instead of `.click()`.

**Setting instructions content reliably:**
```javascript
var ed = document.querySelector('[contenteditable]');
if(ed && ed.contentEditable === 'true'){
  ed.focus();
  ed.innerText = 'New instructions here...';
  ed.dispatchEvent(new Event('input', {bubbles:true}));
  ed.dispatchEvent(new Event('change', {bubbles:true}));
}
```

**CRITICAL — How to save:** The contentEditable div does NOT reliably save via Ctrl+S. After setting content:
1. Click the **Save** button in the page toolbar
2. Or let auto-save fire (wait 5s after the last event)
3. Navigate away and back to verify the content persisted
This is different from the topic code editor (Monaco), where Ctrl+S works reliably.

The topic trigger description is NOT edited by clicking the Edit button. Instead:

1. Click the DESCRIPTION TEXT itself (e.g., "Use ONLY when the user uploads...")
2. This opens an inline `<textarea>` with the current value
3. Set the value and save

```bash
# Click description text to open textarea
npx playwright-cli --session cs eval "(function(){
  var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  var node;
  while(node = walker.nextNode()){
    if(node.textContent.includes('ONLY when the user uploads')){
      node.parentElement.click(); return 'clicked';
    }
  }
})()"
sleep 3

# Set new value
npx playwright-cli --session cs eval "(function(){
  var tas = document.querySelectorAll('textarea');
  for(var i=0;i<tas.length;i++){
    if(tas[i].value && tas[i].value.includes('upload')){
      var nv = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      nv.call(tas[i], 'New description text...');
      tas[i].dispatchEvent(new Event('input', {bubbles: true}));
      tas[i].dispatchEvent(new Event('blur', {bubbles: true}));
      return 'set';
    }
  }
})()"

# Click Save button (Ctrl+S may not persist trigger changes)
npx playwright-cli --session cs click "button:has-text('Save')"
```

---

## 5. BATCH TOPIC UPDATE PATTERN

For updating multiple topics in sequence:

```bash
#!/bin/bash
SESSION="cs"  # simple name, not a path — MSYS doesn't handle paths in --session

npx playwright-cli --session $SESSION open https://example.com
npx playwright-cli --session $SESSION state-load 'C:\Users\kevin\.hermes-browser-session\auth.json'

TOPICS_URL="https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/topics"

# Topic 1
npx playwright-cli --session $SESSION goto "$TOPICS_URL"
sleep 5
npx playwright-cli --session $SESSION screenshot ~/batch_before_topic1.png
# ... search, click, edit, save for topic 1 ...
npx playwright-cli --session $SESSION screenshot ~/batch_after_topic1.png

# Topic 2
npx playwright-cli --session $SESSION goto "$TOPICS_URL"
sleep 5
npx playwright-cli --session $SESSION screenshot ~/batch_before_topic2.png
# ... search, click, edit, save for topic 2 ...
npx playwright-cli --session $SESSION screenshot ~/batch_after_topic2.png

echo "Batch complete. Verify each ~/batch_after_*.png with vision_analyze."
```

---

## 6. CHROME DEVTOOLS PROTOCOL (CDP)

For deep debugging — console errors, network requests, performance — and for **full Copilot Studio automation** when playwright-cli sessions have auth issues.

**For Copilot Studio automation via CDP**, use the full workflow documented in `references/cdp-copilot-studio-automation.md`. This covers: launching Kiro Chrome with CDP, navigating Copilot Studio, clicking elements, reading page content, taking screenshots, extracting bot IDs, and exporting auth.

For debugging only:

```bash
# Start MCP server (background)
npx -y chrome-devtools-mcp@latest --isolated &
# Or with explicit CDP port:
npx -y chrome-devtools-mcp@latest --browser-url http://127.0.0.1:9222 &

# Use the MCP tools for:
# - Reading browser console output
# - Capturing network HAR
# - Inspecting DOM in real-time
# - Profiling rendering performance
```

To connect to a running Chrome with remote debugging:
```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

---

## 7. COMPUTER-USE SUBAGENT INTEGRATION

Hermes has `browser` and `computer_use` toolsets available (verified in platform_toolsets).
For complex multi-step browser workflows, delegate to a subagent:

| Issue | Solution |
|-------|----------|
| `button[aria-label="More"]` not found | Use `button:has-text("More")` instead |
| Paste not working in Monaco | Retry, or use `.fill()` on `.monaco-editor textarea` |
| Large YAML (>5000 chars) pasting fails | Use `page.locator('.monaco-editor textarea').fill(yaml)` |
| Browser console JS errors on Copilot Studio | Platform noise — ignore. Check Topics grid Errors column instead |
| **Knowledge source detail page: Ctrl+S doesn't save** | The knowledge source file detail page ignores Ctrl+S. Click the **"Save knowledge changes"** button in the UI toolbar instead. |
| After Ctrl+S, page navigates away | Expected behavior. Go back to topics list for verification |
| Auth session expired | Re-run `export_kiro_auth.cjs` or re-login with `state-save` after manual login |
| Chrome not on PATH | Already added to `~/.bashrc`. If still missing, use full path. |
| `.playwright-cli/` directory fills up | Clean up old `.yml` and `.png` snapshot files periodically |
| Copilot Studio rejects YAML changes | Verify YAML structure matches CS editor expectations. Take screenshot after save to confirm. |
| **Copilot Studio topic toggle: `.click()` doesn't work** | CS toggle switches (`input[type=checkbox][role=switch]`) don't respond to `.click()`. Set `.checked = true` directly, then dispatch `change` + `click` events. Wait 3-5s for UI to update. |
| **Trigger description editing: click text, not Edit button** | Unlike the Instructions editor, the topic trigger description must be edited by clicking the DESCRIPTION TEXT itself (not the Edit button in the toolbar). This opens an inline `<textarea>`. |
| **Knowledge file rename: Ctrl+S doesn't persist** | On the knowledge source detail page, the Save button ("Save knowledge changes") must be clicked. Ctrl+S silently fails. Always use the button. |
| **Auth export: localStorage must come from CS page** | Exporting auth from `about:blank` gives 0 localStorage items. Navigate Kiro Chrome to `copilotstudio.microsoft.com` first, wait for full page load, THEN export cookies + localStorage. MSAL tokens live in CS's localStorage. The `scripts/export_fresh_auth.cjs` script handles this automatically. |
| **Browser closes unexpectedly (MOST COMMON FRUSTRATION)** | The terminal timeout kills the Node.js process, which Playwright propagates to kill Chrome. Even without calling `browser.close()`, the window disappears when the terminal command ends. Fix: use `headless: true` for automated data collection (works fine in terminal), or launch Chrome independently via `--remote-debugging-port=9223` and connect via CDP. NEVER call `browser.close()` unless the user explicitly asks. See `references/browser-lifecycle.md`. |
| **`headless: false` fails in background terminal** | On Git Bash/MSYS, `headless: false` inside a `terminal(background=true)` process will fail with "stdin is not a tty". The Git Bash PTY can't serve as a display. Use `headless: true` instead, or launch Chrome separately. |

| **Instructions editor is contentEditable div, not textarea** | In CS Overview, the Instructions section is a `div[contenteditable]` inside a `[role=textbox]`. Click the Edit button next to the Instructions heading first to make it `contentEditable=true`. Then use `Ctrl+A` → clipboard paste → `Ctrl+S`. **Programmatic paste fails:** React intercepts all DOM mutations (innerText, innerHTML, execCommand) on this editor. `execCommand('insertText')` returns `true` for all text sizes but React silently reverts inserts above ~100 chars. Short text (~22 chars) succeeds; full instructions (~3000 chars) fail. Base64+atob transport works for JS delivery but the React boundary still blocks insertion. **Manual Ctrl+V is the only reliable method.** |
| **Copilot Studio page loads are VERY slow** | SPA takes 15-45 seconds to fully render after navigation. Use polling loops and generous waits. |
| **POPUPS BLOCK ALL AUTOMATION** | Copilot Studio "What's New", feature announcements, and cookie banners are modals that block the entire UI. `document.body.innerText` returns EMPTY when a popup is open. Sidebar tabs, buttons, and grids all appear missing. Before ANY interaction: Escape × 5 + click `button[aria-label="Close"]` + iterate visible buttons for text "Got it"/"Skip"/"Dismiss"/"Close"/"OK"/"Next"/"Accept". Popups reappear after navigation — dismiss after EVERY page.goto(). |
| **`:has-text()` is Playwright-only, NOT vanilla JS** | Inside `page.evaluate()`, Playwright selectors like `:has-text("X")` throw SyntaxError. Use plain JS: iterate `document.querySelectorAll('button')` and check `.textContent.trim()`. |
| **Custom web components reject `.fill()`** | Elements like `<lightning-input>` (Salesforce), `<slds-input>`, and other custom web components are NOT standard `<input>`/`<textarea>` elements. Playwright `.fill()` and `.click()` may fail with "Element is not an <input>, <textarea>, <select> or [contenteditable]". Workaround: `.click()` to focus, then `page.keyboard.type()`. Inspect the tagName and available properties before assuming standard input behavior. |
| **Lightning comboboxes need `role=` selector** | For Salesforce Lightning `lightning-combobox` elements, `page.locator('lightning-combobox').click()` fails with box-model timeout. Use the accessibility selector instead: `page.locator('role=combobox[name="*Program Type"]').select_option(label='Option Name')`. This bypasses shadow-DOM click failures. |
| **Persistent Playwright auth via storageState** | Alternative to playwright-cli state-load: use `chromium.launch()` + `browser.newContext({storageState: 'path/to/state.json'})`. Export once after manual sign-in via `context.storageState({path})`. Tokens are MSAL-encrypted in localStorage (not extractable as plaintext) — use CDP `Network.enable` to capture live Bearer tokens from API calls for direct Dataverse access. |
| **Dataverse-origin repair for live topic YAML parse blockers** | Copilot Studio may reject direct PATCHes to `botcomponents.content` with `Unexpected character encountered while parsing value: k` even when the field currently contains YAML. For draft-only parse repair, use Edge CDP after signing into the Dataverse org (`https://<org>.crm.dynamics.com/main.aspx`), run `page.evaluate(fetch(..., credentials:'include'))`, backup/read the component, PATCH `botcomponents.data` with clean YAML starting at `kind: AdaptiveDialog`, then re-read and exact-match verify. Run the fleet scanner afterward; it prefers parseable `content` but falls back to parseable `data`, so this clears live YAML parse blockers without publishing. |
| **Monaco Save button wake-up** | After pasting YAML into Monaco code editor, the Save button stays `disabled: true` even if content changed. Workaround: click the bottom-right of the editor area + `page.keyboard.type(' ')` + `page.keyboard.press('Backspace')`. This marks the model as dirty and enables Save. Space+Backspace is more reliable than Ctrl+S. |
| **`pac copilot extract-template` crashes on agents with knowledge sources** | `pac` v2.7.4 bug. Use `pac solution clone` for metadata, or extract topics individually via CDP code editor. |
| **`pac copilot status --bot-id` fails with componentstate_Property** | Another `pac` v2.7.4 bug. Use `pac copilot list` instead to verify publish state. |
| **Auth format conversion needed between CDP and playwright-cli** | CDP returns cookies with `partitionKey` objects that playwright-cli rejects. Strip partitionKey and other protocol-internal fields. The export scripts handle this. |
| **playwright-cli `fill` resolves 2 textareas on CS page** | CS Overview page has both a Description textarea and a Test pane textarea. Use specific selectors: the instructions editor is `[role=textbox]` (a div), not `textarea`. |
| **Knowledge page: "All" view hides uploaded files** | The "All" filter only shows Public website and SharePoint sources. Click the **Files** tab to see uploaded PDFs and documents. |
| **Pasting large text into Instructions editor fails** | Shell eats newlines in `fill` command, `innerText`/`innerHTML` assignments ignored by React, base64+atob approach also fails — React contentEditable rejects ALL programmatic DOM manipulation. Tested extensively Jun 10: fill → only first line; innerText setter → length stays 56; innerHTML with <p> tags → same result; base64+atob decoded via eval → React ignores it. | **Manual copy-paste is the only reliable method.** This is the "paste wall" — a React platform limitation, not a fixable automation gap. Give the user the text file path and have them paste manually. |


---

## 9. REFERENCE FILES & OVERLAPPING SKILLS

⚠️ **Overlap note:** `playwright-codex` is a direct copy of Codex's Playwright skill — it uses different session handling and references Codex-specific paths. Use `playwright-hermes` (this skill) for Hermes-native browser automation. The `playwright-codex` copy is kept for reference only.

| File / Path | Purpose |
|-------------|---------|
| `references/browser-lifecycle.md` | **Browser lifecycle management** — root cause of unexpected window closure, headless vs headed mode guidance, CDP persistence pattern, MSYS limitations |
| `C:\\\\Users\\\\kevin\\\\\\\\.hermes-browser-session\\\\\\\\auth.json` | Exported auth state (cookies + MSAL localStorage) |
| `scripts/export_kiro_auth.cjs` | Auth export script (CDP-based, cookies + localStorage) |
| `scripts/export_fresh_auth.cjs` | Alternative auth export — uses USERPROFILE env var, writes to profile/home/fresh_auth.json |
| `references/cdp-copilot-studio-automation.md` | **CDP-based Copilot Studio automation** (navigation, clicks, screenshots, bot discovery, auth export) |
| `references/cdp-token-capture.md` | **CDP Network token capture** — intercept Power Platform bearer tokens for direct Dataverse API access. Avoids MSAL encrypted localStorage limitation. |
| `C:\\Users\\kevin\\AppData\\Local\\Programs\\Kiro\\.playwright-auth\\` | Kiro's Chrome profile (source of auth) |
| `C:\Users\kevin\.codex\skills\playwright\SKILL.md` | Codex's original Playwright skill (reference) |
| `C:\Users\kevin\.codex\skills\copilot-debug\SKILL.md` | Copilot Studio debugging workflow |
| `C:\Users\kevin\.codex\skills\passagenttesting\SKILL.md` | Evaluation repair workflow |
| `.claude/rules/browser-automation.md` | Browser automation rules from codex projects |
| `.kiro/skills/playwright-topic-editor.md` | Topic editing patterns from codex projects |

---

## 10. COMPLETE EXAMPLE: Edit Topic + Verify

```bash
# 1. Export auth from Kiro (1-time)
#    Launches Chrome with Kiro profile via CDP on port 9223, extracts
#    cookies + MSAL localStorage tokens, writes to auth.json
NODE_PATH=$(npm root -g) node scripts/export_kiro_auth.cjs

# 2. Start session and load auth
npx playwright-cli --session cs open https://example.com
npx playwright-cli --session cs state-load 'C:\Users\kevin\.hermes-browser-session\auth.json'

# 3. Open topics page
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/environments/Default-xxx/bots/<botId>/topics"
sleep 5

# 4. BEFORE screenshot
npx playwright-cli --session cs screenshot ~/verify/before.png
# → vision_analyze("~/verify/before.png", "Topics list baseline — any errors?")

# 5. Search and open topic
npx playwright-cli --session cs snapshot
npx playwright-cli --session cs fill <search-ref> "PT_Intake"
sleep 2
npx playwright-cli --session cs click <topic-link-ref>
sleep 5

# 6. Open code editor
npx playwright-cli --session cs snapshot
npx playwright-cli --session cs click <more-btn-ref>
sleep 1.5
npx playwright-cli --session cs screenshot ~/verify/menu_open.png
npx playwright-cli --session cs click <code-editor-ref>
sleep 4

# 7. Replace content
npx playwright-cli --session cs press "Control+A"
sleep 0.5
npx playwright-cli --session cs eval "navigator.clipboard.writeText(\`kind: Trigger...\`)"
sleep 0.5
npx playwright-cli --session cs press "Control+V"
sleep 1
npx playwright-cli --session cs screenshot ~/verify/content_pasted.png
# → vision_analyze("~/verify/content_pasted.png", "New YAML visible? Any errors?")

# 8. Save
npx playwright-cli --session cs press "Control+S"
sleep 4
npx playwright-cli --session cs screenshot ~/verify/after_save.png
# → vision_analyze("~/verify/after_save.png", "Save succeeded? Any error toast?")

# 9. Navigate back and verify
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/environments/Default-xxx/bots/<botId>/topics"
sleep 5
npx playwright-cli --session cs screenshot ~/verify/after_list.png
# → vision_analyze("~/verify/after_list.png",
#   "Topics list: Errors column = 0? Topic name 'PT_Intake' visible? No red banners?")
```
