# Post-solution-import first-pass checklist

Run before deep domain work whenever an agent was just transported.

1. Re-fetch bot by **name** in target env — botid almost always **new**.
2. Require `provisioningStatus=Provisioned` and `state=Synchronized` (re-publish if stuck Synchronizing).
3. Inventory components (types 9/14/15/16/19).
4. Type-15 greps: `GPT55Chat`, EVALUATION CONTEXT, empty/`len~1` `responseInstructions`, "use ONLY" source traps.
5. Every SASC: `responseCaptureType: FullResponse`, `userInput`, SendActivity before EndDialog.
6. Fallback + Conversational boosting: SASC + SendActivity + clearTopicQueue.
7. file[] / turn.uploadedFiles / FilePrebuiltEntity absent.
8. Report publish times in **Pacific local**.

Worked Doc Defense: `references/post-migration-doc-defense-therapy-ai-dev.md`
