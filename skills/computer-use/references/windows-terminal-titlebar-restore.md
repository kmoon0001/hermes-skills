# Windows terminal title-bar / frame restoration

Use when the user says the terminal title bar or minimize/maximize/close controls disappeared after fullscreen/focus-mode/window manipulation.

## Durable lesson
Windows Terminal / Cascadia windows can be restored without user-visible mouse automation by using Win32 window APIs. This is useful when `computer_use` is unavailable or when the user specifically wants the CLI terminal restored.

## Pattern
1. Enumerate visible windows and identify terminal candidates by title/class:
   - class often: `CASCADIA_HOSTING_WINDOW_CLASS`
   - title may include `cmd.exe`, `Terminal`, `PowerShell`, `bash`, or `Hermes`
2. Call `ShowWindow(hwnd, SW_RESTORE)`.
3. Re-enable normal frame bits with `SetWindowLongW(hwnd, GWL_STYLE, style | WS_CAPTION | WS_SYSMENU | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_VISIBLE)`.
4. Force a non-activating redraw/reframe with `SetWindowPos(..., SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW)`.
5. Verify style bits and rectangle.

## Pitfalls
- Do not assume `IsZoomed` means fullscreen/focus mode; a borderless-looking terminal can report `zoomed=false` while title-bar style bits are missing.
- If running Python through a shell heredoc, bitwise `&` characters can trip Hermes foreground-command guards. Prefer `execute_code` for the Win32 API snippet or escape carefully.
- Avoid changing unrelated Chrome/Copilot Studio windows; enumerate and target the terminal HWND specifically.

## Minimal Python core
```python
import ctypes
from ctypes import wintypes
user32 = ctypes.windll.user32
hwnd = wintypes.HWND(<terminal_hwnd>)
GWL_STYLE = -16
WS_CAPTION=0x00C00000; WS_SYSMENU=0x00080000; WS_THICKFRAME=0x00040000
WS_MINIMIZEBOX=0x00020000; WS_MAXIMIZEBOX=0x00010000; WS_VISIBLE=0x10000000
SW_RESTORE=9
SWP_NOZORDER=0x0004; SWP_NOACTIVATE=0x0010; SWP_FRAMECHANGED=0x0020; SWP_SHOWWINDOW=0x0040
style = user32.GetWindowLongW(hwnd, GWL_STYLE)
newstyle = style | WS_CAPTION | WS_SYSMENU | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_VISIBLE
user32.ShowWindow(hwnd, SW_RESTORE)
user32.SetWindowLongW(hwnd, GWL_STYLE, newstyle)
user32.SetWindowPos(hwnd, None, 168, 100, 1200, 760, SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW)
```
