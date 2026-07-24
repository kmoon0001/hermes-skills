# Topic Deletion Workflow

Topics are deleted from the **Topics page row More menu**, NOT from the individual topic page.

## Steps
1. Navigate to agent Overview → click Topics tab
2. Wait 45s for DataGrid to load
3. Find topic row — More menu button at **x:336, rowY** (left side of each row)
4. Click More → menu shows: Details, Make a Copy, Delete
5. Click **Delete** menu item
6. Confirmation dialog appears — click **Delete** button

## Why not from topic page
The individual topic page (`adaptive/<uuid>`) More menu only shows:
- Analytics
- Open code editor

No Delete option there.

## Row identification
Rows use class `fui-DataGridRow`. Each row has the topic name as its text. The row More button has aria-label "More".

## Toggle state (ON/OFF)
The toggle switch for each row is an `<input role="switch">` child of the `.fui-DataGridRow`. The input's `.checked` property is the real state:
- `checked: true` = ON
- `checked: false` = OFF

Click the `.fui-Switch` container div to toggle (at x~1048, rowY). Do NOT click the hidden `<input>` directly — the click must hit the container div's event handler.

## See also
- `copilot-studio-instructions-editor/references/slp-caregiver-guard-remediation-2026-06.md` for guard topic deletion context
