# Optional UX cleanup + visual verification pattern

Use this when Kevin asks to fix optional Copilot Studio issues "safely" and visually verify the result.

## Scope rule
- Fix only high-confidence, low-risk UX defects that preserve existing clinical/compliance logic.
- Do not remove clinical, compliance, regulatory, or guardrail text while simplifying flow.
- If a change would require restructuring core variables, routing, or audit logic, skip it and report it as intentionally not safe.

## Safe optional cleanup examples
- Document-upload double prompt: if a user already attached a file, add an early `System.Activity.Attachments` check, capture attachment name/content into Topic variables, and route after document-type selection without asking for the same file again.
- End-of-conversation churn: simplify to one CSAT question, one closing SendActivity, and `EndDialog`; avoid extra repeat/choice loops unless they carry real business logic.

## Dataverse workflow
1. Back up the exact live `botcomponents.data` records before patching.
2. PATCH only the `data` field on the target botcomponent.
3. Treat HTTP 204 as necessary but not sufficient.
4. Re-query the same botcomponent and inspect the persisted `data` string for the expected changes.
5. Run schema/YAML validation on the after snapshot when available.
6. Publish via gateway `publishv2-operations` and poll until `isInFinalState=true` and `state=Finished`.
7. Re-query the bot record `synchronizationstatus` / `publishedon` to confirm publish success.

## Visual verification workflow
- Open Copilot Studio in the target environment and agent.
- Verify the custom Topics list shows changed topics as enabled, recently modified, and with no visible errors/blocked flags.
- For deleted/duplicate topics, visually confirm the original topic remains and the copy/duplicate is absent from the custom topic list.
- Switch to the System tab for system-topic changes; verify the changed system topic is enabled, recently modified, and has no visible error/blocked flags.
- Verify the Publish banner/date after publishing.
- If direct editor navigation is flaky, the Topics list plus live Dataverse readback is acceptable evidence; do not waste time repeatedly fighting SPA navigation.

## Reporting
Final response should be concise and bottom-line first:
- what was fixed
- what was intentionally skipped as unsafe, if anything
- what verification passed
- where backups/report files were written
