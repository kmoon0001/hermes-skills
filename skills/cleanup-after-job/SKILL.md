---
name: cleanup-after-job
description: Use when wrapping up a Copilot Studio agent session. Removes temp scripts, screenshots, eval artifacts, .bak files, old debug logs, and test scripts created during the session. Keeps committed files, git history, and config.
category: devops
---

# Cleanup After Job

## Overview
Removes temporary artifacts created during a Copilot Studio agent debug session. Designed to run at the end of a fix loop or when handing off to another session. Leaves committed code, config, and git history untouched.

## What Gets Cleaned

### Scripts
- `C:\Users\kevin\skills-for-copilot-studio\scripts\poll_*.py` — ad-hoc eval polling scripts
- `C:\Users\kevin\skills-for-copilot-studio\scripts\wait_and_run_*.py`
- Any `.py` or `.cjs` file created during the session that starts with `poll_`, `wait_`, `temp_`, `test_`, `debug_`
- Exception: `refresh_eval_token.cjs`, `eval_harness.py`, `poll_robust.py` (reusable) are KEPT

### Screenshots & Images
- `C:\Users\kevin\Desktop\*.png` — browser vision screenshots
- `C:\Users\kevin\*.png` — stray screenshots in home dir
- Hermes cache: `%USERPROFILE%\AppData\Local\hermes\profiles\coding-profile\cache\*`
- Browser download folder temp images

### Eval Artifacts
- `D:\my agents copilot studio\pipeline\*_eval_state.json` — per-session eval state files
- `D:\my agents copilot studio\pipeline\eval_full_details\*.json` — old eval detail dumps (keep last 3)
- `D:\my agents copilot studio\pipeline\_*.cjs` — underscore-prefixed temp scripts

### Agent Workspace Debris
- `D:\my agents copilot studio\*\ot-*.md` — old debug observation transcripts
- `D:\my agents copilot studio\*\pt-*.md`
- `D:\my agents copilot studio\*\tda-*.md`
- `D:\my agents copilot studio\*\*.bak` — topic YAML backups (git handles versioning)
- `D:\my agents copilot studio\*\scratch\*` — scratch/export artifacts
- Exception: KEEP `agent.mcs.yml.bak` (intentional backup)

### Token & Auth Debris
- `C:\Users\kevin\.copilot-studio-cli\*_err.txt` — error logs
- `C:\Users\kevin\.copilot-studio-cli\*_result.json` — per-run result files
- Exception: KEEP `test-agent-token.txt`, `manage-agent.cache.json`, `test-agent.cache.json`

### Cron Jobs
- Old polling cron jobs that have served their purpose
- Exception: KEEP recurring jobs (daily briefings, watchdogs)

## Execution

Run this at workspace root:
```bash
# Remove ad-hoc poll scripts
rm -f /c/Users/kevin/skills-for-copilot-studio/scripts/poll_*.py
rm -f /c/Users/kevin/skills-for-copilot-studio/scripts/wait_and_run_*.py

# Remove temp underscore-prefixed scripts in pipeline
rm -f /d/my\ agents\ copilot\ studio/pipeline/_*.cjs

# Remove eval state JSONs
rm -f /d/my\ agents\ copilot\ studio/pipeline/*_eval_state.json

# Remove debug transcripts from agent workspaces
for dir in /d/my\ agents\ copilot\ studio/*/; do
  rm -f "$dir"ot-*.md "$dir"pt-*.md "$dir"tda-*.md "$dir"*.bak
done

# Remove scratch artifacts
for dir in /d/my\ agents\ copilot\ studio/*/scratch/; do
  rm -rf "${dir}"*
done

# Remove screenshots
rm -f /c/Users/kevin/Desktop/*.png 2>/dev/null

# Remove token error/result debris
rm -f /c/Users/kevin/.copilot-studio-cli/*_err.txt
rm -f /c/Users/kevin/.copilot-studio-cli/*_result.json
rm -f /c/Users/kevin/.copilot-studio-cli/pcch_*.json

# Clear Hermes web cache
rm -rf /c/Users/kevin/AppData/Local/hermes/profiles/coding-profile/cache/web/*
rm -rf /c/Users/kevin/AppData/Local/hermes/profiles/coding-profile/cache/browser/*
```

## Verification
- [ ] No stray `poll_*.py` in scripts directory
- [ ] No `_*.cjs` in pipeline directory
- [ ] No `*_eval_state.json` in pipeline directory
- [ ] No `ot-*.md`, `pt-*.md`, `tda-*.md` in agent workspaces
- [ ] Scratch directories empty
- [ ] Screenshots cleaned from Desktop
- [ ] Token/result debris gone from `.copilot-studio-cli`
- [ ] Cache directories empty
- [ ] `.bak` files removed (exception: agent.mcs.yml.bak if exists)

## Kiro Hook Integration
Save this as a Kiro hook to run automatically after each session:
- File: `C:\Users\kevin\.kiro\skills\cleanup-hook.json`
- Trigger: on session end / on session reset
- Action: execute the cleanup script

## Safety
- NEVER remove: `*.git`, `.mcs/`, `agent.mcs.yml`, `settings.mcs.yml`, `conn.json`, `manage-agent.cache.json`, `test-agent-token.txt`
- NEVER remove: files with uncommitted changes (check `git status` first)
- NEVER remove: node_modules, installed tools, config files
- ALWAYS run `git status` first to confirm no uncommitted work before cleaning
