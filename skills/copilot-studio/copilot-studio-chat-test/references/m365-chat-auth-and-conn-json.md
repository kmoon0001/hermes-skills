# M365 integrated-auth chat testing: conn.json + device-code fallback

Use this when `chat-with-agent.bundle.js --detect-only` fails because a hand-built/copied Copilot Studio workspace is missing `.mcs/conn.json`, or when M365 SDK chat reaches Microsoft auth and stalls.

## Minimal `.mcs/conn.json`

`chat-with-agent.bundle.js` requires `<agentDir>/.mcs/conn.json` plus `settings.mcs.yml`.

A minimal working shape is:

```json
{
  "EnvironmentId": "<environment-guid>",
  "AgentId": "<bot-guid>",
  "DataverseEndpoint": "https://<org>.crm.dynamics.com/",
  "AccountInfo": {
    "TenantId": "<tenant-guid>",
    "Username": "<user-upn>"
  }
}
```

Get stable values from `agent.manifest.json` and live Dataverse/PAC output. For Copilot Studio runtime detection, the live bot schema name may differ from local `settings.mcs.yml`; trust `--detect-only` output.

## Correct chat tester syntax

The bundle does **not** use `send --workspace`. Use positional message plus `--agent-dir`:

```bash
cd "D:/my agents copilot studio/pipeline"
node scripts/chat-with-agent.bundle.js --detect-only \
  --agent-dir "D:/my agents copilot studio/<Agent Folder>"

node scripts/chat-with-agent.bundle.js "hello" \
  --agent-dir "D:/my agents copilot studio/<Agent Folder>" \
  --client-id <public-client-app-id>
```

If the script accidentally finds `pipeline/templates/agents`, it means the wrong syntax/path was used; rerun with explicit `--agent-dir`.

## Device-code fallback for stuck localhost auth

If localhost redirect auth opens but does not complete, seed the same MSAL cache with the `copilot-studio-run-eval` device-code helper. Run it with `pty=true`; non-PTY background runs fail with `stdin is not a tty`.

```bash
cd "D:/my agents copilot studio/pipeline"
node "C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/skills/copilot-studio/copilot-studio-run-eval/scripts/device-code-auth.cjs" \
  <tenant-id> \
  <client-id> \
  https://api.powerplatform.com/.default \
  test-agent \
  "D:/my agents copilot studio/pipeline/package.json"
```

Give the user only:
- `verificationUri`
- `userCode`

Do not ask for passwords or MFA codes. Device codes expire quickly; if expired, kill/restart the helper and provide a fresh code.

## Verification after adding `.mcs/conn.json`

Because this is a local metadata edit, run ad-hoc verification if there is no canonical suite:

1. Create a temp script under `%TEMP%`/`C:\Users\kevin\AppData\Local\Temp` with prefix `hermes-verify-` using `tempfile`.
2. Validate `conn.json` parses and expected IDs match.
3. Run `chat-with-agent.bundle.js --detect-only --agent-dir <agentDir>`.
4. Confirm `status: ok`, expected mode (`m365` for integrated auth), `authenticationmode`, and live schema name.
5. Delete the temp verifier and report this as ad-hoc verification, not suite green.
