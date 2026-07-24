---
name: windows-disk-cleanup
description: "Systematic approach to safely freeing disk space on Windows — scanning techniques that work on 94%+ full drives, tiered cleanup targets, user-safety guardrails, and C: drive recovery. Covers temp files, package manager caches, browser caches, IDE caches, DriverStore, WinSxS, and Windows built-in tools."
category: devops
---

# Windows Disk Cleanup

Systematic approach to freeing disk space on Windows drives. Designed for safety-first cleanup with user approval gates.

## Trigger Conditions
- User asks to "free up space", "clean up C:", "disk full"
- C: drive is >90% full and user reports performance issues
- User reports "low disk space" warnings
- New Windows installation needs post-migration cleanup

## Safety Rules (from user Kevin, confirmed 2026-07-21)

These are hard rules for any disk cleanup operation:

1. **Never delete items actively being used, worked on, or needed for current work.**
2. **List everything before deleting** — user must approve every removal.
3. **Flag old items** — they may be important even if forgotten about.
4. **NO photos or videos may be deleted** — but flag them as cleanup candidates.
5. **Full transparency** on what's targeted and why.

See also the `hermes-windows` skill's "Destructive operations on the Desktop" section for the full context on why `rm -rf` via git-bash is permanent on Windows (no Recycle Bin). When in doubt, move to a staging `_trash/` dir instead of deleting directly.

## Assessment Pipeline

### Phase 1: Initial Disk State

```bash
# Quick disk space check (works everywhere)
df -h /c

# Or via PowerShell (more accurate on Windows)
powershell.exe -Command "Get-PSDrive C | Select-Object Used,Free"
```

### Phase 2: Identify Space Hogs (Windows-specific approaches)

**WARNING — `du` on MSYS/git-bash is SLOW on large drives with many files.**
On a 444 GB used drive, `du -sh` on the user profile times out even with `--max-depth=1`.
`Get-ChildItem -Recurse | Measure-Object` in PowerShell also times out on large directories.

**Fast approach — target known cache/temp locations directly:**

Write PowerShell to a `.ps1` file first (avoids quoting issues in git-bash), then execute:

```powershell
# write this to a .ps1 file, then run via:
# powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\scan.ps1"

function Get-DirSize($path) {
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        if ($size -gt 1GB) { return "$path : $([math]::Round($size/1GB,1)) GB" }
        elseif ($size -gt 1MB) { return "$path : $([math]::Round($size/1MB,0)) MB" }
        else { return "$path : $([math]::Round($size/1KB,0)) KB" }
    }
    return "$path : NOT FOUND"
}

# Run on all known targets
Get-DirSize "$env:TEMP"
Get-DirSize "$env:LOCALAPPDATA\Temp"
Get-DirSize "$env:LOCALAPPDATA\npm-cache"
Get-DirSize "$env:LOCALAPPDATA\pip\cache"
Get-DirSize "$env:LOCALAPPDATA\uv"
Get-DirSize "$env:LOCALAPPDATA\JetBrains"
Get-DirSize "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
Get-DirSize "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
Get-DirSize "$env:APPDATA\Code\Cache"
Get-DirSize "$env:APPDATA\Code\CachedData"
Get-DirSize "$env:LOCALAPPDATA\hermes"
Get-DirSize "C:\Windows\Temp"
Get-DirSize "C:\Windows\SoftwareDistribution\Download"
Get-DirSize "C:\Windows\System32\DriverStore\FileRepository"
Get-DirSize "C:\ProgramData\Microsoft\Windows\WER"
Get-DirSize "$env:LOCALAPPDATA\Yarn\Cache"
Get-DirSize "$env:LOCALAPPDATA\Cargo\registry"
```

**Alternative — `cmd.exe` for quick total (but extremely verbose output):**

```bash
cmd.exe //c "dir /s /a C:\Users\kevin\AppData\Local\Temp | findstr /i \"File(s)\"" 2>/dev/null
```

Note: The `//c` (double slash) is required in git-bash to avoid the forward-slash being interpreted as a path.

**Alternative — Python with traversal cap (good for shallow checks):**

