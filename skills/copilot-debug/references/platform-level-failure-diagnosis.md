# Platform-Level Failure Diagnosis

When ALL agents return "Error" on evaluation test cases simultaneously (including untouched control agents), the issue is NOT agent configuration. It's the evaluation service.

## Diagnostic Checklist (in order)

### 1. Run eval on an UNTOUCHED agent
If an agent that was never modified also returns 0%, it's definitively a platform issue. This is the single most important diagnostic step.

**Evidence (June 18, 2026):** OT_Specialist (untouched since June 17) returned 0% when tested, confirming platform-wide failure.

### 2. Verify agents work in Test pane
The Test pane uses the DRAFT version with the user's browser auth. The evaluation service uses the PUBLISHED version with service-level auth. If Test pane works but eval fails, the eval service's auth path is broken.

### 3. Check environment health via pac CLI
```bash
pac auth list
pac copilot list --environment <orgUrl>
```
If bots show `Active | Provisioned`, the environment is healthy.

### 4. Query Dataverse API
```javascript
// From CRM domain browser context
const resp = await fetch('/api/data/v9.2/bots?$select=name,botid,statecode&$top=10');
```
If returns data, the API layer works.

### 5. Wait and retry (rule out rate limiting)
Wait 5-10 minutes, trigger a fresh eval. If still 0%, it's NOT rate limiting.

### 6. Check for recent Microsoft outages
- Search: "Microsoft Copilot Studio outage [date]"
- Check: https://admin.powerplatform.microsoft.com/health
- Known pattern: June 11, 2026 — faulty deployment broke auth between Copilot, Graph, and Azure OpenAI. 4,500+ users affected.

## Timeline Pattern

Platform failures follow a distinct pattern:
```
3:33 PM  Agent A Conv 100%  ← last successful eval
3:37 PM  Agent B Conv 90%   ← last successful eval
3:50 PM  ALL agents 0%      ← everything broke simultaneously
```

The simultaneous break across all agents (including untouched ones) within a ~17 minute window is the signature of a platform deployment issue.

## What NOT to Do

- Don't diagnose individual agents in isolation
- Don't revert topic/instruction changes that were working before
- Don't make new changes until you confirm the regression is persistent
- Don't assume it's rate limiting without waiting and retrying
- Don't re-publish agents (won't fix a platform issue)

## What TO Do

- Wait and re-test tomorrow
- Check Microsoft service health dashboard
- File a support ticket with environment ID if persists
- Document the timeline and control agent result

## Environment IDs for Reference

| Environment | ID | Org URL |
|------------|-----|---------|
| Ensign Services (default) | Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f | org3353a370.crm.dynamics.com |
| Therapy AI Agents Dev | a944fdf0-0d2e-e14d-8a73-0f5ffae23315 | orgbd048f00.crm.dynamics.com |
