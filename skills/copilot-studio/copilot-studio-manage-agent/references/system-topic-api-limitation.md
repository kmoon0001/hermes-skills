# System Topic API Limitation

## The Claim

Previous guidance stated that system topics (`kind: OnConversationStart`, `OnEscalate`, `OnError`, `OnSystemRedirect`, `OnConversationUpdate`, `OnUnknownIntent`) **CANNOT** be `data`-field PATCHed via the Dataverse API — that doing so causes `SynchronizationSystemError` on publish, and the only fix is a UI code editor restore.

## Reality (Updated Jul 10 2026)

**Conversation Start (`kind: OnConversationStart`) CAN be API-patched and published successfully.** This session proved it:

| Action | Method | Result |
|--------|--------|--------|
| Revert ConvStart from OnRecognizedIntent → OnConversationStart | Dataverse API `PATCH data` | 204 OK |
| Reactivate (statecode change) | Dataverse API `PATCH statecode` | 204 OK |
| Simplify data (remove EndDialog) | Dataverse API `PATCH data` | 204 OK |
| Restore full original YAML from snapshot | Dataverse API `PATCH data` | 204 OK |
| Publish after each change | `pac copilot publish --bot` | Succeeded every time |

**Conclusion:** The `SynchronizationSystemError` may be specific to:
- **Certain system topics** (Escalate, OnError, ResetConversation?) — NOT ConvStart
- **`content` field PATCH**, not `data` field PATCH
- **A transient environment state** that has since resolved
- **A specific YAML structure** that triggers validation differently

**DO NOT assume ANY system topic is blanket-blocked from API patch.** Try the API PATCH first. If publish fails with `SynchronizationSystemError`, THEN fall back to UI code editor restore.

## Detection

If publish fails after patching a system topic, check diagnostics:

```python
import json
ss = json.loads(data['synchronizationstatus'])
lop = ss.get('lastFinishedPublishOperation', {})
if lop.get('status') == 'Failed':
    for detail in lop.get('diagnosticDetails', []):
        print(detail.get('errorCode'), detail.get('errorMessage','')[:120])
```

If `SynchronizationSystemError` found: revert the topic's data via API PATCH to the backup snapshot. If API revert + publish still fails, use UI code editor.

## System Topic List — API-PATCH Verified?

| Copilot Studio Name | `beginDialog.kind` | API-PATCH Works? |
|---|---|---|
| Conversation Start | `OnConversationStart` | **YES — Jul 10 2026** |
| Escalate | `OnEscalate` | Reported failure in past sessions |
| On Error | `OnError` | Reported failure in past sessions |
| Reset Conversation | `OnSystemRedirect` | Reported failure in past sessions |
| End of Conversation | `OnSystemRedirect` | Unknown |
| Goodbye | `OnSystemRedirect` | Unknown |
| Multiple Topics Matched | `OnSystemRedirect` | Unknown |
| Fallback | `OnUnknownIntent` | Unknown |
| Sign in | `OnSystemRedirect` | Unknown |
| Start Over | `OnSystemRedirect` | Unknown |
| Thank you | `OnSystemRedirect` | Unknown |
| Greeting | `OnConversationUpdate` | Unknown |

**Strategy:** Try API PATCH first for any system topic. If publish breaks, revert, use UI code editor, and update this table.

## Prevention

1. **Take a full snapshot backup** before any PATCH operations.
2. **Try API PATCH first** for system topics — don't default to "must use UI."
3. **If publish fails**, check `synchronizationstatus` diagnostics — don't assume the topic was the problem.
4. **For Escalate/OnError/ResetConversation** — be more cautious. These are the topics that previously triggered `SynchronizationSystemError`.
5. **Keep the original snapshot YAML** handy for quick revert via API PATCH.
