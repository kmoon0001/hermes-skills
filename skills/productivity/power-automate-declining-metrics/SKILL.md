---
name: "power-automate-declining-metrics"
description: "Create a Power Automate flow that monitors weekly quality metric declines per facility and sends email/Teams notifications to the facility’s DOR and a central therapy resource."
---

# Power Automate Declining Metrics Skill

## Goal
Automate weekly detection of any patient‑level quality metric declines (e.g., functional score drops) in the Power BI/Fabric dataset and notify the responsible Director of Rehab (DOR) for that facility plus the central therapy resource (kmoon@ensignservices.net). The flow runs every Monday, pulls the latest export (Excel/CSV) from SharePoint, filters by facility, builds a summary, and sends an Outlook email and/or Teams message.

## Prerequisites
- SharePoint list **`Pacific Coast DOR Roster`** (actual name in SharePoint) containing columns: `Facility` (single line text), `DORName` (single line text), `DOREmail` (single line text), `Active` (boolean). This list is the single source of truth for DOR routing. Location: `https://ensignservices.sharepoint.com/sites/PacificCoast_SLP/Lists/Pacific%20Coast%20DOR%20Roster`
  - **IMPORTANT**: The list already exists with 12 DOR records. Column names are `Facility`, `DORName`, `DOREmail`, `Active` — NOT `FacilityName`, `Email`, `State`. Always check actual column names via Graph API before assuming schema.
  - **Site ID**: `ensignservices.sharepoint.com,d03d707d-1a83-4851-aa74-dc1560d1d0c4,a66a3bed-1db7-49f6-b9f8-7708fd56a868`
  - **List ID**: `99359330-0b9a-4abc-98c4-8579da49910d`
- **Power BI Report**: "One Clinical Outcomes Dashboard" in My workspace
  - Report ID: `327a2c21-f64b-4dab-8ee5-edc31f9123cd`
  - Semantic model / dataset ID from Power BI REST report metadata: `827587e6-d966-4a1b-a305-93cc1e04b224`
  - **Key page**: "ADLs and Ambulation" (page ID: `7b2d3705c13dd1b2750d`)
  - Table columns: Patient Name, Facility, Previous/Latest Assessment Date, Avg Functional Score, Previous/Latest Eating, Previous/Latest Sit to Lying, Previous/Latest Sit to Stand, Previous/Latest Toilet Transfer, Previous/Latest Walking 10 Ft, Total Declined, Total Improved
  - "Analyze in Excel" is DISABLED for this report — cannot export directly to Excel from Power BI UI
  - IMPORTANT: Power Automate can see/run the report connection, but REST/Power Automate query fails unless Kevin has required dataset Build/query permission. Error observed: `You cannot query the dataset '827587e6-d966-4a1b-a305-93cc1e04b224' by using the REST API because the dataset was not found or you do not have the required permissions.`
  - See `references/power_bi_report_structure.md` for full table schema
- A SharePoint folder where the weekly exported Excel file lands (e.g., `Shared Documents/MetricExports`). The file naming pattern is `Metrics_YYYY-MM-DD.xlsx`.

### Creating the Pacific Coast DOR Roster List
The list already exists in SharePoint. If it needs to be recreated:

**Option A: Import Excel (Recommended)**
1. Use the pre-formatted Excel file at `C:\Users\kevin\Desktop\Pacific_Coast_DOR_Roster.xlsx`
2. Go to SharePoint site → Lists → New → Import from Excel
3. Map columns: Facility, DORName, DOREmail, Active

**Option B: Manual Creation**
1. Go to SharePoint site → New → List → Blank list
2. Name it "Pacific Coast DOR Roster"
3. Add columns: Facility (text), DORName (text), DOREmail (text), Active (yes/no)
4. Paste DOR data from `references/dor_list.md`

**Option C: Graph API (Programmatic)**
Use Microsoft Graph API with a valid access token:
```
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists
{
  "displayName": "Pacific Coast DOR Roster",
  "list": { "template": "genericList" }
}
```
Then add columns via:
```
POST https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/columns
```
**Token handling pitfall**: Graph Explorer may display a masked/shortened token (`eyJ...`) and MSAL storage entries may be encrypted. Use the Access token tab's **Copy** button, save the full clipboard value locally (not to GitHub), then verify it starts with `eyJ`, has 3 dot-separated parts, and does not contain `...`. The token works for `/me` but may fail for `/sites/` if the URL format is wrong — use `sites/{hostname}:/{server-relative-path}` format.
- Outlook connector enabled in Power Automate (default in most tenants).
- Teams connector enabled (optional – if you want Teams notifications).
- The therapy resource email `kmoon@ensignservices.net` (hard‑coded in the flow).

