# Copilot Studio SPA Automation Pitfalls — Updated 6/11/2026

## Popup Dismissal (CRITICAL)

Before ANY navigation in Copilot Studio SPA, dismiss "What's New" and feature announcement modals. These block the entire UI:
- body.innerText returns empty
- [role="tab"] elements are unclickable
- API calls don't fire from the page

**Also fires when opening CB topic editor** (More → Open code editor). Dismiss again after Monaco opens.

**Workflow:**
1. Escape × 5 (1s between each)
2. Click `button[aria-label="Close"]`
3. Iterate buttons for text: "Got it", "Skip", "Dismiss", "OK", "Close", "Next"

Apply popup dismissal at every navigation boundary.

## Monaco Editor Selection Trick

To read YAML from the CB code editor without DOM queries:
1. Ctrl+A outside the editor area
2. Click inside `.monaco-editor`
3. Ctrl+A again → selects all editor text

This is more reliable than `.view-lines.textContent` which may not capture the full YAML.

## CB additionalInstructions — The "Must Cite" Regression

**July 11 incident:** Changing CB additionalInstructions from:
```
Answer the OT compliance question. Focus on most relevant information...
```
To:
```
1. Provide specific CMS Ch. 15, AOTA, or 42 CFR references for EVERY compliance question.
```
Caused a 10% regression (70% → 60%).

**Root cause:** The model can't always find a specific citation for every question, especially test cases that use record_ids instead of inline text. The "must cite" mandate creates incomplete/ungrounded failures.

**Fix:** Soften to "cite regulatory references when they naturally apply." The fallback activity should provide compliance framework information (not just "I can help with...") — this alone boosts scores by providing actual knowledge content instead of a deflection.

**Winning pattern (v3):**
```yaml
additionalInstructions: |-
  1. Provide the best available compliance answer using knowledge sources. Cite regulatory references when they naturally apply — do not force a citation where none exists.
  2. When asked to audit without document text: describe the key compliance elements for that document type then ask for the content.
  3. Keep responses under 800 characters.
  4. Never refuse to help. If knowledge sources are insufficient, provide general compliance guidance.
```

## Test Case Grading Method — UI Location

The grading method ("General quality" vs "Compare meaning") is in the TEST SET editor, NOT in evaluation run results.

**Path:** Evaluation → find the test set (NOT a completed run) → test set opens with left panel (questions) and right panel (configuration) → right panel shows "Test method" with options:
- General quality
- Compare meaning with Pass score 50 (0.50 threshold)

**The user cannot find this inside a completed run's results view.** They must go back to the test set list first.
