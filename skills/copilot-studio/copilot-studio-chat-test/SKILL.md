---
name: copilot-studio-chat-test
description: Test published Copilot Studio agents by sending chat messages and receiving responses via DirectLine or M365 SDK.
---

# Chat Test Agent

Test published Copilot Studio agents by sending messages and receiving responses.

## Step 1: Detect Auth Mode

```bash
node "D:/my agents copilot studio/pipeline/scripts/chat-with-agent.bundle.js" --detect-only [--agent-dir <path>]
```

Parse JSON output:
- **directline** mode (authenticationmode 1 or 3): no auth needed, use chat-directline
- **m365** mode (authenticationmode 2): integrated auth, use chat-sdk

### Missing `.mcs/conn.json` fallback
If `chat-with-agent.bundle.js --detect-only` fails with `No .mcs/conn.json found`, do not abandon the chat test if live metadata is already known. Create a minimal `<agent>/.mcs/conn.json` from trusted local manifest/Dataverse values, then re-run detect-only:

```json
{
  "EnvironmentId": "<environment-guid>",
  "AgentId": "<bot-guid>",
  "DataverseEndpoint": "https://<org>.crm.dynamics.com/",
  "AccountInfo": {
    "TenantId": "<tenant-guid>",
    "Username": "<signed-in-user-upn>"
  }
}
```

After creating it, run a focused ad-hoc verification with a temporary `hermes-verify-*.py` under the OS temp directory: validate JSON/expected IDs and run `chat-with-agent.bundle.js --detect-only --agent-dir <agent>`. Report this as ad-hoc verification, not full suite green, and clean up the temp script.

**Additional harness requirement:** some `chat-with-agent.bundle.js` builds also require `settings.mcs.yml` at the agent root even when `.mcs/conn.json` exists. If detect-only advances from `No .mcs/conn.json` to `No settings.mcs.yml`, do not report chat/E2E as verified from the ad-hoc folder. Use a real cloned workspace with `settings.mcs.yml`, reconstruct that file only from trusted live/manifest metadata, or test through the Copilot Studio UI instead.

## Step 2a: DirectLine Chat (no auth / manual auth)

```bash
node "D:/my agents copilot studio/pipeline/scripts/directline-chat.bundle.js" send --workspace <path> --message <text> [--conversation-id <id>]
```

Multi-turn: reuse `conversation-id` from response in subsequent calls.

## Step 2b: M365 SDK Chat (integrated auth)

Requires Azure App Registration:
- Platform: Public client / Native
- Redirect URI: `http://localhost`
- API permissions: Power Platform API → `CopilotStudio.Copilots.Invoke`

Correct current bundled syntax is positional message + `--agent-dir`:
```bash
node "D:/my agents copilot studio/pipeline/scripts/chat-with-agent.bundle.js" "<message>" \
  --agent-dir <path> \
  --client-id <id> \
  [--conversation-id <id>]
```

Do not use `send --workspace ... --message ...` unless the script has been updated to support that syntax; older bundles parse it incorrectly and may select `pipeline/templates/agents`.

### Integrated-auth permission blocker
If the user cannot complete Microsoft/device-code sign-in or says they do not have access, stop generating repeated device codes. First verify detect-only, then diagnose permissions. Existing PAC/Azure tokens may list/patch/publish the bot but still fail live chat invocation with `InsufficientDelegatedPermissions` because the app/caller lacks delegated `CopilotStudio.Copilots.Invoke`.

Detailed raw-endpoint diagnostic and message wording: `references/integrated-auth-invoke-permissions.md`.

When the user asks for a workaround because the UI worked previously, use the decision tree in `references/integrated-auth-workaround-decision-tree.md`: prefer Copilot Studio UI/evaluation/test-pane automation with a real browser session; only do a temporary auth/channel flip after explicit approval and with a rollback plan.

Repair boundary:
- Try to inspect/create an app registration only if the user asks to fix invocation permissions.
- If `az ad app create` fails with `Insufficient privileges to complete the operation`, do not keep trying local workarounds; the fix requires an Entra admin or an existing app registration with the Power Platform API delegated `CopilotStudio.Copilots.Invoke` scope.
- Do not silently switch a live integrated-auth bot to no-auth/DirectLine for testing. That changes security posture; require explicit user approval and a rollback plan.