## Step‑by‑Step Flow Design

### Method A: Copilot-Based Creation (Recommended — Fastest)
Use Power Automate's built-in Copilot to generate the flow from a natural language description, then fix the generated expressions.

1. Go to https://flow.microsoft.com
2. In the Copilot text box, paste this prompt:
   ```
   Create a scheduled cloud flow that runs every Monday at 7am Pacific. It should: 1) Get items from SharePoint list called Pacific Coast DOR Roster from site https://ensignservices.sharepoint.com/sites/PacificCoast_SLP 2) Run a query against the Power BI dataset for One Clinical Outcomes Dashboard to get patients with Total Declined greater than 0 from the ADLs and Ambulation table 3) For each declining patient, find their facility match in the DOR roster 4) Send an email to the DOR email address with CC to kmoon@ensignservices.net with subject containing the facility name and a table showing patient name, which categories declined, and previous vs latest scores
   ```
3. Click **Generate** → Review the suggested flow → Click **Keep it and continue**
4. On the connections page, verify all 3 connectors show green checkmarks (SharePoint, Power BI, Office 365 Outlook) → Click **Create flow**
5. **Fix the Power BI step** (see pitfalls below for workspace/dataset selection)
6. **Rename the flow** — Copilot generates an extremely long name from the prompt. Click the title, select all, type a short name like "Weekly ADL Decline Alert"
7. **Fix the Send an email step** — Copilot generates invalid expressions (see pitfalls below)
8. Click **Save**

### Method B: Manual Builder
1. **Recurrence Trigger** – Schedule: Every Monday at 07:00 (Pacific).
2. **Get DOR Roster (SharePoint)** – `Get items` from "Pacific Coast DOR Roster" list. This is the routing table.
3. **Run query against a dataset (Power BI)** – Query the "One Clinical Outcomes Dashboard" dataset for patients where `Total Declined > 0`. If DAX query fails, leave query blank and filter in next step.
4. **Filter array** – From Step 3 output, keep only rows where `item()?['Total Declined'] > 0`.
5. **Apply to each Facility** – Group declining patients by facility.
   - **Get DOR for Facility** – Filter the DOR Roster (Step 2) where `Facility` matches current group.
   - **Condition**: Has declining patients for this facility?
     - **Yes**: Build email body with patient names, category declines (Eating, Sit to Lying, Sit to Stand, Toilet Transfer, Walking 10 Ft), and previous/latest scores.
     - **No**: Skip.
6. **Send Email (Outlook)** – To: DOR email from roster. CC: `kmoon@ensignservices.net`. Subject: `⚠️ Weekly Quality Decline Alert – {{Facility}}`. Body: HTML table with decline details.
7. **Send Teams Message (optional)** – Post to DOR via chat or channel.
8. **Terminate** – Loop continues for each facility.

