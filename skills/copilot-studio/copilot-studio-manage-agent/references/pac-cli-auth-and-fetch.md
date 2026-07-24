# pac CLI as Dataverse Auth + Read Path (when `az` 401s)

Session-verified 2026-07-16 on PacCoast agent (PCCA Package env 077422cf...).

## When to use
`az account get-access-token --resource https://<org>.crm.dynamics.com` returns **HTTP 401** (CA / MFA challenge on the resource) AND a cached Azure identity exists. `pac auth create` authenticates with that cached identity — **no interactive MFA prompt**, unlike `az login` which may pop a device-code / number prompt the user cannot complete in the terminal.

## Authenticate pac to the target org
```bash
pac auth create --environment "https://<org>.crm.dynamics.com/"
pac org who          # confirms live Dataverse connection (org id, env id, user)
pac env list         # lists pac auth profiles / orgs
```
`pac org who` printing the org = authenticated Dataverse session established.

## READ path: pac org fetch (verified working on botcomponents)
The earlier skill note claiming `pac org fetch` crashes on `botcomponents` is OUTDATED — it reads the `data` field fine.
```bash
# Write FetchXML to a Windows-path file (NOT /tmp — may not resolve under MSYS/git-bash)
cat > "C:/Users/kevin/Desktop/_f.xml" <<'EOF'
<fetch>
  <entity name="botcomponent">
    <attribute name="data" />
    <attribute name="versionnumber" />
    <filter><condition attribute="botcomponentid" operator="eq" value="<guid>" /></filter>
  </entity>
</fetch>
EOF
pac org fetch -xf "C:/Users/kevin/Desktop/_f.xml" > out.xml
```
Pitfalls:
- `--xmlFile` alias is `-xf`. Do NOT add `top` attribute — pac injects paging and rejects it ("can't be specified with paging").
- `/tmp/...` paths may not resolve; use a Desktop Windows path.
- The `data` attribute returns as a YAML dump in the XML body (read it back from `out.xml`).

## WRITE path: pac CANNOT PATCH
`pac` has no generic record-update / PATCH verb. Its token is held **in-memory only** (no `msal.cache` file anywhere under `%LOCALAPPDATA%`), so it cannot be extracted for `curl`/Python either.
Implications when a Dataverse write is needed (e.g. revert a broken `botcomponent.data`):
1. `pac org fetch` to read + back up the current `data` (do this BEFORE any write attempt).
2. If `az` is 401-blocked, you cannot write via pac alone. Options:
   (a) User runs `az login --tenant <tenantGuid>` to clear the CA challenge (pops MFA the user approves in browser, no terminal typing).
   (b) Copilot Studio browser session + CDP token capture -> Dataverse PATCH (see `references/browser-token-dataverse-publish-fallback.md`).
3. If `az` works, use the Dataverse REST PATCH via `az rest` (recommended) or Python urllib (see SKILL.md "Direct Dataverse Push/Create Workflow").

## Publish still works through pac
```bash
pac copilot publish --environment "https://<org>.crm.dynamics.com/" --bot "<full-bot-guid>"
```

## Don't assume `az` is the only Dataverse token source
`pac auth create` is often the faster unblock when `az` hits a CA/MFA wall and the user can't complete interactive login.
