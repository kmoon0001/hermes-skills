---
name: copilot-studio-clone-agent
description: "Clone a Copilot Studio agent from the cloud via manage-agent.bundle.js. Guides through environment selection, agent selection, and downloads agent YAML files."
category: copilot-studio
---

# Clone Agent

Guided flow to clone a Copilot Studio agent from the cloud to a local workspace.

## IMPORTANT: Do Not Modify Scripts
If manage-agent script fails, report error to https://github.com/microsoft/skills-for-copilot-studio/issues. Do not attempt to fix.

## Phase 0: Resolve Configuration
Search for existing `.mcs/conn.json` files via Glob. If found, present to user as options. If user provides a Copilot Studio URL, extract env/agent IDs directly.

## Phase 1: Select Environment
Run: `node manage-agent.bundle.js list-envs --tenant-id <tenantId>` (timeout 300s). Present numbered list, ask user to pick.

## Phase 2: Select Agent
Run: `node manage-agent.bundle.js list-agents --tenant-id <tid> --environment-url <url> [--no-owner]` (timeout 300s). Present numbered list, ask user to pick.

## Phase 3: Clone
```bash
node manage-agent.bundle.js clone --workspace "." --tenant-id "<tid>" --agent-id "<aid>" --environment-id "<eid>" --environment-url "<url>" --agent-mgmt-url "<mgmtUrl>"
```
On success, Glob for `**/agent.mcs.yml` and summarize what was cloned.

## Error Handling
| Error | Resolution |
|-------|-----------|
| Browser auth fails | Retry, verify tenant access |
| No environments | Verify tenant ID |
| Clone fails | Check permissions |