# Paste Wall Investigation — Copilot Studio Instructions Editor

Comprehensive record of every approach attempted to programmatically set text in the Copilot Studio Instructions editor (React `contentEditable` div). Maintain this as the definitive reference — when an agent proposes "have you tried X?", point here.

## The React Boundary

The Instructions editor is a `<div contenteditable="true" role="textbox">` controlled by React. React maintains its own virtual DOM snapshot of the editor state. Any direct DOM mutation that doesn't go through React's event pipeline gets reverted on the next reconciliation cycle.

## Approaches Tried

### FAILED — Direct DOM setters

| Approach | Result | Detail |
|----------|--------|--------|
| `innerText = text` | Ignores assignment | React re-renders from virtual DOM |
| `textContent = text` | Ignores assignment | Same mechanism |
| `innerHTML = "<p>text</p>"` | Ignores assignment | With proper `<p>` tags per CS editor structure |

### FAILED — execCommand

| Approach | Result | Detail |
|----------|--------|--------|
| `execCommand('insertText', false, shortText)` (22 chars) | **WORKS** | Short text passes React reconciliation |
| `execCommand('insertText', false, longText)` (3000 chars) | Silently fails | `ok=true` returned but content stays at prior length |
| `execCommand('insertHTML', false, html)` | Ignores | Same as insertText |

**Key finding:** execCommand reports success for all lengths but React intercepts insertions above ~100 characters. This is a false positive — do NOT trust the return value.

### FAILED — Playwright automation

| Approach | Result | Detail |
|----------|--------|--------|
| `fill` command | Single-line only | Shell eats newlines; with escaped newlines, only first line inserted |
| `type` command | Same | No better than fill |
| `press Control+v` after clipboard set | Clipboard set fails | `navigator.clipboard.writeText()` via eval silently fails for long text |

### FAILED — CDP-level approaches

| Approach | Result | Detail |
|----------|--------|--------|
| `Runtime.evaluate` with any DOM setter | Same as direct DOM | Goes through same React boundary |
| `Input.insertText` | Same as execCommand | React intercepts |
| `Input.dispatchKeyEvent` per character | Untested | Would be ~3000 key events — impractical even if it worked |

### FAILED — Transport workarounds (solve shell escaping, not React)

| Approach | Result | Detail |
|----------|--------|--------|
| base64 + `atob()` | Transports text reliably | Gets text into JS context — but React still blocks insertion |
| `$(cat file)` in shell | Transports text | Same — transport works, React blocks |
| Node.js `execSync` + `JSON.stringify` | Transport works | Same — React boundary remains |

### NOT A SOLUTION — Tool alternatives

| Tool | Why not |
|------|--------|
| **Webwright** (`pi-webwright`) | Same Playwright engine. Pi skill wrapper, not a different automation engine. No React contentEditable bypass. |
| Raw CDP via Chrome DevTools | `Runtime.evaluate` is the same mechanism. `Input.*` commands hit same React event handlers. |

## What Does Work

1. **Manual human paste (Ctrl+V)** — the only reliable method. React processes real keyboard events and updates its virtual DOM correctly.
2. **Monaco editor (topic YAML)** — the topic code editor is Monaco, not React contentEditable. `fill` + `Ctrl+S` works there. Only the Instructions editor has this problem.
3. **React native setter** (for `<input>` and `<textarea>` elements) — `Object.getOwnPropertyDescriptor(...).set` + dispatch `input`/`change` events works for form elements. Only contentEditable divs are resistant.

## Session Record

| Date | Agent | Issue | Resolution |
|------|-------|-------|------------|
| 2026-06-09 | SLP | v6 paste attempted; fill command partially worked after multiple retries | Eventually succeeded via fill; unreliable |
| 2026-06-10 | OT | v6/v7 paste attempted; all methods failed | Manual paste required |
| 2026-06-10 | TDA | v2 paste attempted; same wall | Manual paste required |

## Recommendation

If you've tried programmatic instruction editing twice, **stop and give the user the text.** Every approach hits the same React boundary. Write the instructions to a `.txt` file and tell the user to Ctrl+A, Ctrl+V, Save in the open editor.
