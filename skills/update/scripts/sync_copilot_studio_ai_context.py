#!/usr/bin/env python3
"""Sync Copilot Studio root-cause safety guidance across project AI context files.

Usage:
  python sync_copilot_studio_ai_context.py "D:/my agents copilot studio"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CENTRAL_TEXT = """# Copilot Studio Root-Cause Safety Rules

These rules apply to Copilot Studio agent work in this repo.

## Hard Rules

1. Read-only first. Inspect live Dataverse/Copilot Studio state before patching.
2. Live UI is truth. Local YAML files are backup snapshots unless explicitly pushed by user request.
3. Never rewrite Copilot Studio YAML quoting, block scalars, formulas, or node structure unless explicitly asked.
4. Never restructure topic YAML just because an error mentions a node. Find the exact root cause first.
5. Never remove clinical, compliance, regulatory, or guardrail content. Only add safety layers.
6. After any PATCH, verify by re-querying live Dataverse and comparing the exact persisted `data` field.
7. Do not trust `pac copilot publish` alone; it can be silent or stale/cached.
8. Use full YAML text scans for Power Fx issues; narrow regex scans miss nested ConditionGroup expressions.

## Required Workflow

1. Reproduce/read the error.
2. Pull live topic/component data from Dataverse.
3. Identify exact bad line(s) and why they fail.
4. Stop and report root cause if the user asked for diagnosis only.
5. Patch only after explicit user approval.
6. Re-query live data and verify only intended lines changed.
7. Publish only after explicit approval.
8. If a reusable lesson is learned, update this file and sync pointers across all AI context files.
"""

MARKER_START = "<!-- COPILOT-STUDIO-ROOT-CAUSE-RULES:START -->"
MARKER_END = "<!-- COPILOT-STUDIO-ROOT-CAUSE-RULES:END -->"
BLOCK = f"""{MARKER_START}

## Copilot Studio Root-Cause Safety

Before changing Copilot Studio live topics or YAML, read `./copilot-studio-root-cause-rules.md`.

Minimum rule: read-only first, identify exact root cause, do not rewrite YAML quoting/block scalars/formulas/node structure unless explicitly asked, verify persisted Dataverse data after any approved PATCH.

{MARKER_END}
"""


def upsert_block(path: Path, heading: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else f"# {heading}\n\n"
    if MARKER_START in text and MARKER_END in text:
        text = text.split(MARKER_START)[0] + BLOCK + text.split(MARKER_END, 1)[1].lstrip("\n")
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n" + BLOCK
    path.write_text(text, encoding="utf-8")
    return str(path)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not root.exists():
        raise SystemExit(f"Project root not found: {root}")

    changed = []
    central = root / "copilot-studio-root-cause-rules.md"
    central.write_text(CENTRAL_TEXT, encoding="utf-8")
    changed.append(str(central))

    for rel, heading in [
        ("AGENTS.md", "Agent Instructions"),
        ("CLAUDE.md", "Claude Instructions"),
        ("HERMES.md", "Hermes Instructions"),
        ("CODEX.md", "Codex Instructions"),
        (".cursorrules", "Cursor Rules"),
        (".github/copilot-instructions.md", "GitHub Copilot Instructions"),
        (".vscode/README.md", "VS Code AI Context"),
    ]:
        changed.append(upsert_block(root / rel, heading))

    cursor = root / ".cursor/rules/copilot-studio-root-cause.mdc"
    cursor.parent.mkdir(parents=True, exist_ok=True)
    cursor.write_text("""---
description: Copilot Studio root-cause-first safety rules for YAML and live Dataverse topic edits
globs: "**/*.yml,**/*.yaml,**/AGENTS.md,**/HERMES.md,**/CLAUDE.md,**/*.md"
---

# Copilot Studio Root-Cause Safety

Read `./copilot-studio-root-cause-rules.md` before changing Copilot Studio topics, formulas, YAML, or publish flow.
""", encoding="utf-8")
    changed.append(str(cursor))

    kiro_steering = root / ".kiro/steering/copilot-studio-root-cause-safety.md"
    kiro_steering.parent.mkdir(parents=True, exist_ok=True)
    kiro_steering.write_text("""---
inclusion: fileMatch
fileMatchPattern: "**/*.yml,**/*.yaml,**/AGENTS.md,**/HERMES.md,**/CLAUDE.md,**/*.md"
---

# Copilot Studio Root-Cause Safety

Read `./copilot-studio-root-cause-rules.md` before changing Copilot Studio topic YAML, formulas, node structure, publish flow, or Dataverse patches.
""", encoding="utf-8")
    changed.append(str(kiro_steering))

    kiro_hook = root / ".kiro/hooks/copilot-studio-root-cause-sync.kiro.hook"
    kiro_hook.parent.mkdir(parents=True, exist_ok=True)
    kiro_hook.write_text(json.dumps({
        "enabled": True,
        "name": "Copilot Studio Root-Cause Safety Sync",
        "description": "Reminds agents to sync Copilot Studio root-cause rules across project AI guidance files.",
        "version": "1",
        "when": {"type": "postToolUse", "toolTypes": ["shell", "file"]},
        "then": {"type": "askAgent", "prompt": "If this affects Copilot Studio debugging, live YAML, Dataverse PATCH, publishing, memories, skills, hooks, steering, AGENTS.md, HERMES.md, Cursor, Kiro, Antigravity, VS Code, or Codex guidance, update ./copilot-studio-root-cause-rules.md and sync pointers across all relevant project AI context files. Do not patch live Copilot topics unless explicitly asked."},
    }, indent=2), encoding="utf-8")
    changed.append(str(kiro_hook))

    for rel in [
        ".kiro/skills/copilot-studio-root-cause-safety.md",
        ".antigravity/copilot-studio-root-cause.md",
        ".vscode/copilot-studio-root-cause.md",
        ".codex/copilot-studio-root-cause.md",
    ]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# Copilot Studio Root-Cause Safety\n\nRead `./copilot-studio-root-cause-rules.md` before Copilot Studio YAML, formula, Dataverse PATCH, or publish-debug work.\n", encoding="utf-8")
        changed.append(str(p))

    print("Synced files:")
    for p in changed:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
