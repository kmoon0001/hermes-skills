# Monaco Injection & Verification for Copilot Studio Topic YAML Fixes

## The Persistence Problem

Setting `textarea.value` in the Monaco editor's hidden textarea does NOT update the Monaco editor model. The React dirty-state flag does not trigger, so the Save button either stays disabled or saves the unchanged content. The UI may show "Published" but the topic YAML is unchanged.

In June 2026, OT and PT topics were "fixed" via textarea injection + Space+Backspace + Save, but the fixes did NOT persist — scores remained at pre-fix levels for multiple eval cycles.

## Working Injection Method

### Step 1: Open topic in code editor
```
1. Navigate to agent Overview page
2. Click Topics tab
3. Click topic name (or navigate to /adaptive/{topicGuid})
4. Wait for Save button to appear (topic loaded)
5. Click More > Open code editor
6. Wait 8-10 seconds for Monaco to render
```

### Step 2: Inject via Monaco API
```javascript
// Use the Monaco editor API directly — does NOT use textarea
var injected = await page.evaluate(function(yaml) {
  if (typeof monaco !== 'undefined' && monaco.editor) {
    var models = monaco.editor.getModels();
    if (models.length > 0) {
      models[0].setValue(yaml);       // Set full YAML content
      models[0].pushStackElement();    // Mark as undoable change (triggers dirty)
      return 'monaco:' + yaml.length;
    }
  }
  // Fallback: textarea setter + input event
  var ta = document.querySelector('textarea');
  if (ta) {
    var setter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    setter.call(ta, yaml);
    ta.dispatchEvent(new Event('input', { bubbles: true }));
    return 'textarea:' + yaml.length;
  }
  return 'NO_EDITOR';
}, yamlContent);
```

### Step 3: Trigger React dirty state
```javascript
// Space+Backspace after injection marks the document dirty for React
await page.keyboard.press('End');
await sleep(100);
await page.keyboard.press(' ');
await sleep(200);
await page.keyboard.press('Backspace');
await sleep(500);
```

### Step 4: Click Save
```javascript
await page.evaluate(function() {
  var btns = document.querySelectorAll('button');
  for (var btn of btns) {
    if (btn.textContent.trim() === 'Save') { btn.click(); return; }
  }
});
await sleep(3000); // Wait for save to complete
```

### Step 5: VERIFY by re-reading Monaco DOM (with non-breaking space normalization)

**⚠️ CRITICAL: Monaco uses non-breaking spaces (`\u00A0`) which break standard verification.**

```javascript
var verify = await page.evaluate(function() {
  var lines = document.querySelectorAll('.monaco-editor .view-lines .view-line');
  var text = [];
  lines.forEach(function(l) { text.push(l.textContent); });
  return text.join('\n');
});

// Normalize non-breaking spaces BEFORE checking
verify = verify.replace(/\u00A0/g, ' ');

// Check the fix persisted — use regex, not indexOf
var has800 = /800/.test(verify);
// has800 should be false after removing 800-char limits

// Also check for the replacement text
var hasBeConcise = verify.indexOf('Be concise but complete') >= 0;
```

**Why regex:** `indexOf('800 character')` and `indexOf('under 800')` fail when Monaco renders "800" with non-breaking spaces (e.g., "under\u00A0800"). Always normalize with `.replace(/\u00A0/g, ' ')` first, then check with `/800/.test()`.

**Critical: DO NOT skip verification.** Without it you won't know the fix was applied until the next eval completes (10+ minutes wasted). A false-negative verification (no match due to unicode spaces) is just as bad as a false-negative on any other check.

## Detecting Injection Failure

| Symptom | Cause | Fix |
|---------|-------|-----|
| Verify YAML length << injected length | Monaco DOM only renders visible lines (virtualized). The full content IS stored but DOM shows ~60% | Check for key patterns (800-char, EndDialog) instead of comparing lengths |
| Verify still shows 800-char limit | Save didn't persist. React dirty state wasn't triggered | Re-run with Monaco API + pushStackElement() + Space+Backspace |
| Publish shows no confirm dialog | No changes to publish — injection didn't trigger dirty state | Re-inject and verify before publishing |
| **Score REGRESSED after injection** (e.g., 94% → 87%) | Full topic YAML was replaced with an OLD template version that lacked post-export optimizations (triggerQueries, modelDescriptions added since template export) | **NEVER replace entire topic YAML.** Only surgically delete the 800-char line. Restore topic from backup/revert, then apply surgical deletion only. |
| `indexOf('800')` returns false but `indexOf('under\\u00A0800')` would return true | Monaco renders unicode non-breaking spaces | Normalize: `verify.replace(/\\u00A0/g, ' ')` before checking with `/800/.test()` |

### ⚠️ Do NOT Replace Entire Topic YAML

The fix files generated from template exports (`ot_template.yaml`, `pt_template.yaml`) contain entire topic YAML from the EXPORT DATE. Topics may have been optimized since then with:
- New trigger queries (improved routing)
- modelDescription metadata (better topic matching)
- Other per-topic optimizations

Injecting the old template's YAML over the current version removes ALL post-export improvements. **Evidence (June 16, 2026):** OT and PT both dropped from 94% SR → 87-88% SR after full YAML replacement, because the old template lacked trigger query and modelDescription updates that had been added since export.

**Correct approach:** Open the topic code editor, find ONLY the line containing `Keep response under 800 characters`, delete that single line, optionally add `Be concise but complete — prioritize accuracy and actionable findings over strict length limits.` Leave everything else untouched.

## Batch Injection Workflow

For multiple topics across agents:

1. Get topic GUIDs via Dataverse:
   ```javascript
   var filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
   var url = `/api/data/v9.2/botcomponents?$select=name,botcomponentid&$filter=${encodeURIComponent(filter)}&$top=50`;
   ```

2. Inject via direct GUID URL: `/adaptive/{topicGuid}`
   - This bypasses the slow SPA topics list
   - Each topic loads independently from a fresh URL

3. Verify ALL topics, then publish once
