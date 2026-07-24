# Pre-Commit Hooks for Copilot Studio Topic Validation

## Purpose
Automatic gate that blocks commits with common topic YAML defects before they reach the repository. Works across any Copilot Studio agent repo.

## Installation (one-time)

```bash
# Create a global hooks directory
mkdir -p ~/.hermes_hooks

# Write the hook script (see below for content)
# Then set git to use it globally:
git config --global core.hooksPath "C:/Users/kevin/.hermes_hooks"
```

## What the Hook Checks

| Check | Blocks | Pattern |
|-------|--------|---------|
| Missing `knowledgeSources:` | YES | `grep -q '^knowledgeSources:'` on each topic YAML |
| Raw record output (no `.Text.Content`) | YES | Detects `Topic.*AuditReport}` or `Topic.*audit_report}` without `.Text.Content` |
| `in` operator without `Text()` wrapper | YES | Detects `in Topic.` without `Text(Topic.` |
| Dead retry `RetryCount < 0` | YES | Detects `RetryCount < 0` (always false) |
| Duplicate triggerQueries | WARN only | Soft warning, doesn't block |

## Reference Hook Script

```
#!/usr/bin/env bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
block=0
find "$REPO_ROOT" -type f -name "*.yml" -print0 | while IFS= read -r -d '' file; do
    # knowledgeSources check
    if ! grep -q '^knowledgeSources:' "$file"; then
        echo "BLOCK: MISSING knowledgeSources in: $file"
        block=$((block+1))
    fi
    # Raw record output check
    if grep -qE 'Topic\.[A-Za-z0-9_]+(AuditReport|audit_report)\}' "$file"; then
        echo "BLOCK: RAW RECORD output (missing .Text.Content) in: $file"
        block=$((block+1))
    fi
    # Text() wrapper check
    if grep -qE 'in Topic\.' "$file" && ! grep -qE 'in Text\(Topic\.' "$file"; then
        echo "BLOCK: Missing Text() wrapper on in operator in: $file"
        block=$((block+1))
    fi
    # Dead retry check
    if grep -q 'RetryCount < 0' "$file"; then
        echo "BLOCK: Dead retry (RetryCount < 0) in: $file"
        block=$((block+1))
    fi
done
if [ $block -ne 0 ]; then exit 1; fi
```

## When to Add/Update

- When a new topic YAML defect pattern is discovered and validated
- When the agent undergoes an evaluation optimization loop
- Before any publishing pipeline integration
