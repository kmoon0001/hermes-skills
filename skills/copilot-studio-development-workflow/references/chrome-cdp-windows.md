# Chrome Remote Debugging on Windows (git-bash / MSYS)

## Pitfall: `start` Command Breaks Terminal

Using bare `start` in MSYS/git-bash permanently kills the terminal session.
Every subsequent command returns exit 130 (SIGINT) — unrecoverable.

```bash
# WRONG — breaks terminal permanently
start "" "/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9223

# RIGHT — explicit cmd.exe wrapper
cmd.exe //c start "" "C:/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9223
```

## Kill and Relaunch Pattern

```bash
# Kill all Chrome (double-slash in MSYS)
taskkill //F //IM chrome.exe

# Wait for processes to die
sleep 3

# Relaunch with debugging (via cmd.exe)
cmd.exe //c start "" "C:/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9223

# Wait for startup
sleep 5

# Verify
curl -s http://127.0.0.1:9223/json/version
```

## Verify Port Is Listening

```bash
netstat -an | grep 9223
curl -s --connect-timeout 5 http://127.0.0.1:9223/json/version
```

## taskkill Syntax in MSYS

Windows `taskkill` requires double-slash flags in MSYS:
- `taskkill //F //IM chrome.exe` (not `/F /IM`)
- Single slash gets parsed as MSYS path conversion and fails with "Invalid argument/option"
