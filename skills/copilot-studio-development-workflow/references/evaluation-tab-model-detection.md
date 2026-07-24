# Evaluation Tab Click & Model Retirement Detection

## Agent-Level Tab Click Pattern (June 2026)

Copilot Studio agent-level tabs (Overview, Knowledge, Topics, Activity, **Evaluation**, Analytics) are rendered as `<button>` elements containing a `<span>` with the tab text. They do NOT have `role="tab"` — the `role="tab"` selector only finds top-level nav tabs.

### Correct Click Pattern

```javascript
// Click the Evaluation tab — find parent BUTTON of the Evaluation SPAN
await page.evaluate(() => {
  const btns = document.querySelectorAll('button');
  for (const btn of btns) {
    const spans = btn.querySelectorAll('span');
    for (const span of spans) {
      if (span.textContent.trim() === 'Evaluation') {
        btn.click(); return;
      }
    }
  }
});
```

### Reliable Page Load Pattern

1. Navigate to `/testing` URL (NOT `/evaluation` directly)
2. Wait for SPA to render: poll until `document.body.innerText.length > 1500`
3. Click Evaluation tab via the parent-button pattern above
4. Wait for evaluation content: poll until "New evaluation" text appears or 3000+ chars
5. Direct `/evaluation` URL also works but takes 20-30s for SPA to fully render

### Triggering an Evaluation

```
1. Wait for "New evaluation" button text (20-30s after tab click)
2. Click "New evaluation"
3. Find Conversation test set row: text contains "conversation" + "test case"
4. Click "Run" button within that row
5. Confirm in dialog if one appears
6. Wait for completion: Conv 5-15 min, SR 15-45 min
7. Parse scores from document.body.innerText as "SCORE: XX%" lines
```

### Pitfalls

- The `/evaluation/configsDetails` path shows test set details, NOT the evaluation list
- The `/evaluation` path works for direct navigation but SPA renders very slowly
- Never use `[role=tab]` selector — it won't find agent-level tabs
- Multiple "Edit" buttons on Overview: Edit #0 = Description, Edit #1 = Instructions (contenteditable div, NOT textarea)
- Instructions content is in `div[role=textbox][contenteditable=true]`, NOT `<textarea>`

## Model Retirement Detection

When an agent Overview page shows the message:

> "Your selected agent model was retired, so we updated your agent to use another model."

This is a **FIRST-ORDER regression cause** — model changes can cause 5-15% score swings in both SR and Conv evaluations. Always check this before diagnosing other causes.

### Detection Code

```javascript
const text = await page.evaluate(() => document.body.innerText);
const retired = text.includes('was retired') || text.includes('model was retired');
```

### Remediation

1. Note the current model (e.g., GPT-5 Chat)
2. If scores dropped after model change, consider:
   - Updating agent instructions for the new model's behavior
   - Re-running baseline evaluations to establish new norms
   - Checking if other agents using the same model have similar score patterns
