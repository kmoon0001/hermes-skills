# API-vs-UI Cache Conflict Workflow

## The Problem
Copilot Studio's SPA caches topic YAML in browser memory. PATCHing via Dataverse API then opening the topic in the UI shows the cached (pre-PATCH) version. Saving in the UI **overwrites** API changes with the old cached data.

## Symptoms
- Topics "reset" or "undo" after being fixed
- "Can't load variable set action" errors — UI can't render API-modified YAML
- A topic that was valid becomes invalid after UI edit

## Root Cause
SPA loads topics into memory on first open and doesn't re-fetch on navigation. API PATCHes modify server-side data but the UI never knows.

## Workflow Rules
1. **Pick ONE channel** — API PATCH OR UI editor, never both for same topic
2. **If switching channels:** Close browser tab completely → reopen → verify in code editor before saving
3. **Shift+Reload** in Chrome bypasses cache
4. **F12 → Network → Disable cache** checkbox while DevTools is open
5. **Direct URL navigation** bypasses some caching:
   `https://copilotstudio.microsoft.com/environments/{env}/bots/{bot}/adaptive/{topic-guid}`

## Preferred Approach
Write corrected YAML to files → user pastes into UI code editor → UI is sole source of truth. No API PATCHes for topics the user will edit in the same session.
