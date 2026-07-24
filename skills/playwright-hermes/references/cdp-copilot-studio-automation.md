# CDP-Based Copilot Studio Automation

Use raw Chrome DevTools Protocol (via Node.js WebSocket) when playwright-cli auth is broken or when you need deep DOM access that playwright-cli doesn't provide. This is especially useful on Windows where Kiro Chrome has the live MSAL token cache but playwright-cli sessions need conversion.

## 1. LAUNCH KIRO CHROME WITH CDP

```powershell
# Launch Chrome with Kiro's profile and remote debugging on port 9223
# Run as background process (terminal background=true)
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9223 \
  --user-data-dir="C:\Users\kevin\AppData\Local\Programs\Kiro\.playwright-auth" \
  --no-first-run --no-default-browser-check \
  --disable-extensions \
  about:blank
```

Verify it's running:
```bash
curl -s http://127.0.0.1:9223/json/version | grep Browser
```

## 2. CDP HELPER PATTERN

All CDP scripts follow this pattern:

```javascript
const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');

http.get('http://127.0.0.1:9223/json', (res) => {
  let data = '';
  res.on('data', c => data += c);
  res.on('end', () => {
    const pages = JSON.parse(data);
    const page = pages[0]; // First tab
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let callId = 0;
    const calls = {};
    
    function send(method, params) {
      const id = ++callId;
      ws.send(JSON.stringify({id, method, params}));
      return new Promise(resolve => { calls[id] = resolve; });
    }
    
    ws.on('message', (msg) => {
      const r = JSON.parse(msg);
      if (r.id && calls[r.id]) { calls[r.id](r); delete calls[r.id]; }
    });
    
    ws.on('open', async () => {
      // Your automation here...
      await send('Page.navigate', {url: 'https://...'});
      // Always close when done
      ws.close();
      process.exit(0);
    });
  });
});
```

## 3. NAVIGATING COPILOT STUDIO

### 3a. Find an agent's bot ID

Navigate to the agents list, search for the agent name, and extract the URL:

```javascript
// Navigate to agents list
await send('Page.navigate', {url: 'https://copilotstudio.microsoft.com/environments/<envId>/bots'});
await sleep(15000);

// Extract bot IDs from links
const result = await send('Runtime.evaluate', {
  expression: `
    JSON.stringify(
      Array.from(document.querySelectorAll('a'))
        .filter(a => a.textContent.includes('Your Agent Name'))
        .map(a => ({text: a.textContent.trim().substring(0,80), href: a.href}))
    )
  `
});
```

Environment IDs for this user:
- Ensign Services (default): `Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f`
- Therapy AI Agents Dev: `a944fdf0-0d2e-e14d-8a73-0f5ffae23315`
- PCCA Package: `077422cf-d088-e3d7-917e-5c9a9b64710c`

### 3b. Navigate to a specific agent

Direct topic URLs work:
```
https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/adaptive/<topicComponentId>
```

The `/topics` URL redirects to `/overview` in CS SPA. To reach topics:
1. Navigate to `/overview` first
2. Wait for page load (~15s)
3. Click the "Topics" tab button or use `+8` overflow tab

### 3c. Clicking tabs in the agent nav

CS uses Fluent UI tabs. The inner nav (Overview, Knowledge, Tools, Agents, Topics...) uses:
- `<span class="fui-Tab__content">Topics</span>` inside `<button>` elements
- The "+8" overflow button shows remaining tabs

Click pattern:
```javascript
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const spans = document.querySelectorAll('span.fui-Tab__content');
      for (const s of spans) {
        if (s.textContent === 'Topics' && s.offsetParent !== null) {
          s.parentElement.click();
          return 'clicked Topics';
        }
      }
      return 'not found';
    })()
  `
});
```

### 3d. Polling for page content

CS SPA renders after `Page.loadEventFired`. Poll `document.body.innerText`:

```javascript
for (let attempt = 0; attempt < 20; attempt++) {
  await sleep(3000);
  const result = await send('Runtime.evaluate', {
    expression: 'document.body?.innerText?.includes("Expected Text") ? "loaded" : "waiting"'
  });
  if (result.result?.result?.value === 'loaded') break;
}
```

## 4. EXPORTING AUTH FOR PLAYWRIGHT-CLI

When playwright-cli needs auth but state-load fails:

### 4a. Navigate Kiro Chrome to Copilot Studio first

```javascript
await send('Page.navigate', {url: 'https://copilotstudio.microsoft.com'});
await sleep(10000);
```

### 4b. Extract cookies + localStorage

```javascript
const cookiesResp = await send('Network.getAllCookies');
const cookies = cookiesResp.result.cookies;

