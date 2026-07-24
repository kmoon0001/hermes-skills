# Power BI `PowerBIEntityNotFound` debugging notes

Use this when a Power Automate flow step **Run a query against a dataset** fails with `NotFound` or `PowerBIEntityNotFound`.

## What the June 2026 session proved

For the flow **Weekly ADL Decline Alert**:

- Recurrence passed after setting `Interval = 1`.
- SharePoint `Get items` passed after using the Pacific Coast DOR Roster list and filter `Active eq 1`.
- Power BI connection showed green/connected.
- The Power BI step still failed with `NotFound`.
- Failed-run inputs showed:
  - `groupid`: `79784714-0f23-4fe4-b96b-1388c886a6c2`
  - workspace selected in editor: `CrossDomain_Reports_MetricsRankingsOps`
  - `datasetid`: `327a2c21-f64b-4dab-8ee5-edc31f9123cd`
  - query: `EVALUATE FILTER('ADLs and Ambulation', 'ADLs and Ambulation'[Total Declined] > 0)`
- Because the selected workspace produced a real `groupid`, the remaining `NotFound` pointed to the dataset/semantic model ID, not SharePoint, recurrence, or auth.
- `327a2c21-f64b-4dab-8ee5-edc31f9123cd` is likely the report ID or stale assumed ID, not the dataset ID in that workspace.

## Debugging workflow

1. Do not keep retesting blindly. Open the newest failed run.
2. Click the failed **Run a query against a dataset** action.
3. Inspect **Inputs**:
   - `groupid`
   - `datasetid`
   - `specification/query`
4. Interpret results:
   - Green Power BI connection + valid `groupid` + `PowerBIEntityNotFound` = wrong dataset/semantic model ID.
   - Blank or reset Dataset field in the editor = action is not actually bound to a valid dataset.
   - Query table with spaces must be quoted with single quotes.
5. Fix order:
   - Select the correct workspace first.
   - Select the dataset/semantic model from the dropdown if possible.
   - Only use custom GUID after verifying it is a dataset/semantic model ID, not a report ID.
   - Then fix DAX query syntax.
6. Retest once after each meaningful correction and inspect the newest run details.

## Known-good query syntax for table names with spaces

```DAX
EVALUATE
FILTER(
    'ADLs and Ambulation',
    'ADLs and Ambulation'[Total Declined] > 0
)
```

Compact one-line version for Power Automate:

```DAX
EVALUATE FILTER('ADLs and Ambulation', 'ADLs and Ambulation'[Total Declined] > 0)
```

## User workflow preference learned

When fixing Power Automate flows for Kevin, explicitly reassure him that you are editing the **existing** flow, not designing/creating another one. Keep narration minimal and act through the UI/tools rather than giving long instructions.