## Pitfalls & Tips
- **DOR Roster Column Names** — The actual SharePoint list uses `Facility`, `DORName`, `DOREmail`, `Active`. Do NOT assume `FacilityName`, `Email`, `State`. Always query columns via Graph API first: `GET /sites/{site-id}/lists/{list-id}/columns`.
- **User Prefers Programmatic** — When data needs to be added to SharePoint, do it via Graph API. Don't ask the user to manually import/paste. They will say "can you do it" — just do it.
- **Missing Export** — Add a parallel branch after step 2 that checks if the file list is empty. If so, send a warning email to you (the admin) and stop.
- **Date Formats** – Ensure the Excel sheet uses ISO dates (`YYYY‑MM‑DD`) so the *Filter array* action works reliably.
- **Large Files** – If the export exceeds 1 MB, the *Get file content* step may time‑out. In that case split the export into per‑facility CSVs upstream, or use Power BI‑direct query instead.
- **DOR List Updates** – Because the flow reads the Pacific Coast DOR Roster list on each run, you can add/remove facilities without redeploying the flow. Just edit the SharePoint list.
- **Email Limits** – Outlook connector caps at 150 recipients per hour. If you have many facilities, consider batching or using Teams only.
- **Plain‑Text Email Formatting** – Keep email bodies plain text (no markdown). Use simple bullet lists and capitalize headings as per user preference.
- **Graph API Token Truncation / Refresh** – When extracting tokens from Graph Explorer, visible token text and the `jwt.ms` access-token link can be masked/truncated (`eyJ0eX...`). Prefer the **Access token → Copy** button, then read the Windows clipboard and save the full token to `C:\Users\kevin\Documents\graph_token.txt`. Verify the saved token starts with `eyJ`, has 3 dot-separated parts, and does not contain `...`. See `references/session_2026_06_24_flow_hardening_and_github_sync.md` for the exact PowerShell-safe clipboard command.
- **Working Graph API Token Approach** — Save token to a text file, read with Python `open()`, use `requests` library. This works reliably for all Graph API endpoints including `/sites/` and `/sites/.../lists/.../items`:
  ```python
  import requests
  with open(r'C:\Users\kevin\Documents\graph_token.txt', 'r') as f:
      token = f.read().strip()
  headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
  r = requests.get('https://graph.microsoft.com/v1.0/sites/ensignservices.sharepoint.com:/sites/PacificCoast_SLP', headers=headers)
  ```
  Site ID format: `hostname,tenant-id,guid` (e.g., `ensignservices.sharepoint.com,d03d707d-...,a66a3bed-...`)
