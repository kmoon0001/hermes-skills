# Windows Disk Cleanup — Known Targets (2026-07-21 Session)

These are the specific targets, sizes, and commands verified on a Windows 10 system
with C: at 476 GB total, 444 GB used, 33 GB free (94% full).

## Environment

- Host: Windows 10, git-bash (MSYS2) terminal
- User profile: C:\Users\kevin
- Drive: C: (SSD, 476 GB)

## Assessment Results (2026-07-21)

### TIER 1 — Measured auto-recreatable caches

| Target | Found Size | Path |
|--------|-----------|------|
| npm cache | **5.5 GB** | `C:\Users\kevin\AppData\Local\npm-cache` |
| JetBrains IDE caches | **2.0 GB** (29,435 files) | `C:\Users\kevin\AppData\Local\JetBrains` |
| LocalAppData Temp | **1.3 GB** | `C:\Users\kevin\AppData\Local\Temp` |
| VS Code Cache | **190 MB** | `C:\Users\kevin\AppData\Roaming\Code\Cache` |
| pip cache | **150 MB** | `C:\Users\kevin\AppData\Local\pip\cache` |
| Chrome cache | **277 MB** (1,317 files) | `C:\Users\kevin\AppData\Local\Google\Chrome\User Data\Default\Cache` |
| Edge cache | **82 MB** (397 files) | `C:\Users\kevin\AppData\Local\Microsoft\Edge\User Data\Default\Cache` |
| VS Code CachedData | **12 MB** (18 files) | `C:\Users\kevin\AppData\Roaming\Code\CachedData` |

### TIER 2 — System-level

| Target | Found Size | Path |
|--------|-----------|------|
| DriverStore | **7.0 GB** (973 packages) | `C:\Windows\System32\DriverStore\FileRepository` |
| Win Update cache | **2 MB** (5 files) | `C:\Windows\SoftwareDistribution\Download` |
| Win Error Reporting | **1 MB** | `C:\ProgramData\Microsoft\Windows\WER` |
| Docker cache | **28 MB** | `C:\Users\kevin\AppData\Local\Docker` |

### TIER 3 — Flagged for user review

| Target | Size | Notes |
|--------|------|-------|
| `agent-academy/` | **1.6 GB** | Git repo (only `.git` dir visible). Last modified Jul 10. Course/training materials? |
| `.junie/` | unknown | Last modified Sep 6, 2025 (almost 1 year old). Contains `mcp/` subdir. Old coding tool data. |

### Not found / zero

- **Windows.old**: not present
- **Recycle Bin**: not reachable via MSYS path (but likely empty or small)
- **Downloads**: 1 file (desktop.ini only) — essentially empty

## What DID NOT work for scanning

These approaches failed or timed out on a 444 GB used drive:

1. **`du -sh --max-depth=0 ~/*`** — timed out (180s+), even on individual top-level dirs
2. **`Get-ChildItem -Recurse` in PowerShell** — timed out on large dirs like `$HOME` and `$env:APPDATA`
3. **Python `os.walk` on large directories** — timed out without a break/traversal cap
4. **`du -sh` on the user profile top-level** — the loop `for d in ~/*/; do du -sh; done` timed out

## What DID work (tested approaches)

1. **PowerShell `.ps1` files** — write to file first, then `powershell.exe -ExecutionPolicy Bypass -File path\scan.ps1`. Avoids quoting issues in git-bash.
   - Worked for: JetBrains (2.0 GB, 29K files), Chrome cache (277 MB, 1.3K files), Edge cache (82 MB), DriverStore (7.0 GB)
   - Timed out on: user profile root, WinSxS

2. **`cmd.exe //c dir /s /a path | findstr File(s)`** — gives total file count and size for a directory tree
   - Worked for: Temp directories, small to medium targets
   - Produces extremely verbose raw output; pipe through `findstr /i "File(s)"` to extract the summary line

3. **Python `os.walk` with a size cap** (`if total > 5 * 1024**3: break`)
   - Worked for: agent-academy (1.6 GB), Downloads, targeted individual dirs
   - Must set a traversal cap to avoid hanging on very large directories

4. **Targeted non-recursive checks** — `ls -la ~/dirname` to see timestamps and contents, Python to check file sizes non-recursively

## Summary

The 5 largest space hogs found were:
1. DriverStore: 7.0 GB (system-level, Dism-managed)
2. npm cache: 5.5 GB (Tier 1 — safe to delete)
3. JetBrains: 2.0 GB (Tier 1 — safe to delete)
4. agent-academy: 1.6 GB (Tier 3 — user review)
5. LocalAppData Temp: 1.3 GB (Tier 1 — safe to delete)

Total identified: ~18.1 GB of reclaimable space minimum.

## Cleanup Execution Results (2026-07-21)

After user approval, the following were deleted via Python `shutil.rmtree` + recreate:

| Target | Status | 
|--------|--------|
| npm cache | DELETED (dir cleared) |
| JetBrains caches | DELETED (dir cleared) |
| LocalAppData Temp | DELETED (3,006 items removed) |
| VS Code Cache | DELETED (dir cleared) |
| VS Code CachedData | DELETED (dir cleared) |
| pip cache | DELETED (dir cleared) |
| Edge cache | DELETED (dir cleared) |

**Not deleted (user requested to keep):** Chrome cache, agent-academy

**Deferred to admin session:** DriverStore (requires Dism, admin-elevated), WinSxS (pending investigation)

**Result:** C: drive went from 33 GB free (94%) to **46 GB free (91%)** — **13 GB reclaimed**.
