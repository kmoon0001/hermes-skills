# Copilot Studio Knowledge Upload via Computer Use — Patterns and Pitfalls

## Summary

When agent-built knowledge source files (.md, .pdf) need uploading to a Copilot Studio agent, the only path is through the Copilot Studio UI — there is no API for file uploads. Computer use automation of this workflow is unreliable due to Chrome AX tree limitations.

## The UI-Only Constraint

Knowledge file uploads (componenttype 14 — FileAttachmentComponentMetadata) cannot be created via Dataverse API. The `data` field stores a blob reference, not the file content. Files must be uploaded through: **Copilot Studio UI → Knowledge → + Add knowledge → Upload files**.

Markdown (.md) files work as knowledge sources — they index cleanly without formatting artifacts and are well-suited for structured clinical content (scenario banks, competency matrices, scoring rules).

## Upload-Ready Manifest Pattern

For bulk uploads (3+ files), create a `UPLOAD-MANIFEST.md` alongside the knowledge source files:

| Column | Purpose |
|--------|---------|
| File | Exact filename |
| Display Name | Human-readable name (NOT raw filename) |
| Description | 1-3 sentences: what it covers, why authoritative, retrieval terms |

Upload workflow: open bot → Knowledge → Add knowledge → upload each file → paste Display Name + Description from manifest → toggle Official source ON → Save → verify Ready status.

## Automation Failure: Chrome AX Tree Limitation

SPA web apps like Copilot Studio render their page content via JavaScript — this content is NOT exposed to the Windows UIA accessibility tree. Even with `max_elements=200`, only the browser chrome (toolbar, bookmarks, tabs) and high-level Copilot Studio navigation (left sidebar icons, top horizontal nav tabs) appear in `get_window_state`. The page content area (navigation sidebar, Knowledge cards, upload buttons, description fields) is invisible to AX-based element targeting.

**AX tree vs. actual content:** On the Overview page, the AX tree captures the top nav tabs (Overview, Knowledge, Tools, Agents, Topics, etc.) with their labels and frame positions. But the main content area (Knowledge card, Details card, Test pane) appears as empty generic Groups with no children. The page content is there visually (confirmed via screenshot + vision analysis) but is not traversable via UIA.

## Automation Failure: Knowledge Page Renders Blank

The Copilot Studio Knowledge page (`/bots/<id>/knowledge`) specifically fails to render in captured screenshots — the entire page content area appears white/blank even after page refresh. The window title changes from "Knowledge - Pacific Coast..." to just "Microsoft Copilot Studio" after refresh, indicating the SPA hydration failed or the content area isn't painting. **The Overview page (`/overview`) renders correctly** and has a "+ Add knowledge" button in the Knowledge card — use that instead.

## Automation Failure: Chrome Address Bar Input

Both `set_value` (ValuePattern unavailable) and `click` + `type_text` with foreground delivery fail to change the Chrome address bar URL. The type_text tool reports success but the AX tree still shows the old URL value. The only reliable navigation method is `launch_app` with `urls` parameter, which opens URLs via ShellExecuteEx.

## Navigation Method: `launch_app` with `urls`

```json
mcp_cua_driver_launch_app({"urls": ["https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/knowledge"]})
```

This opens the URL in the existing Chrome window as a new tab. Direct URL navigation to specific pages works reliably — use `/overview`, `/knowledge`, `/topics` suffixes.

## CLI and API Discovery Failures

### PAC CLI broken on missing .NET

`pac copilot list` may fail with: `The library 'hostpolicy.dll' required to execute the application was not found`. This is a .NET SDK installation issue. Fall back to Dataverse REST API.

### manage-agent.bundle.js list-agents requires interactive login

The `list-agents` command opens a browser for interactive Microsoft login — times out in non-interactive contexts (30s timeout).

### Environment ID DNS resolution

Copilot Studio environment IDs (e.g. `a944fdf0-0d2e-e14d-8a73-0f5ffae23315`) do NOT resolve via `<envId>.crm.dynamics.com` — DNS fails. `az account get-access-token` succeeds with the resource identifier (Azure AD recognizes it) but `az rest` and Python `urllib` fail on DNS resolution. Use the known org URL from `.mcs/conn.json` or discover bots by querying across known org URLs.

### Python `_validate_path` with OData URLs

Python 3.11+ `http.client._validate_path` rejects URLs containing spaces or control characters in OData `$filter` expressions. Use `az rest` for all GET queries (handles encoding internally) or URL-encode paths carefully.

## Bot ID Mismatch

The Copilot Studio URL GUID (e.g., `7667e9b4-cb86-f111-ab0f-70a8a5ae56f8` from `.../bots/<id>/overview`) is NOT the Dataverse `botid`. Query `bots?$select=name,botid` to find the real Dataverse bot ID. Newly created agents may not appear in the Dataverse `bots` table until first published — API operations are impossible until then.

## Effective Strategy

1. Build knowledge source files locally (.md for text, .pdf for formatted docs)
2. Create UPLOAD-MANIFEST.md with display names and descriptions
3. Hand off to user for UI upload (2-3 minutes for bulk uploads)
4. Do NOT attempt Chrome automation for this workflow — the AX tree limitations make it unreliable
5. After upload, the agent must be published before Dataverse API operations work
