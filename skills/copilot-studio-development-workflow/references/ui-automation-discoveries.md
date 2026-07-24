# Copilot Studio UI Automation Discoveries (2026-06-11)

## Monaco Editor: Reliable Text Selection
- Click OUTSIDE the `.monaco-editor` → Ctrl+A (selects page content)
- Click INSIDE `.monaco-editor` → Ctrl+A again (now selects editor YAML)
- This two-step pattern reliably selects Monaco content when direct Ctrl+A fails
- Also works for reading YAML without "Open code editor"

## CB Editor Popup
- Opening CB topic's code editor triggers a SECONDARY "What's New" popup
- Must dismiss with Escape × 3 after "Open code editor" click
- Check for `.view-lines` visibility as confirmation popup is gone
- Without this dismissal, reading/writing YAML is blocked

## Playwright Persistent Auth
- Launch browser, sign in to Copilot Studio manually
- Save: `context.storageState({ path: '.playwright-auth/state.json' })`
- Reuse: `browser.newContext({ storageState: '.playwright-auth/state.json' })`
- Auth persists across sessions — no sign-in needed for subsequent runs

## Token Capture for Eval API
- CDP `Network.enable` → listen for `Network.requestWillBeSent`
- Filter for `api.powerplatform.com` in URL + `Bearer ` auth header
- Token is ~4500 chars, valid ~1 hour, read-only
- Navigate to any Copilot Studio page to trigger token generation

## Eval API Patterns (api-version=2024-10-01)
- `state` field is STRING: "NotStarted" | "InProgress" | "Completed" | "Failed"
- Run list: `/testruns?$orderby=startTime%20desc&$top=3`
- Run detail: `/testruns/{id}?$expand=testCasesResults`
- Failures have `aiResultReason` for conversation, empty for single-response
- Grading data fields: `abstention`, `relevance`, `groundedness`, `completeness`

## Grading Methods
- "General quality" = default. Detects relevance, completeness, groundedness
- "Compare meaning" at 0.50 threshold = semantic similarity check. Fixes false
  negatives where response is correct but uses different wording
- The 0.50 is a semantic threshold (0-1 scale), NOT a pass rate
- For citation false negatives: switch from General quality → Compare meaning
- Must be changed in test set editor (NOT in evaluation run view)
- Cannot be changed via API (read-only token)

## Agent Instruction Size Ranges
- PT/OT: 3,000-5,500 characters
- SLP: 1,800-3,000 characters
- TDA: 4,000-7,000 characters
- Over upper range = likely duplicated/corrupted

## Architecture Alignment Strategy
- When a failing agent has a passing peer, match configs
- Example: SLP failing → align to PT/OT pattern (same webBrowsing, knowledge type, instructions format)
- NEVER disable CB on SLP (SLP uses CB as primary router — disabling = 0%)