```python
import os
total = 0
for root, dirs, files in os.walk(target_path):
    for f in files:
        try: total += os.path.getsize(os.path.join(root, f))
        except: pass
    if total > 5 * 1024**3:  # 5GB cap to avoid hanging
        break
print(f"{total/1024**3:.1f} GB" if total > 1e9 else f"{total/1024**2:.0f} MB")
```

**Limitation — WinSxS is too large to scan via walking.**
Skip direct scan and use Dism instead (see Phase 3).

### Phase 3: Cleanup Targets (Tiered)

#### TIER 1 — Auto-recreatable caches (zero risk, user typically approves)

| Target | Typical Size | Cleanup Command |
|--------|-------------|-----------------|
| npm cache | 1-6 GB | `npm cache clean --force` or delete `$env:LOCALAPPDATA\npm-cache` |
| pip cache | 50-200 MB | `pip cache purge` or delete `$env:LOCALAPPDATA\pip\cache` |
| uv cache | 0-2 GB | `uv cache clean` or delete `$env:LOCALAPPDATA\uv` |
| JetBrains IDE caches | 1-3 GB | Delete `$env:LOCALAPPDATA\JetBrains` (IDEs recreate on launch) |
| Chrome cache | 100-500 MB | Delete `$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache` |
| Edge cache | 50-200 MB | Delete `$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache` |
| VS Code cache | 100-300 MB | Delete `$env:APPDATA\Code\Cache` and `CachedData` |
| LocalAppData Temp | 1-5 GB | Delete `$env:LOCALAPPDATA\Temp` (skip files in use) |
| Windows Temp | 0-2 GB | Delete `C:\Windows\Temp` |

#### TIER 2 — Needs review / system-level

**DriverStore (old driver packages):** 5-10 GB
```powershell
# Check current size
Get-ChildItem C:\Windows\System32\DriverStore\FileRepository -Recurse -File |
    Measure-Object -Property Length -Sum

# Clean old driver packages (safe — keeps active drivers)
Dism /Online /Cleanup-Image /StartComponentCleanup
```

**WinSxS (Windows component store):** 5-15 GB
```powershell
# Analyze first
Dism /Online /Cleanup-Image /AnalyzeComponentStore

# Clean old versions
Dism /Online /Cleanup-Image /StartComponentCleanup
```

**Windows Update cache:**
```powershell
# Usually small (<100 MB), but can bloat after failed updates
# Stop the service, clear, restart
net stop wuauserv
net stop bits
# Delete C:\Windows\SoftwareDistribution\Download contents
net start wuauserv
net start bits
```

#### TIER 3 — User-data review (flag, don't delete)

