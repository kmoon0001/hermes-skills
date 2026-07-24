---
name: windows-cua-driver
description: "Windows desktop automation patterns via cua-driver MCP tools — fallback when computer_use returns 0x0, WinForms quirks, app launch/restore, click delivery modes, Chromium workarounds."
version: 1.0.0
platforms: [windows]
metadata:
  hermes:
    tags: [cua-driver, windows, desktop-automation, mcp, winforms]
    category: computer-use
---

# Windows cua-driver MCP Patterns

When the Hermes `computer_use` tool returns 0x0 captures (empty screens, no elements),
fall back to the `mcp_cua_driver_*` MCP tools directly. They are lower-level but work
reliably on Windows. This skill covers patterns learned operating Windows desktop apps:
Edge, Chrome, WinForms, ClickOnce launchers, and UWP-packaged apps.

## When to Use This Skill

- `computer_use` returns 0x0 consistently on Windows
- You need to drive a WinForms desktop app (DataGridView, scrollbars)
- You need to launch/restore/click Windows apps in the background
- You hit Chromium input routing issues (PostMessage dropping keystrokes)

## Quick Health Check

```
mcp_cua_driver_health_report()
```
`"overall": "ok"` = UIA + DXGI both reachable. You're good.

## Discovery → Capture → Act Pipeline

1. **List everything:** `mcp_cua_driver_get_accessibility_tree()` — returns all processes and visible windows with PIDs and window_ids
2. **Capture a window:** `mcp_cua_driver_get_window_state(pid, window_id)` — returns screenshot + UIA tree with numbered elements
3. **Act by element index:** `mcp_cua_driver_click(element_index=N, pid, window_id)` — use `element_index` > pixel coords

After any state change, re-capture. Window IDs are ephemeral — always re-enumerate if `get_window_state` returns "No window with window_id X exists".

## Launching Windows Apps / Opening URLs

```python
# Launch an app by path
mcp_cua_driver_launch_app(
    path="C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    start_minimized=True
)

# Open URL in default browser — PREFERRED for Chrome navigation
# Use this instead of address bar typing (set_value + type_text both broken on Chromium)
mcp_cua_driver_launch_app({"urls": ["https://example.com/path"]})
```

`urls` opens each URL via `ShellExecuteEx` in the default browser without activation. New URLs open as tabs in the existing browser window (no new process). This is the only reliable way to navigate Chromium browsers — address bar `set_value` fails (no ValuePattern), `click` + `type_text` silently drops characters, and pressing Enter is ignored.

## Restoring Minimized Windows

Minimized windows cannot be captured. Restore first:

```python
import ctypes
SW_RESTORE = 9
hwnd = <window_id from list_windows>
ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
```

Use `list_windows(pid)` to get the HWND (window_id field).

## Click Delivery Modes — CRITICAL

| Mode | Use Case |
|------|---------|
| `delivery_mode: "background"` (DEFAULT) | Try FIRST for everything. Win32, UWP, UIA-capable elements |
| `delivery_mode: "foreground"` | ONLY after receiving `background_unavailable` error |

**NEVER guess foreground preemptively.** The driver decides when background is impossible.
A guessed foreground click steals the user's focus needlessly.

### Chromium/Electron Address Bar Navigation — Use `launch_app` with `urls`

Chromium drops PostMessage keystrokes in the address bar. Both AX-based approaches are broken:

- **`set_value` on address bar Edit**: The Chrome address bar Edit does NOT implement `ValuePattern` — returns error immediately.
- **`click` + `type_text` with foreground delivery**: Even after clicking the address bar and typing via foreground SendInput, the URL value in the AX tree does NOT update — old URL persists. Typed text may not land in the renderer. Wastes multiple round-trips for no result.

**DO NOT try address bar typing.** The only reliable navigation method for Chromium browsers is:

```json
mcp_cua_driver_launch_app({"urls": ["https://target-url.com/path"]})
```

