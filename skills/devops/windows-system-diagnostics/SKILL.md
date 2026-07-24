---
name: windows-system-diagnostics
description: Systematic approach to diagnosing Windows system and hardware issues — disk health, USB devices, event logs, hardware-to-logical mapping, phantom USB devices.
category: devops
---

# Windows System Diagnostics

Systematic approach for diagnosing hardware, disk, and system-level issues reported by users on Windows. This skill covers the full pipeline: user reports a problem → enumerate hardware → check health → map to logical drives → inspect event logs → identify phantom/transient USB devices.

## Trigger Conditions
- User reports: "hard drive not working", "disk failing", "USB device issues", "system slow", "hardware errors"
- You need to check physical vs logical disk health
- You need to identify phantom USB storage devices (monitor card readers, built-in hubs)
- You need to map "which drive letter" to "which physical disk"
- You need to read Windows System Event Log for hardware errors

## Diagnostic Pipeline (preferred order)

### 1. Quick Physical Health Scan
Start here for an overview. Returns all physical disks with their health status.

```powershell
Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,Size,BusType
```

Also list all disk drives with model, status, and interface:

```powershell
Get-WmiObject Win32_DiskDrive | Select-Object Model,Status,Index,InterfaceType | Format-Table -AutoSize
```

### 2. Map Drive Letters to Physical Disks
The user says "my C: drive" — you need to know which physical disk that is.

```powershell
Get-WmiObject Win32_LogicalDiskToPartition | ForEach-Object { 
  $d = $_.Dependent; $p = $_.Antecedent; Write-Output "$d <- $p" 
}
```

Pattern of output: `\\HOST\root\cimv2:Win32_LogicalDisk.DeviceID="C:" <- \\HOST\root\cimv2:Win32_DiskPartition.DeviceID="Disk #0, Partition #0"`

### 3. Check Disk Space
```powershell
Get-PSDrive C,D | Select-Object Name,Used,Free,Root
```

## Disk Space Cleanup Procedure

When the user asks to free up space, use this systematic, user-approval-gated workflow.

### Guiding Rules (User Preferences)
These rules were given by Kevin (Ensign Services, Therapy AI Dev) and MUST be stated before any deletion:

1. Never delete actively-used files, work-in-progress, or tools needed for current work
2. List ALL targets before deleting — user must approve every removal
3. Flag old/forgotten items explicitly — they may be important
4. NO photos or videos deleted — flag them as candidates only
5. Full transparency on what's targeted and why

### Assessment Pipeline

#### 1. Quick Disk Overview
```bash
df -h /c
```
Or from PowerShell:
```powershell
Get-PSDrive C | Select-Object @{N='FreeGB';E={[math]::Round($_.Free/1GB,1)}}, @{N='UsedGB';E={[math]::Round($_.Used/1GB,1)}}
```

#### 2. Target Safe Directories (Avoid Full Recursive Scans)
On a 94%+ full 476GB drive, `du` and `Get-ChildItem -Recurse` time out. Instead, probe known cache/temp locations using targeted checks:

```python
# Python: fast targeted size check with depth cap
import os
def quick_size(path, max_depth=2):
    if not os.path.exists(path): return 0, 0
    total = 0; count = 0
    for root, dirs, files in os.walk(path):
        depth = root.replace(path, '').count(os.sep)
        if depth >= max_depth: dirs.clear()
        for f in files:
            try: total += os.path.getsize(os.path.join(root, f)); count += 1
            except: pass
    return total, count
```

Or use cmd.exe for instant totals (no file-depth issues):
```batch
cmd /c "dir /s /a C:\Users\kevin\AppData\Local\Temp | findstr File"
```

**Primary cleanup targets (safe to clear — auto-rebuild):**