- **Token Truncation in Chat** — When user pastes a JWT token (~3800 chars) into chat, it gets truncated by the context system. The token may appear to have only 1 dot instead of 2. NEVER use a token pasted into chat directly — always ask user to save it to a file, or extract it from Graph Explorer.
- **Graph Explorer Token Refresh** — Graph Explorer and Power Automate MSAL localStorage often store encrypted token blobs, while visible token/link text may be masked with `...`. The reliable path is: open Graph Explorer, sign in/select Kevin's account, open **Access token**, click **Copy**, then read the full JWT from the Windows clipboard into `C:\Users\kevin\Documents\graph_token.txt`. Verify `starts=True`, `parts=3`, and `hasEllipsis=False` before using it. See `references/graph_token_and_roster_validation.md`.
- **Adding Items to SharePoint via Graph API** — Use `POST /sites/{site-id}/lists/{list-id}/items` with `{"fields": {...}}` payload. Check existing column names first via `GET .../columns`. Columns map to field names in the payload.
- **Browserbase Remote Browser** — The Browserbase browser is SEPARATE from the user's local browser. The user cannot see what you're doing in the remote browser. Don't ask them to "sign in" to the remote browser — they can't see it. Use local Playwright headed mode instead.
- **Playwright Headed Mode on Windows** — Works for showing the user a browser they can interact with. Use `playwright_cli.sh open <url> --headed`. The user can then type passwords, click buttons, etc. in the visible browser window.
- **Device Code Flow Too Complex** — Users find MSAL device code flow confusing ("do i need an access code?"). It also times out if the user doesn't act quickly. Avoid it — use Playwright headed mode for auth or have the user paste a token from Graph Explorer.
- **Copilot Generates Long Flow Names** — Power Automate Copilot uses the entire prompt as the flow name (500+ chars). Immediately rename after creation: click the title, Ctrl+A, type short name like "Weekly ADL Decline Alert".
- **Copilot Expression Errors in Send an email** — Copilot generates the flow structure correctly but often produces invalid expressions in the Send an email step. The flow will save but show "Invalid parameters" on the email step. **FIX VIA COPILOT CHAT**: Instead of manually editing, type in the Copilot chat box: `"Fix the Send an email step body to use dynamic content from the Power BI query results. Replace [Patient Name] with Patient Name, [Total Declined] with Total Declined, [Previous]/[Latest] in each column with the corresponding score fields. Replace [DOR Name] with DORName from Get items, [Facility Name] with Facility, and Assessment Dates with Power BI fields. Also fix Subject to use Facility from Get items."` Then type `"yes apply the changes"` when prompted. This works — Copilot successfully replaces placeholder text with `@items('Foreach_2')?['FieldName']` expressions.
- **Copilot CANNOT Set From Field but CAN Remove It** — The "From (Send as)" field in Send an email V2 is optional. If Copilot adds it with an empty value, the flow errors: "The 'From' field is required." Copilot will say it CANNOT update the From field value. **Fix**: Ask Copilot to REMOVE it: `"Remove the From field from the Send an email step entirely."` Copilot CAN do this. Alternatively, manually: open the Send an email step → click "Show all" under Advanced parameters → find "From (Send as)" → click the X/remove button next to it. The email will send from the default sender (your account) without the From field.
- **To Field Needs Manual Setting** — Copilot may generate the Send an email step with an empty "To" field. The flow will error: "To is required." **Fix**: Click the Send an email step → find the "To" field → click "Open People Picker" → type the email address → press Enter to confirm. The People Picker requires you to type the email and press Enter to add it as a recipient chip. Just typing the email without Enter won't save it.
- **Filter Query for Performance** — The "Get items" step warns about missing filter query. Add `Active eq 1` to the Filter Query field in Advanced parameters. This limits results to only active DORs and improves performance. The field is in: Get items → Advanced parameters → Show all → Filter Query.
- **Test with Admin Email First** — Before testing the full flow with all DORs, change the "To" field to just your email (kmoon@ensignservices.net) and test. This prevents bombarding all 12 DORs with test emails. After verifying it works, change "To" back to the DOR roster emails.
- **User Prefers "Do It" Over Instructions** — When the user says "can you do it?" or "you are confusing me", stop explaining and start doing. Don't provide copy-paste instructions for things you can automate via Playwright. The user wants hands-on execution, not documentation.
- **Monaco Editor Not Interactable via Playwright** — Power Automate's Code view uses a Monaco editor. The "Toggle code view" button is DISABLED when the Parameters tab is active. Even when Code view is open, the Monaco editor intercepts all Playwright clicks and keyboard events. Do NOT attempt to edit JSON in Code view via Playwright — use Copilot chat instead.
- **Power BI Dataset Selection Pitfall** — In Power Automate's "Run a query against a dataset" action, the Workspace and Dataset dropdowns may not show the correct options. Do not assume the report GUID is the dataset/semantic-model GUID. Verify the real `datasetId` from Power BI REST report metadata before saving or retesting. For this project, report ID `327a2c21-f64b-4dab-8ee5-edc31f9123cd` and semantic model/dataset ID `827587e6-d966-4a1b-a305-93cc1e04b224` are different; Power Automate should use `My Workspace` plus the semantic model ID, and the remaining `PowerBIEntityNotFound` after that indicates missing Build/query permission.
- **Recurrence Trigger Missing Interval** — Copilot generates the Recurrence trigger but may leave the **Interval** field EMPTY. The flow will fail immediately with: "The recurrence input for 'Interval' is required." **Fix**: After creating the flow, click the Recurrence step → find the "Interval" textbox in Basic settings → type `1`. Also verify Frequency is set to "Week" and set "At these hours" to `7` and "At these minutes" to `0` for 7:00 AM. Without these, the flow runs at midnight or not at all.
- **Power BI Dataset "NotFound" Error** — The "Run a query against a dataset" step may fail with `NotFound` / `PowerBIEntityNotFound`. This usually means the selected dataset/semantic model ID is not valid in the selected workspace, even if the Power BI connection is green. Do **not** keep retesting the same action. Open the failed run → failed Power BI action → Inputs/parameters and inspect `groupid`, `datasetid`, and `specification/query`.
  - If `datasetid` equals a report ID, replace it with the real dataset/semantic model ID; report ID and dataset ID are often different.
  - For this project, the actual Power BI REST report metadata showed report ID `327a2c21-f64b-4dab-8ee5-edc31f9123cd` and semantic model/dataset ID `827587e6-d966-4a1b-a305-93cc1e04b224`. The report `webUrl` was under `groups/me`, so Power Automate should use `My Workspace`, not `CrossDomain_Reports_MetricsRankingsOps`.
  - If runs show `datasetid 827587e6-d966-4a1b-a305-93cc1e04b224` with `groupid myworkspace` and still fail, inspect the detail value. In June 2026 the remaining error was a permission issue: `You cannot query the dataset ... by using the REST API because the dataset was not found or you do not have the required permissions.` That requires dataset/semantic model **Build** permission from a workspace admin or dataset owner.
  - To discover the real dataset ID from a logged-in Power BI browser session, inspect sessionStorage for a Power BI access token (`analysis.windows.net/powerbi/api`) and call `https://api.powerbi.com/v1.0/myorg/reports/{reportId}` from `page.evaluate`; the JSON response includes `datasetId`. Do not print the token.
  - The Dataset textbox may appear filled after typing a GUID, but if it is not a valid/selectable dataset for that workspace or the user lacks Build/query permission the saved action can still fail. Prefer selecting the dataset/semantic model from the dropdown or verifying via Power BI REST before saving.
  - If the DAX query fails after the dataset is confirmed, quote table names with spaces: `EVALUATE FILTER('ADLs and Ambulation', 'ADLs and Ambulation'[Total Declined] > 0)`. If DAX remains brittle, query broadly or leave Query Text blank and filter in Power Automate.
  - `references/power_bi_notfound_debugging.md` – Exact run-inspection workflow for `PowerBIEntityNotFound`, including `groupid`, `datasetid`, and query checks.
  - `references/power_bi_dataset_permission_and_email_setup.md` – Known report/dataset IDs, browser-session REST technique for finding `datasetId`, Build permission blocker wording, and final Outlook/email setup pitfalls.
  - `references/session_2026_06_24_flow_hardening_and_github_sync.md` – Session-specific notes for Graph Explorer token refresh via clipboard, DOR roster validation criteria, and private GitHub backup/sync pattern.
