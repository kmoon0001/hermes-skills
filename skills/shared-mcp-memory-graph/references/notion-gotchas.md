# Notion API Gotchas (compiled from live sessions)

## 1. Integration Name Case-Sensitivity

"Hemres" and "hermes" are **different integrations**. An account can have both. An API key works for exactly one integration. If a page is shared with Hemres but your key is for hermes, every endpoint returns 404.

**Check which integration your key belongs to:**
```bash
curl -s "https://api.notion.com/v1/users" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
# Look for the bot entry — that's the integration name
```

Share pages with that exact name (case-sensitive): Page → `...` → Connections → `<integration name>`

## 2. Page Sharing = Mandatory (404 Until Shared)

Even with a valid key, every endpoint returns 404 until the page/database is explicitly shared with the integration. Search returns 0 results. No workspace-level access for internal integrations.

**Fix:** Page menu `...` → Connections → Connect to → `<integration name>`

## 3. database_id vs data_source_id (v2025-09-03)

Every database has TWO IDs that are DIFFERENT UUIDs:
- **`database_id`**: For creating pages: `{"parent": {"database_id": "..."}}`
- **`data_source_id`**: For querying: `POST /v1/data_sources/{id}/query`

Using wrong one = "Could not find database" or "Could not find data_source."

**Get the full database_id from a data_source:**
```bash
curl -s "https://api.notion.com/v1/data_sources/{data_source_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | jq '.parent.database_id'
```
Search results truncate the UUID — always fetch the data_source details for the full ID.

## 4. API Key Persistence Across Sessions

`export` in terminal persists within one session but not across sessions. Save to `.env`:
```bash
# In ~/AppData/Local/hermes/profiles/coding-profile/.env:
NOTION_API_KEY=ntn_your_actual_key
```

## 5. Windows Python Path Quirks

- `C:/Users/...` works in Python's `os.path.exists()` on Windows
- `/c/Users/...` works in bash/curl but returns `False` in Python
- When piping curl output to python3, use the python3 that's on PATH (may differ from `python`)

## 6. Empty PATCH/POST Body Required

Gateway publish and some Notion endpoints require `{}` body — empty body returns error.
