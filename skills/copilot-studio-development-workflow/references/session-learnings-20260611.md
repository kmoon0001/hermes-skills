# Copilot Studio Automation Tips (6/11/2026)

## Popup Dismissal — CRITICAL First Step

Copilot Studio spawns multiple popups that block ALL automation:
- **"What's New" onboarding popup** — on evaluation page, overview page, and after publishing
- **CB editor popup** — when opening "Open code editor" on any topic
- **Consent popup** — when testing an agent shared by another user

**Dismissal routine (before ANY navigation or click):**
1. Press Escape × 5 (500ms between)
2. Iterate all buttons: click any with text "Got it", "Skip", "Dismiss", "Close", "OK", "Next", "Confirm"
3. After navigating deeper into the SPA, repeat Escape × 3

Without this, `body.innerText` returns empty, tabs are unclickable, and SPA navigation fails silently.

## Monaco Code Editor Selection

The code editor (powered by Monaco) has an invisible text layer that DOM selectors can't read directly.

**To SELECT all text in the editor:**
1. Ctrl+A on outer page (or click page background first)
2. Click inside the `.monaco-editor` area
3. Ctrl+A again → this selects all Monaco text

**To READ the YAML:**
- After selecting with the trick above, `document.getSelection().toString()` returns the content
- Alternative: `.view-lines.textContent` after normalizing `\u00a0` → space

## CB additionalInstructions — The "Must Cite" Regression

**DON'T** force citations in additionalInstructions:
- "Cite CMS per response" → regresses scores by ~10%
- "Cite when naturally applicable" → stable

**DO** tell the model what to do when it can't find specific content:
- "Provide the compliance framework for this document type"
- "List the key Medicare elements that would be checked"
- "Never refuse — give general guidance if specific knowledge isn't available"

The fallback message should provide real compliance content, not just "I can help with..."

## Compare Meaning — SR Only

Compare meaning grading method is ONLY available for **Single Response** test sets. Conversation test sets use "General quality" only. Cannot be changed.

## KB Quality — The Real Fix for Ungrounded Failures

Most "knowledge sources not cited" failures are caused by:
1. **Blank descriptions** — GPT filter treats descriptions as intent matching; blank = random selection
2. **Duplicate sources** — Same content in SharePoint AND uploaded files → noisy retrieval
3. **No official markings** — Authoritative content should be marked "Official" (classic mode only)

**Fix priority:**
1. Remove duplicate paths (SharePoint vs uploaded files)
2. Add specific descriptions to every source
3. Mark authoritative sources as Official
