# YAML Condition Quoting for Copilot Studio

## Critical Finding (Jul 11 2026)

**Copilot Studio has TWO different condition formats that are NOT interchangeable.** Using the wrong format causes silent data loss.

### UI Code Editor — Bare Inline, NO quotes

When pasting YAML directly into the Copilot Studio code editor (`</>` button), conditions MUST use bare inline format:

```yaml
# ✅ WORKS in the editor
condition: =!IsBlank(First(System.Activity.Attachments))
condition: =!IsBlank(Trim(Topic.DocumentText))
condition: =!IsBlank(Topic.DocumentText)

# ❌ FAILS in the editor — strips to empty =!IsBlank()
condition: '=!IsBlank(First(System.Activity.Attachments))'
```

**The single-quoted form causes the editor's YAML parser to strip the content inside parentheses**, resulting in `condition: =!IsBlank()` with a PowerFxError. Verified across 6 topics on Medicare Part B Compliance Agent, Jul 10-11 2026.

**Validation:** Treatment Encounter Note Review has working bare conditions (`=!IsBlank(First(System.Activity.Attachments))` and `=!IsBlank(Trim(System.Activity.Text))`) stored in live Dataverse that survive editor round-trips.

### Dataverse API PATCH — Single-Quoted (Preferred)

When patching topic YAML via `PATCH /botcomponents({id})`, the single-quoted form IS preferred because backslash escaping compounds across JSON → YAML → Power Fx layers:

```yaml
# ✅ WORKS for API PATCH
condition: '=!IsBlank(First(System.Activity.Attachments))'
condition: '=!IsBlank(Trim(Topic.DocumentText))'
```

### Reference Table

| Environment | Format | Example | Result |
|-------------|--------|---------|--------|
| Code Editor | Bare inline | `condition: =!IsBlank(Topic.Var)` | ✅ Works |
| Code Editor | Single-quoted | `condition: '=!IsBlank(Topic.Var)'` | ❌ Strips to `=!IsBlank()` |
| API PATCH | Bare inline | `condition: =!IsBlank(Topic.Var)` | ⚠️ May work but less safe |
| API PATCH | Single-quoted | `condition: '=!IsBlank(Topic.Var)'` | ✅ Works, prevents backslash compounding |

## Simple Variable Checks (no function calls)

Bare inline works in both environments for simple variable references:

```yaml
condition: =!IsBlank(Topic.DocumentText)        # ✅ Editor
condition: '=!IsBlank(Topic.DocumentText)'       # ✅ API PATCH (also works)
```

The stripping only occurs when the condition contains function calls with parentheses inside an unquoted... actually, the stripping occurs when SINGLE-QUOTED. The bare format is what survives the editor. This was confirmed on Jul 10-11 2026 by comparing Treatment Encounter (bare, works) with Discharge Summary (single-quoted, broken).
