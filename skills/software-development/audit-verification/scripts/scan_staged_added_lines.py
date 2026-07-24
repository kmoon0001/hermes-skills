#!/usr/bin/env python3
"""Fail-closed static scan of added lines in the staged Git diff.

The report contains only finding categories and counts, never matched source
text, so credentials are not copied into logs. Exit codes: 0 clean, 1 finding,
2 scanner or Git failure.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

PATTERNS: dict[str, re.Pattern[str]] = {
    "hardcoded_secret": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|token|passwd)\b\s*[:=]\s*"
        r"(['\"])[^'\"\r\n]{6,}\1"
    ),
    "shell_injection": re.compile(r"os\.system\(|subprocess[^\n]*shell\s*=\s*True"),
    "dangerous_eval": re.compile(r"\b(?:eval|exec)\s*\("),
    "unsafe_pickle": re.compile(r"\bpickle\.loads?\s*\("),
    "sql_format": re.compile(
        r"execute\s*\(\s*f['\"]|\.format\s*\([^\n]*(?:SELECT|INSERT|UPDATE|DELETE)",
        re.IGNORECASE,
    ),
}


def staged_added_lines() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--unified=0", "--no-color"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "git diff --cached failed"
        raise RuntimeError(message)
    return [
        line[1:]
        for line in result.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def main() -> int:
    try:
        added = "\n".join(staged_added_lines())
    except (OSError, RuntimeError) as exc:
        print(json.dumps({"scanner_error": str(exc)}))
        return 2

    findings = {
        name: len(pattern.findall(added))
        for name, pattern in PATTERNS.items()
        if pattern.search(added)
    }
    print(json.dumps({"passed": not findings, "findings": findings}, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
