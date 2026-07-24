# Tool .cache Directory Reference

Cleanup mapping for `C:\Users\kevin\.cache\` on Windows. These are downloaded tool runtimes and model files that can be safely deleted and auto-recovered.

| Directory | Typical Size | What It Is | Auto-Recoverable? |
|-----------|-------------|------------|-------------------|
| `puppeteer/` | 1.9 GB | Chromium for Playwright/Puppeteer | ✅ Re-downloads on next script run |
| `codex-runtimes/` | 1.4 GB | OpenAI Codex CLI runtime cache | ✅ Re-downloads on next `codex` |
| `chrome-devtools-mcp/` | ~950 MB | Chrome DevTools MCP tools | ✅ Re-downloads on next use |
| `webwright/` | ~410 MB | Microsoft Webwright browser agent | ✅ Re-clones on next use |
| `huggingface/` | ~230 MB | ML model files | ✅ Re-downloads on next model use |
| `claude/` | 0-50 MB | Claude AI cache | ✅ Auto-rebuilds |
| `vscode-ripgrep/` | ~2 MB | VS Code ripgrep search tool | ✅ Re-downloads |
| `kilo/` | ~20 MB | Unknown npm tool cache | Likely |

## When to Clean
- C: drive critically low (< 5% free)
- Tool is no longer in active use
- Before large software installations

## How to Clean Specific Tools
```bash
# All at once
rm -rf ~/.cache/*

# Specific
rm -rf ~/.cache/codex-runtimes    # 1.4 GB — Codex runtimes
rm -rf ~/.cache/webwright          # 410 MB — Webwright
rm -rf ~/.cache/huggingface        # 230 MB — ML models
```
