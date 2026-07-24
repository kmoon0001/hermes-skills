---
name: copilot-studio-instructions-editor
description: "Workflow for programmatically editing Copilot Studio agent instructions and applying cross-agent bug fixes via Playwright + CDP. Tested on SLP, OT, PT, and TDA agents. Covers hedging removal, citation ban, conciseness fixes, and eval triggering."
version: 2.1.0
author: Hermes Agent
platforms: [windows]
---

# Copilot Studio Instructions Editor

Workflow for editing agent-level instructions in Copilot Studio programmatically using playwright-cli with CDP-exported auth.

## Notepad Formatting for Manual Paste

When preparing instructions for manual paste via Notepad, use clean formatting:
- NO markdown headers (#) — they look cluttered in Notepad
- Blank lines between sections for readability
- Section names as plain text headers (CONTENT SAFETY, ROLE, SCOPE, etc.)
- Each numbered instruction gets its own paragraph (not running together)
- Bullet points with dashes, not asterisks
- No special characters that might confuse the Lexical editor

Example:
```
CONTENT SAFETY

This agent provides quality measure analysis...

ROLE

You are SimpleLTC QM Coach V2...


INSTRUCTIONS

1. Identify the request type...

2. For QM analysis: identify the specific measure(s)...

3. For decline detection: compare current vs prior quarter...
```

## Prerequisites

- playwright-cli installed globally: `npm install -g @playwright/cli`
- Kiro Chrome or Chrome with CDP on port 9223 (or accessible debug port)
- Valid MSAL session in the browser (ESTSAUTHPERSISTENT cookie)

## Auth Workflow

### Export from Kiro Chrome (port 9223)

```javascript
// Connection to Kiro Chrome CDP
const ws = new WebSocket(page.webSocketDebuggerUrl);

// Navigate to Copilot Studio
await send('Page.navigate', {url: targetUrl});
// Wait 15-20s for SPA load

// Check if login needed
const loc = await send('Runtime.evaluate', {expression: 'window.location.href'});
// If contains 'login.microsoft' → SSO redirect expired, user must log in manually

// Export auth
await send('Network.enable', {});
await send('DOMStorage.enable', {});
const cookies = (await send('Network.getAllCookies', {})).result.cookies;
const localStorage = (await send('DOMStorage.getDOMStorageItems', {storageId: {securityOrigin: 'https://copilotstudio.microsoft.com', isLocalStorage: true}})).result.entries;

// Save as Playwright storageState format
const pwAuth = {
  cookies: cookies.map(c => { if (c.partitionKey && typeof c.partitionKey === 'object') delete c.partitionKey; return c; }),
  origins: [{origin: 'https://copilotstudio.microsoft.com', localStorage: localStorage.map(e => ({name: e[0], value: e[1]}))}]
};
```

### Load into playwright-cli session

```bash
npx playwright-cli --session cs open https://example.com
npx playwright-cli --session cs state-load /path/to/fresh_auth.json
```

## Editing Instructions

### Finding the Right Edit Button

The Overview page has 3 Edit buttons:
1. **ref=e176**: Description/Details editor (name + description)
2. **ref=e279**/**ref=e277** (varies by page state): Instructions editor
3. **ref=e524-539** (varies): Secondary/collapsed edit

**The Instructions Edit button is always the second visible Edit button**, NOT counting disabled ones. In snapshots it's typically `e279` or `e277`.

**Pitfall**: The ref IDs change every time the page navigates. Always take a fresh snapshot first:

```bash
npx playwright-cli --session cs snapshot | grep 'Edit"' | head -3
```

### Click Instructions Edit

```bash
npx playwright-cli --session cs click e279
```

Wait 3-4 seconds for the React editor to become editable (`contentEditable=true`).

### Verify Editor is Active

```bash
npx playwright-cli --session cs eval "(function(){ var ed=document.querySelector('[role=textbox]'); if(!ed) return 'no textbox'; return 'ce='+ed.contentEditable; })()"
```

Should return `ce=true`.

### Get the Textbox Ref

```bash
npx playwright-cli --session cs snapshot | grep 'textbox'
```

The first textbox with placeholder "Describe what you want this agent to do, its tone, and rules." is the instructions editor.

### Fill Instructions

```bash
cd /path/to/home && node -e "
const { execSync } = require('child_process');
const fs = require('fs');
const instr = fs.readFileSync('instructions_v6.txt', 'utf8').replace(/\r\n/g, '\n');
execSync('npx playwright-cli --session cs fill e284 ' + JSON.stringify(instr), {shell:true, timeout:30000});
"
```

### Save

```bash
npx playwright-cli --session cs snapshot | grep 'Save"' | head -3
npx playwright-cli --session cs click e691
```

The Save button ref varies. Check after pasting.

## Publishing

```bash
npx playwright-cli --session cs snapshot | grep 'Publish"' | head -3
npx playwright-cli --session cs click e143
```

Wait 8+ seconds for publish to complete. Verify:
```bash
npx playwright-cli --session cs eval "document.body?.innerText?.includes('Published')"
```

## Editing Knowledge Source Names

Navigate to the agent's Knowledge page:
```bash
npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/environments/.../bots/.../knowledge"
```

Click "Files" tab, then find the file row, click its More menu, select "Edit details", update name/description, click Save.

## Instruction Iteration Methodology

**Pre-condition — KB-first triage:** Before iterating instructions, audit the agent's Knowledge Sources. KB descriptions = GPT retrieval router (blank = random = ungrounded). See `references/../copilot-studio-development-workflow/references/kb-first-triage.md` for the full checklist. Only change instructions after confirming KB quality.

For Conversation test-set failures where the agent has knowledge but still fails record_id cases, first check `references/conversation-evaluation-remediation.md`. It includes the PT record_id-hardening pattern, the SLP citation-artifact regression warning, direct config run checks, and topic-edit persistence pitfalls. For the SLP caregiver competency/safety/cognitive-capacity class specifically, also check `references/slp-caregiver-guard-remediation-2026-06.md`; it records the 95% guard-off baseline, the unsafe YAML-fixed re-enable regression, and the Microsoft Learn-aligned long-term replacement pattern.

For reading evaluation run results programmatically, use `references/eval-polling-pattern.md`. It documents the proven headless Playwright approach: navigate to evaluation page → wait 60s for SPA data load → read `document.body.innerText` → find run by timestamp name → parse Running/score. This is more reliable than structured DOM parsing or the Playwright accessibility snapshot approach for evaluation data.

A common fix is to harden the agent instructions so a `record_id` is treated as sufficient evaluation context and the agent completes the audit instead of hedging, asking for the document, or ending with “would you like me to…”. However, do **not** apply this broadly when failures are isolated to SLP guard topics or citation artifacts; inspect failed rows first and prefer topic/tool architecture remediation when caregiver guard topics are involved.

When iterating instruction versions, distinguish between **instruction bugs**, **topic-level citation/duplication bugs**, and **topic queue bugs** before changing the format directive:

- Grader says "refuses to help by showing an error message" → **topic queue bug** — see `references/topic-level-pitfalls.md`. Do NOT change instructions.
- Grader says _"too short"_ or _"missing format"_ → **instruction content bug** — see `references/instruction-iteration-playbook.md`.
- Grader says "didn't cite knowledge sources", "incomplete", or relevance fails while the response visibly includes [1]: cite:1, Citation-1, bracket footnotes, or duplicated answer blocks → **topic-level citation/duplication bug**. Do NOT add stronger global Source Anchors sections until failed rows prove the issue is agent-level; in SLP caregiver guard topics this broad patch regressed Conversation from 90% to 35%. Use `references/conversation-evaluation-remediation.md` and fix the specific topic/YAML instead.
- SR eval drops significantly after adding a new topic with triggerQueries → **static template regression bug**. Check if the topic uses static SendActivity with bracket placeholders ([Assessment...]). The triggerQueries may capture SR questions and return template text instead of generative answers. Fix: use CreateGenerativeAnswers instead of static SendActivity, or disable the topic. See pitfall 15 and `references/slp-caregiver-guard-remediation-2026-06.md`.

**Key finding** (3-agent fleet, June 2026): The unconditional "Always use RESPONSE FORMAT" (v4) outperformed the conditional approach (v5) because single-response tests expect the structured format universally. Conversation regressions under v4 were actually caused by topic-level bugs, not the format directive.

## Conversational Boosting (CB) Topic

The CB topic is a **system topic** (filter "System (N)" on Topics page, URL: `.../adaptive/<uuid>`) that handles unknown-intent queries. Its configuration has a critical impact on both Conversation and Single Response scores.

**Proven stable configuration** (95% Conv / 96% SR):
- Uses `SearchAndSummarizeContent` (NOT `CreateGenerativeAnswers` — system topic limitation)
- `additionalInstructions`: `"Keep response under 600 characters. Give the most relevant 2-3 points only. - Always cite knowledge sources using [Source Name] format in every response"`
- `applyModelKnowledgeSetting: true`
- `webBrowsing: false`
- Full YAML template at `templates/cb-topic-original.yaml`

**Critical pitfall — CB changes cause massive SR regression:**
- Removing the 600-character limit → eval runs 40+ minutes, answers become excessively long, and SR can drop from 95% to **35%**
- Adding anti-citation instructions ("NEVER include citations") conflicts with platform-level citation rendering and also degrades scores
- Microsoft Learn states citations are platform behavior: "citations returned from a knowledge source can't be used as inputs to other tools or actions"
- **Do NOT modify the CB topic unless baseline evaluations show a specific, measurable problem traced to CB behavior.** The original configuration is the proven correct setup.

## Topic Toggle (ON/OFF) via Playwright

To toggle a topic ON/OFF from the Topics page:
- Each topic row uses `fui-DataGridRow` elements
- The switch container is `.fui-Switch` within the row
- **Must click the `.fui-Switch` div, NOT the `input[role="switch"]` hidden input**
- Clicking the input does nothing; click the visible switch container div instead
- After toggle: `input[role="switch"].checked === true` means ON, `false` means OFF

## Topic Deletion via Playwright

From the Topics page, each row has a More button at approximately x:336 on the row's y center:
1. Click More button at `(336, rowY)`
2. Menu appears with: "Details", "Make a Copy", "Delete"
3. Click "Delete" menu item — it's the third item at roughly the same x but lower y
4. Confirmation dialog: click the "Delete" button to confirm
5. **Must publish after deletions**, otherwise topics may reappear

Note: System topics (Conversational boosting, Fallback, etc.) have different menus and may not offer a "Delete" option.

12. **Playwright mouse.click does NOT activate Edit buttons — use CDP Input.dispatchMouseEvent** (June 18, 2026) — `page.mouse.click()` on the Instructions Edit button does NOT trigger the React event handler that activates the Lexical contenteditable editor. The editor stays `contenteditable="false"` and `aria-readonly="true"`. **Fix:** Use raw CDP mouse events via `p.context().newCDPSession(p)` then `client.send('Input.dispatchMouseEvent', ...)`. This bypasses Playwright's event layer and sends the actual browser-level mouse event that React responds to. **Evidence:** PT, SLP, TDA Edit buttons all failed with `page.mouse.click()` but succeeded with CDP `Input.dispatchMouseEvent` on June 18, 2026. **Pattern:**
```javascript
const client = await p.context().newCDPSession(p);
await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
await sleep(50);
await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
```
Same pattern works for clicking Evaluate, Save, and any button that doesn't respond to Playwright's synthetic events.

13. **Evaluate button requires scrollIntoView before clicking** (June 18, 2026) — The Evaluate button on the configsDetails page is positioned at y≈1958 (off-screen in a sticky footer). CDP click at that position does NOT register until `scrollIntoView` brings it into the viewport. **Fix:**
```javascript
await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate');
    if (btn) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
});
await sleep(2000);
// Then click with CDP mouse event
```
Without scrollIntoView, the button stays at y=1958 and clicks at that position hit the page background, not the button.

14. **Fresh page avoids Test pane overlay** (June 18, 2026) — The "Test your agent" sidebar persists across SPA navigation and blocks eval result reading. Opening a fresh page via `context.newPage()` starts without the overlay. Use fresh pages for eval score polling.

15. **Platform-wide eval failure pattern** (June 18, 2026) — When ALL agents (including untouched ones) return "Error" on every eval case while the Test pane works perfectly, the issue is the EVALUATION SERVICE, not agent configuration. **Diagnostic:** Trigger an eval for an agent you KNOW you didn't modify. If it also returns 0%/Error, it's a platform issue. **Evidence:** OT (untouched since yesterday) returned 0% Conv on June 18, 2026, same as PT/SLP/TDA. All agents worked in Test pane. Root cause: Microsoft evaluation service failure in the environment. **What NOT to do:** Don't spend hours debugging agent instructions/topics/knowledge sources when the eval service itself is broken. Check early by testing an untouched agent. **Resolution:** Wait for platform recovery, check Microsoft service health dashboard, or try the REST API as an alternative endpoint.

## Agent Instruction File Quick Reference (June 2026)

Canonical file paths for each agent's current instructions. These are the HYBRID FORMULA versions (OT behavioral patterns + discipline content):

| Agent | File | Chars | Format | Status |
|-------|------|-------|--------|--------|
| **OT** | `D:\my agents copilot studio\ot_instructions_v9_final.txt` | ~3,500 | Unconditional RF | STABLE 99%/100% — DO NOT TOUCH |
| **PT** | `D:\my agents copilot studio\pt_instructions_consolidated.txt` | 3,957 | Conditional RF | Needs re-paste + eval |
| **SLP** | `D:\my agents copilot studio\slp_instructions_consolidated.txt` | 3,626 | Conditional RF | Needs re-paste + eval |
| **TDA** | `D:\my agents copilot studio\tda_instructions_consolidated.txt` | 2,589 | Routing (no RF) | Needs re-paste + eval |

**Backups**: `pt_instructions_final.txt`, `slp_instructions_fixed.txt`, `tda_instructions_fixed.txt` in the same directory.

**Injection priority**: CDP `Input.dispatchMouseEvent` + `keyboard.insertText()` (proven June 2026 on PT, SLP, TDA, QM Coach V2) → Manual Notepad paste (always works) → Playwright `fill()` (unreliable — fails on most agents).

**CDP injection is the primary method.** Playwright's `page.mouse.click()` silently fails on most agents' Edit buttons. CDP `Input.dispatchMouseEvent` works reliably. See `references/instructions-editor-real-mouse-pattern.md` for the full pattern.

## User Preferences (Workflow)

- **Full instruction blocks, NEVER snippets**: When providing corrected agent instructions, ALWAYS deliver the complete text block ready for copy-paste. Never use find-and-replace snippets or diff-style patches — the user explicitly rejects "inserting snippets." Write the full corrected text to a file AND display it inline. Use `D:/my agents copilot studio/<agent>_instructions_fixed.txt` as the canonical path.

- **Notepad formatting: NO markdown headers** — When writing instruction files for Notepad paste, do NOT use markdown `#` headers. Use plain text section headers (e.g., `CONTENT SAFETY` on its own line, not `# CONTENT SAFETY`). Add blank lines between sections for readability. Break numbered instructions into separate paragraphs. User explicitly said "FORMAT THE NOTEPAD INSTRUCTIONS BETTER" (June 2026). The Lexical editor renders plain text headers cleanly.

- **Open in Notepad for copy-paste**: User prefers `notepad <path>` to open the file directly for easy Select All + Copy. Do not just display inline — open the file in Notepad. The user said "NOTE PAD" explicitly (June 2026).

- **Direct execution over delegation**: Work in the main session, one Playwright/CDP script at a time. Never spawn subagents for Copilot Studio browser automation — they hang due to CDP session conflicts.

- **Minimal builds, maximal output**: Settings toggle > instruction change > topic creation. No topic sprawl for narrow cases.

- **One eval at a time**: Copilot Studio processes evaluations sequentially. Trigger all needed evals, then poll for results (~15 min per 100-case SR).

**Minimal builds for maximal output.** Do NOT create new topics when a settings toggle or instruction change can solve the problem. Prefer:
1. Settings toggle (e.g., "Allow ungrounded responses") — zero risk, instant effect
2. Agent-level instruction addition — generalized, no topic sprawl
3. Topic creation — LAST resort, only when instructions + settings cannot handle the case

Do NOT create topics that handle specific names, personas, or narrow edge cases. Use generative AI's general capability instead. The user explicitly rejects "build a topic for one person's name" approaches.

**Direct execution, not delegation.** When the user says "do X," execute it directly in the current session. Do NOT spawn subagents (delegate_task) for Copilot Studio work — Playwright + CDP tasks hang in subagents due to browser session conflicts. Work in the main session, one step at a time.

## Launching Notepad from Git-Bash

**Pitfall**: `notepad` in git-bash resolves to a wrapper script, NOT Windows notepad.exe. The wrapper shows shell script content instead of the file.

**Fix**: Use PowerShell to launch the real Notepad:
```bash
powershell.exe -Command "Start-Process notepad 'C:\Users\kevin\Desktop\file.yaml'"
```

## Pitfalls

0h. **Playwright `mouse.click` does NOT activate the Instructions Edit button — use raw CDP `Input.dispatchMouseEvent` instead** (June 18, 2026) — `page.mouse.click(x, y)` on the Edit button fails silently: the Lexical editor stays `contenteditable="false"` and `aria-readonly="true"`. This was confirmed across PT, SLP, and TDA agents. **The fix:** use CDP raw mouse events via `page.context().newCDPSession(page)`:

```javascript
const client = await page.context().newCDPSession(page);
// Get Edit button center coordinates via page.evaluate
const edits = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button'))
        .filter(b => b.textContent?.trim() === 'Edit' && b.getBoundingClientRect().width > 0)
        .map((b, i) => { const r = b.getBoundingClientRect(); return { i, x: r.x + r.width/2, y: r.y + r.height/2 }; });
});
const target = edits[1]; // Instructions Edit = 2nd button

await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: target.x, y: target.y, button: 'left', clickCount: 1 });
await sleep(50);
await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: target.x, y: target.y, button: 'left', clickCount: 1 });
await sleep(5000);

// Verify: editor should now be contenteditable="true"
const state = await page.evaluate(() => {
    const ed = document.querySelector('div[role="textbox"]');
    return ed ? { ce: ed.contentEditable, readonly: ed.getAttribute('aria-readonly') } : null;
});
```

**Why it works:** Playwright's `mouse.click` generates synthetic DOM events that React/Lexical may not process. CDP `Input.dispatchMouseEvent` sends raw input events at the browser engine level, bypassing DOM event synthesis. This is the same mechanism Chrome DevTools uses for real user interactions.

**Also works for:** clicking editor areas, Save buttons, Evaluate buttons, and any other React-controlled UI element that doesn't respond to Playwright clicks.

0i. **Buttons at y>1000 require `scrollIntoView` before clicking** (June 18, 2026) — The Evaluate button on the configsDetails page is at y≈1958 (off-screen in a sticky footer). CDP clicks at that coordinate do nothing because the button is outside the viewport. **Fix:** call `scrollIntoView` before clicking:

```javascript
await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate');
    if (btn) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
});
await sleep(1000);
// Now get updated coordinates and click
const btn = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate' && !b.disabled);
    if (b) { const r = b.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2 }; }
    return null;
});
if (btn) { /* CDP click at btn.x, btn.y */ }
```

**Key:** After `scrollIntoView`, re-query the button's bounding rect — the coordinates change.

0j. **Test pane placeholder text varies by agent** (June 18, 2026) — The Test pane chat input does NOT have a consistent placeholder. PT uses `"Ask a question or describe what you need"`, other agents may use `"Type your message"`. When finding the textarea via script, use a broader selector:

```javascript
const ta = document.querySelector('textarea[placeholder*="Ask"], textarea[placeholder*="Type"], textarea[placeholder*="message"]');
```

Or find by position (right side of page, x > 400):

```javascript
const ta = Array.from(document.querySelectorAll('textarea')).find(t => t.getBoundingClientRect().x > 400 && t.getBoundingClientRect().width > 50);
```

0k. **Fresh page (`context.newPage()`) avoids Test pane overlay** (June 18, 2026) — The Test pane persists across SPA navigation and blocks eval result reading. Instead of toggling it off, open a fresh page: `const p = await ctx.newPage()`. Fresh pages start without the Test pane overlay and inherit auth from the browser context.

0l. **Evaluation "Error" on ALL cases while Test pane works = publish/platform issue** (June 18, 2026) — When an agent's evaluation returns "Error" (0%) on every test case but the agent responds correctly in the Test pane, the issue is NOT the agent configuration. The Test pane uses the DRAFT version; evaluations may use the PUBLISHED version. Check for:
1. **Topics with YAML errors** — a broken topic in the published version causes errors on every eval case
2. **"1 Warning" on Overview** — click Review to see the specific topic/config issue
3. **Knowledge source auth expired** in the published version
4. **Multiple agents crashing simultaneously** = platform-level issue (not agent-specific)

When PT, SLP, and TDA all went to 0% at the same time (3:37-3:50 PM June 18), it was a shared platform issue, not individual agent config. OT (which wasn't modified) continued working.

1. **Checklist placement rule** (Jun 17, 2026): Explicit element checklists ("MUST include", Met/Missing/Verify) belong in topic YAML `additionalInstructions`, NOT agent instructions. Checklists in instructions cause 5-15% regression (PT 85%→80%, 90%→85%). Topics scope the impact to only that trigger. See `copilot-studio-topic-yaml-fixes` for templates.

2. **Inline citations**: Citations must be embedded inline within the response body ("Per CMS Chapter 15..."), not in a separate source section at the end. Grader marks end-of-response sources as "didn't cite knowledge sources."

3. **MANDATORY/CRITICAL language ban**: Words like MANDATORY, CRITICAL, NEVER in instructions cause 5%+ regression. Use soft language.

-1a. **Prefer minimal, generalized fixes over specific topic creation** — When conversation evals fail on specific personas or scenarios, do NOT create topic handlers for that specific case. Instead: (1) check "Allow ungrounded responses" is ON, (2) add generalized conversation handling instructions to the agent, (3) trust the Conversational Boosting system topic + generative orchestration. Per MS Learn generative orchestration guidance: "Topics now act as modular instructions that the agent can call upon when orchestrating a conversation. Generative orchestration handles most routing by interpreting user input dynamically." Building specific topics for specific eval personas creates topic sprawl and routing conflicts.

0. **"Allow ungrounded responses" OFF = conversation refusals — but NOT the fix for "incomplete" failures** — Per MS Learn, when this setting is OFF in Settings > Generative AI > Knowledge, the platform BLOCKS any response where the agent didn't use a knowledge source or tool. Conversational inputs get blocked and the Fallback topic fires. **This is a PLATFORM-LEVEL override** that supersedes agent instructions. **Fix when the grader says "refuses to help" or "error message":** Toggle ON in Settings > Generative AI > Knowledge, then Publish. **Do NOT toggle ON when the grader says "incomplete", "didn't cite knowledge sources", or "one or more questions not answered"** — these are instruction-level problems (see pitfall 22). Toggling ON when the real problem is hedging language actually makes things worse by enabling lower-quality ungrounded responses that score even lower. **Evidence:** SLP Conv 90% with toggle OFF → 85% with toggle ON (June 2026). The real fix was removing hedging language from instructions. See `references/hedging-language-grader-failures.md` for the full decision tree.

0x. **Description vs Instructions** — The Description field on Overview is USER-FACING (what the agent does in 1-2 sentences). The Instructions field is for system prompts, response format rules, and AI behavior directives. **RED FLAG**: If Description reads like a system prompt (numbered rules, response format requirements, disclaimers, persona instructions), it belongs in Instructions not Description. When fixing: first confirm the instructional text already exists in the Instructions field before overwriting Description. **Description can be edited via Playwright** — click first Edit button (Details section), find textarea with old description text, `ta.fill(newDesc)`, click Save, then Publish. See `evaluation-driven-agent-optimization/references/agent-description-conflict.md` for full pattern and correct templates.

0x. **Description field affects model behavior** — GPT-5 Chat reads the Description as system-level context. If Description says "Returns deterministic JSON" but Instructions say "Use RESPONSE FORMAT: numbered list", the model follows the DESCRIPTION. PT SR dropped 96%→82% from this conflict. Audit agents: description should say "Returns compliance findings with risk levels, scores, and recommendations", NOT "Returns JSON".

0a. **Writing .cjs scripts via write_file mangles backslash-escapes** — The `write_file` tool and terminal `heredoc` both mangle double-quote backslash sequences (`\"true\"` becomes literal `\"true\"` in the file), causing JavaScript syntax errors. **Workaround**: use `execute_code` with a Python triple-quoted string (`"""..."""`) and `open(path,'w').write(...)` to write .cjs files cleanly. This is the only reliable way to get unmodified JS content onto disk.

0b. **Topic creation dialogs do not render in Playwright/CDP automation** — Clicking "Add topic" or "Add trigger" on the Topics page navigates back to Overview without showing the create dialog. This is a fundamental SPA limitation confirmed across both `chromium.launch()` and `chromium.connectOverCDP()`. **Topic creation requires manual user action** — the agent should present a clear manual step (navigate to Topics, click Add trigger, fill name+description, click Create, then click More → Open code editor) and take over from the Monaco code editor step where YAML injection via clipboard paste is reliable. Do not spend time trying to automate the creation dialog — it will not work.

0b-2. **Authored topic action kinds differ from system topic action kinds** — For authored topics, use `AnswerQuestionWithAI` (not `CreateGenerativeAnswers`). The property for user input is `UserInput` (capital U), NOT `userQuestion`. System topics like Conversational Boosting CAN use `SearchAndSummarizeContent` and `CreateGenerativeAnswers`, but authored topics are restricted to the valid authored-topic action kinds listed in the YAML schema validation error. When the schema rejects `CreateGenerativeAnswers`, switch to `AnswerQuestionWithAI` and use `UserInput: =System.Activity.Text`.

0b.1 **Contenteditable editor auto-saves on Playwright fill() — Space+Backspace not needed for instructions** — June 2026 correction: Playwright's `locator.fill(newText)` on the agent instructions contenteditable div triggers the editor's internal change tracking. The content persists even if the Save button remains disabled and you click Cancel. **Verified:** content changed from 6078→6242 chars, hedging text removed, new text confirmed present in view mode after cancel. This means the "Space+Backspace to unlock Save" step is OPTIONAL for the instructions editor when using Playwright fill(). However, for the **topic code editor** (Monaco), Space+Backspace is still required — see the CompositionEvent approach below.

**Proven pattern for contenteditable instructions editor (June 2026):**
```javascript
// 0. Get CDP session (CRITICAL — Playwright mouse.click does NOT activate Edit)
const client = await p.context().newCDPSession(p);
// 1. Click Edit button (2nd Edit on the page, for Instructions) via CDP raw mouse
await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
await sleep(50);
await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
// 2. Set a unique ID on the editor div
const client = await p.context().newCDPSession(p);
const edits = await p.evaluate(() => {
    return Array.from(document.querySelectorAll('button'))
        .filter(b => b.textContent?.trim() === 'Edit' && b.getBoundingClientRect().width > 0)
        .map((b, i) => { const r = b.getBoundingClientRect(); return { i, x: r.x+r.width/2, y: r.y+r.height/2 }; });
});
const target = edits[1]; // Instructions Edit = 2nd button
await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: target.x, y: target.y, button: 'left', clickCount: 1 });
await sleep(50);
await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: target.x, y: target.y, button: 'left', clickCount: 1 });
await sleep(5000);
// 2. Verify editor activated: contenteditable="true", aria-readonly=null
// 3. Click editor with CDP, Ctrl+A, keyboard.insertText(newInstructions)
// 4. Space + Backspace to wake save tracker
// 5. Click Save via CDP
// 6. Cancel edit mode, then Publish
```
**Evidence (June 18 2026):** Playwright `mouse.click` failed on PT (y=888) and SLP (y=856) — editor stayed `contenteditable="false"`. CDP `Input.dispatchMouseEvent` activated editor on first try for PT and TDA. SLP was already correct so activation wasn't needed.

For topic YAML injection, the Monaco code editor still requires the CompositionEvent + iframe approach. See `cdp-instructions-injection` skill.

**Force-setting contenteditable does NOT enable insertText**: Even after `ed.setAttribute('contenteditable','true')` and `ed.removeAttribute('aria-readonly')`, `page.keyboard.insertText()` and clipboard paste do NOT update the Lexical editor's internal state. The visible content appears unchanged. Verified on QM Coach V2 in the dev environment (June 2026) in addition to the production agents. The only path is the real Edit button activation via CDP mouse events, or manual paste by the user.

0c. **Web Chat test pane DOM is unreachable via Playwright selectors** — The Copilot Studio test pane Web Chat component is rendered inside an iframe or React portal whose DOM is not accessible via standard `page.evaluate()` selector queries. `document.querySelector('.webchat__send-box-text-box__input')` consistently returns null. **Workaround**: use `page.mouse.click` at known coordinates (from a prior successful sendbox location), `page.keyboard.type`, then `page.screenshot` + `vision_analyze` to read the bot's response. Direct DOM extraction of bot responses from the test pane is unreliable; screenshot-based inspection is the reliable path.

0d. **Conversational Boosting (CB) system topic — AGENT-TYPE MATTERS** — 
- **Audit agents (OT/PT/SLP)**: REMOVE `Keep response under 800 characters` from CB. Replace with `Be concise but complete. Prioritize accuracy over strict length limits.` Longer, more complete responses score better.
- **Routing agents (TDA)**: KEEP `Keep response under 800 characters` in CB. Short, focused routing decisions score better. Removing it caused TDA 99% → 92% SR regression.

**June 2026 evidence**: TDA was at 99% SR with 800-char CB limit. Removing it → 92%. Reverting → 93%. Stable at 92-93%.

0d. **Chrome CDP on main user data dir silently fails** — Launching Chrome with `--remote-debugging-port=9223` AND the main user data dir (`C:\\Users\\<user>\\AppData\\Local\\Google\\Chrome\\User Data`) silently fails to open the debug port. Chrome runs but CDP doesn't listen. **Fix:** Use a separate user data dir: `--user-data-dir=C:\\Users\\<user>\\AppData\\Local\\Google\\Chrome\\User Data Debug`. This requires signing in to Copilot Studio manually in that profile. Auth state from `.playwright-auth/state.json` expires and cannot be reliably reloaded.

22. **Hedging language in instructions causes grader "incomplete" failures — WHACK-A-MOLE PROBLEM** — The Copilot Studio evaluation grader penalizes agent responses that hedge about missing context. Phrases like "direct verification is limited", "best-effort", "since the note wasn't provided", "I could not locate the record" cause the grader to mark responses as "One or more answers seem incomplete" or "One or more questions not answered" even when the agent provides a full audit. **Root cause:** The instructions tell the agent to "State that direct verification is limited" when document text is unavailable. The grader interprets this as a refusal. **WHACK-A-MOLE WARNING:** Banning specific hedging phrases does NOT fully solve the problem — the model generates NEW hedging variants that weren't banned (e.g., "Since you didn't include the actual text", "I'll base this on", "Here's what to look for"). **The correct fix is a BALANCED instruction that neither hedges nor fabricates:** "NEVER mention that document text is missing or unavailable. NEVER hedge with phrases like 'since you didn't include' or 'I'll base this on.' Instead, provide authoritative compliance guidance: describe what the document type requires per CMS/ASHA standards, list the key elements a compliant document must contain, and give specific recommendations. Do not fabricate specific scores or findings for documents you cannot see — use ranges if estimating and qualify with 'per standard requirements.'" **CRITICAL PITFALL — DO NOT USE 'write as if you have the document in front of you':** This causes the model to FABRICATE specific scores and findings for documents it cannot see. The grader detects this as inaccurate → SR regression. Evidence: SLP SR 94% dropped to 91% after adding "write as if you have the document in front of you." Reverting to the balanced approach above restored the score. **Evidence:** SLP Conv 80%→90% (banning specific phrases) → 100% (balanced guidance + conciseness fix). SLP SR 94%→91% (aggressive "write as if" regressed it) → reverted. See `references/hedging-language-grader-failures.md`.

23. **cite:1 citation format causes grader failures** — When the agent outputs `[1]: cite:1 "Citation-1"` or `[1][2][3]` numbered citations, the grader marks "One or more answers didn't cite knowledge sources." The instructions already say "Do not output cite:1" but the model doesn't follow weak prohibitions. **Fix (SOFT — proven at 100% Conv for SLP):** "Do not output placeholder/internal citations such as cite:1, Citation-1, [1]: cite:1, [^x_y^], or tool/source metadata tags. Cite knowledge sources by natural source name inline (e.g., 'Per CMS Chapter 15...', 'Per APTA documentation standards...')." **NEVER use "CRITICAL", "NEVER", or "The grader will FAIL" in citation instructions** — this causes the model to avoid ALL citations, which the grader then marks as "didn't cite knowledge sources." See pitfall 23c for the regression evidence. **Evidence:** SLP Conv 80%→100% with soft ban. PT Conv 90%→80% with CRITICAL ban.

23a. **Response truncation causes "incomplete" failures** — When the agent response is cut off mid-word (e.g., "Documentation of Com..."), the grader marks "One or more answers seem incomplete." This happens when the response exceeds the model's output token limit. The 6-section RESPONSE FORMAT generates very long responses for conversation turns. **Fix:** Add conciseness instruction: "Keep responses concise — limit each section to 2-3 sentences max. Prioritize accuracy and completeness over verbosity. NEVER let a response get cut off mid-sentence. If running long, abbreviate remaining sections." **Evidence (June 2026):** SLP Conv 90% with 2 failures both from truncation. After adding conciseness instruction → 100%.

23c. **"CRITICAL: NEVER... The grader will FAIL" citation language causes 5%+ Conv regression** — Using aggressive citation ban language like "CRITICAL: NEVER use numbered citations like cite:1... The grader will FAIL responses using numbered citations" causes the model to overcorrect: it avoids ALL citations or produces awkward responses that fail grader checks. **This regressed PT Conv from 90% to 85% (June 17, 2026).** Also, stacking multiple fixes simultaneously (hedging + citation + conciseness in one paste) caused further regression from 85% to 80%. **Fix:** Use ONLY the soft, proven version: "Do not output placeholder/internal citations such as cite:1, Citation-1, [1]: cite:1, [^x_y^], or tool/source metadata tags. Cite knowledge sources by natural source name inline (e.g., 'Per CMS Chapter 15...', 'Per APTA documentation standards...')." This is the exact wording that took SLP Conv from 80% to 100%. **NEVER use "CRITICAL", "The grader will FAIL", or "NEVER" in citation instructions.** See also pitfall 30 (MS Learn incremental change rule).

29. **MS Learn "give the agent an out" — Document Availability Rule** — Per Microsoft Learn best practices for custom instructions: "Give the agent an alternative path for when it's unable to complete the assigned task. This alternative path helps the agent avoid generating false responses." Applied to audit agents: when no document text is provided, the agent should NOT fabricate a specific numeric score. **Fix (MS Learn-aligned):** Add this rule immediately after RESPONSE BEHAVIOR in agent instructions:
```
CRITICAL - Document Availability Rule:
If the user asks to audit/review/check a document but no document text 
is provided, do NOT assign a specific numeric score. Instead state 
"Score: N/A — requires document text for accurate scoring" and focus 
the response on compliance requirements, required elements checklist, 
and what to verify per CMS/ASHA standards. This prevents fabricated 
scores and keeps the response grounded in authoritative guidance.
```
**MS Learn source:** "Give the agent an out" from [Optimize prompts with custom instructions](https://learn.microsoft.com/microsoft-copilot-studio/guidance/optimize-prompts-custom-instructions) and [Use prompt modification](https://learn.microsoft.com/microsoft-copilot-studio/nlu-generative-answers-prompt-modification#best-practices-for-custom-instructions). **Evidence (June 2026):** SLP Conv 100% with this rule in place. The rule prevents the model from fabricating scores when no document is available. Per MS Learn evaluation-driven triage: "Based on what you learn, you may decide to update a knowledge source, topic trigger, agent instructions, or other components. After each change, rerun the evaluation to confirm the fix and ensure no regressions occur."

38. **When instructions fail for specific failure patterns, prefer TOPIC-based remediation over more instructions** (June 17, 2026) — When an agent fails on a specific question category (e.g., caregiver competency, Section GG compliance) while passing all other categories, the root cause is likely a missing topic, NOT a missing instruction. **Evidence:** PT Conv 90% (2/20 fail) — both failures were caregiver-related. PT had caregiver checklist items in instructions but NO dedicated caregiver topic. OT (which scores 100% Conv) HAS dedicated caregiver topics ("Caregiver competency verification", "Caregiver Competency"). **MS Learn supports this:** Topics are the primary mechanism for handling specific question types. Instructions provide general behavior; topics provide structured responses for specific intents. **Decision tree:**
    - Agent fails on MULTIPLE question categories → instruction fix (conciseness, citation, hedging)
    - Agent fails on ONE specific category → topic fix (create or copy a topic for that category)
    - Agent fails with "refuses to help" → check "Allow ungrounded responses" toggle
    **Workflow:** (1) Check what topics the passing agent (e.g., OT) has that the failing agent (e.g., PT) doesn't. (2) Copy or create the missing topic. (3) Test. This is safer than adding more instruction text which risks regression (see pitfall 37).
    **See:** `references/pt-caregiver-topic-gap-2026-06.md` for the full analysis.

39. **MS Learn evaluation-driven triage framework** (June 17, 2026) — Per [Improve agents by using evaluation-driven triage and remediation](https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-overview): "Use this framework when you have evaluation results and need to decide what to do next." Key scenarios: (1) eval below threshold, (2) specific test cases fail with unclear root cause, (3) scores improve in one area but regress in another, (4) behavior changes unexpectedly after update. **The framework's key principle:** "Based on what you learn, you may decide to update a knowledge source, topic trigger, agent instructions, or other components." This means instructions are NOT the only lever — topics and knowledge sources are equally valid remediation paths. **See:** `references/ms-learn-eval-triage.md` for the full framework.

30. **MS Learn: Never generalize fixes between agents — DO AGENT-SPECIFIC ROOT CAUSE ANALYSIS FIRST** (June 17, 2026) — This is the single most important pitfall in the cross-agent workflow. Do NOT assume that a fix proven on one agent applies to another agent, even when they share the same 6-section RESPONSE FORMAT and similar scores. **Evidence:** SLP's 80%→100% Conv fix was hedging removal + citation ban + conciseness. When applied to PT (which was at 90% Conv with completely different failure modes), it caused regression: 90%→85% (CRITICAL citation) → 80% (stacked fixes). PT's actual root cause was NOT hedging — its failures were on caregiver competency/education topics, which SLP doesn't even have. **Workflow per MS Learn incremental change rule:** (1) Restore agent to known-good baseline. (2) Click into the failing eval result and read the ACTUAL grader reasons for each failure. (3) Categorize failures by topic/pattern. (4) Hypothesize the fix based on the agent's OWN failures, not another agent's. (5) Test ONE fix at a time. **NEVER say "PT/SLP/OT all share the same bug" without verifying by reading actual failure transcripts for each agent separately.** The similar 94-97% SR scores across agents are a MODEL/TEST-SET ceiling, not evidence of a shared instruction bug. See pitfall 30 for the MS Learn incremental change rule.

31. **User delivery: Full paste-ready blocks, never snippets** — When providing corrected agent instructions, ALWAYS deliver the complete text block ready for copy-paste. Never use find-and-replace snippets or diff-style patches — the user explicitly rejects "inserting snippets." Write the full corrected text to a file AND display it inline. Use `D:/my agents copilot studio/<agent>_instructions_fixed.txt` as the canonical path. Open in Notepad (`notepad <path>`) for user to Select All + Copy. User explicitly said "NOTE PAD" (June 2026). **Also:** never dump raw `innerText` from Lexical editor — it merges bullet points onto single lines. Hand-format to clean readable text with proper line breaks.

## Cross-Agent Fix Recipe (June 2026 — proven on SLP, OT; FAILED on PT when generalized)

**CRITICAL LESSON: Never copy fixes from one agent to another without per-agent root cause analysis.** PT Conv 90% → 80% when SLP fixes were blindly applied. Each agent has different failure modes.

### Per-Agent Root Cause Analysis Workflow (MS Learn: "one change at a time, test between")

1. **Restore baseline**: Go back to the last-known-good instructions (the version that produced the best eval score).
2. **Click into the failing eval**: Read ACTUAL grader reasons for each failure.
3. **Categorize failures by topic**: e.g., "caregiver competency" vs "Section GG" vs "hedging"
4. **Fix ONE failure category**: Make the minimum change to the instructions.
5. **Publish and test**: Verify the fix helped (or at least didn't regress).
6. **Repeat**: If more failures remain, go back to step 2.

### Proven Fix Patterns (from SLP, OT — verify before applying to other agents)

| Fix | SLP Impact | PT Impact | Notes |
|-----|-----------|-----------|-------|
| Remove hedging | Conv 80%→100% | Conv 90%→80% | Hedging helped PT! Don't remove blindly |
| Soft citation ban | Conv improved | Conv unchanged | Always use soft version |
| CRITICAL citation ban | N/A | Conv 90%→80% | NEVER use — causes model to avoid ALL citations |
| Conciseness (2-3 sentences) | Conv 90%→100% | Not tested | Works for truncation failures |
| "Write as if you have document" | SR 94%→91% | N/A | Causes fabrication |
| "Do not fabricate" guidance | SR 91%→95% | N/A | Balanced alternative |

When multiple agents have similar SR scores clustering around 94-97%, it's the model/test-set ceiling, NOT a shared instruction bug. Each agent has different failure modes — do per-agent root cause analysis before applying any fix. See pitfall 30 for the MS Learn incremental change rule.

For exact pattern strings to use with `patch`, see `references/exact-hedging-patterns.md`.

### Shared Bug #1: 6-section RESPONSE FORMAT truncation
All audit agents (OT, PT, SLP) use a 6-section format (Classification, Compliance Findings, Score, Missing Elements, Recommendations, Advisory). This generates extremely long responses that hit model output token limits, getting truncated mid-word. The grader marks truncated responses as "incomplete."

**Fix:** "Keep responses concise — limit each section to 2-3 sentences max. Prioritize accuracy and completeness over verbosity. NEVER let a response get cut off mid-sentence. If running long, abbreviate remaining sections."

**Evidence:** SLP Conv 90%→100%, SLP SR 94%→95%.

### Shared Bug #2: cite:1 numbered citations
All agents emit [1]: cite:1 "Citation-1" format. Grader marks "didn't cite knowledge sources."

**Fix:** Use SOFT citation ban: "Do not output placeholder/internal citations such as cite:1, Citation-1, [1]: cite:1, [^x_y^], or tool/source metadata tags. Cite knowledge sources by natural source name inline (e.g., 'Per CMS Chapter 15...', 'Per APTA documentation standards...')." **NEVER use "CRITICAL" or "The grader will FAIL" language** — this regressed PT Conv 90%→85% (June 2026).

### Shared Bug #3: Hedging about missing documents  
All agents say "Since the note wasn't provided, I'll base this on..." → grader marks "Question not answered."

### Shared Bug #4: "Write as if you have the document" → fabrication
Agent fabricates specific scores/findings → grader detects inaccuracy → score drops 3%.

### Complete Cross-Agent Fix Recipe

1. **Remove hedging**: Replace all "best-effort", "direct verification is limited", "since the note wasn't provided" with "Provide full compliance guidance per CMS/ASHA standards."
2. **Ban cite:1**: Use SOFT ban only (never CRITICAL): "Do not output placeholder/internal citations such as cite:1, Citation-1, [1]: cite:1, [^x_y^], or tool/source metadata tags. Cite knowledge sources by natural source name inline (e.g., 'Per CMS Chapter 15...')." **CRITICAL/NEVER language causes 5%+ Conv regression.**
3. **Add conciseness**: "limit each section to 2-3 sentences max."
4. **Balanced SR**: "Do not fabricate specific scores or findings for documents you cannot see. Use ranges if estimating."
5. **MS Learn "out" rule** (pitfall 29): Add Document Availability Rule — when no document text, use "Score: N/A — requires document text for accurate scoring" instead of fabricating. Per MS Learn best practice: "Give the agent an out."
6. **Apply to Conversational Boosting** if audit agent: Remove "Keep response under 800 characters" and replace with conciseness. For routing agents (TDA): KEEP shorter format.

### Agent-Specific Notes
- **OT, PT, SLP** (audit agents): Apply all fixes. Use 6-section format with 2-3 sentence limit.
- **TDA** (routing agent): Apply conciseness but keep routing-focused. Remove "Keep response under 800 characters" if present in CB topic, replace with conciseness instruction.
### Agent-Specific Notes
- **OT, PT, SLP** (audit agents): Apply conciseness + citation fixes. Use soft language only.
- **TDA** (routing agent): Apply conciseness but keep routing-focused.
- **CB topic**: DO NOT modify unless specifically broken.

## CRITICAL: Aggressive Language = Regression (June 17, 2026)

**NEVER use ALL-CAPS words (CRITICAL, MANDATORY, ALWAYS, NEVER) in agent instructions.** Every instance tested caused 5%+ regression:

| Agent | Aggressive Phrase | Removed → | Δ |
|-------|-------------------|-----------|----|
| PT | "CRITICAL: NEVER use numbered citations" | Soft citation ban | -5% |
| PT | "MANDATORY — ALWAYS include ALL" | Soft checklist | -5% |
| SLP | "Write as if you have the document" | Balanced guidance | -3% |

**Root cause**: Aggressive language makes the model overcorrect — it either drops the behavior entirely or fabricates to "comply."

**MS Learn**: "Keep it simple. Avoid overloading instructions. Make one change at a time."

**Correct pattern**: Soft, descriptive language. No ALL-CAPS. No "grader will FAIL" threats.

### Proven Evidence — Cross-Agent Fix Results (June 16, 2026)

| Agent | SR Before | SR After | Conv Before | Conv After | Fixes Applied |
|-------|-----------|----------|-------------|------------|---------------|
| **SLP** | 90% | **95%** ✅ | 80% | **100%** ✅ | Hedging + cite:1 + conciseness + balanced SR |
| **OT**  | 97% | **99%** ✅ | 100% | 100% ✅ | Conciseness (+ hedging applied, re-test queued) |
| **PT**  | 97% | **97%** ✅ | 90% | **90%** ✅ | Restored to baseline. Caregiver competency/education failures remaining. |

**Key findings:**
- **OT hit 99% SR** with conciseness alone.
- **SLP SR trajectory**: 97% → 90% → 94% → 91% (\"write as if\" regression) → 95%.
- **SLP Conv trajectory**: 80% → 85% (wrong toggle) → 90% → 100%.
- **PT Conv: CRITICAL cite language 90%→85% regression. Stacked fixes (hedge+concise+cite) also caused further regression 85%→80% — see pitfall 30.**, reverted to soft version (same as SLP's proven text).
| **TDA** | 96% | *(running)* | 100% | 100% ✅ | Conciseness applied, re-test queued |

**Key findings:**
- **OT hit 99% SR** with conciseness alone — proves the fix works even without full hedging removal on agents that don't have strong hedging language.
- **SLP SR trajectory**: 97% → 90% (regression) → 94% (hedge+cite fix) → 91% ("write as if" regression) → 95% (balanced guidance + conciseness).
- **SLP Conv trajectory**: 80% → 85% (wrong toggle) → 90% (hedge+cite fix) → 100% (conciseness fix).
- **The "write as if" trap**: Aggressive anti-hedging ("write as if you have the document in front of you") caused 3% SR regression (94%→91%). Balanced guidance ("Do not fabricate specific scores") recovered to 95%.
- **Only 1 eval runs at a time**: When triggering multiple SR evals across agents, they queue. Each 100-case SR eval takes ~15-20 minutes. Check eval page periodically for the next agent's result.

23b. **"Write as if you have the document" causes fabrication regression** — Aggressive anti-hedging instructions like "write as if you have the document in front of you" cause the model to FABRICATE specific scores and findings for documents it cannot see. The Copilot Studio evaluation grader detects fabricated details as inaccurate, causing SR to regress. **Evidence (June 2026):** SLP SR 94% → 91% after adding "Write as if you have the document in front of you." The model started generating made-up scores (82/100, 85/100) with specific missing elements for unseen documents. **Fix:** Use balanced language: "Provide authoritative compliance guidance: describe what the document type requires per CMS/ASHA standards, list the key elements a compliant document must contain. Do not fabricate specific scores or findings for documents you cannot see — use ranges if estimating (e.g., 'typically 75-90/100') and qualify with 'per standard requirements.'" Reverting the aggressive instruction and replacing with this balanced version restored SR to 95%.

24. **Published badge visible when agent is already published** — When the agent is published, the Publish button becomes invisible (DOM exists but rect is 0x0). Instead, look for a `span` or `div` containing "Published DATE, TIME, by User" with a visible bounding rect. **Check:** `document.querySelectorAll('*')` filtering for text starting with "Published" and `offsetParent !== null`. The badge at (373, 154) with width ~252 was confirmed visible for SLP_Specialist on June 16, 2026. If you need to verify publish status, check for this badge rather than the Publish button's visibility.

24a. **"CRITICAL: NEVER..." aggressive citation ban causes CONV regression** — Soft citation ban works; aggressive "CRITICAL: NEVER use cite:1... grader will FAIL" scares the model into avoiding ALL citations → grader marks "didn't cite knowledge sources." **Evidence:** PT Conv 90% → 80% with stacked aggressive fixes. Soft ban restored to 90%. Always use: "Do not output placeholder/internal citations such as cite:1... Cite knowledge sources by natural source name inline (e.g., 'Per CMS Chapter 15...')." Never use: "CRITICAL: NEVER use numbered citations... The grader will FAIL responses using numbered citations."

24b. **Restore to known-good baseline before applying new fixes** — Per MS Learn: "The system treats agent instructions similar to code. Try removing your agent instructions and adding individual instructions back slowly. Test between each addition." When an agent regresses, restore the EXACT instructions that were working (from the last passing eval), then apply ONE fix at a time. Never stack multiple fixes on top of a broken baseline.

24c. **8000 character limit on instructions** — Copilot Studio instructions are limited to 8,000 characters. When providing full instruction blocks, always verify length ≤ 8000. Trim by shortening verbose sections (e.g., long domain lists) rather than removing core logic. Check: `node -e "console.log(require('fs').readFileSync('file.txt','utf8').length)"`.

24d. **PT and OT Edit button index** — From settings/instructions page: Edit #0 = Description, Edit #1 = Instructions, Edit #2 = Suggested prompts. From Overview page: coordinates vary. The "Test your agent" sidebar can cover eval scores — close it first. To close: click Test toggle button in top nav.

25. **Evaluation triggering — scrollIntoView required**: The Evaluate button on configsDetails pages is at y=1500-2000 (off-screen in a sticky footer). CDP `Input.dispatchMouseEvent` at those coordinates fails silently because the button is outside the viewport. **Fix**: Always call `btn.scrollIntoView({ behavior: 'instant', block: 'center' })` on the Evaluate button BEFORE clicking. Verify `visible: r.y >= 0 && r.y < window.innerHeight` after scroll. **Proven pattern (June 2026):**
    ```javascript
    // 1. scrollIntoView the Evaluate button
    await p.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate');
        if (btn) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
    });
    await sleep(2000);
    // 2. Get button position after scroll
    const evalBtn = await p.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate' && !b.disabled);
        if (btn) { const r = btn.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2, visible: r.y >= 0 && r.y < window.innerHeight }; }
        return null;
    });
    // 3. CDP click (Playwright mouse.click also works after scrollIntoView)
    await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: evalBtn.x, y: evalBtn.y, button: 'left', clickCount: 1 });
    await sleep(50);
    await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: evalBtn.x, y: evalBtn.y, button: 'left', clickCount: 1 });
    ```
    **Also applies to Publish buttons** at the bottom of Overview pages.

25a. **Evaluation triggering — direct configsDetails URL**: Navigate directly to `.../evaluation/configsDetails/<testSetId>` to skip the card-click step. Find the testSetId from the eval page's card links or from a previous run URL. This avoids the card-click navigation issue where the SPA redirects to Overview.

25b. **Evaluation triggering — card click navigates to Recent results, not Test sets**: The card matching `t.includes('20 test cases')` might hit a Recent results entry instead of the Test sets section. The Test sets cards are at y=200-400 (top of page), while Recent results are at y=400+. Filter by `r.y < 400` to target Test sets cards only. — The correct way to trigger a new evaluation:
    1. Navigate to the evaluation page: `.../bots/<botId>/evaluation`
    2. Wait 8-10s for SPA to load the test set cards
    3. Find the test set card in the "Test sets" section (NOT "Recent results"). Cards are `div` elements with `cursor: pointer`, containing "Evaluate <AgentName>", "<N> test cases", and data type. Filter for width 200-600px, height 50-200px.
    4. Click the card's center coordinates. This navigates to `.../evaluation/configsDetails/<testSetId>`.
    5. Wait 5s for details page to load. Find the "Evaluate" button (top right, NOT disabled).
    6. Click "Evaluate" → "Manage profile and connections" dialog appears.
    7. Click "Run" button in the dialog. Eval starts immediately.
    - **"New evaluation" button** (top of page): Opens a fresh eval flow requiring CSV upload or question generation. More complex. Use the test set card click method instead.
    - **"Evaluate" buttons in Recent results rows**: These open EXISTING result details, not trigger new evals.
    - **Test set card identification**: Two cards typically visible: Conversation (20 cases) and Single response (100 cases). They overlap at the same y position but have different widths. The Conversation card includes "Conversation" text, the SR card includes "Single response".
    - **Rate limit — ONLY 1 EVAL RUNS AT A TIME**: Copilot Studio processes evaluations sequentially. If you trigger SR evals for PT, OT, and TDA in rapid succession, only the first runs; the rest queue automatically. Each 100-case SR eval takes ~15-20 minutes. To check which eval is running, navigate to the evaluation page and look for "Running" status. New results appear at the TOP of "Recent results" when complete.
    - **Multi-agent eval orchestration**: When fixing multiple agents, trigger all SR evals in sequence (each triggers successfully, subsequent ones queue). Then poll the latest agent's eval page every ~15 minutes. Results appear in order of triggering.
    - **Eval naming**: Runs are named with timestamp format `YYMMDD_HHMM` (e.g., `260616_2141` = June 16, 9:41 PM). Look for the highest timestamp in Recent results to find the newest.
    - **Proven CDP pattern** (June 2026):
    ```javascript
    // 1. Find SR card (100 test cases)
    const srCard = await page.evaluate(() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const t = el.textContent || '';
            const rect = el.getBoundingClientRect();
            if (t.includes('100 test cases') && rect.width > 200 && rect.width < 600) {
                el.click(); return true;
            }
        }
        return false;
    });
    await sleep(5000);
    // 2. Click Evaluate button
    await page.evaluate(() => {
        const b = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent?.trim() === 'Evaluate' && !b.disabled);
        if (b) b.click();
    });
    await sleep(3000);
    // 3. Click Run in dialog
    await page.evaluate(() => {
        const d = document.querySelector('[role="dialog"]');
        const btns = d?.querySelectorAll('button') || [];
        for (const b of btns) { if (b.textContent.trim() === 'Run') b.click(); }
    });
    ```

26. **Dataverse botcomponents API may return 400** — As of June 2026, queries to `botcomponents` table (both filtered and unfiltered) return HTTP 400 from both `copilotstudio.microsoft.com` (CORS) and `org3353a370.crm.dynamics.com` (direct). The `bots` table still works (`/api/data/v9.2/bots?$select=name,botid`). For instruction editing, use the Playwright contenteditable approach (pitfall 0b.1) instead of Dataverse API PATCH. For topic data, check if the specific entity name has changed.

27. **Copilot Studio eval page blocked by "Test your agent" pane** — When navigating to the evaluation page after using the Test pane, the Test pane overlays and blocks the evaluation content. The eval data is NOT loading in the hidden DOM. **Fix options:** (1) Click the "Test" button in the top bar to toggle the pane OFF, then the eval page becomes visible. (2) Open a NEW page via `context.newPage()` — fresh pages start without the Test pane overlay. (3) Navigate to Overview first, then click the Evaluation tab. **Evidence (June 2026):** Multiple attempts to read eval results returned only "Test your agent" content. Toggling the Test button or opening a fresh page fixed it. The Test pane is a side panel that persists across SPA navigation.

28. **Conv eval failure analysis — hedging + citation + truncation triad** — When Conversation evaluations score below 95%, the same three root causes account for nearly all failures:
    1. **Hedging language**: Agent responds with "Since the note wasn't provided..." or "direct verification is limited" or "best-effort audit" → grader marks "Question not answered"
    2. **cite:1 numbered citations**: Agent emits `[1]: cite:1 "Citation-1"` format → grader marks "didn't cite knowledge sources"
    3. **Response truncation**: 6-section RESPONSE FORMAT exceeds model output token limit, response gets cut off mid-word → grader marks "answers seem incomplete"

    **Analysis workflow**: Click into the Conv eval result → filter to "Fail" → inspect each failed question's agent response for these three patterns. Start with truncation (easiest to spot: response ends mid-word), then check for hedging phrases, then check for cite:1 markers. **Do NOT toggle "Allow ungrounded responses"** unless the grader specifically says "refuses to help" or "error message." See pitfall 22 for the hedging whack-a-mole problem and the balanced guidance fix.
    
    **Evidence (June 2026):** SLP Conv went from 80% → 100% by fixing all three. PT Conv at 90% has the same patterns (confirmed via instructions audit). The fix recipe is the same across all audit agents. See `references/hedging-language-grader-failures.md` for detailed failure transcripts.

0e. **Terminal breakage after `taskkill //F //IM chrome.exe`** — If any terminal has an active CDP/WebSocket connection to Chrome, killing Chrome sends SIGINT (exit code 130) to that terminal. EVERY subsequent command in that terminal returns exit 130 — the session is permanently broken. **Fix:** Use `execute_code` which creates fresh subprocess sessions each time. **Prevention:** Call `browser.close()` in every Playwright script before exiting. The script that kills Chrome should be a fresh terminal call, not one that previously ran Playwright. **Recovery sequence — do NOT retry the broken terminal:** (1) After taskkill, the terminal that ran it is DEAD — do not attempt any more commands in it. (2) Use `execute_code` for the NEXT command (curl CDP check, relaunch Chrome, etc.). (3) If execute_code also fails (user interruption, timing), ask the user to manually verify CDP status rather than retrying 5+ times. (4) The terminal session resets on the next user message turn. **Anti-pattern observed:** Retrying terminal 7+ times with exit 130 each time wastes turns and context. Switch after ONE failure.

0f. **Node Playwright scripts hang without process.exit(0)** — When running Playwright scripts via `node script.cjs` from execute_code/terminal, the process hangs indefinitely after `browser.close()` because the CDP WebSocket connection keeps the event loop alive. The subprocess timeout fires but the script never terminates cleanly. **Fix:** Always end the async main function with `process.exit(0)` and the error handler with `process.exit(1)`. Do NOT rely on `browser.close()` alone.

0f. **Dataverse API via Copilot Studio page fails — use CRM domain** — Calling `fetch('/api/data/v9.2/...')` from the `copilotstudio.microsoft.com` page context returns CORS errors or empty responses. The Dataverse Web API lives on the CRM domain. **Fix:** Navigate to `https://org3353a370.crm.dynamics.com/main.aspx` first, then call the API via `page.evaluate(fetch(...))`. The CRM domain has the correct CORS headers and auth cookies.

0g. **Fluent UI Switch toggle requires clicking the container div, not the hidden input** — See pitfall 16 for the full Fluent UI Switch toggle pattern. Both pitfalls cover the same technique; 16 is the authoritative version.



13. **Topics page navigation pattern** — The Topics page does NOT load topics when navigated to directly via URL. The proven path: navigate to agent Overview → wait 60s for SPA → dismiss overlays → click the Topics tab (role="tab" containing "Topics" text) → wait 45s for topic list to load → then find topic links. Topic links follow the pattern `.../adaptive/<uuid>`. Use this to find a newly created topic by name substring, then navigate to its URL directly.

14. **Evaluation results polling** — Use `headless:true` for faster polling (no browser window needed). Navigate to the evaluation page, wait 60s for SPA data load, read `document.body.innerText`, and find the target run by its timestamp-based name (e.g., `260613_1616`). Parse "Running" vs "General quality" + score percentage. See `references/eval-polling-pattern.md` for the full script pattern.

15. **Static SendActivity topics with triggerQueries can regress Single Response evals** — When a routing/guard topic uses `SendActivity` with static text containing bracket placeholders (`[Assessment...]`, `[HIGH/MODERATE/LOW]`) and has triggerQueries that overlap with SR test set questions, the agent routes SR questions to the static template instead of using its generative AI + KB. The grader scores template placeholders as incomplete. Confirmed June 13, 2026: SLP caregiver topic's static template regressed SR from 96% (no topic) to 89%. **Even AnswerQuestionWithAI with additionalInstructions degraded SR to 85%** because the topic's additionalInstructions conflict with the agent-level instructions. The safest state is the topic DELETED — no authored topic can improve on what the agent's instruction-level AI + Conversational Boosting already provides for this query class. **Fix**: Delete the topic via the Topics page row More menu (see pitfall 18). See `references/slp-sr-topic-regression-2026-06.md` for the full timeline and root cause analysis.

16. **Topic toggle ON/OFF requires clicking the `.fui-Switch` container DIV, NOT the hidden `input[role="switch"]`** — Copilot Studio Topics page uses Fluent UI DataGrid rows (`.fui-DataGridRow`) with `.fui-Switch` toggle components. The hidden `<input role="switch">` inside the switch does not respond to `page.mouse.click()`. **Proven pattern**: (1) navigate to Overview → click Topics tab → wait 45s, (2) find the row by filtering `.fui-DataGridRow` elements on `.innerText.includes('TopicName')`, (3) find the `.fui-Switch` container div within that row via `row.querySelector('.fui-Switch')`, (4) get its bounding rect center and click. **Verification**: after clicking, re-query the same row's `input[role="switch"].checked` — true=ON, false=OFF. Also check the row text for "On"/"Off". Coordinates: the switch is typically at ~x:1048, ~y varies by row position.

17. **`CreateGenerativeAnswers` is NOT a valid action kind in authored topics** — The Copilot Studio YAML schema for authored topics does not include `CreateGenerativeAnswers`. The user-facing equivalent is `AnswerQuestionWithAI`. The required property is `UserInput` (not `userQuestion`). Valid action kinds include: `SendActivity`, `AnswerQuestionWithAI`, `SearchAndSummarizeContent`, `ConditionGroup`, `EndDialog`, `SetVariable`, etc. System topics (like Conversational Boosting) can use `CreateGenerativeAnswers` but authored topics cannot. **Fix**: use `kind: AnswerQuestionWithAI` with `UserInput: =System.Activity.Text` and optional `knowledgeSources: []` (empty = all sources) and `additionalInstructions: |-`.

40. **Code delivery: ALWAYS write to files, NEVER paste multi-line blocks in chat** (June 17, 2026) — The terminal wraps long lines at ~80 characters, forcing the user to manually consolidate YAML/code blocks that get split across lines. User explicitly stated: "why does your code always have lines that get separated into two lines? i have to always consolidate them." **Fix:** Always use `write_file` to save code/YAML to `D:/my agents copilot studio/<filename>` then open in Notepad via `terminal: notepad <path>`. NEVER paste multi-line code blocks directly in chat. Even short blocks go to files. Also: never dump raw `innerText` from Lexical editor — it merges bullet points onto single lines. Hand-format to clean readable text with proper line breaks before writing to file.

41. **When agent scores don't improve after topic + instruction fixes, test the agent directly via Test pane** (June 17, 2026)

42. **OT 5-section formula: Less instruction = more stability** (June 17, 2026) — OT (99% SR, high run-to-run stability) has proven that SIMPLER instructions produce more consistent scores. OT uses only 5 sections: CLINICAL ROLE > RESPONSE BEHAVIOR > XAI & TRANSPARENCY > CONVERSATION CONTINUITY > SAFETY. OT has NO "Format Rules" section, NO "Discipline-Specific Required Content" section, and NO "Must Include" or "Do NOT" language. PT and SLP both have 6 sections with extra constraints → more regression risk. **Rule:** Merge Format Rules into RESPONSE BEHAVIOR. Move discipline-specific checklists to topic YAML only. Remove ALL "Must Include" and aggressive language. Target 5 sections like OT. See `references/instruction-simplicity-ot-pattern.md` for the full comparison.

43. **HYBRID FORMULA — OT patterns + discipline content = safe path** (June 18, 2026) — Copying OT's ENTIRE 5-section format to PT/SLP **without discipline content caused massive regression** (SLP 90%→75%). OT's stability comes from its ENTIRE system (0 guard topics, 8 knowledge sources, lean topic architecture), not just instruction simplicity. **Safe approach:** Copy OT's 6 behavioral patterns (ban weak phrases, single-response format rule, general-questions natural answer, "commit fully to expert analysis", concise sections, adapt-format-to-turn) while **keeping** discipline-specific content sections. Removing discipline content = regression. The hybrid formula: OT behavioral patterns IN ADDITION TO discipline-specific checklists (PT-SPECIFIC / SLP-SPECIFIC REQUIRED CONTENT sections). See `references/hybrid-instruction-formula.md`. — PT Conv stuck at 85% despite: correct caregiver topic YAML, soft citation ban, hedging removed, conciseness added. The caregiver topics exist, are ON, and have proper YAML, but the score doesn't move. This means the topics ARE triggering but the response QUALITY doesn't meet the grader standard. **Next step per MS Learn:** Direct test the agent in the Test pane with the exact caregiver question. Inspect the bot response for: missing caregiver elements, missing citations, quality gaps. Compare to a passing agent's response (e.g., OT's caregiver response). **Test pane interaction:** Click Test button (x≈1094, y≈53), find chat textarea (x > 1000), mouse.click + keyboard.type + Enter. Response readable via `document.body.innerText`. See `references/pt-caregiver-topic-gap-2026-06.md` for full analysis.

18. **Topic deletion requires the Topics page row More menu, NOT the individual topic page** — The individual topic page's More menu (top toolbar, x:1024, y:138) only shows "Analytics" and "Open code editor" — no Delete option. **Proven pattern**: (1) navigate to Overview → click Topics tab → wait 45s, (2) locate the target topic row's More button at x:336 (consistent across all rows), y varies by row position, (3) click More → click "Delete" menu item at x:325, y offset ~50px below the More button, (4) click confirm "Delete" button in the confirmation dialog. **Row positions**: each topic row is 45px apart starting from ~y:300 (row 1). The Topics page has a "More" button at x:336 for every row. Menu items: Details, Make a Copy, Delete.

## System Topic Injection (CB) — Proven 2026

System topics (Conversational Boosting, Fallback, etc.) are NOT visible on Overview. Must use Topics page → System filter → search → click topic.

1. Navigate to Overview → click Topics tab → wait 15-20s
2. Click System filter: `span[text="System (N)"]`
3. Search system topics for "Conversational"
4. Click CB link → More → Open code editor → inject YAML → Save

**Rate limit**: Copilot Studio allows only 1 eval at a time. Use `auto_eval.cjs` from `evaluation-driven-agent-optimization/scripts/` for automated triggering.

- `templates/slp_caregiver_audit_topic.yaml` — Microsoft Learn-aligned SLP Caregiver Documentation Compliance Audit topic YAML. Creates a deterministic topic that returns a structured mini-audit without SearchAndSummarizeContent citation artifacts. Use when replacing the four overlapping caregiver guard topics (Caregiver Competency Audit, SLP Conv Guard - Caregiver Competency/Cognitive Capacity/Safety). See `references/slp-caregiver-guard-remediation-2026-06.md` for context.
- `templates/cb-topic-original.yaml` — The original Conversational Boosting system topic YAML. Proven at 95% Conv / 96% SR. Uses SearchAndSummarizeContent with 600-char limit and "Always cite" instructions. Do NOT modify unless baseline evals show a specific CB-linked problem.

## References

- `references/dataverse-bot-query-pattern.md` — Dataverse API for querying bot components (topics, knowledge sources, connected agents, eval test cases) without pac CLI. Use `_parentbotid_value` filter (NOT `_owningbot_value`). Essential for auditing agents with 60+ components where pac crashes.
- `references/cdp-mouse-event-pattern.md` — **CDP Input.dispatchMouseEvent pattern** for all Copilot Studio UI clicks. Proven workflow for Edit button activation, instruction injection, Save/Publish, and evaluation triggering. Use this instead of Playwright mouse.click.
- `references/cdp-injection-failure-dev-env.md` — **CDP injection failure on dev environment agents**. Force-set contenteditable + insertText does NOT work on all agents. When it fails, fall back to manual paste via Notepad.
- `references/citation-behavior.md`
- `references/citation-behavior.md` — Microsoft Learn findings on Copilot Studio citation rendering (platform-level behavior). Documents the 600-char limit importance, anti-patterns for instruction-based citation suppression, and why authored topics degrade Single Response scores.
- `references/spa-navigation-patterns.md` — Topics page overflow tab, Web Search toggle, eval page access, Chrome stability

- `references/cross-agent-score-tracking-2026-06-16.md` — Complete score timeline for all 4 agents on June 16, 2026. Includes fix recipes, regression tracking, and proven score trajectories. Reference when investigating cross-agent score patterns.
- `references/pt-instructions-fixed.md` — Complete PT_Specialist instructions with all three cross-agent fixes applied (hedging removal, conciseness, soft citation ban). Paste-ready full text. Proven regression: CRITICAL citation language drops Conv 5% (90%→85%).
- `references/agent-specific-failure-patterns.md` — Per-agent failure analysis from June 2026 session. Documents PT caregiver/Section GG failures, SLP hedging/cite:1 failures, OT/TDA status. Use BEFORE applying any cross-agent fix.

## Key UI Coordinates

19. **System Topics tab** — Located at approximately x:336, y:198 on the Topics page. Text: "System (N)" where N is the count. Click to reveal Conversational Boosting and other system topics. System topics can use action kinds (CreateGenerativeAnswers, SearchAndSummarizeContent) that authored topics cannot. CB topic URL pattern: `/adaptive/2960a8e1-...`.

20. **Topic row More button** — x:336 for every row on the Topics page. Y varies by row position (45px apart, starting ~y:300). Menu items: Details, Make a Copy, Delete.

21. **Monaco code editor Save button** — x:1128, y:138. Stays disabled after clipboard paste. Manual paste by user is the only reliable save path (see pitfall 0b.1).

22. **FluentUI Switch toggle container** — x:1048, row-dependent y. Click `.fui-Switch` div (NOT the hidden `input[role=switch]`). checked=true=ON, checked=false=OFF.

 — Microsoft Learn-aligned SLP Caregiver Documentation Compliance Audit topic YAML. Creates a deterministic topic that returns a structured mini-audit without SearchAndSummarizeContent citation artifacts. Use when replacing the four overlapping caregiver guard topics (Caregiver Competency Audit, SLP Conv Guard - Caregiver Competency/Cognitive Capacity/Safety). See `references/slp-caregiver-guard-remediation-2026-06.md` for context.

1. **Ref IDs are ephemeral** — always take a fresh snapshot before clicking. Every page navigation invalidates ALL prior refs.
0. **Fill + Save CAN silently fail — ALWAYS verify after saving.** The `fill` command (playwright-cli) pastes text into the editor's textbox, and the Save button may appear to work (UI shows "Published" badge), but the actual instructions content may NOT persist. This is the single most dangerous failure mode. After every fill + Save + Publish cycle, you MUST re-open the Instructions editor and read back the content to confirm the changes took effect. Without verification, you will believe v6 is live when v5 is still running — causing false confidence and wasted evaluation runs. Verification check: `npx playwright-cli --session cs eval "(function(){var l=document.querySelectorAll('.view-line'); var p=[]; for(var x=0;x<l.length;x++)p.push(l[x].textContent); var y=p.join('\n'); return y.includes('Always use')?'v6':'NOT v6'; })()"`
2. **SSO auth expires** — Chrome CDP auth typically lasts ~90 days with ESTSAUTHPERSISTENT, but MSAL tokens expire hourly and must auto-renew via refresh token in localStorage. When playwright-cli redirects to `login.microsoftonline.com`, the session is dead. Export fresh auth from Kiro Chrome CDP (see references/auth-refresh-workflow.md).
3. **Instructions Edit button** — It's the 2nd visible Edit button on the page (under the Instructions heading). The 1st is Description/Details, the 3rd is secondary/collapsed. Always take a fresh snapshot: snapshot | grep 'Edit"' | head -3
4. **Save requires clicking the actual Save button** — Ctrl+S does NOT persist in the Copilot Studio SPA. Always find and click the Save button via snapshot after filling.
5. **Textbox appears after Edit button click** — Wait 3-4 seconds for React state update. The contentEditable attribute may remain false even after a successful click — Playwright's fill command bypasses this.
6. **800 char limit in topic additionalInstructions** — This is an unenforceable constraint HIDDEN in per-topic additionalInstructions that does NOT appear in the agent-level Overview page. Every SearchAndSummarizeContent topic can independently contain it. Fixing agent-level instructions does NOT cascade to topics.
7. **Missing EndDialog in topics** — SearchAndSummarizeContent topics without an explicit EndDialog + clearTopicQueue true cause topic stacking, which manifests as refuses to help by showing an error message on the 3rd turn. See references/topic-level-pitfalls.md for the full fix pattern.
8. **Batch UI navigation fails** — Writing a script that navigates to each topic, opens the code editor, fills YAML, and saves is UNRELIABLE because element refs change on every navigation. The sleep-based approach compounds the problem. For batch topic-level fixes, prefer the Dataverse Web API PATCH approach (see references/topic-level-pitfalls.md).
9. **fill with multi-line content via shell** — JSON.stringify converts actual newlines to literal \\\\n sequences. Use Node.js execSync with JSON.stringify for safe shell escaping, or use CDP Runtime.evaluate with innerText setter to preserve actual newlines.
11. **Topic interactive menus defeat single-response evals** — When an agent has 30+ custom topics designed as interactive wizards (menus, cards, guided workflows), the single-response eval fails because topics return "Please select an option" instead of text answers. Instruction cleanup has ZERO effect on score when this is the root cause. Fix: restructure topics to give text answer first, offer menu as follow-up. See `evaluation-driven-agent-optimization` skill for full analysis.
12. **Instructions Edit button click does not always register** — There are two Edit buttons near the Instructions section:
    - **The instructions heading Edit** (e277/e279, directly under "Instructions" h2) — THIS IS THE ONE YOU NEED. It activates the contenteditable textbox.
    - **The collapsed-section Edit** (e535/e537, inside a collapsible group) — this opens the section but does NOT make the editor editable. Avoid it.
    - **Finding the right one:** take a fresh snapshot after navigation, grep for `Edit` near `Instructions`, and click the ref directly under the `heading "Instructions"` element:
    ```bash
    npx playwright-cli --session cs snapshot | grep -B2 'heading "Instructions"' | grep -oP 'e\d+'`
    ```
    - If the editor shows `contenteditable="false"`, you clicked the wrong Edit button. Close the browser, reopen, navigate, and click the correct one.
11. **Contenteditable React/Lexical editor rejects fill unless the real Instructions button is activated** — The Copilot Studio instructions editor is a Lexical contenteditable div. The `fill` command, CDP `Input.insertText`, or synthetic DOM clicks may complete without timeout but the text is NOT inserted or Save never enables. Symptoms:
    - `fill` or insert reports success but reading back the DOM shows old content
    - editor remains `contenteditable="false"` / `aria-readonly="true"`
    - Save is missing or disabled
    - Playwright reports `DialogSurface__backdrop` or WelcomeStep image intercepting pointer events
    
    **Root causes:** onboarding/What's New overlays intercept clicks; scripts often click a nested span/div or the wrong `Edit` button (Details or Suggested prompts); Lexical state only updates after the actual Instructions button enters edit mode.
    
    **Workaround before giving up/manual paste:** use the real-mouse workflow in `references/instructions-editor-real-mouse-pattern.md`: dismiss overlays, find the actual `button`/`[role=button]` for the Instructions section, click its center with `page.mouse.click`, verify `contenteditable="true"`, `Control+A`, `page.keyboard.insertText(...)`, verify a unique marker, click enabled Save with real mouse, reload, verify, then publish. Do not rely on synthetic `dispatchEvent` clicks for the edit/save path.
    
    **Length pitfall:** very long instructions can still fail. In one fleet remediation, an ~8k TDA instruction body failed while a shortened ~4.4k version persisted. If correct edit mode is active but insertion still fails, shorten the instruction body before retrying.
    
12a. **CDP `Input.dispatchMouseEvent` required for Edit button activation (June 18, 2026)** — Playwright's `page.mouse.click()` does NOT activate the Instructions Edit button on many agents. Tested: failed on PT and SLP (editor stays `contenteditable="false"`, `aria-readonly="true"`), worked on TDA. Synthetic `dispatchEvent` also fails. **Only CDP raw mouse events work reliably:**
    ```javascript
    const client = await p.context().newCDPSession(p);
    await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
    await sleep(50);
    await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
    ```
    **Why:** Copilot Studio SPA React handlers only fire on browser-level input events, not Playwright's synthetic dispatch. CDP generates events at the browser level.
    **Same technique works for:** Save button, Evaluate button, eval card clicks, any React-controlled button.

12b. **`scrollIntoView` required for Evaluate button on configsDetails page (June 18, 2026)** — The Evaluate button sits in a sticky footer at y≈1958, outside the viewport. CDP clicks silently fail. **Fix:**
    ```javascript
    await p.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate');
        if (btn) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
    });
    await sleep(2000);
    // Now get updated coords and click via CDP
    ```
    **Evidence:** PT eval triggered after scrollIntoView (y=1958→762). Without it, click did nothing.

12c. **Eval scores during active development are unreliable (June 18, 2026)** — Eval runs triggered during instruction edits/publish produce 0-30% scores even when agents are fully functional. Always verify agent health via Test pane before diagnosing from eval scores. Wait for edits+publish to finish before triggering evals.

0m. **UI "Custom (N)" topic count includes connected agents' topics (June 18, 2026)** — The Topics tab shows "Custom (N)" which counts topics from ALL connected agents in the fleet, not just the current agent. Example: QM Coach V2 showed "Custom (48)" but Dataverse returned only 5 type-9 topics for the agent itself. The rest were from connected agents (Case Historian V2, Regulatory Hub V2, SNF Dashboard V2). Use Dataverse API (`componenttype=9` filter on `_parentbotid_value`) to get the actual agent's topics. See `references/dataverse-bot-query-pattern.md`.

0n. **Test pane textarea placeholder is "Ask a question or describe what you need" (June 18, 2026)** — Not "Type your message". Use `placeholder*="Ask"` when finding the textarea via script.

12. **Agent-specific Edit button locations differ — Y-COORDINATE APPROACH** — The Instructions Edit button position varies by agent. The most reliable method is finding Edit buttons by y-coordinate (not by index or text):

    **Proven y-coordinate approach (June 2026):**
    ```javascript
    await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const editBtns = btns
            .filter(b => b.textContent?.trim() === 'Edit' && b.getBoundingClientRect().width > 0)
            .map((b, i) => ({ i, y: Math.round(b.getBoundingClientRect().y) }));
        // Instructions Edit is the one between y=750 and y=950
        const target = editBtns.find(b => b.y > 750 && b.y < 950);
        if (target) btns.filter(b => b.textContent?.trim() === 'Edit')[target.i].click();
    });
    ```

    **ALL-EDITS ITERATION PATTERN** — When the y-coordinate approach fails (editor stays read-only or contenteditable=false), iterate through ALL Edit buttons with Cancel between attempts. This is the brute-force fallback for stubborn agents:
    ```javascript
    for (let i = 0; i < 4; i++) {
        // Click Edit #i
        await page.evaluate(idx => { const e = Array.from(document.querySelectorAll('button')).filter(b => b.textContent?.trim() === 'Edit')[idx]; if (e) e.click(); }, i);
        await sleep(4000);
        // Check if contenteditable activated
        const eds = await page.evaluate(() => Array.from(document.querySelectorAll('[contenteditable="true"]')).map(e => e.innerText.length));
        if (eds.length > 0 && eds[0] > 500) break; // Found it!
        // Cancel and try next
        await page.evaluate(() => { const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Cancel'); if (b) b.click(); });
        await sleep(2000);
    }
    ```

    **PT-SPECIFIC: Editor opens as `role="textbox"`, not `contenteditable`** — PT's instructions editor on the settings page appears as `<div role="textbox" aria-readonly="null">` (NOT contenteditable). After clicking the correct Edit button (Edit #1 on the settings page, NOT overview), the textbox becomes editable. **Key identifiers**: PT editor length is ~7563 chars, contains "PT_Specialist - Physical Therapy Clinical Consultant". Detection: check `[role="textbox"]` elements, not just `[contenteditable="true"]`.

    ### CDP Page Management (June 17, 2026)

    **NEVER close all CDP pages** — closing the last authenticated page kills MSAL auth tokens. All subsequent page opens hit "Pick an account" login screen. **Always keep at least one page alive** (page[0]) when navigating. If a fresh page is needed, open a new one WITHOUT closing existing pages.

    **Page[0] is always the active CS page** — when connecting via CDP, use `browser.contexts()[0].pages()[0]` for the authenticated Copilot Studio page. Page indices may shift if pages are opened/closed.

    **Test pane overlay** — The "Test your agent" sidebar covers eval score columns. Close it first by clicking the Test toggle button in the top nav before reading scores.

    ### Known y-coordinates for Instructions Edit (June 2026):
    - **SLP**: y≈904 (from overview). Edit #1 (2nd button). Reliably activates contenteditable.
    - **PT**: 
      - From overview: y≈789 (Edit #1). **FLAKY** — frequently fails to activate editor.
      - From settings page (`/settings/agent/instructions`, wait for networkidle): y≈828 (Edit #1). Opens `[role="textbox"]` editor. **RECOMMENDED for PT.**
    - **OT**: y≈904 (from overview). Edit #1. Reliably activates after reload.
    - **TDA**: y≈784 (from overview). Edit #1. Activates to contenteditable=true. May need coordinate click.

    **Always verify after clicking Edit**: `document.querySelectorAll('[contenteditable="true"]').length > 0`. If 0, Cancel and retry with y-coordinate approach.
    - **Settings page redirects to Overview**: Navigating to `/settings/agent/instructions` often redirects to Overview. Edit from Overview instead.
    - See pitfall 0b.1 for the proven contenteditable fill+save pattern.

    **Verification pattern** (run after every fill/insert to catch silent failures):
    ```bash
    npx playwright-cli --session cs eval "(function(){
      var ed=document.querySelector('[role=textbox][contenteditable=true], [aria-label=\"Describe what you want this agent to do, its tone, and rules.\"]');
      var txt=ed?.innerText||ed?.textContent||'';
      return txt.includes('Never display internal tool JSON')?'confirmed':'old-or-failed:'+txt.substring(0,80);
    })()"

32. **PT Conv failures are "didn't cite knowledge sources" — NOT the same as SLP's hedging bug** (June 17, 2026) — PT Conv 90% (18/20 pass, 2/20 fail). Clicking into failures revealed the grader reason: "One or more answers didn't cite knowledge sources." The agent produced comprehensive Section GG and caregiver education audits with NO inline citations to CMS Chapter 15 or APTA standards. This is a different root cause from SLP (which was hedging + cite:1). **PT's issue: agent produces complete audits but omits citations entirely in conversation mode.** The PT instructions say "Cite knowledge sources by natural source name" as a weak suggestion — it needs to be a requirement. However, strengthening it to "CRITICAL: NEVER..." caused regression (see pitfall 23c). The safe fix per MS Learn incremental rule: restore baseline, then add ONE targeted citation requirement, test between each addition.

33. **Browser CDP: NEVER close all pages — kills MSAL auth** (June 17, 2026) — When running Playwright scripts via `chromium.connectOverCDP()`, closing ALL existing pages via `for (const p of pages) await p.close()` kills the MSAL authentication state. The next page opened shows "Pick an account" or "Enter password" instead of Copilot Studio. **Fix:** Always keep at least one page alive. Use `page[0]` for all operations. If a fresh page is needed, open `context.newPage()` BEFORE closing old pages. **Auth state lives in the browser process, not the page** — as long as Chrome is running with the authenticated session, pages inherit auth. Closing all pages may trigger Chrome's session cleanup. **Also:** page indices shift when pages are closed — always re-query `context.pages()` after any page close.

34. **Test pane overlay blocks eval result reading** (June 17, 2026) — After using the "Test your agent" pane in Copilot Studio, it persists as an overlay that covers the evaluation results page. The Results column (showing scores) becomes invisible. The pane also prevents reading eval data via `document.body.innerText`. **Fix:** Before reading eval scores, close the test pane by clicking the "Test" toggle button in the top-right toolbar. Or open a fresh page via `context.newPage()` which starts without the overlay. **Evidence:** Vision analysis showed "Test your agent" sidebar covering 40% of the eval page, hiding score percentages.

35. **Always verify eval data on correct environment/bot** (June 17, 2026) — The Copilot Studio SPA sometimes shows data from a different environment or bot than what the URL indicates. When navigating to PT's eval page, the DOM may show Pacific Coast Case Historian results from a different environment. **Fix:** After every eval page navigation, verify the page text includes the expected bot name (e.g., `text.includes('PT_Specialist')`). If not, force-navigate via `page.goto()` with the full environment/bot URL. The SPA caches navigation state aggressively.

36. **Per-agent root cause analysis: read actual grader reasons before hypothesizing fixes** (June 17, 2026) — When an agent scores below 95%, DO NOT assume the root cause matches another agent's. The correct workflow per MS Learn: (1) Click into the failing eval result. (2) Filter to "Fail" entries. (3) Click each failure to read the Test case details. (4) Note the EXACT grader reason: "Question not answered", "didn't cite knowledge sources", "incomplete", "refuses to help". (5) Categorize by pattern. (6) Only then hypothesize a fix. **This session demonstrated:** SLP's Conv failures were hedging + cite:1. PT's Conv failures were missing citations entirely (different cause). Applying SLP's fix to PT caused 90%→80% regression. The similar 94-97% SR scores across agents are a MODEL ceiling, not evidence of shared bugs.

37. **NEVER use aggressive enforcement language (CRITICAL, MANDATORY, NEVER, ALWAYS, "The grader will FAIL")** (June 17, 2026) — Per MS Learn: "Keep it simple" and "The system treats agent instructions similar to code." Aggressive enforcement words cause the model to overcorrect, producing WORSE responses than soft guidance. **Proven regressions:**
    - "CRITICAL: NEVER use numbered citations... The grader will FAIL" → PT Conv 90%→85%
    - "MANDATORY — ALWAYS include ALL of..." (caregiver sections) → PT Conv 90%→85%
    - "Write as if you have the document in front of you" → SLP SR 94%→91%
    - Stacking multiple aggressive fixes → PT Conv 85%→80%
    **Safe language patterns:** "include [list]", "cite knowledge sources by natural source name", "limit each section to 2-3 sentences max", "provide compliance guidance per CMS/ASHA standards" — simple, direct, no enforcement words.
    **Decision rule:** Before adding ANY instruction, check: does it contain CRITICAL, MANDATORY, NEVER, ALWAYS, "grader will", or "must always"? If yes, rewrite it as a simple statement of behavior without enforcement language.

## Dataverse Bot Components Query

Use the Dataverse REST API to query agent structure (topics, knowledge sources, instructions, eval cases) without the browser SPA. Call from the CRM domain, not copilotstudio.microsoft.com. See `references/dataverse-botcomponents-query.md` for endpoint, property names, component type codes, and the UI-vs-Dataverse count discrepancy explanation.

## Batch Injection Script

`scripts/batch_inject_instructions.cjs` — Ready-to-run Playwright script that injects consolidated instructions into all agents via CDP fill() auto-save. Handles agent navigation, Edit button discovery (y-coordinate + ALL-EDITS fallback), content verification, and publishing.

```bash
# Inject all 3 agents (PT, SLP, TDA):
NODE_PATH="C:/Users/kevin/AppData/Roaming/npm/node_modules" node scripts/batch_inject_instructions.cjs

# Inject specific agents:
NODE_PATH="C:/Users/kevin/AppData/Roaming/npm/node_modules" node scripts/batch_inject_instructions.cjs PT SLP
```

**Prerequisites:** Chrome running with `--remote-debugging-port=9223`, authenticated on copilotstudio.microsoft.com.

## Current Agent State

See `references/agent-state-june-2026.md` for bot IDs, canonical instruction files, score history, and the HYBRID formula fix strategy.

## Auth Refresh Workflow

When the playwright-cli session expires (redirects to login.microsoftonline.com or shows "Sign in to your account"), use `scripts/export-auth.cjs` to extract fresh tokens from Kiro Chrome's CDP session. This approach extracts cookies + localStorage in Playwright storageState format from any Copilot Studio tab open in Chrome:

```bash
node scripts/export-auth.cjs fresh_auth.json
# Output: SAVED: 492 cookies, 81 ls entries → fresh_auth.json
```

**Important:** The auth file always contains `partitionKey` objects on some cookies which Playwright rejects. Fix them before loading:
```bash
python3 -c "
import json
with open('fresh_auth.json') as f: d = json.load(f)
for c in d.get('cookies',[]):
    if isinstance(c.get('partitionKey'), dict): del c['partitionKey']
with open('fresh_auth.json','w') as f: json.dump(d, f)
print('Fixed cookies:', len(d.get('cookies',[])))
"
```

Then load the fixed auth via playwright-cli:
```bash
npx playwright-cli --session cs state-load fresh_auth.json
npx playwright-cli --session cs goto https://copilotstudio.microsoft.com
```