## Error Handling
  --client-id <id> \
  [--conversation-id <id>]
```

If the workspace was not cloned by the VS Code extension and is missing `.mcs/conn.json`, create the minimal metadata file from the manifest/live bot data, then verify with `--detect-only`. See `references/m365-chat-auth-and-conn-json.md`.

If localhost browser auth stalls, seed the `test-agent` cache with the device-code helper from `copilot-studio-run-eval` using a PTY-backed process, then rerun the chat command. Device codes expire quickly; restart the helper for a fresh code rather than troubleshooting an expired one.

## Verification

After adding `.mcs/conn.json` or changing local chat metadata, and when no canonical test/lint suite exists, create a temporary `hermes-verify-*.py` script under the OS temp directory. It should validate the JSON fields and run `chat-with-agent.bundle.js --detect-only --agent-dir <agentDir>`. Clean up the temp script and report the result as **ad-hoc verification**, not suite green.

## Live-UI test-pane upload testing — native file dialog fragility

When verifying an upload fix through the Copilot Studio test pane (the user is at the machine; integrated-auth bots cannot be driven via DirectLine), the paperclip opens a native Windows "Open" dialog. Driving it via cua-driver/UIA is fragile:

- **Ctrl+click modifier fails:** `mcp__cua_driver__click` with `modifier: ["ctrl"]` on a list item returns `Invalid window handle` on this dialog (the UIA cache/modifier path errors). Plain clicks work but replace the selection instead of adding.
- **Element cache expires between calls:** `get_window_state` caches element indices per call; a plain `click` on a cached index in a *later* call also returns `Invalid window handle` because the dialog's window handle changed. Re-capture immediately before each action, and do multi-select via the File-name box instead: `set_value` the full path on the File name edit box, then click Open.
- **The dialog can self-close** on a failed modifier click, forcing a re-open + re-capture.

**Practical rule:** For a live multi-file upload proof, hand the final click-test to the user at the machine (they click paperclip → select files → Send). Drive programmatically only when you can capture-and-act in the SAME tool call sequence. Always refresh the Copilot Studio tab (Ctrl+Shift+R) after a Dataverse PATCH so the authoring canvas resyncs — the canvas may show stale pre-fix structure even though the published `data` field has the new logic.

See `copilot-studio-author-topic` `references/file-upload-question-pattern.md` for the upload-Question schema and the verified fix pattern.

## Error Handling
  --agent-dir "<agent workspace>" \
  --client-id <id> \
  [--conversation-id <id>]
```

If this starts a localhost interactive login, run it with a PTY/background process while the browser sign-in completes. Preserve the full auth URL query string when opening it; if it hangs or Microsoft login strips parameters, seed the `test-agent` MSAL cache with the device-code helper from `copilot-studio-run-eval` and retry the chat command.

## Reference Details

- `references/m365-chat-conn-json-and-auth.md` — tested fallback for reconstructing `.mcs/conn.json`, correct M365 chat command syntax, device-code/PTY auth pitfalls, and ad-hoc verification expectations.

## Error Handling

| Error | Cause | Resolution |
|---|---|---|
| No `agent.mcs.yml` | No agent in workspace | Clone agent first |
| No `.mcs/conn.json` | Not cloned via VS Code | Clone with VS Code Copilot Studio extension |
| Token expired | Auth token expired | Re-authenticate |
| `No .mcs/conn.json found` | Workspace was not cloned through VS Code extension or metadata file is missing | Create minimal `.mcs/conn.json` from known tenant/environment/agent/Dataverse values, then run detect-only as ad-hoc verification |
| Command selects `pipeline/templates/agents` | Used unsupported `send --workspace` syntax with older bundled script | Use positional message + `--agent-dir <agent path>` |
| Raw chat endpoint returns `403 InsufficientDelegatedPermissions` | Caller/app can access Dataverse/PAC but lacks delegated invoke permission for integrated-auth chat | Stop auth loops; require account/app with `CopilotStudio.Copilots.Invoke`, or test through UI/Teams/DirectLine alternative |
