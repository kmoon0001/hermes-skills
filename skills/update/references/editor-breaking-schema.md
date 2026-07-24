# Editor-Breaking Schema (Dataverse PATCH → blank canvas)

## Symptom
After a Dataverse PATCH to a topic `data` field (HTTP 204) + `pac copilot publish` (success), the **Copilot Studio authoring canvas renders blank/frozen** and the **code editor will not load**. The test pane may still work (agent responds), so it looks like only the editor is broken — but the root cause is the `data` schema.

## Root cause
The Copilot Studio runtime/publish pipeline accepts a broader YAML schema than the **authoring UI's deserializer**. A node type/property the editor can't build nodes from causes a silent deserialize failure → empty canvas, no error banner.

## Confirmed case (2026-07-16, Pacific Coast "Therapy Documentation Compliance Audit and Defense" topic)
- Added a Question node: `inputType: file[]`, `property: turn.uploadedFiles`.
- PATCH returned 204; `GET` then showed `turn.uploadedFiles` present; `pac copilot publish` succeeded.
- Test pane: agent responded ("Loading up...") — runtime accepted it.
- Authoring canvas: blank. Vision + UIA confirmed `flow-editor-container` had no child nodes. Code editor would not open.
- Diagnosis: the editor cannot deserialize `inputType: file[]` / `turn.uploadedFiles` in a Question node → blank canvas. This is the "topic is total frozen / code editor wont load" report.

## Why publish succeeded but editor failed
Publish validates against the runtime schema; the editor validates against its (stricter) authoring schema. They are NOT the same. 204 + publish success ≠ editor-health.

## Recovery
1. Restore the known-good `data` backup (the pre-PATCH topic YAML) via Dataverse PATCH.
   - Requires working Dataverse auth (`az account get-access-token --resource https://<org>.crm.dynamics.com`). If that returns 401 (CA/MFA challenge), the restore is blocked until the user re-auths (`az login --tenant <tid>`).
2. After restore, confirm the canvas renders nodes again.

## Re-implementing file upload WITHOUT breaking the editor
The `file[]` / `turn.uploadedFiles` approach is editor-incompatible in this authoring version. Prefer one of:
- **UI-native upload path:** keep the text Question but route the upload through the test-pane attachment path that populates `System.Activity.Attachments`, and condition on `CountRows(System.Activity.Attachments) > 0` (the classic 3-branch pattern). This renders fine in the editor.
- **Create/Update variable node** with a schema the canvas supports, then reference that variable in the SASC/condition nodes.
- Validate the chosen schema by opening the topic in the editor (render check) BEFORE publishing — not after.

## Detection heuristic
If a topic `data` PATCH "succeeds" but the user reports a frozen topic or dead code editor, suspect an editor-incompatible schema FIRST. Re-PATCH the backup, then test the schema in the editor before re-publishing.
