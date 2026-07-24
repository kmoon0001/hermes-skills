# Topic YAML Editing Pitfalls

## Dataverse API Cannot Update Topic Content (Jun 19, 2026)

The PATCH endpoint for botcomponents returns 400 when updating the `content` field. Only DELETE works reliably via API (returns 204). Content updates must be done via the Copilot Studio UI (code editor with manual paste).

```javascript
// DELETE works:
await fetch(`https://org.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, { method: 'DELETE' });
// Returns 204

// PATCH content fails:
await fetch(`https://org.crm.dynamics.com/api/data/v9.2/botcomponents(${id})`, { method: 'PATCH', body: JSON.stringify({ content: yaml }) });
// Returns 400
```

## Notepad Issues on Windows (Jun 19, 2026)

When launching Notepad via `cmd.exe /c start notepad.exe <file>`, the system may invoke a git wrapper script instead of the actual Notepad.exe. The wrapper shows a bash script with `unix2dos.exe`/`dos2unix.exe` calls.

**Fix:** Copy file to Desktop and open Explorer:
```powershell
powershell.exe -Command "Start-Process explorer 'C:\Users\<user>\Desktop'"
```

## Switch to Manual Faster (Jun 19, 2026)

When the user says "this is taking too long" or "are you stuck", switch to writing files + opening Notepad/Explorer immediately. Don't retry CDP approaches that have already failed. The user is fast at manual actions and prefers paste-ready files over slow automation.

## Monaco Injection Corrupts Topics (Jun 17-19, 2026)

CDP injection into Monaco editors via `Input.insertText`, clipboard paste, or textarea.value setter reliably CORRUPTS topics. The content appears to be present in the DOM (view-lines show text) but Monaco's internal model is NOT updated. When the user saves, Monaco commits the old/empty content.

**Only reliable path:** User manually types in the code editor to trigger React's onChange handler, then pastes content.
