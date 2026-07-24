# Topic Textarea Edit Pitfall

## Problem
Copilot Studio topic "Describe what the topic does" textarea can be filled via Playwright but the Save button stays disabled and changes do NOT persist on reload.

## Root Cause
Same React dirty-state detection issue as instructions editor. The textarea value change via CDP/Playwright does not fire the events React listens for to mark the form dirty.

## Workaround
Use **More > Open code editor** to open the YAML Monaco editor instead of the visual textarea. Edits in the code editor persist normally.

## Alternative
Turn off/deleting the problematic topic entirely and let the agent's base instructions handle the queries (if base instructions already cover the topic area).