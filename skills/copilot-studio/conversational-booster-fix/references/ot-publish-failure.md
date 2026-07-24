# OT_Specialist Publish Failure — Investigated State

## Symptom
`pac copilot publish --environment <url> --bot <ot-bot-id>` returns:
```
Failed to publish. 73b45e98-af7a-443a-aa12-6d8a05118530 Failed [7/3/2026 7:26:12 AM].
```
Same timestamp on every retry — the CLI returns a cached failure state, not a fresh attempt.

## What Was Tried (None Worked)
| Attempt | Result |
|---------|--------|
| `pac copilot publish` (3x) | Same cached timestamp each time |
| `PvaPublish` API (Dataverse POST) | HTTP 200 but empty response body (silent fail) |
| `PublishAsync` API | Endpoint not found (404) |
| Navigate browser to OT overview page | SPA didn't re-auth — redirected to sign-in page |

## Likely Cause
A validation error in the topic data that Dataverse detects during publish but the tool doesn't surface. Possible candidates:
- Reference to a knowledge source or file that was deleted since the YAML was written
- Malformed YAML that passes basic syntax check but fails Copilot Studio's deeper validation
- Agent configuration mismatch (Work IQ enabled? Response Formatting misconfigured?)

## Recommended Fix Path
1. Publish OT from the Copilot Studio UI (signed-in browser tab) — click Publish button
2. If UI also fails, check the Activity log for detailed error messages
3. Verify no deleted Knowledge sources are referenced in any topic
4. Check Response Formatting and Work IQ settings in Settings → Generative AI
