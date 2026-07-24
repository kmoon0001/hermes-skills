# Power Automate Copilot Flow Reference

## Flow: "Weekly ADL Decline Alert"
- **Flow ID**: `920b9702-8e8a-4670-be66-9b3aaee53616`
- **URL**: https://flow.microsoft.com → My flows → Weekly ADL Decline Alert
- **Status**: Enabled (as of 6/24/2026)
- **Environment**: Ensign Services (default)

## Copilot Prompt Used
```
Create a scheduled cloud flow that runs every Monday at 7am Pacific. It should:
1) Get items from SharePoint list called Pacific Coast DOR Roster from site https://ensignservices.sharepoint.com/sites/PacificCoast_SLP
2) Run a query against the Power BI dataset for One Clinical Outcomes Dashboard to get patients with Total Declined greater than 0 from the ADLs and Ambulation table
3) For each declining patient, find their facility match in the DOR roster
4) Send an email to the DOR email address with CC to kmoon@ensignservices.net with subject containing the facility name and a table showing patient name, which categories declined, and previous vs latest scores
```

## Generated Flow Structure
1. Recurrence (Every Monday 7:00 AM)
2. Get items (SharePoint - Pacific Coast DOR Roster)
3. Run a query against a dataset (Power BI)
4. Foreach
5. Foreach 2
6. Condition
7. Send an email (Office 365 Outlook)

## What Copilot Got Right
- SharePoint connector and list selection
- Power BI connector (workspace: My Workspace)
- DAX query: `EVALUATE FILTER(ADLs_and_Ambulation, ADLs_and_Ambulation[Total Declined] > 0)`
- Nested Foreach structure (facilities → patients)
- Condition for declining patients
- CC field with kmoon@ensignservices.net

## What Copilot Got Wrong (Fixed)
1. **Interval field empty** — Recurrence trigger had no Interval value → flow failed with "recurrence input for 'Interval' is required" → Fixed by setting Interval = 1
2. **From field added with empty value** — Caused "From field is required" error → Fixed by removing the From field entirely via Copilot chat
3. **To field empty** — Copilot didn't set To field → Fixed by manually adding kmoon@ensignservices.net via People Picker
4. **Subject had placeholder** — Subject showed `[Facility]` instead of dynamic content → Fixed via Copilot chat
5. **Body had placeholders** — Body showed `[Patient Name]`, `[Total Declined]`, etc. → Fixed via Copilot chat (replaced with `@items('Foreach_2')?['FieldName']` expressions)
6. **Filter Query missing** — Get items step had no filter → Fixed by adding `Active eq 1`

## Unresolved Issues
1. **Power BI dataset "NotFound"** — The "Run a query against a dataset" step fails with "NotFound". The dataset GUID `327a2c21-f64b-4dab-8ee5-edc31f9123cd` may not be the correct dataset. The report is "One Clinical Outcomes Dashboard" but the dataset that powers it might be in a different workspace or have a different GUID. Needs investigation.

## Testing Status
- Flow has been tested multiple times — all runs show "Failed" at the "Run a query against a dataset" step
- The Recurrence and Get items steps work correctly
- The Power BI connection is the blocking issue

## Next Steps
1. Fix the Power BI dataset connection (verify dataset GUID, check workspace)
2. Test the flow end-to-end
3. Change To field from kmoon@ensignservices.net to individual DOR emails
4. Add proper HTML email body with dynamic content
