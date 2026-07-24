---
name: notebooklm-research
description: "NotebookLM CLI and MCP integration — create research notebooks, add sources via deep web research, generate slide decks (PPTX). Auth, setup, and full workflow."
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos, windows]
metadata:
  notebooklm:
    cli_package: notebooklm-mcp-cli
    mcp_tools: 39
tags: [notebooklm, mcp, research, slides, knowledge-base]
---

# NotebookLM Research Workflow

## Overview

NotebookLM can be driven programmatically via `nlm` CLI or the `notebooklm-mcp` MCP server. Use for: building knowledge bases, research aggregation, slide deck generation from curated sources.

## Install

```bash
# Install CLI + MCP server (single PyPI package)
uv tool install notebooklm-mcp-cli

# Installs two executables: nlm, notebooklm-mcp
```

## Authentication

### Automated (Windows - works with Windows Hello passkey)
```bash
nlm login
# Opens Chrome, user signs in to Google/NotebookLM
# If Windows Hello passkey is available, click the passkey option
# Result: 32+ cookies extracted, saved to ~/.notebooklm-mcp-cli/profiles/default
```

### Check auth status
```bash
nlm login --check
# Expected: "Authentication valid! Notebooks found: N"
```

### Manual Cookie Method (fallback)
```bash
nlm login --manual -f /path/to/cookies.txt
```

## Hermes MCP Server Integration

```bash
# Add to Hermes config
hermes mcp add notebooklm-mcp --command "C:\Users\kevin\.local\bin\notebooklm-mcp.exe"
# 39 tools available after /reset
```

## CLI Workflow

### Create Notebook
```bash
nlm notebook create "Notebook Title"
# Returns { notebook_id, title, url }
```

### Add Sources by URL
```bash
nlm source add <notebook-id> \
  -u "https://example.com/doc1" \
  -u "https://example.com/doc2" \
  --wait
# --wait blocks until sources are processed (recommended for reliability)
```

### Deep Web Research
```bash
nlm research start "Research query" \
  -n <notebook-id> \
  --mode deep \
  --auto-import
# deep = ~5 min, ~40-90 sources
# fast = ~30 sec, ~10 sources
# --auto-import = wait + import discovered sources automatically
```

### Query Notebook
```bash
nlm notebook query <notebook-id> "Your question about the sources"
# Returns structured answer with citations (source IDs referenced)
```

### Generate Slide Deck
```bash
nlm slides create <notebook-id> --confirm
# Returns artifact-id for tracking
```

### Check Slide Deck Status
```bash
nlm studio status <notebook-id> --artifact-id <id> --full --json
# Status transitions: unknown → (wait) → completed
# MUST pass --full to see the download URL. A NON-full status call returns
#   slide_deck_url: null even when status is "completed" — the URL only appears
#   in the --full JSON (read the slide_deck_url field, NOT the top-level 'url').
# Extract: ... | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['slide_deck_url'])"
```

### Download Artifacts
```bash
# Subcommand is HYPHENATED: slide-deck (NOT slide_deck — that errors)
# artifact-id is a --id FLAG, NOT a positional arg
nlm download slide-deck <notebook-id> \
  --id <artifact-id> \
  -o ~/Desktop/deck.pdf \
  --format pdf           # pdf (default) | pptx
# Also supports: audio, video, report, infographic, data_table, quiz, flashcards
```

## Pitfalls

- Windows: use the native Windows path for `hermes mcp add` (e.g. `C:\Users\kevin\.local\bin\notebooklm-mcp.exe`), NOT MSYS paths
- Chrome navigation via UIA often fails with Enter key — use `delivery_mode: "foreground"` for pixel-level clicks on Chrome's address bar
- `nlm research start` takes query as positional argument, notebook-id via `-n` flag
- `nlm studio create` does NOT exist — use `nlm slides create` for slide decks
- Slide deck generation status shows "unknown" for several minutes while processing
- Some URL sources may return 404 (page not found) — delete those with `nlm source delete <id> --confirm`
- The `hermes-webui` community package does NOT work on Windows (filesystem access errors)
- The official `hermes dashboard` IS the correct GUI for Windows — starts at `http://127.0.0.1:9119` (or custom port)
- **`nlm download` subcommand is hyphenated:** use `nlm download slide-deck` (NOT `slide_deck` — that errors "No such command 'slide_deck'. Did you mean 'slide-deck'?")
- **artifact-id is a `--id` flag, not positional:** `nlm download slide-deck <nb> --id <artifact-id> -o out.pdf`. Passing it as a 2nd positional arg fails with "Got unexpected extra argument(s)".
- **Default download format is `pdf`** (not pptx). Pass `--format pptx` for PowerPoint. PDF is smaller and reliably downloadable.
- **`nlm studio status` needs `--full` to reveal the URL:** a non-`--full` status returns `slide_deck_url: null` even when status == "completed". Read `slide_deck_url` (not `url`) from the `--full --json` output.

## Related MCP Tools

- `notebooklm-mcp` — 39 tools including: notebook_list/create/query, source_add, research_start/status/import, studio_create/status, download_artifact, batch, cross_notebook_query
