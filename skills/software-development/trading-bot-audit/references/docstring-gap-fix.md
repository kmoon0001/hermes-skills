# Docstring Gap Fix — Systematic Mechanical Fix Pattern

When an audit finds "N missing docstrings on public functions," don't add them
one at a time by hand. Use this two-phase approach: scan with AST, then
delegate in parallel.

## Phase 1: AST-Based Gap Scan

Use `execute_code` with Python's `ast` module to find every public function and
method missing a docstring. This is more accurate than grep/regex because it
understands Python structure (top-level vs class methods, public vs private).

```python
import ast
import os

project_root = r"C:\path\to\project"
exclude_dirs = {'.venv', '.git', '__pycache__', '.pytest_cache', '.mypy_cache'}

missing = []
for root, dirs, files in os.walk(project_root):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if not file.endswith('.py'):
            continue
        with open(os.path.join(root, file)) as f:
            source = f.read()
        tree = ast.parse(source)
        relpath = os.path.relpath(os.path.join(root, file), project_root)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Public: doesn't start with _ (but allows __init__, __repr__, etc.)
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                if not ast.get_docstring(node):
                    # Skip trivial pass-only functions
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        continue
                    # For class methods, include the class name
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef) and node in ast.walk(parent):
                            name = f"{parent.name}.{node.name}"
                            break
                    else:
                        name = node.name
                    missing.append((relpath, node.lineno, name))
```

**Output format:** `(filepath, lineno, function_name)` — sorted by file, then line.

## Phase 2: Parallel Delegation

Group files by domain and dispatch 3 parallel subagents, each handling one
domain. Give each subagent the exact list of functions needing docstrings with
file:line and a description of what the function does.

**Domains for a typical trading bot:**
1. **Production** — check_alerts, execute_trades, generate_signals, watchdog, etc.
2. **Research + Stocks** — backtest engines, parameter sweeps, experiment runners
3. **Tests** — test files (these have very descriptive names; a one-line docstring
   paraphrasing the snake_case name is sufficient)

**Subagent brief template:**

> Add docstrings to all listed functions in [repo path]/[domain]/.
> For each function, read the code, understand what it does, and add a proper
> triple-quoted docstring right after the function definition.
> Match existing code style. Do NOT change any logic — only add docstrings.

**For test methods:** Since method names are already descriptive (e.g.,
`test_uptrend_has_all_momenta`), translate snake_case to a one-line docstring:
`"""Verify uptrend conditions produce positive momentum across all lookback windows."""`

## Pitfalls

- **Don't use `git add -A`** — venv files may be caught. Stage specific files.
- **Verify after each batch** — run `python -c "import ast; ast.parse(open(f).read())"` on every modified file, or run the test suite.
- **Tests count is lower than expected** — The AST scan includes more functions than the audit report because it counts top-level functions that the audit may have skipped (e.g., isolated helper functions in test files). Both numbers are "correct" for their scopes.
- **Don't change logic** — Adding a docstring is purely additive. If a subagent changes anything else, revert that file.
