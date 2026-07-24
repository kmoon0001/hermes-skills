# Dataverse PATCH for Newly Created Empty Topic Injection

Validated: Jun 20, 2026 on SimpleLTC QM Coach V2 in Therapy AI Agents Dev.

## When to use

Use this only for newly created blank/empty topics or simple topic shells where the Dataverse `botcomponent.content` field is currently empty or obviously incomplete. It is safer than Monaco/clipboard injection when the topic is fresh and the YAML is a complete simple `AdaptiveDialog`.

Do not use this as a blanket replacement for the Copilot Studio editor on mature topics with complex component wiring. PATCH has previously returned 400 or caused validation issues for complex topic content.

## Safe workflow

1. Query live topic components:

```javascript
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
const url = `${ORG}/api/data/v9.2/botcomponents?$select=name,botcomponentid,content,modifiedon&$filter=${encodeURIComponent(filter)}&$top=200`;
const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } });
```

2. Identify empty or short topics that the user intentionally created.

3. Validate local YAML before patching:
   - first line is `kind: AdaptiveDialog`
   - contains `beginDialog:`
   - contains an `EndDialog`
   - no invalid `{$Topic.` references
   - no raw citation metadata strings or system variables in user-facing text
   - no `OnUnknownIntent` unless the topic is truly a system/fallback topic

4. PATCH one topic first as a test:

```javascript
await fetch(`${ORG}/api/data/v9.2/botcomponents(${topicId})`, {
  method: 'PATCH',
  credentials: 'include',
  headers: {
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ content: yaml })
});
```

If correcting a typo in a newly created topic name, include `name` in the same PATCH:

```javascript
body: JSON.stringify({ name: 'FacilityTrendReporter', content: yaml })
```

5. Immediately GET the same topic and require exact match after normalizing CRLF:

```javascript
const exactMatch = (after.content || '').replace(/\r\n/g, '\n') === yaml.replace(/\r\n/g, '\n');
if (!exactMatch) throw new Error('Dataverse read-back mismatch; stop batch');
```

6. Batch remaining topics only if the one-topic test succeeds.

7. Publish with PAC CLI instead of relying on the UI Publish button:

```bash
pac copilot publish --environment "https://orgbd048f00.crm.dynamics.com" --bot "<botId>"
```

8. Verify live topic state again after publish by querying topics and checking there are no empty topics and no missing `AdaptiveDialog` / `beginDialog` blocks.

## Critical pitfall: fake Conversational boosting topics

Do not create a blank/custom topic named `Conversational boosting` and patch it with `OnUnknownIntent` system-topic YAML. In the SimpleLTC QM Coach V2 session, this caused Copilot Studio publish to crash with "Something went wrong". The fix was to delete the unsafe custom CB topic via Dataverse API and keep the existing `Fallback` system topic active.

Rule: `OnUnknownIntent` belongs only in real system/fallback topics. For a manually created custom topic, use `OnRecognizedIntent` with trigger queries, or configure the system topic through the proper Copilot Studio system topic path.

## Why this matters

This pattern avoids the Monaco/clipboard corruption path while still requiring hard verification. It is especially useful when the user has already created blank topics in the UI and wants the agent to populate their YAML safely.
