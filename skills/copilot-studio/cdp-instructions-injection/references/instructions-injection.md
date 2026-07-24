# Instructions Injection via CDP

Inject agent instructions into the contenteditable div on the Overview page.

## Proven Pattern (June 19, 2026 — QM Coach V2)

```javascript
const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
    const b = await chromium.connectOverCDP('http://127.0.0.1:9223');
    const ctx = b.contexts()[0];
    const p = ctx.pages()[0];
    const client = await p.context().newCDPSession(p);
    
    // Step 1: Navigate to Overview, wait for SPA
    await p.goto(`${BASE}/overview`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    for (let i = 0; i < 20; i++) {
        await sleep(3000);
        const loaded = await p.evaluate(() => {
            return Array.from(document.querySelectorAll('button'))
                .filter(b => b.textContent?.trim() === 'Edit' && b.getBoundingClientRect().width > 0).length;
        });
        if (loaded >= 2) break;
    }
    
    // Step 2: Close test pane
    await p.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Test');
        if (btn && btn.getBoundingClientRect().width > 0) btn.click();
    });
    await sleep(2000);
    
    // Step 3: CDP click on Instructions Edit (index 1)
    const editBtn = await p.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent?.trim() === 'Edit' && b.getBoundingClientRect().width > 0);
        if (btns.length >= 2) {
            const r = btns[1].getBoundingClientRect();
            return { x: r.x + r.width/2, y: r.y + r.height/2 };
        }
        return null;
    });
    
    await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: editBtn.x, y: editBtn.y, button: 'left', clickCount: 1 });
    await sleep(50);
    await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: editBtn.x, y: editBtn.y, button: 'left', clickCount: 1 });
    await sleep(5000);
    
    // Step 4: Force-set contenteditable
    await p.evaluate(() => {
        const ed = document.querySelector('div[role="textbox"]');
        if (ed) {
            ed.setAttribute('contenteditable', 'true');
            ed.removeAttribute('aria-readonly');
            ed.focus();
        }
    });
    await sleep(1000);
    
    // Step 5: Focus editor via CDP click
    const editorBox = await p.evaluate(() => {
        const ed = document.querySelector('div[role="textbox"]');
        const r = ed.getBoundingClientRect();
        return { x: r.x + r.width/2, y: r.y + r.height/2 };
    });
    await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: editorBox.x, y: editorBox.y, button: 'left', clickCount: 1 });
    await sleep(50);
    await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: editorBox.x, y: editorBox.y, button: 'left', clickCount: 1 });
    await sleep(1000);
    
    // Step 6: Select all + insert
    await p.keyboard.press('Control+A');
    await sleep(500);
    
    const newInstr = fs.readFileSync('instructions.txt', 'utf8').replace(/\r\n/g, '\n');
    await client.send('Input.insertText', { text: newInstr });
    await sleep(3000);
    
    // Step 7: Save
    await p.keyboard.press('Space');
    await sleep(100);
    await p.keyboard.press('Backspace');
    await sleep(2000);
    
    const saveBtn = await p.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Save' && b.getBoundingClientRect().width > 0);
        if (btn) { const r = btn.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2 }; }
        return null;
    });
    
    if (saveBtn) {
        await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: saveBtn.x, y: saveBtn.y, button: 'left', clickCount: 1 });
        await sleep(50);
        await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: saveBtn.x, y: saveBtn.y, button: 'left', clickCount: 1 });
        await sleep(8000);
    }
    
    // Step 8: Publish
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
})();
```

## Key Details

- **Edit button index**: Index 0 = Description, Index 1 = Instructions, Index 2+ = other
- **Editor element**: `div[role="textbox"]` (NOT textarea)
- **Force-set contenteditable**: Required because Playwright mouse.click doesn't activate the Edit button
- **CDP Input.insertText**: Works for contenteditable divs (NOT for Monaco editors)
- **Save tracker**: Space + Backspace to wake the save tracker

## Pitfalls

- Chrome must be on port 9223 with CDP enabled
- SPA needs 12-60 seconds to load (poll for Edit buttons)
- Test pane overlay can block clicks — close it first
- If injection fails, the contenteditable div may need manual activation
- Content length may differ from file length due to contenteditable normalization
