#!/usr/bin/env bash
# Global pre-commit hook for all Copilot Studio agents.
# Blocks commits with:
#   1. Missing `knowledgeSources:` block
#   2. Raw generative-answer record references (no .Text.Content)
#   3. `in` operator without Text() wrapper
#   4. Dead retry: RetryCount < 0
# Works for any repository containing Copilot Studio topic files.
#
# Install: git config --global core.hooksPath "/path/to/.hermes_hooks"

REPO_ROOT="$(git rev-parse --show-toplevel)"
block=0

find "$REPO_ROOT" -type f -name "*.yml" -print0 | while IFS= read -r -d '' file; do
    # 1: BLOCK — missing knowledgeSources on SearchAndSummarizeContent nodes
    if grep -q 'SearchAndSummarizeContent' "$file" && ! grep -q '^knowledgeSources:' "$file"; then
        echo "❌ BLOCK: MISSING knowledgeSources in: $file"
        block=$((block+1))
    fi

    # 2: BLOCK — raw record output (any AuditReport/audit_report var without .Text.Content)
    if grep -qE 'Topic\.[A-Za-z0-9_]+(AuditReport|audit_report)\}' "$file"; then
        echo "❌ BLOCK: RAW RECORD output (missing .Text.Content) in: $file"
        block=$((block+1))
    fi

    # 3: BLOCK — in operator without Text() wrapper on topic variables
    if grep -qE 'in Topic\.' "$file" && ! grep -qE 'in Text\(Topic\.' "$file"; then
        echo "❌ BLOCK: Missing Text() wrapper on in operator in: $file"
        block=$((block+1))
    fi

    # 4: BLOCK — dead retry: RetryCount < 0
    if grep -q 'RetryCount < 0' "$file"; then
        echo "❌ BLOCK: Dead retry (RetryCount < 0) in: $file"
        block=$((block+1))
    fi
done

if [ $block -ne 0 ]; then
    echo "❌ Commit blocked due to $block error(s). Fix them before committing."
    exit 1
fi

echo "✅ All checks passed."
exit 0
