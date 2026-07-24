# GitHub Guardrails for Power Automate Flows

Use this pattern when a Power Automate flow is business-critical but not yet mature enough for full Power Platform solution-based ALM.

## When to use
- The flow is mostly configured in the Power Automate designer.
- The user wants protection against accidental documentation drift, wrong IDs, token leakage, or lost setup details.
- Full Power Platform solution export/deploy is overkill or blocked by environment/admin constraints.

## Lightweight guardrail repo
Create a private GitHub repo containing:
- `README.md` with flow name, flow ID, report ID, semantic model/dataset ID, remaining blockers, and current status.
- `docs/permission-request.md` with the exact Power BI Build-permission request.
- `docs/post-permission-checklist.md` with Kevin-first validation before DOR routing.
- `docs/dor-roster-validation.md` with current SharePoint roster validation results.
- `docs/hardening-packet.txt` with operating notes and known pitfalls.
- `scripts/verify_dor_roster.py` for local/manual roster validation with a local Graph token file.
- `.gitignore` excluding `graph_token.txt`, `.env`, auth state, HAR files, and other secrets.

## GitHub Actions guardrail
Add `.github/workflows/validate.yml` that runs on push, pull_request, and workflow_dispatch:
- `python -m py_compile scripts/*.py`
- `python scripts/ci_validate.py`

`ci_validate.py` should check:
- Required files exist.
- Required flow/report/dataset IDs are present in docs.
- Power BI Build permission is still mentioned in the permission request.
- DOR roster validation doc still reflects expected active count and zero issues.
- Kevin-first validation remains documented before DOR rollout.
- No obvious JWTs, GitHub tokens, client secrets, passwords, or refresh tokens are committed.

## What NOT to automate in GitHub yet
Do not put Microsoft Graph tokens, Power BI tokens, browser auth state, or tenant credentials into GitHub secrets just to run live roster validation. For this workflow, local/manual validation is safer until a formal service principal or managed ALM setup is approved.

## Full ALM later
If the flow becomes production-critical across environments, graduate to Power Platform solution-based ALM:
1. Move the flow into a Power Platform Solution.
2. Export the solution.
3. Commit the exported solution/package to GitHub.
4. Use Power Platform CLI / GitHub Actions for controlled import to test/prod environments.

This is a later step; the lightweight guardrail repo is the safer first hardening layer.
