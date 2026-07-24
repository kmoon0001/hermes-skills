# Monaco Code Editor: React Dirty-State Trigger for Save

## Problem
CDP/Playwright text injection into Copilot Studio's Monaco code editor never triggers the Save button. The text is injected into the editor model but React's controlled component doesn't detect the change. The Save button stays disabled.

## Root Cause
Copilot Studio uses a React controlled component wrapping Monaco. React's onChange handler only fires on REAL user interactions — not programmatic DOM changes. Any of the following fail:
- `textarea.value` setter + dispatchEvent(input)
- `monaco.editor.getModels()[0].setValue(yaml)`
- `page.keyboard.press('End')` + Space + Backspace (keyboard events hit wrong DOM layer)
- `Input.insertText` via CDP (text appears but React doesn't notice)

## Solution: Click a `.view-line` Element First

The ONLY reliable trigger is: click a rendered view-line in Monaco, THEN type a character and delete it.

```javascript
// 1. Inject YAML into textarea
await page.evaluate((yaml) => {
  const ta = document.querySelector('textarea');
  if (ta) {
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(ta, yaml);
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  }
}, newYaml);
await sleep(500);

// 2. Click a view-line element in Monaco to give it proper React focus
await page.evaluate(() => {
  const vl = document.querySelector('.view-line');
  if (vl) vl.click();
});
await sleep(500);

// 3. Type space + backspace — this triggers React's onChange
await page.keyboard.type(' ');
await sleep(200);
await page.keyboard.press('Backspace');
await sleep(500);

// 4. Now Save button should be enabled
```

## What Does NOT Work
- Clicking `.monaco-editor` surface — no React focus
- Focusing `textarea.inputarea` — wrong element
- `page.keyboard.press('x')` without first clicking view-line — event goes to wrong layer
- Triple-clicking Monaco — focus is inconsistent
- `dispatchEvent(new MouseEvent('click', ...))` on Monaco — doesn't give React focus

## Batch Processing Pitfall
When processing multiple topics in sequence, page navigation between topics causes state leakage. Each topic should be processed in its own Playwright session OR with explicit cleanup (Escape to close any open dialogs, extra wait times after navigation).

## Verification
Always verify by re-reading Monaco DOM lines after save:
```javascript
const verify = await page.evaluate(() => 
  Array.from(document.querySelectorAll('.monaco-editor .view-lines .view-line'))
    .map(l => l.textContent).join('\n'));
// Normalize non-breaking spaces (\u00a0) to regular spaces
const normalized = verify.replace(/\u00a0/g, ' ');
```

⚠️ Non-breaking spaces in Monaco will fool simple `indexOf` checks. Use regex: `/8[^a-zA-Z0-9]*0[^a-zA-Z0-9]*0/i` or normalize first.
