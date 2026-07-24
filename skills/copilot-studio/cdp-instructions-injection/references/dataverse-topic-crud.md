Reference: Dataverse API for Topic Management
Generated: June 19, 2026

## Topic GUID Discovery

Query all topics for a bot:
```
GET /api/data/v9.2/botcomponents?$select=name,botcomponentid,content&$filter=_parentbotid_value eq '{botId}' and componenttype eq 9&$top=100
```

Key: Property is `_parentbotid_value` NOT `botid`. componenttype=9 for topics.

## Topic Deletion (VERIFIED WORKING)

```
DELETE /api/data/v9.2/botcomponents({topicId})
→ Returns 204 No Content on success
```

Batch delete pattern:
```javascript
const toDelete = [
    { name: "Topic Name", id: "guid-here" },
    // ...
];
for (const topic of toDelete) {
    const resp = await fetch(`https://org.crm.dynamics.com/api/data/v9.2/botcomponents(${topic.id})`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
    });
    // 204 = success, 404 = already deleted
}
```

VERIFIED: 10/10 deletes succeeded on QM Coach V2 (June 19, 2026).

## Topic Content Update (DOES NOT WORK)

```
PATCH /api/data/v9.2/botcomponents({topicId})
Body: { "content": "new YAML content" }
→ Returns 400 Bad Request
```

The content field cannot be updated via PATCH. The API rejects it.
Only manual paste via Monaco editor works for topic YAML changes.

## Topic Content Reading (VERIFIED WORKING)

```
GET /api/data/v9.2/botcomponents?$select=name,content&$filter=_parentbotid_value eq '{botId}' and componenttype eq 9 and name eq '{topicName}'
```

Returns full YAML in the `content` field. Useful for:
- Extracting trigger phrases (search for `triggerQueries:`)
- Checking for broken references to deleted topics
- Auditing topic structure

## Topic Overlap Detection Pattern

1. Get all topic names via API
2. Group by functional area based on name keywords
3. Identify exact duplicates (same topic created twice, different casing)
4. Identify overlapping topics (different names, same function)
5. For each overlap: keep the more mature/developed one, delete the rest

Keyword groups for QM Coach V2:
- escalation: escalate, hitl, human review
- hipaa: hipaa, compliance, safety
- drivers: driver, analysis, qm analysis
- intake: resident, intake, submission
- workflow: workflow, menu, orchestrator, action plan
- documentation: document, classify, validate, extract

## Post-Deletion Checklist

After deleting topics:
1. Search remaining topics for references to deleted topic names
2. Fix any broken references (menu options, BeginDialog calls)
3. Republish agent
4. Run single-response eval first (faster, more reliable)
5. Then run conversation eval
6. If conversation eval returns "--" (empty) on all cases:
   - Check for broken topic references first
   - If no broken refs found, it may be a platform rate limit
   - Wait 1 hour and retry