Opens the URL via `ShellExecuteEx` in the default browser. May open as a new tab in an existing Chrome window. Returns pid immediately — call `list_windows(pid)` after a moment if windows aren't reported. This is a one-shot, deterministic navigation method that bypasses all Chromium input routing issues.
- **`click` + `type_text` with foreground delivery**: Even after clicking the address bar and typing via foreground SendInput, the URL value in the AX tree does NOT update — old URL persists. Typed text may not land in the renderer at all.

**Reliable workaround: use `launch_app` with `urls` parameter.** Opens the URL via `ShellExecuteEx` — most reliable way to navigate Chrome:

```json
mcp_cua_driver_launch_app({"urls": ["https://copilotstudio.microsoft.com/"]})
// Returns pid. May open as new tab in existing Chrome.
// Windows may not appear immediately — call list_windows(pid) a moment later.
```

Do NOT waste time typing into the Chrome address bar via AX — both `set_value` and `type_text` paths are broken. `launch_app` urls is the one-shot navigation method.

**CRITICAL: always include the `http://` prefix.** Chrome's omnibox treats bare `host:port` as a search query. Always type full URLs with protocol prefix.

## WinForms DataGridView Scrolling

WinForms grid scrollbars have broken UIA patterns:
- Page Up/Page Down buttons are NOT indexed (unlabeled siblings in the scrollbar tree)
- `set_value` on the scrollbar is silently ignored
- Line Down clicks work but are 1-row per click

**Workaround:** Send `pagedown` key directly:
```python
mcp_cua_driver_press_key(key="pagedown", pid=<pid>, delivery_mode="foreground")
```

## Electron Webview Panels Need an On-Screen Window

VS Code (and other Electron apps) render extension panels inside a webview. The webview's
DOM/content is **not exposed to UIA or screenshots while the window is minimized** — the
capture returns `cannot capture minimized window … no rendered content` (PrintWindow / BitBlt
return all-black for iconic windows).

What still works minimized: UIA clicks on the **native chrome** (activity-bar tabs, menus,
toolbar buttons) via the SelectionItem/Invoke pattern. You CAN switch tabs (e.g. click the
"Copilot Studio" activity-bar item) while minimized — the click lands and the panel mounts —
but you cannot yet *see or read* the panel's inner content.

To inspect the panel content, restore the window to the screen first:

```python
import ctypes
SW_RESTORE = 9
ctypes.windll.user32.ShowWindow(<window_id>, SW_RESTORE)  # or mcp_cua_driver_list_apps(pid, raise_window=True)
```
One brief on-screen flash is enough to capture/screenshot the webview, then re-minimize.
`bring_to_front(pid)` also restores but steals foreground focus (see Click Delivery Modes).

Use this sequence for extension-driven panels (Copilot Studio clone/preview/apply, etc.):
launch minimized → UIA-click the tab (background-safe) → restore → screenshot to find buttons
→ drive the webview. Verified live: minimized VS Code accepted the Copilot Studio tab click;
the panel only became inspectable after restore.

## Pitfalls

- **Window IDs expire** after window recreation (session timeout, restart). Always re-list before capture.
- **Element indices are snapshot-scoped** — a new `get_window_state` replaces the index map.
- **WinForms `DataGrid` scrollbar** `set_value` is ignored; prefer keyboard paging.
- **`bring_to_front` doesn't restore minimized windows** — use `ShowWindow` first.
- **`start_minimized` in `launch_app` works for ShellExecuteEx apps** but may not for packaged (UWP) apps.
- **SPA web-app page content invisible to AX tree.** Heavy JS-rendered SPAs (Copilot Studio, Power Apps, modern SharePoint) often expose only the browser chrome (toolbar, tabs, bookmarks) in the AX tree — the page content below the toolbar is absent even with high `max_elements`. **Workaround:** Use `vision_analyze` on the captured screenshot to understand page layout and identify pixel coordinates for navigation targets. Pixel clicks may still be unreliable due to coordinate translation — prefer `launch_app` with `urls` for navigation, and accept that some UI operations require manual user steps.
- **Admin/UAC elevation impossible via background automation.** `computer_use` cannot trigger the Win+X menu, Start menu searches, or Ctrl+Shift+Enter reliably from background mode — the Win key press does not open the Start menu on the secure desktop, right-click context menus don't render in the AX tree, and foreground delivery may not be supported by the installed cua-driver build. UAC prompts appear on a separate secure desktop invisible to capture. `Start-Process -Verb RunAs` triggers a UAC prompt the user must approve manually. `schtasks /Create /RU SYSTEM` also needs admin rights (chicken-and-egg). **Workaround:** Ask the user to open Terminal (Admin) themselves and paste the command — a 10-second ask when they're present.

