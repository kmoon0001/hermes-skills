# Topic de-duplication and poll-loop cleanup

Use this pattern when a Copilot Studio agent has duplicate topics competing for the same trigger phrases, or a topic has a polling loop that never exits.

## Duplicate topic cleanup

1. Back up live topics first:
   - Query `botcomponents` with `_parentbotid_value eq '<botId>' and componenttype eq 9`.
   - Select at least `botcomponentid,name,schemaname,componentstate,statecode,statuscode,modifiedon,data`.
2. Identify the copy by both display name and schema name. UI names may differ from the prompt; copied topics often have schema suffixes like `...Copy` while the display name may be `- Text Paste` or similar.
3. Verify the original/non-copy topic is active (`statecode=0`) and has the intended trigger phrases.
4. Search all topic YAML for references to the copy schema before deletion. Do not delete a topic that is still targeted by `BeginDialog` or other schema references.
5. Deactivate the duplicate first with `PATCH /botcomponents(<id>)` and body `{"statecode":1,"componentstate":2}`.
6. Re-query. Treat `statecode=1` as inactive even if `componentstate` still reads `0`.
7. If the original remains active and no refs point to the copy, DELETE the duplicate botcomponent.
8. Re-query to verify only the original remains, then publish.

## Poll-loop cleanup

For count-based polling variables, avoid conditions that test only blankness after increment. Example infinite loop:

```yaml
- id: condition_poll_continue
  condition: =!IsBlank(Topic.OCRpoll)
```

If `Topic.OCRpoll` is incremented before the condition, it will never be blank. Replace with an explicit bounded comparison:

```yaml
- id: condition_poll_continue
  condition: =Topic.OCRpoll < 3
```

Before patching, verify the old string occurs exactly once in the live `data` field. After patching, re-query and count old/new occurrences (`old=0`, `new=1`).

## Work IQ/tool verification

Work IQ preview tools can appear as `componenttype=9` TaskDialog records even though they are tools/actions. Search all botcomponents for `Work IQ`, `WorkIQ`, and `workiq`. A disabled/off Work IQ component may show `statecode=1`; publish can proceed if no active Work IQ tool remains.
