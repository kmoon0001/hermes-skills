# Notion API v2025-09-03 — Behavior Changes from v2022

The 2025-09-03 API version (required on all requests) introduced breaking changes to database creation and property management. These quirks are NOT covered by the official skill (which still shows the old patterns).

## Database Creation is Now Two-Step

**Old** (doesn't work): `POST /v1/data_sources` with full properties inline.
**New**: `POST /v1/databases` — but properties passed in the create call are IGNORED. Properties must be added via a second PATCH call.

### Step 1: Create the database

```python
result = notion("POST", "databases", {
    "parent": {"type": "page_id", "page_id": parent_id},
    "title": [{"text": {"content": "My Database"}}],
    "properties": {"Name": {"title": {}}},  # Only Name property accepted
    "is_inline": True,
})
db_id = result["id"]                     # For creating pages
ds_id = result["data_sources"][0]["id"]  # For PATCHing properties + querying
```

**Critical:** Note the `parent` format changed — requires `"type": "page_id"` explicitly:
```python
# OLD (400 error):
{"parent": {"page_id": "xxx"}}
# NEW (required):
{"parent": {"type": "page_id", "page_id": "xxx"}}
```

### Step 2: PATCH the data source to add properties

Properties are stored on the DATA SOURCE, not the database. Must use data source property format (NOT page property format):

```python
# Correct — data source property format (explicit "type" key):
patch_ds_properties(ds_id, {
    "Status": {"type": "select", "select": {"options": [
        {"name": "OK", "color": "green"},
        {"name": "Error", "color": "red"},
    ]}},
    "Value": {"type": "number", "number": {}},
    "Date": {"type": "date", "date": {}},
    "Notes": {"type": "rich_text", "rich_text": {}},
})

# WRONG — page property format (no explicit "type"):
{"Status": {"select": {"options": [...]}}}
```

## Two Separate IDs

Every database has TWO IDs:

| ID | Purpose | Example |
|----|---------|---------|
| `database_id` | Creating pages: `{"parent": {"database_id": db_id}}` | `118bf11a-9bf2-437d-ae41-fac036d9ce91` |
| `data_source_id` | PATCHing properties + querying | `dbfd30b3-6ff6-4eaf-ba24-ba824ddf3de5` |

The `database_id` comes from the create response's `id` field. The `data_source_id` comes from the `data_sources[0].id` nested array.

When creating pages in a database, use `database_id`. When querying, use `data_source_id`. Mixing them up returns 404 or incorrect results.

## Cannot Create a Second Title Property

Databases are created with a default "Name" title property. You CANNOT create a second title property via PATCH — it returns:
```
"message": "Cannot create new title property."
```

**Fix:** Rename the existing title property. Include `"name": "NewName"` in the PATCH:

```python
patch_ds_properties(ds_id, {
    "Name": {"type": "title", "title": {}, "name": "Key"},
    # ...other properties
})
```

The `"name"` field isn't listed in Notion's documented property format but it's accepted for title properties.

## Page Creation Still Works the Same

Creating pages in a database uses the SAME property format as before:
```python
{
    "parent": {"database_id": db_id},
    "properties": {
        "Name": {"title": [{"text": {"content": "Entry Title"}}]},
        "Status": {"select": {"name": "OK"}},
        "Value": {"number": 42},
    }
}
```

This format (without explicit `"type"`) is for PAGE creation, not data source property definition.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `body.parent.type should be defined` | Missing `"type": "page_id"` in parent | Add `"type": "page_id"` |
| `Cannot create new title property` | Adding second title via PATCH | Rename existing "Name" with `"name": "NewName"` |
| `Key is not a property that exists` | Using wrong ID for page creation | Use `database_id`, not `data_source_id` |
| `Creating new databases with data sources is not supported` | Using `/v1/data_sources` instead of `/v1/databases` | Use `POST /v1/databases` |
| `401 unauthorized` when key works from shell | Stale env var vs correct .env value | Unset stale env var, restart shell |

## UUID Format

Notion accepts UUIDs with or without dashes. Both work:
- With dashes: `"3a411c0f-403f-8063-9df2-c604af51c9e5"`
- Without dashes: `"3a411c0f403f80639df2c604af51c9e5"`

The API returns UUIDs with dashes. Page URLs use the no-dash format.

## Three-Database Architecture

The canonical setup has three databases under a parent page:

| Database | Purpose | Key Properties |
|----------|---------|----------------|
| **Status Log** | One row per run/event | Name (title), Date, Status (select), Equity (number), Agent (select), Summary (rich_text), Duration (number), Metric (number) |
| **Agent Memory** | One row per session/decision | Title (title), Date, Category (select), Detail (rich_text), Tags (multi_select), Commit (rich_text) |
| **Bot Config** | One row per parameter | Key (title), Value (rich_text), Category (select), Agent (select), LastUpdated (date), Notes (rich_text) |

All three are universal — any agent can write for any domain.

## Summary of Changes

| Old (pre-2025-09) | New |
|--------------------|-----|
| `POST /v1/data_sources` to create DB | `POST /v1/databases` to create DB |
| `parent: {"page_id": id}` | `parent: {"type": "page_id", "page_id": id}` |
| Properties set during creation | Two-step: create then PATCH data source |
| One ID per database | Two IDs: `database_id` + `data_source_id` |
| Properties in create work | Properties in create are IGNORED |
| Title name customizable at creation | Default "Name" — rename via PATCH with `"name"` field |