## Chrome CDP Port Binding on Windows — Known Pitfall

Launching Chrome with `--remote-debugging-port=N` (e.g. port 9223) for `execute_javascript` does NOT reliably work on Windows.

**Symptoms:**
- `netstat -ano | Select-String ':9223'` returns empty after launch
- `Get-WmiObject Win32_Process` shows `--remote-debugging-port=9223` on child/renderer processes, but the main browser process never binds the port
- `curl http://127.0.0.1:9223/json/version` returns connection refused
- `mcp_cua_driver_page(action='execute_javascript', ...)` errors: "relaunch the browser with --remote-debugging-port=N"

**Root cause:** On Windows, the Chrome process model shares a single browser process per user data directory. The `--remote-debugging-port` flag is inherited by child processes (renderer, GPU, utility) but the parent browser process that actually opens the TCP socket ignores it. Even `taskkill //F //IM chrome.exe` doesn't fully reset the shared browser process state.

**Attempted workarounds that didn't reliably work:**
- `taskkill //F //IM chrome.exe` then fresh launch with `--remote-debugging-port=9223`
- `cmd /c "start \"\" \"chrome.exe\" --remote-debugging-port=9223"`
- `Start-Process` with `--remote-debugging-port` from PowerShell
- `--user-data-dir=<fresh-dir>` (forces new profile but still CEF may detach)
- `mcp_cuda_driver_launch_app` with `additional_arguments`

**Workarounds when CDP isn't available:**
1. **`query_dom(css_selector)`** — UIA-based read-only DOM queries. Supports simple tags: `button`, `a`, `input`, `h1-h6`, `p`, `span`, `select`, `textarea`, `li`, `img`; also `tag#id` and `[role=…]`. No CDP needed.
2. **`get_text()`** — UIA TextPattern read (fails on some Chromium pages that don't expose it).
3. **Bookmark workaround** — Create a bookmark named `cua-driver-eval` in Chrome's Favorites bar. The driver overwrites its URL on first use, enabling `execute_javascript` without CDP.
4. **UIA enter-key workaround** — Chromium drops `PostMessage(WM_KEYDOWN, VK_RETURN)` in the address bar. Use `set_value` on `Edit` element to type URL, then click the Reload button (element index) rather than pressing Enter.
5. **`az` CLI fallback** — For Copilot Studio auth, use `az account get-access-token --resource '<resource>' --query accessToken -o tsv` via `powershell -Command` instead of browser CDP. This is the most reliable auth path for Dataverse REST API and gateway API.

## Reference Files

- `references/copilot-studio-knowledge-upload.md` — Copilot Studio knowledge file upload patterns via computer use: UI-only constraint, upload-ready manifest pattern, Chrome AX tree limitation for SPAs, address bar input failure, bot ID mismatch, and effective handoff strategy.
- `references/nethealth-optima.md` — NetHealth Rehab Optima (Care Operations Manager): architecture, installation, reports console, automation strategy, key reports for SLP CMI detection
- `references/pcc-api.md` — PointClickCare EHR REST API v2: endpoints, auth, ICD-10 swallowing codes, access tiers, data limitations
- `references/monitoring-browser-ai-agents.md` — Polling and verifying completion of browser-based AI agents (Gemini, Copilot) in Chrome. Covers: Chrome crash recovery + conversation history restoration, Power Automate flow testing and node search, Dataverse "Invalid Character" documentbody fix, and all known pitfalls for Chromium automation on Windows.
- `references/project-flow-mapping.md` — Project-specific flow-to-topic mapping for Therapy AI Agents Dev environment. Lists all 8 topics that reference the OCR Text Extraction flow, their binding patterns, and the flow input resolution chain. Useful when debugging flow failures or verifying topic correctness.
