# Kiro Full MCP Stack (snapshot 2026-07-24)

Real-world reference: 8 MCP servers powering a production Copilot Studio agent development environment alongside Hermes. Extracted from `C:\Users\kevin\.kiro\settings\mcp.json`.

## Server Inventory

| Server | Transport | Command | Purpose |
|--------|-----------|---------|---------|
| `filesystem` | npx | `@modelcontextprotocol/server-filesystem "D:\my agents copilot studio"` | Read/write agent YAML, topics, settings |
| `memory` | npx | `@modelcontextprotocol/server-memory` | Cross-agent shared knowledge graph |
| `playwright` | npx | `@playwright/mcp` with session persistence | Browser automation for Copilot Studio UI |
| `git` | uvx | `mcp-server-git --repository "D:\my agents copilot studio"` | Structured git ops on agent repo |
| `fetch` | uvx | `mcp-server-fetch` | URL fetching (raw, no summarization) |
| `sequential-thinking` | npx | `@modelcontextprotocol/server-sequential-thinking@latest` | Structured multi-step reasoning |
| `github` | npx | `@modelcontextprotocol/server-github` | GitHub API (needs GITHUB_PERSONAL_ACCESS_TOKEN) |
| `pdf-tools` | python | Custom Python server at `C:\Users\kevin\.kiro\tools\pdf-tools-server.py` | PDF merge, split, text-to-PDF, info |

## Hermes Gaps (as of 2026-07-24)

Hermes has 4 MCP servers (microsoft-learn, cua-driver, shared_memory, notebooklm-mcp). Servers from Kiro's stack worth adding:

- **sequential-thinking** — clear gap; structured reasoning for complex decomposition
- **git** — structured JSON output beats raw terminal git for LLM parsing
- **github** — structured API; check if GH token available
- **fetch** — redundant with Hermes `web_extract`; low priority

Servers NOT worth adding:
- **filesystem** — Hermes native file tools (read_file, write_file, search_files, patch) are superior
- **playwright** — Hermes browser tools + computer_use cover this

## Key Config Pattern: autoApprove

Kiro auto-approves specific tools per server. Hermes uses global `approvals.mode:smart`. This is a design difference, not a gap — Hermes' `smart` mode delegates approval to an auxiliary LLM rather than a static allowlist.

## Memory Server Gotcha (confirmed)

Kiro's memory server has `"env": {}` (empty), which per the native-mcp skill's GOTCHA 2 means it falls back to a file inside the npx cache directory instead of the shared graph path. This is a known issue — the `shared-mcp-memory-graph` skill documents the fix: set `MEMORY_FILE_PATH` to the absolute path of the shared `.jsonl` file.

## Full Raw Config

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "D:\\my agents copilot studio"],
      "env": {},
      "disabled": false,
      "autoApprove": ["read_text_file", "read_file", "read_multiple_files", "read_media_file",
        "write_file", "edit_file", "create_directory", "move_file", "search_files",
        "get_file_info", "list_directory", "list_directory_with_sizes", "directory_tree",
        "list_allowed_directories"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {},
      "disabled": false,
      "autoApprove": ["read_graph", "create_entities", "create_relations", "add_observations",
        "open_nodes", "search_nodes", "delete_entities", "delete_observations", "delete_relations"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp",
        "--output-dir", "D:\\my agents copilot studio\\.playwright-mcp",
        "--user-data-dir", "D:\\my agents copilot studio\\.playwright-auth",
        "--save-session", "--timeout-navigation", "90000", "--timeout-action", "10000"],
      "env": {},
      "disabled": false,
      "autoApprove": ["browser_navigate", "browser_snapshot", "browser_click",
        "browser_take_screenshot", "browser_console_messages", "browser_tabs",
        "browser_type", "browser_close", "browser_wait_for", "browser_hover",
        "browser_select_option", "browser_fill_form", "browser_press_key",
        "browser_evaluate", "browser_navigate_back", "browser_drop",
        "browser_file_upload", "browser_resize", "browser_handle_dialog",
        "browser_network_requests", "browser_network_request", "browser_drag",
        "browser_run_code_unsafe", "browser_find", "browser_run_code"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "D:\\my agents copilot studio"],
      "env": {"FASTMCP_LOG_LEVEL": "ERROR"},
      "disabled": false,
      "autoApprove": ["git_add", "git_commit", "git_status", "git_diff_unstaged",
        "git_diff_staged", "git_diff", "git_log", "git_show", "git_create_branch",
        "git_checkout", "git_branch", "git_reset"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {"PYTHONIOENCODING": "utf-8", "FASTMCP_LOG_LEVEL": "ERROR"},
      "disabled": false,
      "autoApprove": ["fetch"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking@latest"],
      "env": {},
      "disabled": false,
      "autoApprove": ["sequentialthinking"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"},
      "disabled": false,
      "autoApprove": ["get_file_contents", "search_repositories", "search_code",
        "search_issues", "search_users", "list_commits", "list_issues", "get_issue",
        "get_pull_request", "list_pull_requests", "get_pull_request_files",
        "get_pull_request_status", "get_pull_request_comments", "get_pull_request_reviews",
        "create_or_update_file", "push_files", "create_repository", "create_issue",
        "update_issue", "add_issue_comment", "create_pull_request",
        "create_pull_request_review", "merge_pull_request", "fork_repository",
        "create_branch", "update_pull_request_branch"]
    },
    "pdf-tools": {
      "command": "python",
      "args": ["C:\\Users\\kevin\\.kiro\\tools\\pdf-tools-server.py"],
      "env": {},
      "disabled": false,
      "autoApprove": ["merge_pdfs", "split_pdf", "text_to_pdf", "pdf_info"]
    }
  }
}
```
