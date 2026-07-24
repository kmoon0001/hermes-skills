# Playwright connectOverCDP + Code Editor Workflow

## Overview

The Copilot Studio visual canvas editor has a React Save button that stays
disabled after programmatic content changes (CDP Input.insertText, fill, type,
etc.). The **code editor** (More → Open code editor) opens a Monaco editor that
properly tracks edits, making Save work. Combined with Playwright's
`connectOverCDP()`, this provides reliable programmatic topic editing.

## Prerequisites

- Chrome running with `--remote-debugging-port=9223`
- `playwright-core` npm package installed globally: `npm install -g playwright-core`
- Copilot Studio agent open in a Chrome tab

## Step-by-Step

### 1. Connect to Chrome via CDP

```javascript
const { chromium } = require('playwright-core');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
const contexts = browser.contexts();

// Find the right page by bot ID in the URL
let page;
for (const ctx of contexts) {
  for (const p of ctx.pages()) {
    if (p.url().includes('<botId>')) {
      page = p;
      break;
    }
  }
}
```

### 2. Navigate to Topic and Open Code Editor

```javascript
// Click Topics in sidebar
await page.locator('button:has-text("Topics")').first().click();
await page.waitForTimeout(5000);

// Click the topic name
await page.locator('text=My Topic Name').first().click();
await page.waitForTimeout(5000);

// Open code editor via More menu
await page.locator('button:has-text("More")').first().click();
await page.waitForTimeout(1000);
await page.locator('text=Open code editor').first().click();
await page.waitForTimeout(5000);
```

### 3. Edit the YAML

```javascript
// Click into Monaco editor to focus it
const monacoEditor = page.locator('.monaco-editor').first();
await monacoEditor.click();
await page.waitForTimeout(1000);

// Select all (Ctrl+A)
await page.keyboard.press('Control+a');
await page.waitForTimeout(500);

// Write new YAML to clipboard, then paste
const newYaml = `kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  ...`;

await page.evaluate((text) => {
  navigator.clipboard.writeText(text);
}, newYaml);
await page.waitForTimeout(500);
await page.keyboard.press('Control+v');
await page.waitForTimeout(2000);
```

### 4. Save

```javascript
const saveBtn = page.locator('button:has-text("Save")').first();
const saveEnabled = await saveBtn.isEnabled();
console.log('Save enabled:', saveEnabled);

if (saveEnabled) {
  await saveBtn.click();
  console.log('Saved!');
  await page.waitForTimeout(8000); // Wait for "Saving topic..."
}
```

### 5. Handle Dark Overlay (Multi-User Conflict)

If `ms-Overlay--dark` blocks Save after editing:

```javascript
await page.keyboard.press('Escape');
await page.waitForTimeout(1000);
await saveBtn.click({force: true}).catch(() => {});
await page.waitForTimeout(5000);
```

## Key Findings

1. **Code editor Save works** — Monaco properly detects edits, enabling the Save
   button. The visual canvas does NOT (React dirty-state tracking bug).

2. **Clipboard paste is reliable** — `navigator.clipboard.writeText()` + Ctrl+V
   properly inserts multi-line YAML into Monaco.

3. **Ctrl+A selects all code** — After clicking the Monaco editor area, Ctrl+A
   selects all YAML content for replacement.

4. **Don't use `fill()` on Monaco** — Playwright's `fill()` targets the
   hidden textarea behind Monaco, not the visible code. Use clipboard paste instead.

5. **Don't use `Input.insertText`** — While this works for the Instructions
   contentEditable, it doesn't properly track edits in Monaco. Use clipboard paste.

## Power Fx Variable Syntax in Topic YAML

When replacing hardcoded record_ids with variable references:

- **CORRECT:** `Topic.varRecord` (Power Fx syntax, no `$`)
- **WRONG:** `$Topic.varRecord` (causes PowerFxError: "Unexpected character")
- **In SendMessage activity:** Use `{Topic.varRecord}` for interpolation

Per Microsoft Learn: topic variables use `Topic.` prefix, global use `Global.`,
system use `System.`, environment use `Environment.` — never `$`.

## Complete Example: Fix Fallback Topic

```javascript
const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  
  for (const ctx of browser.contexts()) {
    for (const page of ctx.pages()) {
      if (page.url().includes('73b45e98')) {  // Bot ID
        // Navigate to Fallback topic
        await page.goto('https://copilotstudio.microsoft.com/.../adaptive/<topicId>');
        await page.waitForTimeout(8000);
        
        // Open code editor
        const moreBtn = page.locator('button:has-text("More")').first();
        await moreBtn.click();
        await page.waitForTimeout(1000);
        await page.locator('text=Open code editor').first().click();
        await page.waitForTimeout(5000);
        
        // Edit YAML
        await page.locator('.monaco-editor').first().click();
        await page.waitForTimeout(1000);
        await page.keyboard.press('Control+a');
        await page.waitForTimeout(500);
        
        const newYaml = `kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: ConditionGroup
      id: conditionGroup_LktzXw
      conditions:
        - id: conditionItem_tlGIVo
          condition: =System.FallbackCount < 3
          actions:
            - kind: SendActivity
              id: sendMessage_QZreqo
              activity: I can help with OT documentation compliance, including evaluation audits, daily note reviews, progress note checks, recertification analysis, discharge summaries, and denial risk assessment. Could you provide more detail about what you'd like me to evaluate?
            - kind: EndDialog
              id: end_fallback_retry
              clearTopicQueue: true
      elseActions:
        - kind: BeginDialog
          id: 5aXj5M
          dialog: copilots_header_8c921.topic.Escalate`;
        
        await page.evaluate((text) => navigator.clipboard.writeText(text), newYaml);
        await page.waitForTimeout(500);
        await page.keyboard.press('Control+v');
        await page.waitForTimeout(2000);
        
        // Save
        const saveBtn = page.locator('button:has-text("Save")').first();
        if (await saveBtn.isEnabled()) {
          await saveBtn.click();
          await page.waitForTimeout(8000);
          console.log('Fallback topic saved!');
        }
        
        break;
      }
    }
  }
  
  await browser.close();
})();
```

## Session Evidence

- Jun 10, 2026: Fallback topic edited and saved successfully using this workflow.
  Save button was enabled after clipboard paste into Monaco code editor.
- Jun 10, 2026: Progress Missing Elements topic edited but had PowerFxError
  from `$Topic.varRecord` — corrected to `Topic.varRecord`.
