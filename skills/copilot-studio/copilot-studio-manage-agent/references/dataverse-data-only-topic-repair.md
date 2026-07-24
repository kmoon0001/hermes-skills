# Dataverse data-only topic repair workaround

Use this when Copilot Studio local YAML has already been validated, the user cannot complete the Copilot Studio API/LSP interactive login, and `pac`/Azure auth can still access Dataverse.

## Pattern

1. Get a Dataverse token for the target org with Azure CLI:
   - resource: `https://<org>.crm.dynamics.com`
   - tenant: target tenant GUID
2. Query live topic components:
   - table: `botcomponents`
   - filter: `_parentbotid_value eq '<botId>' and componenttype eq 9`
   - select: `botcomponentid,name,schemaname,content,data`
3. Back up exact live records before patching.
4. Prefer targeted edits to `data` only for malformed YAML/metadata repairs.
5. Verify by re-querying `data` and scanning for the exact repaired condition.
6. Publish with PAC:
   - `pac copilot publish --environment <orgUrl> --bot <botId>`
7. Confirm visibility with:
   - `pac copilot list --environment <orgUrl>`

## Important pitfalls

- The `content` field may contain a leading Markdown-style header such as `# Topic Name`. Direct PATCH to `content` can be rejected by the Dataverse/Copilot plugin with: `Unexpected character encountered while parsing value: #. Path '', line 0, position 0.`
- If `content` PATCH is rejected, do not keep retrying whole-record replacement. Patch only `data` with the minimal change and verify.
- `pac copilot status` may be unreliable in some tenants/CLI versions, returning an attribute error such as `bot entity doesn't contain attribute ... componentstate_Property`. Treat `pac copilot list` plus successful publish output as the safer verification path.
- `pac copilot status` uses `--bot-id`, while `pac copilot publish` accepts `--bot` in observed PAC CLI 2.7.4.
- The LSP-backed `manage-agent.bundle.js validate` path can fail if the VS Code extension runtime dependency `vscode-jsonrpc/node` is missing. If that happens, use a local YAML syntax sanity check before any direct Dataverse patch, but do not label the LSP as permanently broken.

## Minimal repair example

For duplicate malformed descriptions in live `data` payloads:

```python
import re

def fix_data(s: str) -> tuple[str, bool]:
    before = s
    # Keep first top-level description; remove indented duplicate line.
    s = re.sub(r"(?m)^(description:\\s*[^\\r\\n]*)(\\r?\\n)[ \\t]+description:\\s*[^\\r\\n]*", r"\\1", s)
    # Optional mojibake cleanup for known pasted emoji corruption.
    for bad, good in {
        'âš ï¸': 'Warning:',
        'âš ': 'Warning:',
        'âœ‹': 'Select',
        'ðŸƒ': 'Run',
        'ðŸ—£ï¸': 'Communicate',
        'ðŸ¥': 'Facility',
    }.items():
        s = s.replace(bad, good)
    return s, s != before
```

Always back up live JSON before PATCH and require HTTP 204 for success.