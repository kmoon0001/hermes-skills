---
name: playwright-topic-editor
description: Update existing Copilot Studio topic content via Playwright UI code editor when Dataverse API PATCH fails on locked components (iscustomizable=False). Validated selectors, batch update patterns, and known issues.
category: copilot-studio
---

# Playwright Topic Code Editor — Bulk Update

Use when Dataverse API PATCH fails on locked botcomponents. The Copilot Studio UI code editor accepts content that the API rejects.

## When to Use
- API PATCH returns 500 or `iscustomizable=False` on topic components
- Need to update topic content on locked/managed topics
- Batch-updating multiple existing topics

## Hermes Tool Mapping

Kiro uses `@playwright/mcp`. Hermes uses the built-in `browser` tool:

| Kiro (Playwright MCP) | Hermes (browser tool) |
|----------------------|----------------------|
| `page.goto(url)` | `browser_navigate(url)` |
| `page.locator('...').click()` | `browser_click(ref)` — find ref from snapshot |
| `page.keyboard.press('Ctrl+A')` | `browser_press(key='Control+a')` |
| `navigator.clipboard.writeText(yaml)` | `browser_console(expression='navigator.clipboard.writeText(...)')` |
| `page.keyboard.press('Ctrl+V')` | `browser_press(key='Control+v')` |
| `page.keyboard.press('Ctrl+S')` | `browser_press(key='Control+s')` |

## Steps

### 1. Navigate to the agent's custom topics page
```
browser_navigate → https://copilotstudio.microsoft.com/environments/{envId}/bots/{botId}/tools/custom-topics
```

### 2. Search and open the target topic
```
browser_snapshot → find the search input ref
browser_type(ref, text="Topic Name")
browser_snapshot → find the topic link ref
browser_click(ref) → opens the topic editor
```

### 3. Open the code editor
```
browser_snapshot → find "More" button ref
browser_click(ref)
Wait 1.5s for menu
browser_snapshot → find "Open code editor" menu item ref
browser_click(ref)
Wait 4s for Monaco editor to load
```

### 4. Replace content
```
browser_console(expression='navigator.clipboard.writeText(`...YAML...`)')
browser_press(key='Control+a')  # select all
browser_press(key='Control+v')  # paste
Wait 1s
```

### 5. Save
```
browser_press(key='Control+s')
Wait 3s for save to complete
```

## Known Issues

- **Selector reliability:** Use `button:has-text("More")` NOT `button[aria-label="More"]` — aria-label doesn't match in all page states
- **Monaco paste failure:** Sometimes first clipboard paste doesn't register. Retry Ctrl+V if content doesn't change
- **Large YAML (>5000 chars):** Use `browser_console(expression)` to set Monaco's value directly instead of clipboard: `document.querySelector('.monaco-editor textarea').value = '...'`
- **Browser console noise:** 3-7 JS errors on every page load are platform noise, NOT topic errors
- **Validation errors:** Show as numbers in the Errors column of topics grid, not in console
- **Stale state:** Navigate back to topics list before opening next topic to prevent stale editor state

## Batch Pattern

For updating multiple topics, repeat steps 1-5 for each topic. Navigate back to topics list between topics.

## When to Use API Instead

Prefer Dataverse API PATCH for topics that accept it (componenttype 9, not locked). Only fall back to Playwright when API returns 500 or `iscustomizable=False`. The API is faster, more reliable, and automatable.

## Related Skills

- `cdp-instructions-injection` — Creating NEW topics via Playwright (not updating existing)
- `copilot-studio-live-patch` — API-based topic patching (preferred when API works)
- `agent-builder-pipeline` — Full build pipeline uses API first, Playwright as fallback
