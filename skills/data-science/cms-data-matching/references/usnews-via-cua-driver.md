# Accessing US News via User's Chrome (cua-driver)

health.usnews.com blocks Playwright browsers and curl with **infinite SSL renegotiation** — the connection establishes but the server never sends data. However, it loads fine from a **real Chrome instance** with a residential IP (Cox, etc.).

## Using cua-driver to navigate user's Chrome

1. **Launch** the app via `mcp_cua_driver_launch_app` or find an existing instance with `list_apps`
2. **Get the window** with `list_windows(pid=<pid>)` to find the window_id
3. **Navigate** by setting the address bar value and pressing Enter:
   - Set via `mcp_cua_driver_set_value(element_index=<addr_bar_idx>, pid=<pid>, window_id=<wid>, value="url")`
   - Press Enter via `mcp_cua_driver_press_key(key="enter", pid=<pid>, window_id=<wid>, delivery_mode="foreground")`
   
**IMPORTANT:** Chrome's address bar is a UIA Edit element. `set_value` via UIA ValuePattern works but the renderer may not observe it. Always verify by checking the screenshot afterward.

## Caveats

- **No CDP by default**: Chrome isn't launched with `--remote-debugging-port`. To use `execute_javascript`, relaunch with that flag or set up the `cua-driver-eval` bookmark bypass.
- **Foreground delivery required**: Chromium web content doesn't accept background PostMessage clicks. Use `delivery_mode="foreground"` for all clicks on page content.
- **Coordinate mapping**: Screenshot pixels ≠ window-local pixels when the window is on a HiDPI display. The driver auto-translates but off-screen elements break.
- **get_text and query_dom** only return the UIA tree, not the actual DOM — they show Chrome chrome (tabs, address bar), not page content. For page text, you need the CDP path.
- **Page content is in a GPU-rendered surface** not exposed to UIA as individual elements. You can't click buttons by element_index on the page content — only pixel coordinates work.

## URL Patterns for US News Nursing Homes

- Search: `https://health.usnews.com/best-nursing-homes/search?q=<name>&city=<city>&state=<state_abbr>`
- By city: `https://health.usnews.com/best-nursing-homes/<state>/<city>`
- Individual facility: pattern appears to use slug-based URLs like `https://health.usnews.com/best-nursing-homes/<state>/<city>/<facility-slug>-<id>`
