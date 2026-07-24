# Codex Windows Sandbox Error 1312

## Symptom

Running `codex exec "<prompt>"` on Windows fails immediately with:

```
exec error: windows sandbox: runner failed during SpawnChild:
CreateProcessAsUserW failed: 1312
(A specified logon session does not exist. It may already have been terminated.)
```

## Cause

Codex's sandbox runs as a Windows service (or elevated process) that attempts
to create a child process in the user's logon session via `CreateProcessAsUserW`.
When invoked from certain terminal contexts (e.g. git-bash, Windows Terminal,
or from another agent like Hermes), the parent process may not have a valid
Windows logon session token that the sandbox can duplicate.

This is **not** an auth issue — Codex's OAuth token is valid. The model loads
successfully, but the sandbox cannot spawn shell commands.

## Affected Environments

- git-bash (MSYS2 / MinGW) running from Hermes terminal
- Any non-Win32-native parent process
- Scheduled tasks or services that run without an interactive logon session

## Fix

Use `--yolo` flag to bypass the sandbox entirely:

```bash
codex exec --yolo "<prompt>"
```

This runs Codex directly on the host without sandboxing. File changes apply
immediately with no approval prompt (`--yolo` implies `--no-approve`).

### Safety Considerations

- `--yolo` gives Codex full access to your filesystem
- Use only in trusted repositories
- Pair with `git status` / `git diff` to review changes after execution
- For sensitive work, prefer a VM or separate worktree

### Recommended Invocation (Windows + ChatGPT OAuth)

```bash
codex exec --yolo --model gpt-5.5 "<prompt>"
```

- `--yolo`: bypasses broken Windows sandbox
- `--model gpt-5.5`: required because `gpt-5.6-sol` is unavailable on ChatGPT accounts
- `pty=true`: required when calling from Hermes terminal

## Alternative: Fix the Sandbox (Untested)

If you need sandbox mode, you can try:
1. Run Codex from PowerShell or CMD (not git-bash)
2. Run the terminal as the same user that started the Codex daemon
3. Set `[windows] sandbox = "elevated"` in `config.toml`
4. Launch Codex from an interactive desktop session, not a background service
