# M365 Chat Test: conn.json Reconstruction and Auth Pitfalls

Use this when testing a published Copilot Studio agent with `chat-with-agent.bundle.js` and the local workspace was not cloned by the VS Code extension.

## Symptom

`--detect-only` fails with:

```text
No .mcs/conn.json found at <agent>/.mcs/conn.json. Is this a Copilot Studio agent cloned with the VS Code extension?
```

## Minimal `.mcs/conn.json`

If the agent identity is already trusted from `agent.manifest.json`, Dataverse, or PAC output, create:

```json
{
  "EnvironmentId": "<environment-guid>",
  "AgentId": "<bot-guid>",
  "DataverseEndpoint": "https://<org>.crm.dynamics.com/",
  "AccountInfo": {
    "TenantId": "<tenant-guid>",
    "Username": "<upn>"
  }
}
```

Then verify:

```bash
cd "D:/my agents copilot studio/pipeline"
node scripts/chat-with-agent.bundle.js --detect-only --agent-dir "<agent workspace>"
```

Expected integrated-auth result:

```json
{
  "status": "ok",
  "mode": "m365",
  "authenticationmode": 2,
  "schemaName": "<live schema name>"
}
```

## Correct send syntax

The script expects the message as a positional argument and the agent path as `--agent-dir`:

```bash
node scripts/chat-with-agent.bundle.js \
  "hello" \
  --agent-dir "<agent workspace>" \
  --client-id <client-id>
```

Do not use `send --workspace --message`; that belongs to other tooling and can cause the script to auto-discover the wrong template agent.

## Auth handling

For M365/integrated-auth agents:
- If localhost interactive login starts, keep the process alive with PTY/background tracking while the user signs in in the browser.
- Preserve the complete auth URL query string. Wrapped terminal output may split the URL across lines; reconstruct it before opening.
- If localhost auth stalls, seed the same `test-agent` MSAL cache with the `copilot-studio-run-eval` device-code helper, then retry the chat command.
- Device-code helper needs a TTY. Start it with `pty=true` if running through Hermes background process tools; otherwise it can fail with `stdin is not a tty`.

## Verification expectation

When creating `.mcs/conn.json`, run a focused temporary verifier named `hermes-verify-*.py` under the OS temp directory. It should validate JSON/expected IDs and run detect-only. Clean it up and report it as ad-hoc verification, not canonical suite green.
