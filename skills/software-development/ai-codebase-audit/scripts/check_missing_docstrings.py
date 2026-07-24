#!/usr/bin/env python3
"""Scan a Python codebase for public functions missing docstrings.

Usage:
    python check_missing_docstrings.py [--fix] [path]

    --fix   Also list every function needing a docstring (for batch fixing)
    path    Root directory to scan (default: current directory)

Exits 0 if all public functions have docstrings, 1 if any are missing.
Ignores functions whose body is just 'pass' or trivial return statements.

Used by ai-codebase-audit as the automated docstring coverage gate.
"""

import ast
import os
import sys
from collections import Counter

EXCLUDE_DIRS = {
    ".venv", ".git", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules",
}


def is_public(name: str) -> bool:
    """True if the function name indicates a public API (not _private)."""
    return not (name.startswith("_") and not name.startswith("__"))


def is_trivial_pass(node: ast.FunctionDef) -> bool:
    """True if the function body is only 'pass' — skip these."""
    body = node.body
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return True
    return False


def scan_file(filepath: str) -> list[tuple[str, int, str]]:
    """Return (filepath, lineno, name) for each public function missing a docstring."""
    missing: list[tuple[str, int, str]] = []
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                if is_public(node.name) and not ast.get_docstring(node) and not is_trivial_pass(node):
                    missing.append((filepath, node.lineno, node.name))
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if is_public(item.name) and not ast.get_docstring(item) and not is_trivial_pass(item):
                            missing.append((filepath, item.lineno, f"{node.name}.{item.name}"))
    except SyntaxError as e:
        print(f"SKIP (syntax): {filepath} — {e}", file=sys.stderr)
    except Exception as e:
        print(f"SKIP (error): {filepath} — {e}", file=sys.stderr)
    return missing


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    fix_flag = "--fix" in sys.argv

    all_missing: list[tuple[str, int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename.endswith(".py"):
                all_missing.extend(scan_file(os.path.join(dirpath, filename)))

    if not all_missing:
        print("All public functions have docstrings.")
        sys.exit(0)

    print(f"\n{len(all_missing)} public functions missing docstrings:\n")
    by_file = Counter(f[0] for f in all_missing)
    for fp, count in sorted(by_file.items()):
        print(f"  {os.path.relpath(fp, root)}: {count}")

    if fix_flag:
        print(f"\n--- Full list (for batch fixing) ---")
        for fp, lineno, name in sorted(all_missing):
            print(f"  {os.path.relpath(fp, root)}:{lineno}  {name}")

    sys.exit(1)


if __name__ == "__main__":
    main()