| Target | Typical Size | Path |
|--------|-------------|------|
| npm cache | 0.5-6 GB | `%LOCALAPPDATA%\npm-cache` — `_cacache/` is deeply nested; use `dir /s` not `du` |
| JetBrains IDE caches | 1-4 GB | `%LOCALAPPDATA%\JetBrains` |
| User Temp | 1-3 GB | `%LOCALAPPDATA%\Temp` |
| pip cache | 0-500 MB | `%LOCALAPPDATA%\pip\cache` |
| Chrome cache | 0-500 MB | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache` |
| Edge cache | 0-300 MB | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache` |
| VS Code cache | 0-500 MB | `%APPDATA%\Code\Cache` |
| VS Code CachedData | 0-100 MB | `%APPDATA%\Code\CachedData` |
| uv cache | 0-500 MB | `%LOCALAPPDATA%\uv` |
| Windows Temp | 0-1 GB | `C:\Windows\Temp` |

#### 3. System-Level Targets (Require Admin)
- **DriverStore** (`C:\Windows\System32\DriverStore\FileRepository`) — 5-10 GB typical. Run:
  ```batch
  Dism /Online /Cleanup-Image /StartComponentCleanup
  ```
- **WinSxS** — Windows Component Store (5-15 GB). First analyze, then clean:
  ```batch
  Dism /Online /Cleanup-Image /AnalyzeComponentStore
  Dism /Online /Cleanup-Image /StartComponentCleanup
  ```
  Aggressive (no rollback for recent updates):
  ```batch
  Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase
  ```
- **Windows.old** — if present, use Disk Cleanup or `Dism`
- **Recycle Bin** — `cmd /c "dir /a C:\$Recycle.Bin"` to check

#### 4. Admin Elevation — The Blocking Problem
Dism and DriverStore cleanup need admin rights. The agent CANNOT reliably trigger this:
- `Start-Process -Verb RunAs` → UAC prompt on secure desktop (invisible to agent)
- `schtasks /Create /RU SYSTEM` → also needs admin
- `computer_use` background keyboard → can't open Start menu or interact with UAC
- `delivery_mode: "foreground"` → may not be supported by the installed cua-driver build

**Workaround:** Ask the user to open **Terminal (Admin)** (right-click Start → Terminal (Admin)) and paste the Dism commands. Takes 10 seconds when the user is present.

### Deletion Implementation
```python
import os, shutil
# For whole-directory targets:
for path in [target_paths]:
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path, exist_ok=True)

# For Temp (delete contents, keep folder):
for item in os.listdir(temp_path):
    item_path = os.path.join(temp_path, item)
    try:
        if os.path.isfile(item_path) or os.path.islink(item_path): os.unlink(item_path)
        elif os.path.isdir(item_path): shutil.rmtree(item_path, ignore_errors=True)
    except: pass
```

### Verification
After cleanup:
```bash
df -h /c
```
Report delta: "Before: X GB free → After: Y GB free (Freed: Z GB, P% → Q% used)"

### Pitfalls
- **Recursive scans on full drives WILL timeout.** Use `cmd /c "dir /s /a <path> | findstr Dir"` for instant totals.
- **npm cache reports incorrectly with shallow walks.** `_cacache/` is deeply nested; use `dir /s`, not Python `os.walk` with depth limit.
- **Browser caches may have locked files** — browser should be closed. `shutil.rmtree(ignore_errors=True)` skips gracefully.
- **WinSxS is NEVER safe to delete manually** — always use Dism.
- **Temp files in use by running processes** — `ignore_errors=True` handles this.

### 4. System Event Log — Disk & Storage Errors
This is the most important step. Filter to disk-related providers only.

```powershell
Get-WinEvent -LogName System -MaxEvents 50 | 
  Where-Object { $_.LevelDisplayName -eq 'Error' -and 
    $_.ProviderName -match 'disk|ntfs|storahci|partmgr|volmgr' } | 
  Format-Table TimeCreated,Id,ProviderName,Message -Wrap -AutoSize
```