const lsResp = await send('Runtime.evaluate', {
  expression: 'JSON.stringify(Object.entries(localStorage))'
});
const lsEntries = JSON.parse(lsResp.result.result.value || '[]');
```

### 4c. Convert to Playwright storageState format

```javascript
const pwCookies = cookies.map(c => ({
  name: c.name,
  value: c.value,
  domain: c.domain,
  path: c.path || '/',
  expires: c.expires || -1,
  httpOnly: c.httpOnly || false,
  secure: c.secure || false,
  sameSite: c.sameSite || 'Lax'
}));

const storageState = {
  cookies: pwCookies,
  origins: [{
    origin: 'https://copilotstudio.microsoft.com',
    localStorage: lsEntries.map(([name, value]) => ({name, value}))
  }]
};
```

Save as JSON and load with `npx playwright-cli --session <name> state-load <path>`.

**Critical**: The localStorage MUST come from a page that was navigated to Copilot Studio (not `about:blank`). MSAL token cache lives in `copilotstudio.microsoft.com` localStorage.

## 5. EDITING AGENT INSTRUCTIONS

The Instructions section on the Overview page is a `div[contenteditable]` inside a `[role=textbox]`. It starts as `contentEditable=false`.

### 5a. Make it editable

Click the Edit button next to the Instructions heading:
```javascript
// Find the Edit button
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        if (btn.textContent.trim() === 'Edit') {
          btn.click();
          return 'clicked';
        }
      }
      return 'not found';
    })()
  `
});
```

### 5b. Verify editable state

```javascript
// Should return contentEditable=true
await send('Runtime.evaluate', {
  expression: 'document.querySelector("[role=textbox]")?.contentEditable'
});
```

### 5c. Replace content

1. Focus editor
2. Select all (`document.execCommand('selectAll')`)
3. Copy new text to clipboard (via PowerShell `Set-Clipboard`)
4. Press Ctrl+V

### 5d. Save

Press Ctrl+S. The page should show no error toasts. Verify by checking the Publish button state — it becomes enabled when unsaved changes exist, and disabled after save.

## 6. EXTRACTING TOPIC YAML

Each topic has a direct URL:
```
https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/adaptive/<componentId>
```

Find component IDs by navigating to topics grid and extracting hrefs from topic name links.

To extract YAML content:
1. Navigate to topic URL
2. Wait for topic canvas to load (~15s)
3. Click "More" → "Open code editor" (the menu item text is "Open code editor", not "Code editor")
4. Wait for Monaco editor (~8s)
5. Extract content from `.monaco-editor .view-line` elements

## 7. PUBLISHING VIA CDP

1. Make changes (instructions, knowledge, topics)
2. The Publish button becomes enabled (no longer `[disabled]`)
3. Click Publish → confirm dialog appears → click Publish in dialog
4. Wait 30-60s for publish to complete
5. Verify: check "Published <date>" changes to today's date

## 9. EDITING TOPIC TRIGGER DESCRIPTIONS

The trigger description in a topic editor ("Describe what the topic does") is NOT the same as the Instructions editor. It renders as plain text but clicking the description text itself opens an inline textarea.

### 9a. Open trigger description for editing

Click the DESCRIPTION TEXT directly (not the "Edit" button):

```javascript
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node;
      while (node = walker.nextNode()) {
        if (node.textContent.includes('ONLY when the user uploads')) {
          node.parentElement.click();
          return 'clicked description text';
        }
      }
      return 'not found';
    })()
  `
});
await sleep(3000);
```

### 9b. Update the description textarea

After clicking, a `<textarea>` appears with the current description value. Update it using the native setter:

```javascript
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const tas = document.querySelectorAll('textarea');
      for (const ta of tas) {
        if (ta.value && ta.value.includes('upload')) {
          const setter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
          ).set;
          setter.call(ta, 'Your new trigger description here.');
          ta.dispatchEvent(new Event('input', {bubbles: true}));
          ta.dispatchEvent(new Event('change', {bubbles: true}));
          ta.dispatchEvent(new Event('blur', {bubbles: true}));
          return 'updated';
        }
      }
      return 'not found';
    })()
  `
});
```

### 9c. Save trigger description

Click the "Save" button in the topic toolbar (Ctrl+S may not persist for trigger edits):

