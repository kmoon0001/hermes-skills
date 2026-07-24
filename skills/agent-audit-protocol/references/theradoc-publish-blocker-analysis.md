# TheraDoc Workbench — Publish Blocker Analysis

## Overview
TheraDoc Workbench (bot `e09954e1`) is a card-based note generation agent with 304 components, 45 topics, 22 SASC nodes, 20 AdaptiveCards, and 33 KB sources. It had ~500 publish-blocking errors across 6+ categories.

## The Publish Masking Sequence

Errors masked each other across 4 layers. Each publish resolved the visible layer and revealed the next:

### Layer 1: Dialog References (22 topics)
- **Error:** `Dialog with id 'pcca_theradocworkbench.topic.AuditExistingNote' not found`
- **Root cause:** Topics referenced `AuditExistingNote` via `BeginDialog`, but that topic was renamed to `TheraDoc - Compliance Audit V2` with schema name `pcca_theradocworkbench.action.ComplianceAuditV2`
- **Also:** `WelcomeStart` → renamed to `ConversationStart`
- **Fix:** Replace the dialog reference with the correct schema name, then ACTIVATE the target topic (statecode → 0). If the target can't be found, remove the BeginDialog block entirely.
- **Tool/technique:** To find which topics reference missing dialogs, grep the `pac org fetch` output for the missing dialog name. Then PATCH each referencing topic to update or remove the BeginDialog block.

### Layer 2: Variable Scope (19→21 topics)
- **Error:** `Identifier not recognized in expression: Topic.Answer`
- **Root cause:** SASC nodes had `userInput: =Concatenate(...)` but NO `variable:` field. Subsequent `SendActivity(activity: "{Topic.Answer}")` referenced a variable that was never set.
- **Fix:** Add `variable: Topic.Answer` at the SAME indent level as `responseCaptureType` and `userInput`. Using deeper indent makes it a child property → publish fails with `Missing required property 'UserInput'`.
- **CRLF trap:** The regex `re.sub(r'\n        variable: Topic\.Answer', '', data)` doesn't match against `\r\n        variable:` because the data uses `\r\n`. Always normalize: `data.replace('\r\n', '\n')` → edit → `fixed.replace('\n', '\r\n')`.
- **Verify:** After PATCH, re-read the topic and confirm all three fields (`responseCaptureType`, `variable`, `userInput`) are at 6-space indent before the next `- kind:` action.

### Layer 3: Phantom Errors (OutputType + errorMessage)
- **Error:** `Missing required property 'OutputType'` (13) + `Required adaptive-card input is missing an error message` (89)
- **Root cause:** **Phantom errors caused by Layer 2**. Once the SASC variable issue was fixed, these errors disappeared — they were validation cascades from the broken SASC, not real issues with the cards.
- **Lesson:** Don't chase phantom errors until earlier layers are resolved. Always publish after fixing each layer.

### Layer 4: Output Binding / Flow Errors (50+ fields)
- **Error:** `Output binding 'therapistName' is not found, refresh this flow to get the latest bindings` (same for dateOfService, cptCodes, assistLevel, skilledJustification... 50+ unique fields)
- **Root cause:** A Power Automate flow was registered at the Copilot Studio bot level expecting 50+ output fields from Master Patient Context topic. The topic stores data in `Global.MPC_*` variables and has `outputType: {}` (empty). The flow's expected field names (therapistName, dateOfService) matched the AdaptiveCard Input names from the 20 note card topics, NOT the MPC topic's output.
- **Fix:** This is NOT a YAML fix — the flow registration is at the Copilot Studio platform level, not in botcomponent data. The orphaned flow must be deleted from Copilot Studio → Actions page.
- **Detection:** `pac org fetch` for type-100 components returned empty. The flow registration is at the bot/platform level, not as a botcomponent.

## Key Technical Lessons

### InvokeFlowAction vs InvokeConnectedAction
`InvokeFlowAction` with `action:` (no `flowId:`) → `Missing required property 'FlowId'`.
`InvokeConnectedAction` with `action: pcca_agent.action.X` → `Node is unknown to the system`.
The correct approach for cross-agent audit logging is `InvokeFlowAction` with a valid `flowId:` (Power Automate GUID). If the flow doesn't exist, remove the action block entirely.

### Master Patient Context outputType
Topics that store data in `Global.*` variables don't need `outputType` properties. The `outputType: {}` (empty) is correct. Adding a `properties:` block after `outputType: {}` at 2-space indent is INVALID YAML — `outputType: {}` is a completed mapping, so the next property at 2-space indent is parsed as a root-level key, not a child.

### Comparing Agents (TheraDoc vs Therapy Documentation Assistant)
See `references/theradoc-vs-tda-comparison.md` for the full structured comparison.
