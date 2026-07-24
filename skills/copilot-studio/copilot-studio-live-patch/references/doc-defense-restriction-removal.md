# Doc Defense Agent — Knowledge Source Restriction Removal

**Bot:** Pacific Coast Documentation Defense Agent
**Org:** pccapackage.crm.dynamics.com
**Bot ID:** `9e7b871d-1d80-f111-ab0f-000d3a5b0d6c`
**Topic:** Therapy Documentation Compliance Audit and Defense
**Topic ID:** `917ec3e5-7780-f111-ab0f-000d3a5b0d6c`

## Original Issue

The topic was missing `responseCaptureType: FullResponse` and `allowLatencyMessage: false`.
After an Option A fix through the API, the `data` field had `file[]` / `turn.uploadedFiles`
which **blanked the Copilot Studio editor canvas** (confirmed blank via `get_window_state`).

## State before this session's fix

The `file[]` node had already been removed (by an earlier session or manual revert).
What remained were two KB restrictions:

1. `SearchSpecificFiles` — locked to 14 hardcoded PDF file references
2. `SearchSpecificKnowledgeSources` — present but with NO sources listed (effectively
   blocks ALL KB retrieval)

The `SendActivity` had a concatenation bug:
```yaml
activity: "{Topic.Answer}{System.Activity.Text}"
```
This concatenated the user's input text onto the agent's answer.

## Fix Applied

**1. Removed SearchSpecificFiles block** (17 lines including file list)
**2. Changed SearchSpecificKnowledgeSources → SearchAllKnowledgeSources**
**3. Fixed SendActivity** from `{Topic.Answer}{System.Activity.Text}` to `={Topic.Answer}`

## Key Findings

- `az` token on pccapackage **now works** (was 401 in earlier sessions due to CA/MFA).
  `az account get-access-token --resource "https://pccapackage.crm.dynamics.com" -o tsv`
- `python3` (3.13) `urllib.request` on Windows still has the `_validate_path` issue.
  Using `curl` from bash with `TOKEN=$(cat token.txt)` bypasses it entirely — more
  reliable than the patched urllib workaround for one-shot PATCHes.
- After PATCH + publish, verify via `GET /bots/{id}?$select=publishedon,name`.
