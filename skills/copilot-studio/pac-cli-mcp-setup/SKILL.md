---
name: pac-cli-mcp-setup
description: Setup guide for Power Platform CLI MCP server — enables natural language PAC CLI commands through VS Code Copilot. Covers installation, MCP configuration, and PAC CLI best practices.
---

# Power Platform CLI MCP Server Setup

Source: microsoft/agent-academy (special-ops/pac-cli-mcp)

## Overview
The Power Platform CLI (v1.44+) includes a built-in MCP server that exposes 20+ PAC CLI commands as tools for AI assistants. Issue natural language commands; the AI handles translation to PAC CLI syntax.

## Installation

### 1. Install PAC CLI (global)
```bash
dotnet tool install --global Microsoft.PowerApps.CLI.Tool
```
Verify: `pac` → shows version (e.g., Microsoft PowerPlatform CLI v2.4.1)

Update: `dotnet tool update --global Microsoft.PowerApps.CLI.Tool`

### 2. Configure MCP Server in VS Code
1. Open VS Code command palette (Ctrl+Shift+P)
2. Search for "MCP" and select `MCP: Add Server`
3. Select `Command (stdio)`
4. Paste: `pac copilot mcp --run`
5. Name: `Power Platform CLI MCP`

### Supported Operations
- Environment Management — List, create, manage Power Platform environments
- Solution Operations — Import, export, package solutions
- Authentication — Handle auth profiles, tenant connections
- Dataverse Operations — Work with tables, data, configurations
- Power Pages — Manage website deployments
- Component Management — Handle PCF controls

### Best Practices
- Enable only the commands the mission requires
- Review tool permissions before granting access
- Use environment-specific configurations
- Monitor MCP server logs for all executed commands

### Troubleshooting
- MCP Server Not Found → Verify path with `pac copilot mcp`, ensure CLI v1.44+
- Authentication Errors → Run `pac auth list`, use `pac auth create` to set up
- Tool Access Warnings → Check Output window in VS Code for MCP messages
