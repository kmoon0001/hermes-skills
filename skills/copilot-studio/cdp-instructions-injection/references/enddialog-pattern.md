# EndDialog Fix Pattern for Copilot Studio Topics

## The Bug

SearchAndSummarizeContent topics that use `CancelAllDialogs` instead of `EndDialog` cause topic queue overflow on conversation turns 2-3. The agent responds correctly on turn 1, then "refuses to help" or asks to "rephrase" on subsequent turns.

**Symptom in evaluation:** 15/18 failures = "refuses to help" on turns 2-3.

## The Fix

Replace this block (usually the LAST action before `inputType: {}`):

```yaml
    - kind: CancelAllDialogs
      id: cancel_queued_eval_guard_topics
```

With:

```yaml
    - kind: EndDialog
      id: done
      clearTopicQueue: true
```

## Detection via pac CLI

Query topics for an agent:
```bash
pac org select --environment "https://org3353a370.crm.dynamics.com/"
pac org fetch --xml "<fetch><entity name='botcomponent'><attribute name='name'/><filter><condition attribute='parentbotid' operator='eq' value='<botId>'/><condition attribute='componenttype' operator='eq' value='9'/></filter></entity></fetch>"
```

`pac org fetch` crashes when reading memo fields (content, data). Use CDP code editor to read topic YAML instead.

## Verification via CDP

Navigate to adaptive editor with codeEditor=true:
```
https://copilotstudio.microsoft.com/environments/<envId>/bots/<botId>/adaptive/<componentId>?codeEditor=true
```

Open code editor (More → Open code editor), read `.view-line` content, check for `CancelAllDialogs` vs `EndDialog`.

## Evidence (Jun 10, 2026)

**OT_Specialist:** Two topics (OT Recertification Missing Elements Exact Intake, OT Progress Missing Elements Exact Intake) had `CancelAllDialogs`. This caused conversation score to drop from 60% → 25% → 10% as the topic queue overflowed on every follow-up turn. Fixing both to `EndDialog` + `clearTopicQueue: true` is expected to restore to 85%+.
