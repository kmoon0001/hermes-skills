# YAML Condition Expression Double-Escape Pitfall

## The Problem

When editing Power Fx conditions in a topic's Dataverse YAML via API PATCH, the condition expression can end up with **double-escaped backslashes** (`\\\"` instead of `\"`), causing Copilot Studio's expression parser to emit:

```
ExpressionError: Unexpected character in expression '\'
at position 0-1, source: "\"
```

The error message literally shows a stray backslash as the source character.

## Root Cause

The condition uses a YAML double-quoted string containing a Power Fx `in` operator:

```yaml
condition: "=\"Status: Completed\" in Topic.ocr_payload"
```

In YAML double-quoted strings, `\"` is the escape sequence for a literal `"`. The condition value resolves to:

```
="Status: Completed" in Topic.ocr_payload
```

If the YAML is stored with an extra level of escaping (two backslashes instead of one: `\\\"` instead of `\"`), YAML interprets `\\` as a literal backslash character, producing a value that starts with a stray `\`:

```
\="Status: Completed" in Topic.ocr_payload
# ^ stray backslash causes ExpressionError
```

## Detection

Compare the condition line byte-by-byte against a known-working topic (e.g., Discharge Summary). The working format has:

```
condition: "=\"Status: Completed\" in Topic.ocr_payload"
```

In Python repr, the working line shows `\"=\\"` (single backslash before each inner quote).
The broken line shows `\"=\\\\"` (double backslash before each inner quote).

## Fix

1. Get the current YAML from Dataverse: `GET /botcomponents({id})?$select=data`
2. Find the condition line and replace `\\\"` with `\"` before and after the string constant
3. PATCH the corrected data back

In Python:
```python
old_line = '          condition: "=\\"Status: Completed\\" in Topic.ocr_payload"'
lines = data.split('\n')
new_lines = [old_line if (
    'condition:' in l and 'Status: Completed' in l
) else l for l in lines]
new_data = '\n'.join(new_lines)
# Verify: ensure only ONE backslash per \" in the condition
```

## Prevention

When building replacement YAML strings in Python, use:
```python
correct = '          condition: "=\\"Status: Completed\\" in Topic.ocr_payload"'
#            The \" are single-backslash-escaped quotes for YAML
```

Avoid building the condition string via multi-step replacement or concatenation that might add extra escaping. Always compare against a working topic's raw bytes using `repr()` to catch extra backslashes.

## Verification

After PATCH, call `GET /botcomponents({id})?$select=data` and verify the condition line byte-for-byte matches the working topic. The hex dump should show `0x5c 0x22` (backslash + quote), not `0x5c 0x5c 0x22` (double backslash + quote).
