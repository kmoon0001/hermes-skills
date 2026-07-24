# Topic YAML 800-Character Limit — Validated Eval Failure Pattern

## The Pattern

Every SearchAndSummarizeContent topic YAML's `additionalInstructions` field
may contain `Keep response under 800 characters.` (or any strict char limit).
This causes the model to truncate audit responses. The grader marks these as
"incomplete" → score drops 10-25%.

## Validated Across All 3 Agents (June 2026)

| Agent | Topics Affected | Impact | Fix Applied |
|-------|----------------|--------|-------------|
| SLP | Analyze SLP Daily Therapy Note | Conv 90%→85% | Removed 800-char limit |
| OT | All 5 audit topics fixed in v7→v8 | SR 90%→98% | Removed 800-char limit, unconditional RF |
| PT | All 5 audit topics (Daily, Progress, Discharge, Eval, Recert) | Conv unknown→75% | Removed 800-char limit, added citation rule |

## The Fix

Replace `Keep response under 800 characters.` with:
```
Be concise but complete. Prioritize accuracy over strict length limits.
```

Also add citation instruction (most agents lack it):
```
Cite CMS Chapter 15 and [APTA/ASHA/AOTA] guidelines by natural source name.
Do not cite:1 or output metadata tags.
```

## Complete YAML Injection Pattern

The Monaco code editor accepts YAML via `Input.insertText` but the Save button
stays disabled. The user MUST manually type a char + Backspace to trigger
React's onChange, then click Save. See `references/cdp-code-editor-workflow.md`
for the full injection workflow.

## User Preference: Full Code, Not Snippets

When providing topic YAML fixes, deliver the COMPLETE `beginDialog:` block
(triggerQueries + actions + inputType/outputType) — NOT just the
`additionalInstructions:` replacement snippet. The user explicitly requested:
"give me the full code from now on."

A partial replacement risks missing indentation or YAML structure errors that
a full-block paste avoids.

## Detection Script (via pac copilot extract-template)

```bash
# PT extraction works (48 components, 990 lines)
pac copilot extract-template \
  --bot "<botId>" \
  --templateFileName "/path/to/template.yaml" \
  --overwrite

# SLP extraction CRASHES (63 components, AddKSComponent ArgumentException)
# Knowledge-heavy agents with many SharePoint sources trigger pac 2.7.4 bug
# Alternative: use Dataverse API or manual topic inspection
```

After extraction, search for the 800-char pattern:
```bash
grep -n "800 characters\|under 800\|Keep response under" template.yaml
```

## Verifying the Fix

After applying + publishing + re-evaluating:
- Create a fresh eval tab via CDP `curl -X PUT /json/new`
- Wait 25s for SPA
- Read `get_scores.cjs` or `body.innerText` with keyword "Recent results"
- Score should improve 10-20% if 800-char limit was the primary cause
