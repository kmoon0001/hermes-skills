# SharePoint Folder Creation via Playwright

This reference documents the exact steps used in the session to automate the creation of a folder in a SharePoint document library using the Playwright CLI wrapper.

## Steps
1. **Open the SharePoint library URL** with `playwright-cli open <url> --headed`.
2. **Snapshot** the login page to obtain stable element refs.
3. **Log in** manually (the Playwright window pauses for user input). No credentials are stored.
4. **Snapshot** again after successful login to capture the library UI.
5. **Click "New → Folder"** using the element reference for the "New" button (e.g., `e45`) and the folder name input (e.g., `e70`).
6. **Enter folder name** `Pacific Coast DOR Roster` and confirm.
7. **Take a final snapshot** and optionally a screenshot to verify the folder appears.

## Tips & Pitfalls
- Always snapshot after navigation or any UI change; element refs become stale otherwise.
- If the login page introduces MFA, the Playwright session will pause – simply complete the MFA prompt in the browser.
- Use `--headed` so you can see the UI and intervene when needed.
- The default document library is usually `Shared Documents`; adjust the URL accordingly.
- The reference file is stored under `playwright-codex/references/` so any future Playwright tasks can import it.