Key event IDs:
- **Event 11 (disk):** "The driver detected a controller error on \Device\HarddiskN\DRN" — USB controller error, often from phantom devices
- **Event 7 (disk):** "The device, \Device\HarddiskN\DRN, has a bad block" — actual disk failure
- **Event 134 (storahci):** Storage controller errors
- **Event 157 (disk):** Disk has been surprise-removed

### 5. Enumerate All USB Storage Devices
Finds everything that looks like a disk on USB, including phantom devices (card readers, monitor hubs, etc.).

```powershell
# All USB storage and portable devices with classifications
Get-WmiObject Win32_PnPEntity | Where-Object { 
  $_.PNPDeviceID -match 'USBSTOR|WPD' 
} | Select-Object Caption,Description,PNPClass,Status | Format-Table -AutoSize -Wrap

# Full USB tree including VID/PID for identification
Get-WmiObject Win32_PnPEntity | Where-Object { 
  $_.PNPClass -eq 'USB' -and $_.DeviceID -match 'VID_' 
} | Select-Object Caption,Description,Manufacturer,Status,DeviceID | Format-Table -AutoSize -Wrap
```

### 6. Check SMART Predictive Failure Data
```powershell
Get-WmiObject -Namespace root\wmi -Class MSStorageDriver_FailurePredictStatus | 
  Select-Object InstanceName,PredictFailure,Reason
```

### 7. Read Raw Disk Info for a Specific Index
When you have a specific HarddiskN from an event log error:

```powershell
Get-WmiObject Win32_DiskDrive | Where-Object { $_.Index -eq N } | 
  Select-Object Caption,Size,PNPDeviceID,InterfaceType,MediaLoaded,MediaType
```

## Pitfalls

### Phantom USB Storage Devices (Most Common Trap)
- Many **monitors with built-in card readers** enumerate as "Generic STORAGE DEVICE" even when no card is inserted — they have an active USB controller regardless of media presence
- **Realtek (VID_0BDA)** and **Genesys Logic (VID_05E3)** are the most common card reader chips built into monitors
- These throw **Event 11 controller errors** in the System log even though no actual drive is attached and failing
- **How to spot:** check `Size` field — phantom devices often show no size (empty) while real drives report capacity. They may also lack a drive letter and only appear as a WPD (Windows Portable Device) entry
- **Realtek USB CD-ROM** appearing alongside a "Generic STORAGE DEVICE" is a dead giveaway — Realtek card readers enumerate as a virtual CD-ROM (driver disc) + storage device

### DisplayLink Monitor Hubs
- Monitors using **DisplayLink (VID_17E9)** connect entirely via USB (chipset like DisplayLink-6950)
- The monitor's internal USB hub may host: card readers (Realtek), audio, Bluetooth, webcam, downstream USB ports
- These internal devices are **not separate hardware failures** when they throw USB errors
- Identify by: `PNPClass='Display'` and `DeviceID` matching `VID_17E9`

### Distinguishing Disk Full vs Disk Failing
- **C: at 90%+** = performance issue, not hardware failure. User may report "drive isn't working" when it's just out of space
- Check event logs for actual hardware errors before diagnosing a failing disk
- A truly failing disk shows: Event 7 (bad block), Event 134 (controller timeout), SMART predictive failure

### chkdsk Limitations
- `chkdsk C: /scan` requires admin/elevated prompt from the shell
- Running from a non-elevated terminal will return "Access Denied — you do not have sufficient privileges"
- If chkdsk is needed, run the terminal command elevated or use the full admin path

## Verification
After running through the pipeline, report back to the user with:
1. **Per-drive summary:** letter / physical index / model / capacity / used+free / health status
2. **Error mapping:** what event log errors exist, which \Device\HarddiskN they point to, and what that device actually is
3. **Conclusion:** which device the user was asking about, is it actually failing, or is it a phantom/phantom device, or is it just full
