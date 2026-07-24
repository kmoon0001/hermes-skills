# Live Agent Context Dump via Dataverse

Use this when Kevin asks to “gather all context” on a Copilot Studio agent before providing an execution prompt. This is a read-only workflow: query live Dataverse first, treat live as source of truth, and write a concise brief to Desktop.

## What to capture

- Bot identity: `botid`, `name`, `schemaname`, `statecode`, `statuscode`, `createdon`, `modifiedon`, `publishedon`, `language`, `authenticationmode`, `configuration`, `synchronizationstatus`.
- Core components excluding bulky eval rows: `botcomponents` where `_parentbotid_value eq '<botId>' and componenttype ne 19`, selecting `botcomponentid,name,schemaname,componenttype,componentstate,statecode,statuscode,modifiedon,createdon,data,content`.
- Lightweight total/eval inventory: `botcomponents` where `_parentbotid_value eq '<botId>'`, selecting only lightweight fields with `$count=true&$top=500`. If type 19 is large, count it separately with `componenttype eq 19&$count=true&$top=1`.
- Topics: componenttype 9, write each `data` field to `topics/<safe name>.yml`.
- GPT instructions: componenttype 15, write `data` to `instructions-component.yml`.
- Knowledge files: componenttype 14, capture names/schemas/IDs; the `data` may only be a short metadata stub.
- Publish/sync diagnostics: parse `bot.synchronizationstatus` JSON and summarize `lastFinishedPublishOperation.status`, `currentSynchronizationState.state`, `diagnosticDetails[].diagnosticList[]` grouped by `errorCode`, `bindingKey`, component/dialog/action.
- Action map: scan topic YAML for `flowId:`, `kind: SearchAndSummarizeContent`, `FilePrebuiltEntity`, and `dialog:` BeginDialog references.

## Useful `az rest` query shapes

```bash
ORG='https://<org>.crm.dynamics.com'
BOT='<dataverse-botid>'

az rest --method GET --resource "$ORG/" \
  --url "$ORG/api/data/v9.2/bots?\$filter=botid eq $BOT&\$top=1" \
  > bot.json

az rest --method GET --resource "$ORG/" \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '$BOT' and componenttype ne 19&\$select=botcomponentid,name,schemaname,componenttype,componentstate,statecode,statuscode,modifiedon,createdon,data,content&\$top=500" \
  > components-core.json

az rest --method GET --resource "$ORG/" \
  --url "$ORG/api/data/v9.2/botcomponents?\$filter=_parentbotid_value eq '$BOT' and componenttype eq 19&\$select=botcomponentid,name,componenttype&\$count=true&\$top=1" \
  > eval-count.json
```

Notes:
- Always use the Dataverse `bots.botid`, not the Copilot Studio SPA URL GUID.
- `az rest` output on Windows can contain characters that fail strict UTF-8 reads; when parsing with Python, use `encoding='utf-8', errors='replace'`.
- `@odata.count` on an unfiltered or `$top=500` lightweight query may not represent all rows if paging/nextLink behavior is odd; for eval counts, issue a direct `componenttype eq 19&$count=true&$top=1` query.
- Do not dump secrets/tokens. If any auth material appears, replace with `[REDACTED]`.

## Output package

Write a folder like:

```text
C:/Users/kevin/Desktop/<agent>_context/
  ready-for-prompt-brief.md
  context-report.md
  context-summary.json
  bot.json
  components-core.json
  components-light.json
  sync-diagnostics.json
  topic-action-map.json
  instructions-component.yml
  topics/*.yml
```

The final brief should be bottom-line first and include:
- exact target identity and live state
- component counts
- instruction summary
- knowledge-source list
- topic list and major routing
- flow IDs and broken binding/publish diagnostics
- local backup paths found, but explicitly state live dump is newer/source-of-truth
- explicit note: no live changes made

## Diagnostic pattern: failed publish with broken flow outputs

If `synchronizationstatus` reports `lastFinishedPublishOperation.status = Failed` and diagnostics show repeated `InvalidBindingInvokeAction` for output bindings such as `found`, `job_id`, `job_json`, plus PowerFx errors on completion conditions, the likely repair class is flow output schema/binding refresh for the affected `InvokeFlowAction` nodes followed by fixing dependent PowerFx checks. Do not patch until Kevin explicitly asks.
