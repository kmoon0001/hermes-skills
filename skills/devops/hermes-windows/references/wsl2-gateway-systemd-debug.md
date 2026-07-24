# WSL2 Gateway: systemd User-Bus Debugging

## Context

Kevin runs Hermes Agent on Windows 10 with WSL2 Ubuntu. Originally
used Hermes inside WSL. The gateway service install created a user-level
systemd unit. At some point the systemd user bus stopped working,
causing stale timeout warnings.

## Symptoms

- `systemctl --user status hermes-gateway` → "Failed to connect to
  user scope bus via local transport: No such file or directory"
- `journalctl --user-unit=user@1000` → hangs/times out
- `loginctl enable-linger kevin` → hangs/times out
- `/run/user/1000/bus` socket does NOT exist
- Other files in `/run/user/1000/` exist: `dbus-1/`, `pulse/`, `wayland-0`
- `systemctl status user@1000` → "could not be found" (system-level)

## Root Cause

Running `wsl -d Ubuntu -- bash -c '...'` from Windows does NOT create
a proper PAM login session. The systemd user instance (`user@1000`)
never starts its D-Bus bus socket. Without the bus, ALL `systemctl --user`
commands fail silently.

The system-level systemd works fine (PID 1 is systemd, system services
start). Only the user session is broken.

## WSL Configuration

`/etc/wsl.conf` was correct:
```ini
[boot]
systemd=true

[user]
default=kevin
```

systemd version: 259 (259.5-0ubuntu3)

## Service File

Located at: `~/.config/systemd/user/hermes-gateway.service`
Symlinked into: `~/.config/systemd/user/default.target.wants/`

Key settings:
- `Type=simple`
- `TimeoutStopSec=210`
- `Restart=always`, `RestartSec=60`
- `ExecStart=...python -m hermes_cli.main gateway run --replace`

## Resolution

1. Removed stale service files manually:
   ```bash
   rm -f ~/.config/systemd/user/hermes-gateway*.service
   rm -f ~/.config/systemd/user/default.target.wants/hermes-gateway*.service
   ```

2. Started gateway via tmux (bypasses systemd entirely):
   ```bash
   tmux new-session -d -s hermes \
     "PATH=/home/kevin/.hermes/hermes-agent/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
      HERMES_HOME=/home/kevin/.hermes \
      VIRTUAL_ENV=/home/kevin/.hermes/hermes-agent/venv \
      python -m hermes_cli.main gateway run --replace"
   ```

3. Gateway started successfully (with warnings about no platforms
   configured and no user allowlists).

## Key Commands from Windows Side

```bash
# View gateway logs
wsl -d Ubuntu -- tmux capture-pane -t hermes -p | tail -30

# Stop gateway
wsl -d Ubuntu -- tmux kill-session -t hermes

# Restart gateway
wsl -d Ubuntu -- tmux kill-session -t hermes 2>/dev/null
wsl -d Ubuntu -- bash -c 'tmux new-session -d -s hermes "PATH=... python -m hermes_cli.main gateway run --replace"'
```

## Lesson Learned

When systemd user services break in WSL2 (missing bus socket), don't
waste time trying to restart user@1000 from outside WSL. The PAM
login chain is the bottleneck. Go straight to tmux — it's what the
Hermes installer recommends for WSL anyway.