```javascript
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const btns = document.querySelectorAll('button');
      for (const btn of btns) {
        if (btn.textContent.trim() === 'Save') {
          btn.click();
          return 'clicked Save';
        }
      }
      return 'no Save button';
    })()
  `
});
await sleep(5000);
```

Verify by re-navigating to the topic and checking the description text.

## 10. TOGGLING TOPIC ON/OFF STATE

Topic enabled/disabled state uses `input[type=checkbox][role=switch]` elements in the topics grid rows. These do NOT toggle reliably with `.click()` alone.

### 10a. Find the toggle for a specific topic

```javascript
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const rows = document.querySelectorAll('[role=row]');
      for (const row of rows) {
        if (row.textContent.includes('Upload Instructions')) {
          const sw = row.querySelector('input[type=checkbox][role=switch]');
          if (sw) {
            // Return switch properties for verification
            return JSON.stringify({
              ariaLabel: sw.getAttribute('aria-label'),
              checked: sw.checked,
              id: sw.id?.substring(0, 30)
            });
          }
        }
      }
      return 'not found';
    })()
  `
});
```

### 10b. Toggle ON

Set properties directly and dispatch events:

```javascript
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const sw = document.querySelector('input[role=switch]');
      if (!sw) return 'not found';
      sw.checked = true;
      sw.setAttribute('aria-checked', 'true');
      sw.dispatchEvent(new Event('change', {bubbles: true}));
      sw.dispatchEvent(new Event('click', {bubbles: true}));
      return 'toggled ON';
    })()
  `
});
await sleep(5000);
```

### 10c. Verify state

```javascript
// Check if the row text now contains 'On' (not 'Off')
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const rows = document.querySelectorAll('[role=row]');
      for (const row of rows) {
        if (row.textContent.includes('Upload Instructions')) {
          return row.textContent.includes('On') ? 'ON' : 'OFF';
        }
      }
      return 'not found';
    })()
  `
});
```

**Important**: The simplified `sw.click()` often does NOT work for these toggle switches. Always set `.checked` + dispatch events.

## 11. AGENT DISCOVERY FROM AGENTS LIST

The Copilot Studio `/bots` page shows skeleton loaders for 20-40 seconds before rendering the agents list. Patience is required.

### 11a. Navigate and wait

```javascript
await send('Page.navigate', {
  url: 'https://copilotstudio.microsoft.com/environments/<envId>/bots'
});
// Wait up to 40 seconds, polling for content
for (let i = 0; i < 15; i++) {
  await sleep(3000);
  const r = await send('Runtime.evaluate', {
    expression: 'document.body?.innerText?.includes("My agents") ? "loaded" : "waiting"'
  });
  if (r.result?.result?.value === 'loaded') break;
}
```

### 11b. Extract bot IDs

Agent links use `.ms-Link` class with empty `href` (JS-driven navigation). To get the bot ID, click the agent name link and capture the resulting URL:

```javascript
// Click the agent name
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const links = document.querySelectorAll('a.ms-Link');
      for (const link of links) {
        if (link.textContent.trim() === 'Therapy Documentation Audit Agent') {
          link.dispatchEvent(new MouseEvent('click', {
            bubbles: true, cancelable: true, view: window
          }));
          return 'clicked';
        }
      }
      return 'not found';
    })()
  `
});
await sleep(8000);

// Read resulting URL
const urlResult = await send('Runtime.evaluate', {
  expression: 'window.location.href'
});
// URL format: .../bots/<botId>/overview
```

### 11c. Switch environments

Click the environment selector in the top bar, then click the target environment name in the side panel:

```javascript
// Click current environment
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const all = document.querySelectorAll('span, button');
      for (const el of all) {
        if (el.textContent.trim() === 'Therapy AI Agents Dev') {
          el.click(); return 'opened env selector';
        }
      }
    })()
  `
});
await sleep(3000);

// Click target environment in side panel
await send('Runtime.evaluate', {
  expression: `
    (() => {
      const all = document.querySelectorAll('span, div, button, [role=option]');
      for (const el of all) {
        if (el.textContent.trim() === 'Ensign Services (default)') {
          el.click(); return 'switched environment';
        }
      }
    })()
  `
});
await sleep(8000);
```

Known environments for this tenant (ensignservices.net):
- `Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f` — Ensign Services (default)
- `a944fdf0-0d2e-e14d-8a73-0f5ffae23315` — Therapy AI Agents Dev

When CDP is too slow, `pac` CLI can provide quick info:

```bash
# List all agents in environment
pac copilot list

# Export solution (metadata only — no bot source files)
pac solution clone --name "SolutionName" --outputDirectory ./cloned

# Verify publish state
pac copilot list | grep "Agent Name"
```

Known pac bugs (v2.7.4):
- `pac copilot extract-template` crashes on agents with knowledge sources (`System.ArgumentException` in `AddKSComponent`)
- `pac copilot status --bot-id` fails with `componentstate_Property` error
- Use `pac copilot list` for publish verification instead
