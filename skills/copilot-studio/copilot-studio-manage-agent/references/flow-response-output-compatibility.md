# VirtualAgent flow response output compatibility

When repairing Power Automate flows called by Copilot Studio `InvokeFlowAction`, do not assume the prompt's requested outputs are the only outputs live topics need.

## Safe workflow

1. Back up the flow from both planes when possible:
   - Dataverse `workflows(<id>)?$select=workflowid,name,modifiedon,clientdata`
   - Power Automate management API `GET /providers/Microsoft.ProcessSimple/environments/<env>/flows/<flowNameOrId>`
2. Inspect the response action under `clientdata.properties.definition.actions` / `properties.definition.actions`.
3. Add or rename the requested outputs in the response action's `inputs.body` and `inputs.schema.properties`.
4. Before removing any output, search all live topic YAML for `InvokeFlowAction.output.binding` entries that target this `flowId`. Preserve any currently-bound keys unless the user explicitly asks to migrate topics.
5. Patch `workflows.clientdata` through Dataverse if the management API is blocked by `ActiveUnpublished` draft state.
6. Re-query both Dataverse and management API to verify the response schema/body persisted.
7. Publish the agent and inspect `bots.synchronizationstatus` for `InvalidBindingInvokeAction`, `BindingKeyNotFound`, and `FinishedWithUserErrors`.

## Compatibility example

A flow repair may be asked to add three new user-facing outputs:

```json
{
  "job_id": "...",
  "message": "...",
  "processing_status": "..."
}
```

But live topics may still bind legacy outputs such as:

```yaml
output:
  binding:
    found: Topic.found
    job_id: Topic.job_id
    job_json: Topic.ocr_payload
```

If publish diagnostics report missing `found` or `job_json`, preserve/add those outputs in the flow response too. That resolves the live binding error without rewriting many topics. Then separately decide whether to migrate topic YAML to the new output names.

## Verification cues

- Flow management API should show `state: Started`, `componentState: Published`, and the expected schema keys.
- Gateway publish should finish with `state: Finished`, `exceptionType: null`.
- Bot sync/publish diagnostics should have zero `InvalidBindingInvokeAction` and zero `BindingKeyNotFound` occurrences.
