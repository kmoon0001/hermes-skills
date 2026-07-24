# Monaco Code Editor — Read & Write via CDP/Playwright

## Reading YAML

Standard approach (`.view-lines.textContent`):
```javascript
const yaml = await page.evaluate(() => document.querySelector('.view-lines')?.textContent || '');
```

But `view-lines` may not render if the editor hasn't focused. Use the **double Select All** trick:

1. Click outside the editor (background, another element)
2. Ctrl+A (selects page content)
3. Click inside `.monaco-editor`
4. Ctrl+A again (now selects editor text)

```javascript
await page.keyboard.press('Control+A');
await page.waitForTimeout(200);
// Click the editor
const editor = await page.evaluate(() => {
  const el = document.querySelector('.monaco-editor');
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {x: r.x + r.width/2, y: r.y + r.height/2};
});
if (editor) {
  await cdp.send('Input.dispatchMouseEvent', {type:'mousePressed', x:editor.x, y:editor.y, button:'left', clickCount:1});
  await cdp.send('Input.dispatchMouseEvent', {type:'mouseReleased', x:editor.x, y:editor.y, button:'left', clickCount:1});
  await page.waitForTimeout(500);
  await page.keyboard.press('Control+A');
}
```

## Writing YAML

```javascript
// Focus the Monaco editor
await page.keyboard.press('Control+A');
// Click inside the editor
coord = await page.evaluate(() => {
  const el = document.querySelector('.monaco-editor');
  const r = el.getBoundingClientRect();
  return {x: r.x + r.width/2, y: r.y + r.height/2};
});
await cdp.send('Input.dispatchMouseEvent', {type:'mousePressed', x:coord.x, y:coord.y, button:'left', clickCount:1});
await page.waitForTimeout(300);

// Clear and paste via clipboard
await page.keyboard.press('Control+A');
await page.waitForTimeout(200);
await page.evaluate((yaml) => navigator.clipboard.writeText(yaml), YAML_CONTENT);
await page.waitForTimeout(500);
await page.keyboard.press('Control+V');
await page.waitForTimeout(1000);
```

## Saving — The Space+Backspace Wake Trick

Monaco's save tracker stays `disabled: true` even after changing content via clipboard. To wake it:

```javascript
// Click the editor bottom-right margin
const bottomRight = await page.evaluate(() => {
  const el = document.querySelector('.monaco-editor');
  const r = el.getBoundingClientRect();
  return {x: r.x + r.width - 20, y: r.y + r.height - 10};
});
await cdp.send('Input.dispatchMouseEvent', {type:'mousePressed', x:bottomRight.x, y:bottomRight.y, button:'left', clickCount:1});
await cdp.send('Input.dispatchMouseEvent', {type:'mouseReleased', x:bottomRight.x, y:bottomRight.y, button:'left', clickCount:1});
await page.waitForTimeout(300);

// Type space + Backspace — triggers save tracker
await page.keyboard.type(' ');
await page.waitForTimeout(100);
await page.keyboard.press('Backspace');
await page.waitForTimeout(500);

// Now Save button is enabled — click it
const saveCoord = await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    if (b.textContent?.trim() === 'Save' && b.getBoundingClientRect().width > 0) {
      const r = b.getBoundingClientRect(); return {x: r.x+r.width/2, y: r.y+r.height/2};
    }
  }
  return null;
});
```

## CB Editor Popup

Opening the CB code editor (More → Open code editor) triggers another "What's New" popup inside the editor panel. Dismiss with Escape × 3 before reading or writing. See `references/popup-dismissal.md`.
