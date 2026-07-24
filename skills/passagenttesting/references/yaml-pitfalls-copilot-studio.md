# YAML Pitfalls in Copilot Studio Topic Editor

This file documents YAML parsing quirks that cause the Monaco code editor to reject valid-looking YAML.

## Problem: Unquoted Values with Dots

**Pattern:** A value like `42 CFR 424.24.` contains multiple dots followed by a space — the YAML parser interprets the dots as the start of a new mapping key.

**Error message:**
```
Error reading YAML content near line 28 position 39: UnexpectedToken, 
token: 'Practice, PDPM, and 42 CFR 424.24.' (UnquotedValue), 
expected: PropertyName or EndObject
```

**Fix:** Replace dots with hyphens in the problematic value. The actual content doesn't need to match the exact regulation citation format — using `42 CFR 424-24` is acceptable since the agent interprets it the same way.

## Problem: Bold/Italic Formatting in Block Scalars

**Pattern:** When using the `|-` (literal block scalar) or `>` (folded block scalar) YAML syntax, asterisks used for bold (`**text**`) can confuse the YAML parser.

**Error message:**
```
Error reading YAML content near line 66 position 19: UnexpectedToken,
token: 'UnexpectedCharacter' (Error),
expected: UnquotedValue or QuotedStringValue or MultilineStringValue
```

**Fix:** Remove all `**` bold formatting from the block scalar. Use plain text section headers instead of markdown bold. For example:
- `**Classification**:` → `Classification:`
- `**Score**: X/100` → `Score: X/100`

## Problem: Non-breaking Spaces in Monaco

Monaco code editor renders YAML with non-breaking spaces (`\u00A0`) instead of regular spaces. JavaScript regex `\s` does NOT match these. Use:
- `indexOf()` with literal strings instead of regex patterns for content matching
- `.replace(/\u00A0/g, " ")` to normalize before processing

## Problem: `|-` vs `>` Block Scalars

YAML offers two block scalar types:
- `|-` (literal block): Newlines are preserved. Best for multi-line text where formatting matters.
- `>` (folded block): Newlines are converted to spaces. Sometimes causes parsing issues in Copilot Studio's topic editor.

When pasting topic YAML containing `additionalInstructions` with a block scalar:
- Prefer `|-` over `>` — folded block scalars occasionally trigger "UnexpectedCharacter" errors at the end of the block
- If `>` causes errors, switch to `|-` and reformat the text to use explicit `\n` line breaks
