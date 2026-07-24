# Copilot Studio Automation — Battle-Tested Patterns

## Popup Dismissal (MANDATORY FIRST STEP)

Copilot Studio fires "What's New" and feature announcement popups that block the entire UI. These modals prevent:
- body.innerText from returning page content (shows empty or just "Skip to main content")
- Tabs from being clickable
- Page state from being interrogated

**Dismissal procedure:**
1. Press Escape ×5 (500ms between each)
2. Hunt buttons for text: "Got it", "Skip", "Dismiss", "Close", "OK", "Next", "Accept"
3. Click `button[aria-label="Close"]` and `button[title="Close"]`
4. CB editor popup: fires AGAIN when opening "Open code editor" — dismiss ×3 after opening

```javascript
// Popup dismissal (runs in page.evaluate)
for (let i = 0; i < 5; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(500); }
await page.evaluate(() => {
  let clicked = 0;
  for (const btn of document.querySelectorAll('button')) {
    const t = (btn.textContent || '').trim();
    if (['Got it','Skip','Dismiss','Close','OK','Next','Accept'].includes(t)) {
      if (btn.getBoundingClientRect().width > 0) { btn.click(); clicked++; }
    }
  }
  const close = document.querySelector('button[aria-label="Close"], button[title="Close"]');
  if (close?.getBoundingClientRect().width > 0) { close.click(); clicked++; }
  return clicked;
});
```

## Monaco Editor — Reading Text

The Monaco `.view-lines.textContent` approach works for small YAML but fails for long content. The user discovered a reliable trick:

1. **Click outside** the editor to lose focus
2. **Ctrl+A** (selects page content)
3. **Click inside** `.monaco-editor`
4. **Ctrl+A** again — now selects Monaco text
5. Read clipboard or `.view-lines.textContent` and normalize `\u00a0` → space

## Conversational Boosting YAML Evolution

Three iterations learned the hard way:

| Version | additionalInstructions | Fallback Activity | Result |
|---------|----------------------|-------------------|--------|
| v1 | Generic "Answer the question, focus on (list)" | "I can help with X... could you provide more detail?" | Too passive — trigger refusal failures |
| v2 | "Cite specific CMS per response, never refuse" | Same as v1 but with actual compliance info | Too aggressive — regression! Model can't always cite, marked incomplete |
| v3 | "Cite when naturally applies, do not force a citation where none exists" | Substantive: "Key Medicare requirements include skilled service justification per CMS Ch. 15..." | Balanced |

**Rule:** Fallback activity must include actual compliance information, not just redirection. `additionalInstructions` must say "cite when naturally applies" — never "must cite per response."

**CB YAML rules (from painful experience):**
- `activity:` must be ONE continuous line — no line wrapping
- No commas (they break YAML list parsing)
- No question marks (`?`) in the string
- No contractions (`you'd` → `you would`)
- Action kind: `SearchAndSummarizeContent` (NOT `CreateGenerativeAnswers`)
- Power Fx: `{Topic.var}` NOT `{$Topic.var}`
- EndDialog must include `clearTopicQueue: true`

## Systematic MS Learn Evaluation Approach

Per Microsoft Learn evaluation triage framework, apply in strict order:

**Layer 1.5 (KB quality — ALWAYS FIRST):** Check knowledge source descriptions, official/authoritative markings, content freshness BEFORE any agent config changes.

**Layer 2 (Eval setup):** Fix grading method (Compare meaning at 0.50 threshold) before agent config. Record_id test cases that simulate Dataverse lookups are evaluation setup issues — accept as known limitations or switch grading method.

**Layer 3 (Agent config):** Only after Layer 1.5 and Layer 2 are addressed.

**Layer 4 (Document):** Track patterns across iterations.
