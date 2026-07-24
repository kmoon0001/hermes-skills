# CDP Input.dispatchMouseEvent Pattern for Copilot Studio

## Problem
Playwright's `page.mouse.click(x, y)` fails to activate React/Lexical controlled UI components in Copilot Studio:
- Instructions Edit button click doesn't enable `contenteditable`
- Save button clicks don't register
- Evaluate button clicks don't trigger dialogs
- Test pane textarea clicks don't focus

## Solution: Raw CDP Mouse Events
Use Chrome DevTools Protocol `Input.dispatchMouseEvent` via `page.context().newCDPSession(page)`.

```javascript
const client = await page.context().newCDPSession(page);

// Click any element at coordinates
async function cdpClick(client, x, y) {
    await client.send('Input.dispatchMouseEvent', {
        type: 'mousePressed', x, y, button: 'left', clickCount: 1
    });
    await sleep(50);
    await client.send('Input.dispatchMouseEvent', {
        type: 'mouseReleased', x, y, button: 'left', clickCount: 1
    });
}
```

## Proven Workflow: Edit Instructions via CDP

```javascript
// 1. Navigate to agent overview, wait 15-20s for SPA hydration
// 2. Dismiss overlays
await p.evaluate(() => {
    Array.from(document.querySelectorAll('button')).forEach(b => {
        const t = b.textContent?.trim()?.toLowerCase();
        if (['skip','got it','dismiss','close','ok','next','done'].includes(t) && b.getBoundingClientRect().width > 0) b.click();
    });
});
await p.keyboard.press('Escape');
await sleep(2000);

// 3. Find Edit buttons
const edits = await p.evaluate(() => {
    return Array.from(document.querySelectorAll('button'))
        .filter(b => b.textContent?.trim() === 'Edit' && b.getBoundingClientRect().width > 0)
        .map((b, i) => {
            const r = b.getBoundingClientRect();
            return { i, x: r.x + r.width/2, y: r.y + r.height/2 };
        });
});

// 4. CDP click on Instructions Edit (2nd button, index 1)
const target = edits[1];
await cdpClick(client, target.x, target.y);
await sleep(5000);

// 5. Verify editor activated
const state = await p.evaluate(() => {
    const ed = document.querySelector('div[role="textbox"]');
    return { ce: ed.contentEditable, readonly: ed.getAttribute('aria-readonly') };
});
// state.ce should be 'true', state.readonly should be null

// 6. Focus editor, select all, insert new text
const editorBox = await p.evaluate(() => {
    const ed = document.querySelector('div[role="textbox"]');
    const r = ed.getBoundingClientRect();
    return { x: r.x + r.width/2, y: r.y + r.height/2 };
});
await cdpClick(client, editorBox.x, editorBox.y);
await sleep(1000);
await p.keyboard.press('Control+A');
await sleep(500);
await p.keyboard.insertText(newInstructions);
await sleep(3000);

// 7. Wake save tracker
await p.keyboard.press('Space');
await sleep(100);
await p.keyboard.press('Backspace');
await sleep(2000);

// 8. CDP click Save button
const saveBtn = await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Save' && b.getBoundingClientRect().width > 0);
    if (btn) { const r = btn.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2, disabled: btn.disabled }; }
    return null;
});
if (saveBtn && !saveBtn.disabled) {
    await cdpClick(client, saveBtn.x, saveBtn.y);
    await sleep(8000);
}

// 9. Cancel edit mode, then Publish
await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Cancel');
    if (btn) btn.click();
});
await sleep(3000);

await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Publish');
    if (btn) btn.click();
});
await sleep(15000);
```

## scrollIntoView for Off-Screen Buttons

Buttons at y>1000 (sticky footers, bottom-of-page actions) don't respond to clicks even with CDP. Fix:

```javascript
// 1. scrollIntoView
await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate');
    if (btn) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
});
await sleep(1000);

// 2. Re-query coordinates (they changed after scroll)
const btn = await p.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate' && !b.disabled);
    if (b) { const r = b.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2 }; }
    return null;
});

// 3. CDP click
if (btn) await cdpClick(client, btn.x, btn.y);
```

## Evaluation Trigger Pattern (proven June 18, 2026)

```javascript
// 1. Navigate to eval page, wait 15s
// 2. Find and click test set card (scrollIntoView not needed — cards are at top)
const card = await p.evaluate(() => {
    const all = document.querySelectorAll('*');
    for (const el of all) {
        const t = el.textContent || '';
        const r = el.getBoundingClientRect();
        if (t.includes('20 test cases') && r.width > 200 && r.width < 600 && r.height > 30 && r.height < 200) {
            return { x: r.x + r.width/2, y: r.y + r.height/2 };
        }
    }
    return null;
});
await cdpClick(client, card.x, card.y);
await sleep(8000);

// 3. scrollIntoView + click Evaluate button
await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate');
    if (btn) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
});
await sleep(1000);
const evalBtn = await p.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate' && !b.disabled);
    if (b) { const r = b.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2 }; }
    return null;
});
await cdpClick(client, evalBtn.x, evalBtn.y);
await sleep(10000);

// 4. Dialog appears with "Run" button — click it
const runBtn = await p.evaluate(() => {
    const dialog = document.querySelector('[role=dialog]');
    const container = dialog || document;
    const btn = Array.from(container.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Run');
    if (btn) { const r = btn.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2 }; }
    return null;
});
if (runBtn) await cdpClick(client, runBtn.x, runBtn.y);
```

## When to Use Each Click Method

| Method | Works For | Doesn't Work For |
|--------|-----------|-----------------|
| `page.mouse.click` | Simple buttons, links, non-React elements | Edit buttons, Lexical editors, React controlled inputs |
| `page.click(selector)` | Standard DOM elements | React portals, shadow DOM, complex SPA components |
| CDP `Input.dispatchMouseEvent` | Everything in Copilot Studio | Nothing (always works) |
| `element.scrollIntoView()` + CDP | Buttons at y>1000 (sticky footers) | — |

**Default to CDP `Input.dispatchMouseEvent` for ALL Copilot Studio UI interactions.** It's the only method that works reliably across all components.
