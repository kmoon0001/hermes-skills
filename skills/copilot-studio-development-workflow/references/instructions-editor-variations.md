# Instructions Editor Type Variations

## The Problem

The Copilot Studio instructions editor on the Overview page renders differently
depending on environment/UI version:

- **Default / Dev environments**: `div[contenteditable=true][role=textbox]`
- **Therapy AI Agents Prod (observed Jul 2026)**: `<textarea>` after clicking Edit

This matters because the injection strategy differs:

| Editor Type | Reliable Write Method | Save Method |
|-------------|----------------------|-------------|
| textarea | CDP `Input.insertText` | Ctrl+S |
| contenteditable div | CDP `Input.insertText` only | Ctrl+S |

Playwright's `fill()` / `type()` and CDP clipboard paste fail on BOTH types.

## Detection

After clicking the Instructions Edit button:

```javascript
const editorType = await page.evaluate(() => {
  const ta = document.querySelector('textarea');
  if (ta && ta.offsetParent !== null && ta.offsetWidth > 10) {
    return 'textarea';
  }
  const ed = document.querySelector('div[contenteditable="true"]');
  if (ed) return 'contenteditable';
  return 'unknown';
});
```

## Injection Flow

1. Click Edit button (second "Edit" button on Overview page, typically at y ~780)
2. Wait 2-3s for editor to appear
3. Detect editor type
4. **Ctrl+A** to select all existing content
5. **Delete** to clear
6. CDP `Input.insertText` with the fixed instructions
7. Wait 1s
8. **Ctrl+S** to save
9. Wait 3s for save to complete
10. Escape to close
