# SharePoint List Creation via Graph API

## Overview
This reference covers creating SharePoint lists programmatically using Microsoft Graph API, specifically for the ENSG project's Pacific Coast DOR Roster list.

## Prerequisites
- Microsoft Graph API access token (from Graph Explorer or app registration)
- SharePoint site URL: `https://ensignservices.sharepoint.com/sites/PacificCoast_SLP`

## Step 1: Get Site ID
```
GET https://graph.microsoft.com/v1.0/sites/ensignservices.sharepoint.com:/sites/PacificCoast_SLP
```
Response includes `id` field needed for subsequent calls.

## Step 2: Create List
```
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists
{
  "displayName": "DOR Config",
  "list": {
    "template": "genericList"
  }
}
```

## Step 3: Add Columns
```
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/columns

// Text column
{
  "name": "Facility",
  "text": { "maxLength": 255 }
}

// Text column
{
  "name": "DORName",
  "text": { "maxLength": 255 }
}

// Text column
{
  "name": "DOREmail",
  "text": { "maxLength": 255 }
}

// Yes/No column
{
  "name": "Active",
  "boolean": {}
}
```

## Token Handling Pitfalls

### Working Approach (Verified)
Save the Graph Explorer token to a text file, then read it with Python:
```python
import requests
with open(r'C:\Users\kevin\Documents\graph_token.txt', 'r') as f:
    token = f.read().strip()
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
r = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)  # Verify token works
r = requests.get('https://graph.microsoft.com/v1.0/sites/ensignservices.sharepoint.com:/sites/PacificCoast_SLP', headers=headers)
site_id = r.json()['id']  # Format: hostname,tenant-id,guid
```
This approach works for all Graph API endpoints including `/sites/`.

### Issue: JWT Truncation
Graph Explorer tokens are ~3800 characters. When passed through:
- Tool contexts (terminal, execute_code): may be truncated
- Files written via write_file: content truncated to ~100 chars
- Shell commands: quoting issues with long strings

### Solutions
1. **Use environment variables**: Set `$GRAPH_TOKEN` in the shell session
2. **Read token at runtime**: Use browser to copy token, paste directly into script
3. **Use App Registration**: More reliable than user tokens for automation
4. **Graph Explorer UI**: Create list manually via browser when API fails

### Token Format
JWT tokens have 3 parts separated by dots: `header.payload.signature`
- Graph Explorer token: ~3800 chars, 2 dots
- App token: ~1500 chars, 2 dots
- Error "only one dot" = token truncated or malformed

## URL Format for SharePoint Sites
Correct format: `sites/{hostname}:/{server-relative-path}`
Example: `sites/ensignservices.sharepoint.com:/sites/PacificCoast_SLP`

Incorrect formats:
- `sites/{site-id}` (requires GUID, not URL)
- `sites/root` (only works for root site collection)

## Required Graph Permissions
- `Sites.ReadWrite.All` - Create/modify lists
- `Sites.FullControl.All` - Full site access

Check token scopes in JWT payload under `scp` field.

## Fallback: Manual Creation
If Graph API fails:
1. Go to SharePoint site → Documents library
2. Click "New" → "List" → "Blank list"
3. Name it "Pacific Coast DOR Roster"
4. Add columns manually via "Add column" button
5. Column types: Single line text (Facility, DORName, DOREmail), Yes/No (Active)