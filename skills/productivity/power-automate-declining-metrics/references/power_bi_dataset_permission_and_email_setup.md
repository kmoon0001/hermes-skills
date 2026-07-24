# Power BI semantic model permission + final email setup notes

Use this after the `Run a query against a dataset` action has the correct report/dataset IDs but still fails.

## Known IDs from the June 2026 flow

Flow: `Weekly ADL Decline Alert`

Power BI report:
- Name: `One Clinical Outcomes Dashboard`
- Report ID: `327a2c21-f64b-4dab-8ee5-edc31f9123cd`
- Key page: `ADLs and Ambulation`
- Page ID: `7b2d3705c13dd1b2750d`

Power BI semantic model / dataset:
- Dataset ID: `827587e6-d966-4a1b-a305-93cc1e04b224`
- The report metadata endpoint returned `webUrl` under `groups/me`, so Power Automate should use `My Workspace` for this report, not `CrossDomain_Reports_MetricsRankingsOps`.

## How the real dataset ID was found

From a logged-in Power BI browser tab, inspect sessionStorage for a Power BI access token whose key contains:

```text
analysis.windows.net/powerbi/api
```

Then call the Power BI REST report metadata endpoint from inside the browser context. Do not print or save the token.

```js
const keys = Object.keys(sessionStorage);
const atk = keys.find(k => k.includes('accesstoken') && k.includes('analysis.windows.net/powerbi/api'));
const token = JSON.parse(sessionStorage.getItem(atk)).secret;
const reportId = '327a2c21-f64b-4dab-8ee5-edc31f9123cd';
const r = await fetch('https://api.powerbi.com/v1.0/myorg/reports/' + reportId, {
  headers: { Authorization: 'Bearer ' + token, Accept: 'application/json' }
});
const report = await r.json();
// report.datasetId => 827587e6-d966-4a1b-a305-93cc1e04b224
```

## Permission blocker signature

After updating Power Automate to:

- Workspace/groupid: `myworkspace`
- Dataset: `827587e6-d966-4a1b-a305-93cc1e04b224`
- Query: `EVALUATE FILTER('ADLs and Ambulation', 'ADLs and Ambulation'[Total Declined] > 0)`

The run can still fail with `PowerBIEntityNotFound`. Open the failed Power BI action and inspect the detail value. The durable permission-blocker wording is:

```text
You cannot query the dataset '827587e6-d966-4a1b-a305-93cc1e04b224' by using the REST API because the dataset was not found or you do not have the required permissions. Please contact a workspace admin or a dataset owner to grant you the required permissions.
```

That means the account can view the report but lacks semantic model Build/query permission. Ask the Power BI owner/admin to grant Build permission to Kevin / `123713644@ensignservices.net` on semantic model `827587e6-d966-4a1b-a305-93cc1e04b224`.

## Final flow state to leave before permission is granted

Set up everything else so Build permission is the only outside step:

1. Recurrence: Interval `1`; weekly schedule as desired.
2. SharePoint `Get items`: Pacific Coast DOR Roster, filter `Active eq 1`.
3. Power BI query action:
   - Workspace: `My Workspace`
   - Dataset: `827587e6-d966-4a1b-a305-93cc1e04b224`
   - Query: `EVALUATE FILTER('ADLs and Ambulation', 'ADLs and Ambulation'[Total Declined] > 0)`
4. Outer `Foreach`: `outputs('Run_a_query_against_a_dataset')?['body/value']`.
5. Inner `Foreach 2`: `outputs('Get_items')?['body/value']`.
6. Condition + Send Email exist under the true branch.
7. Keep `To` as Kevin for the first validation run if the People Picker rejects raw dynamic expressions. This prevents accidental DOR spam and keeps the flow valid.
8. Use a non-test subject/body with the Power BI row fields so the validation email proves the data pipeline works.

## Outlook action pitfalls

- Copilot may add a long instructional comment instead of changing fields. Verify actual action fields after Copilot responds.
- Long action comments break saving with `ActionDescriptionTooLong` (`maximum 256`). Shorten the comment to something like `Email ADL decline alert.` and save again.
- The People Picker can reject raw expressions like `@{items('Foreach_2')?['DOREmail']}` as invalid. If that happens, keep `To` as Kevin for validation and later use Power Automate's dynamic content picker to select DOREmail rather than typing the raw expression.
- After permission is granted and one validation email succeeds, switch `To` from Kevin to the DOR dynamic content field and keep Kevin in CC.
