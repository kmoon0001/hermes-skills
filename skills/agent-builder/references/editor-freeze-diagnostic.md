# Copilot Studio Authoring-Canvas Freeze — Root Cause & Recovery

Session-derived diagnostic (2026-07-16, Pacific Coast Documentation Defense Agent,
Therapy Documentation Compliance Audit and Defense topic). Keep this reference
current when new editor-freeze causes are found.

## Symptom
- Topic opens but the authoring canvas is BLANK (no nodes render).
- "Code editor won't load."
- Agent still WORKS in the test pane (responds to messages).
- `flow-editor-container` exists in the UIA tree but has NO child nodes.

## Root cause (the trap)
The topic YAML contained an editor-INVALID node the deserializer chokes on, while
still being PUBLISH-valid (runtime accepts it). The specific offender this session:

```yaml
# BROKEN — do NOT ship this in a topic
- kind: Question
  id: question_file_upload
  variable: init:Topic.UploadedFiles
  prompt: Upload your documentation
  entity:
    inputType: file[]          # <-- editor cannot deserialize file[]
  # bound to turn.uploadedFiles  <-- same problem
```

`inputType: file[]` + `property: turn.uploadedFiles` = valid at publish, agent runs,
but the AUTHORING CANVAS renders blank. There is no error toast — it just silently
fails to draw nodes. This is why a 204 PATCH + successful publish is NOT proof of a
healthy topic.

## The fix
Replace with the File+Text dual-input 3-branch ConditionGroup (see SKILL.md §3).
The platform auto-attaches uploaded file content to a `SearchAndSummarizeContent`
node via `First(System.Activity.Attachments)` — you do NOT need a `file[]` Question
node to accept uploads.

## Recovery path when already frozen
1. Check for a stuck "Publishing..." modal overlay first — it can mask a canvas that
   would otherwise render. Query the window state for `flow-editor`/modal; close any
   "Your agent is being published" modal (it blocks the canvas).
2. Close the test pane if it's covering the canvas.
3. Hard-reload the tab (Ctrl+Shift+R). NOTE: on this machine Ctrl+Shift+R via
   cua-driver foreground sometimes MINIMIZES the Chrome window — a minimized window
   cannot be screenshotted ("cannot capture minimized window ... no rendered content").
   Restore it by clicking the Copilot Studio tab in the taskbar before re-capturing.
4. If canvas is STILL blank after reload + modal-close + test-pane-close, the server
   `data` genuinely has an editor-invalid node. Confirm with `pac org fetch`:
   ```
   # FetchXML for the topic botcomponentid, then:
   pac org fetch -xf query.xml > topic_now.xml
   # search the result for: file[] | turn.uploadedFiles | inputType
   ```
   If those strings are present, that's the broken node.
5. Restore: PATCH `data` back to the known-good backup YAML (the version that
   rendered before the bad edit), then re-publish, then re-run the editor-render gate.

## Write-channel reality on this machine (2026-07-16)
- `az account get-access-token` → org 401 (CA/MFA challenge). Cannot curl-PATCH.
- `pac auth create --environment https://pccapackage.crm.dynamics.com/` → SUCCESS,
  cached identity, no MFA. `pac org who` + `pac org fetch` WORK (read + fetch).
- `pac` has NO generic PATCH/record-update verb; its token is in-memory (no
  msal.cache file to extract).
- Browser page cannot cross-origin PATCH crm.dynamics.com (CORS).
- => When `az` is 401-blocked, the reliable WRITE channel is the Copilot Studio UI
  code editor (paste corrected YAML) OR wait for a working `az login`. Reads/fetch/
  publish all go through `pac`.

## The durable lesson
"Published + 204 + agent responds in test" is NOT the same as "editor is healthy."
Always run the editor-render gate (confirm canvas draws nodes) after any topic edit.
A schema can be runtime-valid and authoring-invalid at the same time.
