# Windows Process Cleanup — Diagnosing System Slowness

## Quick Diagnosis

When a user reports their Windows machine is slow, identify stale/leaked/duplicate
processes using these steps.

## 1. Find Top Memory Consumers

```powershell
Get-Process | Sort-Object -Property WorkingSet64 -Descending | `
  Select-Object -First 40 Name, Id, `
    @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, `
    @{N='CPUs';E={[math]::Round($_.CPU,1)}} | `
  Format-Table -AutoSize
```

> **MSYS/Git-Bash Compatibility:** When running from MSYS bash (Hermes terminal tool
> on Windows), `$_.` in calculated properties gets expanded by bash as a variable.
> Use a script file or avoid calculated properties:
> ```bash
> powershell -NoProfile -Command "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 40 Name,Id,CPU,WorkingSet64 | Format-Table -AutoSize"
> ```

## 2. Check Process Command Lines

Use `Get-WmiObject Win32_Process` (more capable than Get-Process for this):

```powershell
# Find all instances of a specific process
Get-WmiObject Win32_Process -Filter "Name like 'node%'" | `
  Select-Object ProcessId,CommandLine | Format-Table -AutoSize -Wrap

# All python processes
Get-WmiObject Win32_Process -Filter "Name like 'python%'" | `
  Select-Object ProcessId,CommandLine | Format-Table -AutoSize -Wrap

# All powershell processes
Get-WmiObject Win32_Process -Filter "Name='powershell.exe'" | `
  Select-Object ProcessId,CommandLine | Format-Table -AutoSize -Wrap
```

## 3. Kill Candidate Processes

```powershell
Stop-Process -Id <PID> -Force
# or via taskkill (note: use -f, not /F, in MSYS/bash)
taskkill -f -pid <PID>
taskkill -f -pid <PID1> -pid <PID2> -pid <PID3>  # batch kill
```

> **MSYS/Git-Bash Compatibility:** `taskkill /F` is interpreted as a path on
> MSYS/bash. Use `taskkill -f` (dash-style flags) instead.

## 4. Check Total System Memory

```powershell
Get-CimInstance Win32_OperatingSystem | `
  Select-Object TotalVisibleMemorySize, FreePhysicalMemory, `
    @{N='UsedMB';E={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/1KB,1)}}
```

## 5. DO NOT KILL — Preserve These

Always check command lines (`Get-WmiObject Win32_Process`) before killing to
avoid terminating critical services:

| Process | Why | Exception |
|---------|-----|-----------|
| **chrome.exe** | User is browsing (check usage) | Kill individual stale tabs only |
| **Kiro.exe** | Kiro IDE — user is actively coding | Leave all instances |
| **Codex.exe** | Codex Desktop app | Leave all instances |
| **moonbridge.exe** | Moon Bridge proxy server (port 38440) | Kill only if user confirms |
| **hermes.exe** | Hermes Agent (yourself) | Never kill |
| **explorer.exe** | Windows shell/desktop | Never kill |
| **svchost.exe** | Windows services | Never kill |
| **MsMpEng.exe** | Windows Defender | Never kill |
| **csrss.exe, wininit.exe, lsass.exe** | Windows core processes | Never kill |
| **Memory Compression** | Windows kernel feature (1-2GB is normal) | Never kill |

### Process Identity Checklist

Before killing ANY process with >100MB or unknown purpose:

- [ ] Check command line via `Get-WmiObject Win32_Process`
- [ ] Is it a system process? (svchost, csrss, lsass, wininit, services)
- [ ] Is it an app the user is actively using? (Kiro, Codex, Chrome)
- [ ] Is it a proxy/server the user set up? (moonbridge, ollama, docker)
- [ ] Does it have multiple instances of the same thing? (duplicates are safe)
- [ ] Is it a stuck script? (PowerShell with high CPU/memory running a .ps1)

## Common Leak Patterns

### PowerShell Scripts That Got Stuck
- **Symptom:** 1GB+ memory, hundreds of CPU seconds
- **Tell:** Running a `.ps1` script that should have completed
- **Fix:** Kill the process; the script needs investigation

### Duplicate MCP Server Instances
- **Symptom:** 5-10 copies of the same node/uv process (~60-120MB each)
- **Common offenders:**
  - `@modelcontextprotocol/server-filesystem`
  - `@modelcontextprotocol/server-sequential-thinking`
  - `@modelcontextprotocol/server-memory`
  - `@playwright/mcp`
  - `mcp-server-fetch` (python)
  - `n8n-mcp`
  - `node_repl` (Codex)
- **Fix:** Kill duplicates; identify if something keeps respawning them

### Leftover Package Manager Processes
- **uv.exe** — Rust package manager; sometimes leaves stale daemon processes (~57MB each)
- **npm/node** — Leftover from failed installs

### Stale Language Server Processes
- **kilo.exe** (Kiro IDE language server) — Should be 1 instance; duplicates are stale

## Red Flags

| Finding | Action |
|---------|--------|
| PowerShell using >500MB | Likely a stuck script — investigate script path |
| 5+ node instances all doing the same thing | Duplicate MCP servers — kill extras |
| 3+ python instances of same MCP server | Leftover fetch/memory servers |
| Process with 0 working set but >100 CPU seconds | Zombie — safe to kill |
| Two kilo.exe processes, one with high CPU | Stale language server — kill the older one |
| uv.exe using 50+MB | Leftover daemon — safe to kill |
