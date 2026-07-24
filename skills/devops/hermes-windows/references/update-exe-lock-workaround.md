# Update exe-lock workaround — full session transcript

## Symptom

```
hermes update
→ error: failed to remove file `...\Scripts\hermes.exe`:
  The process cannot access the file because it is being used by another process. (os error 32)
```

The tool then retries with optional extras, fails again, and leaves an `⚠ A previous \`hermes update\` was interrupted mid-install` banner on every subsequent `hermes version`.

## Root cause

On Windows, a running `hermes.exe` holds an exclusive file lock. The Python `pip install -e .` step can't overwrite the binary in-use. This is a Win32 constraint — the same issue happens with any Python CLI entry-point on Windows.

## Workaround

### Step 1 — Install the Python packages directly via uv

From inside the running session, bypass `hermes update`'s wrapper:

```bash
cd ~/AppData/Local/hermes/hermes-agent
uv pip install -e . --no-build-isolation --no-deps --force-reinstall
```

This replaces the `.pth` file and metadata. `hermes.exe` isn't touched.

If uv complains `No module named 'setuptools'`:

```bash
uv pip install setuptools wheel
```

Then retry the install.

### Step 2 — Clear the interrupted-update marker

```bash
rm ~/AppData/Local/hermes/hermes-agent/.update-incomplete
```

Now `hermes version` returns clean output.

### Step 3 — (Optional) Refresh the launcher

Exit the session and run `hermes update` from a fresh terminal window. No other process holds the lock, so the exe replacement succeeds.

## Verification

```bash
hermes version
# Hermes Agent v0.16.0 (2026.6.5) · upstream 81eaedd0
# Up to date
```

The version shown confirms both git HEAD and installed package match.
