# Monaco Code Editor Save Persistence

## The problem
Clipboard paste into the Copilot Studio Monaco code editor does NOT trigger React dirty-state. The Save button stays `disabled: true` at x:1128, y:138.

## Why clipboard paste fails
Monaco's change detection relies on proper DOM input events. `navigator.clipboard.writeText()` + `Ctrl+V` inserts content visually but doesn't fire the event chain that enables Save. `page.keyboard.type()` + `Backspace` doesn't work either.

## Working workarounds

### Option 1: Ctrl+S (Monaco's native save)
After pasting via clipboard (`Ctrl+A` → `Ctrl+V`), press `Ctrl+S`. This is Monaco's own keyboard shortcut which DOES trigger the underlying model change detection. Then find and click the Save button or rely on the platform to detect the update.

### Option 2: Type then delete a character
After paste, type one character (space) then delete it (backspace). This triggers Monaco's change handler.

## Verification
Always verify after paste:
```javascript
// Read view-line content to confirm
const lines = await page.locator('.view-line').allTextContents();
const yaml = lines.join('\n');
console.log('Has SearchAndSummarize:', yaml.includes('SearchAndSummarizeContent'));
```

Then check the Save button state:
```javascript
const saveBtn = await page.evaluate(() => {
  const btns = [...document.querySelectorAll('button')]
    .filter(b => b.offsetParent && (b.textContent || '').trim() === 'Save');
  return btns.length ? {
    x: btns[0].getBoundingClientRect().x + btns[0].getBoundingClientRect().width / 2,
    y: btns[0].getBoundingClientRect().y + btns[0].getBoundingClientRect().height / 2,
    disabled: !!btns[0].disabled
  } : null;
});
```

## Publishing
After saving, click the agent-level **Publish** button (x:1521, y:78). Check the Overview page shows "Published <date>" to confirm.

## See also
- `references/cdp-code-editor-workflow.md` — full code editor automation pattern
- `references/cb-topic-yaml.md` — CB topic YAML structure
