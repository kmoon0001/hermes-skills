# System Topics API Patch (verified Jul 10 2026)

## ConvStart CAN be API-patched
Conversation Start (kind: OnConversationStart) was successfully PATCHed via Dataverse API + published multiple times:
- Changed from OnRecognizedIntent → OnConversationStart
- Changed data content, statecode
- Each PATCH returned 204, publish succeeded

## Escalate/OnError/ResetConversation
These have reported SynchronizationSystemError in past sessions. Strategy:
1. Try API PATCH first
2. If publish fails, revert via API
3. Fallback to UI code editor

## Key: Do NOT blanket-claim "system topics can't be API-patched"
The claim was disproven. ConvStart works. The limitation may be specific to certain system topic types or `content` field patches.
