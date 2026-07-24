# CDP Injection Failure on Some Agents

**Date:** June 2026
**Agent:** SimpleLTC QM Coach V2 (dev environment a944fdf0)
**Symptom:** Force-setting contenteditable=true + insertText() does NOT update Lexical state. Content remains unchanged.

## What happened

1. Editor found: `div[role="textbox"]` with `contenteditable=false`, 4842 chars
2. Force-set: `ed.setAttribute('contenteditable', 'true'); ed.removeAttribute('aria-readonly'); ed.focus();`
3. CDP click on editor center to focus
4. `Ctrl+A` to select all
5. `page.keyboard.insertText(newContent)` — 5596 chars
6. **Verify returned: len=4842, hasMDS=false** — content UNCHANGED
7. Clipboard paste (`navigator.clipboard.writeText` + `Ctrl+V`) also failed
8. Same result: content unchanged

## Root cause

The Lexical editor's internal state is not connected to the DOM when contenteditable is force-set. The editor needs to be activated through its own Edit button mechanism, not DOM manipulation.

## Workaround

Fall back to **manual paste via Notepad** immediately. Do not retry programmatic approaches — they will all fail on this agent.

## Key difference from production agents

Production agents (PT, SLP, TDA) work with CDP injection. Dev environment agents may have a different Lexical editor version or configuration that resists programmatic editing.

## Notepad formatting preference

When preparing instructions for manual paste, user wants:
- NO markdown headers (#) — cluttered in Notepad
- Section names as plain text (CONTENT SAFETY, ROLE, SCOPE)
- Blank lines between sections
- Each numbered instruction as its own paragraph
- Clean, readable layout
