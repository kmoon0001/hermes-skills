# Live UI File Editing — Renaming & Describing Uploaded Files

Full step-by-step for batch-renaming uploaded files in the Copilot Studio Knowledge page.

## Navigation

1. `npx playwright-cli --session <name> goto "https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/knowledge"`
2. Wait 10-12s for SPA to render
3. Click the **Files** tab (ref=e190 in snapshot)
4. Wait for file list to render

## Click a File

Find the file link ref in the snapshot, then click it:

```bash
npx playwright-cli --session <name> click e1167
```

## Set Name (React Input Setter)

```javascript
var inp = document.querySelector('input[placeholder="Enter name"]');
var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
s.call(inp, 'New Clean Name Without .pdf');
inp.dispatchEvent(new Event('input', {bubbles:true}));
inp.dispatchEvent(new Event('change', {bubbles:true}));
```

## Set Description (React Textarea Setter)

```javascript
var ta = document.querySelector('textarea');
var s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
s.call(ta, 'Provides [content]. Use when [query intent]. Covers [key topics].');
ta.dispatchEvent(new Event('input', {bubbles:true}));
ta.dispatchEvent(new Event('change', {bubbles:true}));
ta.dispatchEvent(new Event('blur', {bubbles:true}));
```

## Save

```bash
# Click "Save knowledge changes" button
npx playwright-cli --session <name> click e182
```

**Ctrl+S does NOT work** on this page. You must click the Save button.

## Batch Pattern

Navigate back to the knowledge list between each file to avoid stale state:

```bash
npx playwright-cli --session <name> goto ".../knowledge"
sleep 12
# Click Files tab
# Click file
# Set name + desc
# Click Save
# Repeat
```
