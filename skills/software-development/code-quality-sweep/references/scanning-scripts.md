# Quality Sweep Scanning Scripts

These are the exact Python scanning scripts used in the July 2026 sweep of the
freqtrade-cycle5-research codebase. Run them from the project root.

## Docstring Coverage Scan

```python
"""Scan a Python codebase for public functions missing docstrings."""
import ast, os, re

exclude_dirs = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if not file.endswith('.py'):
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath) as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    if not (node.name.startswith('_') and not node.name.startswith('__')):
                        if not ast.get_docstring(node):
                            body = node.body
                            # Skip trivial pass/return functions
                            if len(body) == 1 and isinstance(body[0], ast.Pass):
                                continue
                            print(f"{filepath}:{node.lineno}: {node.name}")
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if not (item.name.startswith('_') and not item.name.startswith('__')):
                                if not ast.get_docstring(item):
                                    body = item.body
                                    if len(body) == 1 and isinstance(body[0], ast.Pass):
                                        continue
                                    print(f"{filepath}:{item.lineno}: {node.name}.{item.name}")
        except SyntaxError as e:
            print(f"SKIP (syntax): {filepath}")
```

## Type Annotation Coverage Scan

```python
"""Scan for public functions missing return types and parameter types."""
import ast, os

exclude_dirs = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if not file.endswith('.py') or 'test' in root:
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        if node.returns is None:
                            print(f"{filepath}:{node.lineno}: {node.name} missing return type")
                        for arg in node.args.args:
                            if arg.arg not in ('self', 'cls') and arg.annotation is None:
                                print(f"{filepath}:{node.lineno}: {node.name} missing param type for '{arg.arg}'")
        except SyntaxError:
            pass
```

## Duplicate Function Detection

```bash
# Find functions that appear in multiple files (potential copy-paste)
grep -rn "^def load_json\|^def now_pt\|^def now_iso\|^def atomic_write\|^def compute_metrics" --include="*.py" . | grep -v ".venv\|__pycache__\|.git"
```

## Ruff Lint Commands

```bash
# Auto-fix everything fixable
ruff check . --select=E,F,N,UP --ignore=E501 --fix

# Check remaining manual issues
ruff check . --select=E,F,N,UP --ignore=E501,F401,F841,N802 --output-format=concise

# Categorize remaining issues
ruff check . --output-format=concise | grep -oP "(E402|UP031|E741|N806|E701|F821|F811)" | sort | uniq -c | sort -rn
```

## Full Verification (loop-back check)

```bash
# After all fixes, this should return "All checks passed!"
ruff check . --select=E,F,N,UP --ignore=E501,F401,F841,N802 --output-format=concise

# Final test run
python -m pytest tests/ -q --tb=short
```

## Results from July 2026 Sweep (freqtrade-cycle5-research)

| Category | Before | After |
|----------|:------:|:-----:|
| Docstrings coverage | ~62% (185 missing) | 100% (480/480) |
| Ruff errors | 173 | 0 |
| Runtime bugs (F821) | 3 | 0 |
| Bare excepts | 0 | 0 |
| Duplicated utilities | 7 functions x2-5 copies | 0 (all centralized in production/util.py) |
| Missing return types | 117 | 0 |
| Missing param types | 152 | 0 |
| Hardcoded paths | 2 (benign) | 2 (assessed — comment + env-var fallback) |
| Tests passing | 221 | 221 |
