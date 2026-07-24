# Session notes: flow hardening, Graph token refresh, roster validation, GitHub sync

Date: 2026-06-24/25

## Durable workflow lessons

### Graph Explorer token refresh without exposing the token in chat

When a saved `C:\Users\kevin\Documents\graph_token.txt` token is expired, use Graph Explorer in the logged-in browser rather than asking the user to paste a token.

1. Open `https://developer.microsoft.com/en-us/graph/graph-explorer` in the existing local Playwright browser session.
2. If not signed in, click **Sign in** and select `123713644@ensignservices.net`; user can handle MFA/password directly if prompted.
3. Open the **Access token** tab.
4. Click **Copy**. Do not rely on the visible `eyJ0eX...` token text or the `jwt.ms` link; both can be masked/truncated.
5. Read the Windows clipboard locally and write it to `C:\Users\kevin\Documents\graph_token.txt`.
6. Verify: token should start with `eyJ`, have 3 dot-separated parts, and `hasEllipsis=False`.
7. Immediately call Microsoft Graph `/me` and the target SharePoint endpoint to confirm it works.

PowerShell-safe clipboard save command from Git Bash:

```bash
powershell.exe -NoProfile -Command '$t = Get-Clipboard -Raw; $u = $t.Trim(); [IO.File]::WriteAllText("C:\Users\kevin\Documents\graph_token.txt", $u); Write-Output ("chars=" + $u.Length + " parts=" + ($u.Split(".").Count) + " starts=" + $u.StartsWith("eyJ") + " hasEllipsis=" + $u.Contains("..."))'
```

### Roster validation criteria

For the Pacific Coast DOR Roster SharePoint list, validate before DOR rollout:

- Graph `/me` returns Kevin's account.
- Site lookup succeeds.
- List item query succeeds.
- `total_items == 12`, `active == 12`, `issues == 0` for the current Pacific Coast scope.
- Every active row has `Facility`, `DORName`, `DOREmail`.
- Every active `DOREmail` is syntactically valid and ends with `@ensignservices.net`.

Known verified active facilities from this session:

- Alamitos West
- Beachside
- Coventry Court
- Mainplace Post Acute
- New Orange Hills
- Pacific Haven Subacute
- Palm Terrace
- Sea Cliff Healthcare
- St. Catherine
- St. Elizabeth
- The Hills Post Acute
- Victoria Healthcare

### GitHub backup/sync pattern for this flow

When the user asks to "save, create a github repo and push and sync" for this flow:

1. Create a private repo because docs contain internal facility/DOR emails and Power BI IDs.
2. Save materials under `C:\Users\kevin\Documents\weekly-adl-decline-alert`.
3. Include docs, checklists, and validation scripts, but exclude tokens/secrets.
4. Add `.gitignore` entries for `graph_token.txt`, `*.token`, `*.secret`, `.env*`, auth state, and HAR files.
5. Run the DOR roster verification script once before commit.
6. Create/push with GitHub CLI authenticated as `kmoon0001`.
7. Run `git status --short --branch`, `git ls-files`, and a token grep such as `git grep -n -E "eyJ0eX|access_token|gho_" -- . || true` before finalizing.

Repo created in this session:

- Private repo: `https://github.com/kmoon0001/weekly-adl-decline-alert`
- Local path: `C:\Users\kevin\Documents\weekly-adl-decline-alert`

Do not commit `C:\Users\kevin\Documents\graph_token.txt`.