- **Downloads folder** — flag large files but let user decide
- **Old Git repositories** — large `.git` directories (check `git remote -v` to see if it's a cloned repo or local-only)
- **`agent-academy/` and similar training directories** — may be course materials
- **`.junie/`, `.claude/`, `.codex/`** — old AI coding tool data, safe to clear but flag
- **OneDrive** — Files On-Demand can localize unexpectedly; check via PowerShell
- **Windows.old** — if present, remove via Disk Cleanup tool
- **Large personal files** — flag documents >100 MB, photos/videos for user review

### Phase 4: Windows Built-in Tools

For a quick safe cleanup that catches OS-level items:

```powershell
# Launch Disk Cleanup as administrator
Start-Process cleanmgr.exe -Verb RunAs

# Or target the C: drive directly
cleanmgr /sageset:1  # configure what to clean
cleanmgr /sagerun:1  # run with saved config
```

This catches: Windows Update Cleanup, Delivery Optimization Files, Recycle Bin, Temporary Internet Files, Thumbnails, etc.

### Phase 5: Verification

```powershell
$before = (Get-PSDrive C).Used
# ... do cleanup ...
$after = (Get-PSDrive C).Used
$freed = [math]::Round(($before - $after)/1GB, 1)
Write-Host "Freed $freed GB on C:"
```

## Cleanup Execution (safe approach)

Always follow this execution pattern:

1. **Present complete categorized list** to user before any deletion
2. **Get explicit approval** per tier or per item
3. **Delete in order** — start with Tier 1, present results, then Tier 2, etc.
4. **Verify after each tier** — report how much space was freed
5. **Skip items the user wants to keep** — never push back

### Bulk Approval Pattern

After presenting the full categorized list, users often approve in bulk with a short phrase
(e.g., "the rest is good to delete" or "yes proceed with all Tier 1"). This is valid approval.
Always delete items in a single batch call (not one-by-one) to keep the session moving.

When the user says "keep X" for a specific item, remove it from the deletion list and proceed
with everything else. Never re-ask about items they've already decided on.

### Recommended Deletion Technique (Python via execute_code)

For maximum reliability, use Python's `shutil.rmtree` inside `execute_code`:

```python
import os, shutil

# Two deletion modes:
# 1. 'dir' — remove entire directory and recreate empty
# 2. 'contents' — remove all children but keep the directory itself (e.g., Temp/)

targets = [
    ('npm cache', 'C:\\Users\\kevin\\AppData\\Local\\npm-cache', 'dir'),
    ('LocalAppData Temp', 'C:\\Users\\kevin\\AppData\\Local\\Temp', 'contents'),
]

results = {}
for name, path, mode in targets:
    if not os.path.exists(path):
        results[name] = "not found"
        continue
    try:
        if mode == 'dir':
            shutil.rmtree(path, ignore_errors=True)
            os.makedirs(path, exist_ok=True)  # recreate empty for safety
            results[name] = "DELETED"
        elif mode == 'contents':
            count = 0
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    count += 1
                except Exception as e:
                    results[name] = f"PARTIAL (locked: {e})"
            if name not in results:
                results[name] = f"DELETED ({count} items)"
    except Exception as e:
        results[name] = f"ERROR: {e}"

# Print results table
for name, r in results.items():
    print(f"  [{('OK' if 'DELETED' in r else 'WARN')}] {name}: {r}")

# Then verify with:
#   df -h /c
```
**Note about the `ignore_errors=True` pattern:** This skips files that are locked by other
processes (e.g., DLLs loaded by running apps in `Temp/`). That's correct behavior — you don't
want to force-close handles. A reboot frees them if the user wants a deeper clean.

## Pitfalls

- **`du` on MSYS/git-bash is unusably slow** on drives with millions of files (444 GB+ used). Target individual known directories instead of recursive scanning.
- **Python `os.walk` with a depth cap (`dirs.clear()`) underestimates deeply nested dirs** — the npm `_cacache/` folder is deeply nested (content-addressable). A Python walk capped at depth 3 read only 53 MB while the real size was 5.5 GB. Always verify shallow results with a PowerShell `Get-DirSize` call when available.
- **PowerShell `Get-ChildItem -Recurse` also times out** on large directories. When it does, the error is a silent timeout — there's no partial output.
- **PowerShell scripts with complex quoting** cannot be passed inline through git-bash. Always write them to `.ps1` files first.
- **`cmd.exe /c` in git-bash** — use `//c` (double forward slash) to avoid the git-bash `c:` path expansion, or escape carefully. Long directory names with recursive scans produce verbose output.
- **`rm -rf` via git-bash is PERMANENT on Windows** — no Recycle Bin. Never use it for user content without explicit approval. Prefer moving to `_trash/` staging dir.
- **`cmd.exe //c dir /s /a` produces extremely verbose output** for directories with many subdirectories. Pipe through `findstr` to extract only the size summary line.
- **WinSxS cannot be scanned by walking** — too many hard links. Use `Dism /Online /Cleanup-Image /AnalyzeComponentStore` instead.
- **Recycle Bin is not at `C:\$Recycle.Bin` via MSYS** — the path exists but MSYS may not see it. Use `Start-Process cleanmgr.exe -Verb RunAs` or PowerShell's COM interface: `(New-Object -ComObject Shell.Application).NameSpace(0xa).Items() | %{ $_.Path }`
- **DriverStore cleanup via Dism is safe** but can take 10-30 minutes. It does NOT remove actively-used drivers — only superseded versions.
- **User Temp files in use skip themselves** — that's normal. You can't delete a file Windows is holding open. Reboot first if you want maximum cleanup.

## References

- `references/scan-targets.md` — specific targets and commands tested in session 2026-07-21
- `hermes-windows` skill — destructive operations rules (Desktop/PHI deletion)
- `windows-system-diagnostics` skill — disk health separate from disk cleanup (don't conflate)
