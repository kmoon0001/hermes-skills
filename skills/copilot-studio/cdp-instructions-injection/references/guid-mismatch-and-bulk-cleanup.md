# Pitfalls: GUID Mismatch & Topic Recreation

## GUID Mismatch After Topic Recreation

When a topic is deleted and recreated (e.g., user deletes corrupted topic, creates new one with same name), the new topic gets a DIFFERENT GUID. Any cached topic GUIDs become stale.

**Symptom:** 404 errors when trying to delete/update a topic via Dataverse API.

**Root cause:** The topic_guids.md file was generated before the recreation. The new topic has a different GUID.

**Example:**
- Old HIPPA Guardrail GUID: `65b22680-9856-f111-bec6-7ced8d3b6116`
- New HIPPA Guardrail GUID: `65b22680-b77d-4dee-a32d-c328d62e0e03`

**Fix:** Always re-query the Dataverse API for fresh GUIDs before performing operations:
```javascript
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9 and name eq '${topicName}'`;
const url = `https://org.crm.dynamics.com/api/data/v9.2/botcomponents?$select=name,botcomponentid&$filter=${encodeURIComponent(filter)}`;
```

## Bulk Topic Cleanup Workflow

When an agent has many topics (50+) with duplicates, stubs, and broken references:

1. **Query all topics** via Dataverse API (componenttype eq 9)
2. **Categorize** by content length and patterns:
   - Empty: content.length < 50
   - Stubs: content.length < 300 && includes 'under development'
   - Short: content.length < 500
   - Clean: everything else
3. **Check for broken references** — search content for deleted topic names/GUIDs
4. **Delete in batch** via Dataverse API DELETE
5. **Republish** — empty/stub topics cause publish crashes
6. **Verify** — check console for `$kind` errors

**Key metric:** QM Coach V2 went from 62 topics (71% eval) to 30 topics (95% eval) by removing stubs, duplicates, and interactive menu topics.
