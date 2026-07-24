# Monaco Editor — Reading YAML via Selection Trick

## Problem

The Monaco code editor in Copilot Studio has a React focus trap that blocks programmatic `editor.getValue()` calls from CDP. Normal `page.evaluate` to read the editor content returns empty.

## Solution: Triple-Selection Trick

1. Click OUTSIDE the editor (any non-editor area of the page)
2. Press `Ctrl+A` — selects the page content (not the editor)
3. Click INSIDE the `.monaco-editor` area — re-focuses the editor
4. Press `Ctrl+A` again — selects ALL editor text

Now the editor text is selected and can be read via `page.evaluate(() => window.getSelection().toString())` or copied to clipboard.

## Why This Works

The first Ctrl+A operates on the page level (document body). Clicking into Monaco triggers React's focus handler which registers the editor as active. The second Ctrl+A delegates to Monaco's built-in select-all command which reads the editor's internal model.

## Alternative: Space+Backspace Wake

When the editor's Save button is disabled after YAML injection, type a space character then press Backspace. This triggers Monaco's change tracker which enables the Save button. Does NOT affect content since the space is immediately undone.
