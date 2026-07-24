# Windows stuck-state flag notes

## Observed flag

```
C:/Users/kevin/AppData/Local/hermes/hermes-agent/.update-incomplete
```

## Behavior

When present, many Hermes CLI commands run an automatic recovery step before the real command. On this machine, the recovery repeatedly fails because:

- `hermes.exe` is locked by the running session
- the venv pip install step tries to replace `hermes.exe`
- Windows returns `Access is denied`

That produces a long repeated banner on every invocation.

## Safe workaround

If repeated auto-recovery is blocking other work and the update cannot finish cleanly in-session, move/rename the flag rather than repeatedly retrying the failed installer:

```bash
mv ~/AppData/Local/hermes/hermes-agent/.update-incomplete \
   ~/AppData/Local/hermes/hermes-agent/.update-incomplete.disabled-by-hermes-$(date +%Y%m%d-%H%M%S)
```

## What this does

- Stops the recurring recovery banner
- Does **not** finish the update
- Leaves the session usable while the exe replacement is deferred to a clean restart

## Best next step

Exit the current Hermes session and run `hermes update` from a fresh terminal where no running Hermes process holds the lock.
