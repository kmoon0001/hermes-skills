# Dataverse PATCH for System Topics — Verified Working

**Context:** Earlier constraint "System topics (OnEscalate, OnError, OnConversationStart) CANNOT be API-patched — breaks publish with SynchronizationSystemError" was based on a different bot version or environment.

**Verified on Therapy AI Dev (orgbd048f00, bot b0346795):** All three system topics were successfully patched via `PATCH /botcomponents({guid})` with updated `data` field. The bot published successfully via `pac copilot publish` afterward. No SynchronizationSystemError occurred.

## What Was Patched

- **Conversation Start** (57d758c7): Changed from OnRecognizedIntent back to OnConversationStart, then deactivated (statecode=1). Published without issues.
- **Escalate** (bd785c81): Data patched multiple times. Published without issues.
- **On Error** (59acb80b): Data patched. Published without issues.

## When This Might NOT Work

- Different bot version (e.g. managed solution vs unmanaged)
- Different environment (production vs dev)
- Different publish method (pac copilot publish vs UI publish)

## Safer Approach

Test on ONE non-critical topic first. If publish succeeds, the constraint doesn't apply to your environment. If it fails with SynchronizationSystemError, fall back to the UI code editor approach (More > Open code editor > paste YAML > Save).
