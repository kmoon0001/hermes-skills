---
name: notepad-opener
description: "Open files in Notepad on Windows via git-bash terminal. Avoids git-bash notepad wrapper script."
version: 1.0.0
author: Hermes Agent
tags: [windows, notepad, editor]
---

# Notepad Opener

## Problem
In git-bash, `notepad` is aliased to a shell wrapper script that shows source code instead of opening Notepad. Running `notepad file.yaml` displays the wrapper script content.

## Solution
Use `cmd.exe /c start notepad` to bypass the git-bash wrapper.

## Command
```bash
cmd.exe /c start notepad "C:\full\path\to\file.yaml"
```

## Pitfalls
- MUST use `cmd.exe /c start notepad` — NOT `notepad`, `notepad.exe`, or `powershell.exe Start-Process notepad`
- The git-bash `notepad` alias is a shell script at `/usr/bin/notepad` that wraps `notepad.exe` but also runs `unix2dos`/`dos2unix` and shows the script source on error
- `powershell.exe -Command "Start-Process notepad -ArgumentList 'path'"` works but sometimes opens Notepad behind other windows
- Always use full Windows path with backslashes in quotes: `"D:\path\to\file.yaml"`
- Multiple files: open one at a time, each with its own `cmd.exe /c start notepad` call