- **Power Automate Copilot Flow Structure** — Copilot generates: Recurrence → Get items (SharePoint) → Run query against dataset (Power BI) → Foreach → Foreach 2 → Condition → Send an email. The nested Foreach structure iterates first over facilities, then over patients within each facility. This is correct but may need the inner Foreach's iteration variable adjusted to reference the right collection.
- **Outlook Send Email Cleanup Pitfalls** — Copilot may only add comments/instructions to the Send an email action instead of changing fields. Verify the actual To/Subject/Body fields after Copilot responds. Long action comments can prevent saving with `ActionDescriptionTooLong` (max 256 chars); shorten the comment (e.g., `Email ADL decline alert.`) and save again. Raw expressions such as `@{items('Foreach_2')?['DOREmail']}` may be rejected by the People Picker; if so, keep `To` as Kevin for the validation run and only switch to DOR routing using Power Automate's dynamic content picker after the Power BI permission blocker is resolved.
- **Failure Notification Hardening** — Asking Power Automate Copilot to add a new failure-notification Outlook action may fail with "Office 365 Outlook connector could not be found or accessed" even when an existing Outlook action works. If this happens, do not keep retrying Copilot. After the Power BI permission blocker is resolved, add the admin failure email manually using the designer's plus button and Configure run after on the Power BI query step (failed, timed out, skipped).

## Supporting Files
- `references/power_automate_best_practices.md` – Consolidated guidance on building reliable scheduled flows, handling empty file cases, and using the *Configure Run After* feature.
- `references/dor_list.md` – Pacific Coast DOR roster data (12 facilities with names, emails, states).
- `references/pacific_coast_dor_roster.md` – SharePoint folder setup documentation.
- `references/sharepoint_list_creation.md` – Graph API list creation guide with token handling pitfalls.
- `references/power_automate_copilot_flow.md` – Details on the Copilot-generated flow: prompt used, generated structure, dataset GUID, and what needs manual fixing.
- `references/power_automate_github_guardrails.md` – Lightweight private-GitHub/Actions guardrail pattern for Power Automate flows when full Power Platform solution ALM is not warranted.
- `references/graph_token_and_roster_validation.md` – Graph Explorer token refresh via Copy button and SharePoint DOR roster validation approach.
- `references/session_2026_06_24_flow_hardening_and_github_sync.md` – Session-specific IDs, permission blocker, DOR validation, and GitHub sync notes for this flow.

## Usage
1. Import this skill into your project (`hermes skill import power-automate-declining-metrics`).
2. Verify the **Pacific Coast DOR Roster** list exists in SharePoint with the correct data (see `references/dor_list.md`).
3. Open Power Automate, click **Create → Scheduled cloud flow**, then copy‑paste the **Step‑by‑Step Flow Design** actions.
4. Test by placing a dummy export Excel in the SharePoint folder and run the flow manually.
5. Adjust the email template in the *Send Email* action if you need a different layout.

## Maintenance
- Update the **Pacific Coast DOR Roster** SharePoint list whenever facility leadership changes.
- If the export schema changes (new columns), edit the *Create CSV table* and the **Condition** step accordingly.
- Review the Flow run history weekly to catch throttling or connector failures.

---
