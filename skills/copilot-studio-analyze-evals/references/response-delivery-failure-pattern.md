# Response-delivery failures: evaluation forensics and safe repair

## Trigger

Use this pattern when a completed SR/Conv evaluation is dominated by abstention/incomplete failures and one or more answers are literal Power Fx, especially `=System.Response.FormattedText`.

## Do not misdiagnose instructions as blank

Never infer component text length from an ad-hoc piped `curl` command. Shell quoting and malformed `$select`/`$filter` parameters can return an incomplete projection and make a populated `data` field appear empty.

Use a URL-encoded Dataverse query and inspect both raw fields:

```python
params = urllib.parse.urlencode({
  '$filter': f'_parentbotid_value eq {bot_id}',
  '$select': 'botcomponentid,name,componenttype,statecode,statuscode,data,content'
})
url = f'{base}/botcomponents?{params}'
```

For new-experience agents, treat live component `data` as authoritative. `content` can be stale. Check actual string length only after the API response has been parsed.

## Forensic classification

1. Fetch `GET .../makerevaluations/{runId}/details` only after the run is `Completed`.
2. Count grader properties from `graderMetrics.queryResponseMetrics[0].properties`.
3. Detect exact raw formula leaks with an exact string scan; do not use generic substring scans as a substitute for grader properties.
4. Cross-reference `metrics.triggeredTopicIds` with the live component inventory.

Example decisive signature:
- many `abstention=Yes` / `completeness=No` failures;
- answer equals or contains `=System.Response.FormattedText`;
- an active `OnGeneratedResponse` component sets `System.ContinueResponse=false` then sends `activity: =System.Response.FormattedText`.

## Repair boundary

- Snapshot every component and commit/push before mutation.
- Do **not** API-rewrite a true system-trigger topic's `data` merely to alter its formatter behavior; that can publish unreliably.
- If the formatter is provably the source of raw output, deactivate it reversibly (`statecode: 1`, `statuscode: 2`), do not delete it.
- Verify the component's inactive state by live read-back.

For custom generative routes, use the complete visible-answer path:

```yaml
- kind: SearchAndSummarizeContent
  userInput: =System.Activity.Text
  variable: Topic.Answer
  responseCaptureType: FullResponse
  allowLatencyMessage: false
- kind: SendActivity
  activity: =Topic.Answer
- kind: EndDialog
  clearTopicQueue: true
```

Repair an inactive `OnUnknownIntent` conversational boost only after confirming it is not intentionally deactivated. A catch-all answer branch must send `Topic.Answer` before ending.

## Verification

1. Re-read every changed component from Dataverse.
2. Publish and verify `bots.publishedon` plus `synchronizationstatus.lastFinishedPublishOperation.status == Succeeded`; do not trust a CLI's displayed timestamp alone.
3. Re-run the same completed baseline test set, not a new uncomparable set.
4. Report the score delta and raw-formula count separately from residual groundedness/knowledge-quality failures.

A structural delivery repair can remove abstentions and route errors while leaving groundedness failures; stop structural edits once raw-response, abstention, and wrong-route signatures are gone.