# Windows Disk Cleanup Paths (Verified Safe)

## C: Drive — Tier 1 (Safe, no side effects, auto-rebuilds)

| Item | Typical Size | How to Clear |
|------|-------------|--------------|
| Chrome Service Worker cache | 2+ GB | `rm -rf ~/AppData/Local/Google/Chrome/User Data/Default/Service Worker` |
| Chrome browser cache | 200-300 MB | `rm -rf ~/AppData/Local/Google/Chrome/User Data/Default/Cache` |
| Chrome Code Cache | 150-200 MB | `rm -rf ~/AppData/Local/Google/Chrome/User Data/Default/Code Cache` |
| Edge browser cache | 200-300 MB | `rm -rf ~/AppData/Local/Microsoft/Edge/User Data/Default/Cache` |
| pip cache | 200-250 MB | `pip cache purge` |
| MSYS /tmp | 500-700 MB | `rm -rf /tmp/*` |
| VS Code CachedData | 100-150 MB | `rm -rf ~/AppData/Roaming/Code/CachedData` |
| Windows Temp | 50-500 MB | `rm -rf ~/AppData/Local/Temp/*` |

## C: Drive — Tool Caches (~/.cache/)

| Item | Typical Size | Safe? | Notes |
|------|-------------|-------|-------|
| `puppeteer` | 1.9 GB | Keep if using Playwright | Full Chromium for Playwright |
| `codex-runtimes` | 1.4 GB | Keep if using Codex CLI | Rebuilds by running `codex` |
| `chrome-devtools-mcp` | 900 MB | Keep if using DevTools MCP | Auto-rebuilds |
| `webwright` | 400 MB | Safe to delete | Re-downloads if needed |
| `huggingface` | 200 MB | Safe to delete | ML model cache, re-downloads |
| `claude` | 0 MB | Trivial | - |
| `vscode-ripgrep` | 2 MB | Trivial | - |

## Notes
- Locked files (Chrome running, active processes) can't be deleted until the app is closed
- All caches auto-rebuild when their tool is next used
- Desktop files are excluded from cleanup
