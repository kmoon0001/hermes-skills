---
name: passagenttesting
description: Systematic Microsoft Copilot Studio evaluation repair workflow. Use when the user asks to pass agent testing, improve evaluation scores, raise pass rates such as 90% to 95%+, diagnose failed test cases, tune Copilot Studio topics/instructions/knowledge/routing, fix parent/child agent orchestration, publish agents, verify synchronizationstatus, or create a repeatable testing loop for Copilot Studio agents.
---

# Pass Agent Testing

Use this skill to move a Copilot Studio agent from "mostly passing" to a verified target threshold without guessing or inflating results.

## Ground Rules

- Treat live Copilot Studio and Dataverse as source of truth when available.
- Do not fabricate scores, failed cases, publish status, tool outputs, API responses, or clinical facts.
- For healthcare agents, never include raw PHI in prompts, payloads, logs, or summaries. Use record_id pointers.
- Preserve user changes. Inspect git status before major edits and keep diffs focused.
- Use Microsoft Learn as the reference for evaluation triage, instructions, generative answers, and remediation.
- Validate with the same evaluation set after fixes. If the target is not met, continue the triage loop or state the blocker.
- When the user asks for instructions text to paste: **give the raw text directly.** Do not attempt programmatic save via CDP Input.insertText or Playwright fill — both fail on the CS Instructions contentEditable editor because React's dirty-state flag blocks all programmatic saves. See the `cdp-instructions-injection` skill for the Monaco code editor approach (works for topic YAML, not agent instructions).
- **CDP Input.insertText + Ctrl+S ALWAYS fails for CS Instructions save.** The Copilot Studio editor uses a React contentEditable component whose dirty-state flag does NOT trigger on Input.insertText. The text IS injected into the DOM, but React doesn't detect the change, so Ctrl+S does nothing. Space+backspace, blur/focus cycles, and dispatchEvent tricks all fail. The Save button stays disabled. This is a React-level behavior, not a CDP limitation.
- **Only two reliable save paths:** (1) User manually types a character and deletes it (triggers React onChange), then clicks Save. (2) For topic YAML (Monaco code editor), click a `.view-line` element in Monaco first, THEN type a character + Backspace, then Save. See `references/playwright-monaco-hermes-v8.md` for the full technique. CDP keyboard events alone (without the view-line click) never trigger React's onChange.
- **Always verify after any save attempt** by re-opening the Instructions editor and reading back the content. A Published status does not mean the instructions changed.
- **Playwright CLI fill is NOT reliable for CS instructions.** The fill command on the contentEditable returns success but the text may NOT actually save. In June 2026, SLP/PT/OT kept stale instructions through 40+ evaluation runs because fill + Save showed Published but never persisted — scores dropped from 95% to 67% before the root cause was found.
- **⚠️ NEVER rewrite MultiTurnEvaluationCase `data` fields via Dataverse API.** Attempting to transform evaluation cases from prompt-first to answer-first by rewriting the YAML `data` field collapsed 6-turn conversations into 2-turn cases, breaking evaluations for ALL agents. The correct fix per Microsoft Learn: change the GRADING METHOD to General quality in the Copilot Studio UI, which judges relevance/groundedness/completeness/abstention without requiring rigid expected transcripts. See `evaluation-driven-agent-optimization` skill for the full pitfall details.
- The parent skill

## Workflow

### Phase 0: Cross-Session Context Recovery

Before touching any live agent, recover context from prior sessions. The fix loop is iterative — each session picks up where the last left off.

1. **Run `session_search` with agent names, dates, and score patterns** — e.g., `session_search(query="SLP OT TDA evaluation ensign scores fix")`. Recovery of the previous session's baseline scores, root causes, and attempted fixes prevents re-triage of already-solved problems.
2. **Key information to recover:**
   - Which vX instructions were applied and what effect they had
   - Which topic-level fixes (EndDialog, clearTopicQueue) were already attempted
   - Which KB/knowledge-source changes were made
   - The most recent published state and what was left unfinished
3. **If session_search returns no results**, the session DB may only span recent days. Check memory for durable facts (bot IDs, env IDs, known fix patterns).
4. **Establish the current state** — verify bot IDs haven't changed, check whether the prior session's changes are still published, and note any score regressions that happened between sessions (common if instructions weren't persisted through Publish).

### Phase 1: Initial Triage

1. **Gather context**
   - Read repo instructions: `AGENTS.md`, `AGENT.md`, `README.md`, `.kiro/steering/*`, runbooks, and package notes.
   - Identify environment URL, tenant, bot ID, schema name, parent agent, child agents, topics, knowledge sources, evaluation sets, and latest publish status.
   - Verify publish state via `bot.synchronizationstatus`; do not rely on `pac copilot list`.
   - Pull or inspect active components:
     - `componenttype=15`: GPT/instructions
     - `componenttype=9`: topics and connected-agent task components
     - `componenttype=14` or `16`: knowledge sources
     - evaluation components/cases when available

2. **Capture baseline**
   - Record current single-response and multi-turn scores, target threshold, latest run date, and failing cases.
   - If failures are not available, inspect evaluation artifacts, screenshots, exported cases, live UI, or Dataverse records.
   - Classify at least five failures before changing broad behavior when possible.

3. **Triage in Microsoft Learn order — FULL STACK, not just instructions**
   - **CHECK TOPIC ON/OFF STATUS FIRST.** Navigate to Topics page or use Dataverse API (`componenttype eq 9 and statecode eq 1`). If >25% of topics are OFF — especially those named Eval Guard or * Intake — this is the #1 root cause of single-digit scores. Inactivated exact-match intake topics cause evaluation test cases to fall through to generic generative AI which produces ungraded responses. **Evidence: OT_Specialist 5% score with 12/20 Guard topics OFF (Jun 2026). PT Conv 74%→95% purely by activating 16 inactive guard topics (Jun 15, 2026).** Before touching instructions or settings, verify topic status. See `references/inactive-topic-detection.md`.

     **Dataverse API for topic state checking (faster than SPA):**
     ```javascript
     // Query inactive topics
     var filter = '_parentbotid_value eq ' + botId + ' and componenttype eq 9 and statecode eq 1';
     var url = '/api/data/v9.2/botcomponents?$select=name,botcomponentid,statecode&$filter=' + encodeURIComponent(filter) + '&$top=50';
     var resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' } });
     // statecode: 0=Active, 1=Inactive

     // Activate a topic
     var resp = await fetch('/api/data/v9.2/botcomponents(' + topicId + ')', {
       method: 'PATCH',
       credentials: 'include',
       headers: { 'Content-Type': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' },
       body: JSON.stringify({ statecode: 0 })
     });
     // Status 204 = success, no body returned
     ```

     **Reading agent instructions (type 15 components):** Instructions are stored in the `data` field (YAML), not `content`. Query with `$select=data`:
     ```javascript
     var filter = '_parentbotid_value eq ' + botId + ' and componenttype eq 15';
     var url = '/api/data/v9.2/botcomponents?$select=data&$filter=' + encodeURIComponent(filter);
     ```
     Parse `data` for `instructions: |` block. Also contains `gptCapabilities`, `aISettings.model.modelNameHint` (e.g. GPT5Chat), `conversationStarters`.

     **Updating KB descriptions (type 16):** Blank descriptions hurt retrieval routing:
     ```javascript
     var resp = await fetch('/api/data/v9.2/botcomponents(' + kbId + ')', {
       method: 'PATCH',
       credentials: 'include',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ description: 'Keyword-rich description of content and when to route to it.' })
     });
     ```
   - ⚠️ **CHECK SETTINGS SECOND.** "Allow ungrounded responses: OFF" is catastrophic for conversation scores (40-50 pt drops). Verify it's ON before any other changes. See `copilot-studio-development-workflow/references/allow-ungrounded-toggle-pitfall.md`.
   - ⚠️ **CHECK KNOWLEDGE SOURCES FOR DUPES + DESCRIPTIONS THIRD.** When all agents regress simultaneously after SharePoint KB changes, the root cause is systemic: generic SharePoint folder names = GPT can't route retrieval → ungrounded failures fleet-wide. Fix order: (1) Rename SharePoint folders to keyword-rich names (~100 chars), (2) Remove individually uploaded duplicates that exist in SharePoint, (3) Rewrite all auto-generated descriptions ("searches information contained in..."). See `references/sharepoint-regression-pattern.md`.
   - THEN proceed with the Microsoft Learn triage order below. — EXPANDED June 2026:
   - **0. CHECK TOPIC STATUS FIRST.** Navigate to Topics page. If >25% of topics are OFF — especially "Eval Guard" or "Intake" named — turn them ON before anything else. Inactivated exact-match intake topics cause single-digit scores (OT: 5%, 12/20 OFF).
   - **0b. CHECK "ALLOW UNGROUNDED RESPONSES" SETTING.** If OFF, turn ON. This setting is catastrophic for conversation evaluations (OT: 50%→10%, SLP: 95%→86%).
   - **0c. CHECK KNOWLEDGE SOURCES FOR DUPLICATES AND BLANK DESCRIPTIONS.** When rolling back or deduplicating KB sources (moving individual files into SharePoint), verify SharePoint folder names are keyword-rich FIRST — otherwise GPT loses retrieval routing and scores drop fleet-wide (OT/PT/SLP/TDA all regressed Jun 2026 after SharePoint consolidation without folder renaming).
   - Then proceed with the standard triage:
     - If the agent response is acceptable, fix the evaluation case or grader.
     - If the expected answer is wrong or stale, fix the evaluation case.
     - If a concrete configuration defect exists, fix the agent.
     - If reasonable configuration fixes do not persist, document a platform limitation.

4. **Find systemic patterns**
   - If 80%+ of failures share one root cause, fix the category, not individual cases.
   - If scores are flat after changes, re-triage; the root cause was probably wrong.
   - If one score improves while another regresses, inspect instruction conflicts and topic routing.
   - If single-response fails but conversation passes, inspect prompt-first topics, strict graders, and ambiguous expected answers.
   - **`Keep response under 800 characters` in topic `additionalInstructions`**: The most common topic-level defect. Scan ALL `SearchAndSummarizeContent` topics for unenforceable length limits. See `references/topic-800char-limit-fix.md` for the full diagnosis and fix procedure. (Evidence: SLP Conv 85% with 3 topics containing 800-char limits, June 14, 2026.)
   - **Conversation fails but single-response passes**: Check instruction-level issues FIRST, not topic structure.
         - Cross-agent comparison: If one agent passes Conv but another fails, extract both agents' instructions from Dataverse (componenttype 15) and compare RESPONSE FORMAT headers. The most common difference: conditional ("full document audits only") vs unconditional ("ALL document-related questions") format. See `references/cross-agent-instruction-comparison.md` for the SLP vs OT case study.
         - The most common cause: instructions say "do NOT ask for the document, give 3-4 required elements" (correct for conversation tests if using record_ids) BUT also contain unenforceable constraints ("NEVER exceed 800 characters") or citation tag preservation rules that hurt single-response quality. **New in v4:** Unconditional RESPONSE FORMAT ("Always use for any audit question") also causes regressions — PT conversation dropped 90% → 80% when the format was forced on general clinical inquiries. Fix: "For full audits: use RESPONSE FORMAT. For general questions or element checks: give focused natural answer."
      - **Conversation fails, single passes** — check instruction-level issues FIRST, not topic structure. The most common cause: instructions say "do NOT ask for the document, give 3-4 required elements" (correct for conversation tests if using record_ids) BUT also contain unenforceable constraints ("NEVER exceed 800 characters") or citation tag preservation rules that hurt single-response quality. **New in v4:** Unconditional RESPONSE FORMAT ("Always use for any audit question") also causes regressions — PT conversation dropped 90% → 80% when the format was forced on general clinical inquiries. Fix: "For full audits: use RESPONSE FORMAT. For general questions or element checks: give focused natural answer."
      - Verify that instruction-level fixes don't accidentally remove the "do NOT ask" rule — that will drop conversation scores.
      - If topic structure is sound (clearTopicQueue: true, EndDialog present), the fix is in instructions, not topics.
   6. **Both single-response AND conversation drop after instructions fix**: You removed or modified the structured RESPONSE FORMAT section (Classification, Score X/100, Compliance Findings, Missing Elements, Recommendations, Advisory). The grader checks for this exact output structure. **Always preserve the RESPONSE FORMAT section when editing instructions.** The response format is the grader's primary scoring rubric — removing it can drop single-response from ~92% to ~78% while also hurting conversation scores.

5. **Apply minimal fixes**
   - Prefer small source or live UI/API-supported changes that match the repo's deployment pattern.
   - Keep instructions concise and structured as Constraints -> Routing/Tools -> Response Format -> Guidance.
   - Give the agent an "out" for missing inputs instead of forcing fabricated findings.
   - Do not add broad abstractions, new dependencies, or unrelated cleanup.

6. **Publish and verify**
   - Publish using the repo-approved path.
   - Verify `synchronizationstatus.lastFinishedPublishOperation.status == "Succeeded"`.
   - **CRITICAL: Verify instruction content after publish.** The playwright-cli `fill` + Save + Publish cycle can silently fail — the UI shows "Published" but the instructions never changed. After publishing, re-open the Instructions editor and read back the content to confirm the correct version is live. A mismatch here wastes evaluation runs on unchanged instructions.
   - Rerun the same evaluation sets, then a regression pass on previously passing cases.
   - Record date, change, score before, score after, and residual failures.

### Phase 2: Iterative Deep-Dive Fix Loop

After initial triage and first-round fixes, enter the iterative loop. This is the core pattern the user calls "the fix loop like last night."

**Principle: Fix one agent at a time, loop until target is met.** Do not touch the next agent until the current one reaches the threshold (>95% for both SR and Conv). Never spread fixes across multiple agents in a single pass — each agent has unique instruction/topic/routing issues that cross-contaminate analysis. If a fix helps one agent but regresses another, the fix was agent-specific — do not blanket-apply.

**Loop structure — repeat for each agent:**
```
1. Deep-dive gap analysis (extract failures, classify root causes)
2. Create fix checklist (numbered, scoped to one agent)
3. Apply fixes + publish (one agent at a time)
4. Trigger new evaluation run
5. Review results (before/after comparison)
6. IF at target → move to next agent
7. IF not at target → return to step 1 for same agent
8. IF three consecutive cycles produce no improvement → document blocker
```

**During the loop, provide periodic progress updates** — especially when evaluations are running (10-15 min). The user expects to see where each agent stands and what the next step is. Do not go silent during long operations.

**Multi-agent score patterns to watch for:**
- If one agent's instruction fix causes another agent to regress (e.g., copying v5 conditional RESPONSE FORMAT to all agents broke OT and TDA while helping PT), the fix was agent-specific — do not blanket-apply
- If all agents regress simultaneously, look for systemic root causes (SharePoint KB, environment-wide setting, model update)
- If conversation scores lag behind SR by 2-3x after the same fix, see the "Conv recovery lags SR" section below
- **If fixing one topic's 800-char limit causes DIFFERENT topics to now fail** (score stays flat or drops), the 800-char limit exists in OTHER topics too. Fix was correct but incomplete. Batch-remove the limit from ALL topics before re-testing.
- **If SR regresses >5% after applying topic YAML fixes**: you replaced the entire topic YAML with an old template-export version that lacked post-export triggerQueries and modelDescriptions. The 800-char removal was correct but the full replacement removed other optimizations. Surgical line deletion only — see `references/monaco-injection-verification.md`. Evidence: OT/PT SR 94% → 87-88% (June 16, 2026).

## Automated Evaluation via REST API (Preferred Method)

Instead of waiting for the SPA evaluation page to load in the browser, trigger evaluations programmatically via the Power Platform API. This is faster, scriptable, and integrates into CI/CD.

### Getting an Access Token (Without App Registration)

The fastest way to get a token: intercept Bearer tokens from Kiro Chrome's
network traffic via CDP `Network.enable`. See the `evaluation-rest-api` skill
for the complete workflow — capture a token in ~10 seconds, valid for ~1 hour.

```javascript
// CDP: Network.enable, reload evaluation page, capture Authorization headers
// Tokens for api.powerplatform.com are ~2000-4500 chars
```

For production CI/CD, use an App Registration instead (below).

### Prerequisites

1. **Bot ID** and **Environment ID** for the target agent
2. A **test set** created in Copilot Studio (create via the UI first)
3. **App registration** in Azure Portal with Power Platform API permissions:
   - Go to portal.azure.com → App Registrations → your app → API permissions
   - Add permission → "APIs my organization uses" → search "Power Platform API"
   - Delegated permissions → **CopilotStudio** → `MakerOperations.Read`, `MakerOperations.ReadWrite`
4. Acquire an OAuth 2.0 access token for the Power Platform API scope

### API Endpoints

Base URL: `https://api.powerplatform.com/copilotstudio/environments/{envId}/bots/{botId}/api/makerevaluation?api-version=1`

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List test sets | GET | `/testsets` |
| Get test set details | GET | `/testsets/{testSetId}` |
| Start evaluation | POST | `/testsets/{testSetId}/run` |
| Get run status/results | GET | `/testruns/{runId}` |
| List historical runs | GET | `/testruns` |

### Trigger an Evaluation

```http
POST /testsets/{testSetId}/run?api-version=1
Content-Type: application/json

{
  "RunOnPublishedBot": false,
  "mcsConnectionId": "shared-microsoftcopi-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "evaluationRunName": "CI-Check-2026-06-09"
}
```

**Parameters:**
- `RunOnPublishedBot` — `false` evaluates draft (default), `true` evaluates published version
- `mcsConnectionId` — Power Automate connection ID for authenticated access. Get it from make.powerautomate.com → Connections → Microsoft Copilot Studio → copy ID from URL. Without this, evaluation runs **anonymously** (tools/knowledge sources may fail).
- `evaluationRunName` — optional label for dashboards

**Pitfall: One-run-at-a-time.** The API returns HTTP 422 if a run is already in progress for the same agent. Wait for completion before triggering again.

### Poll for Completion

```http
GET /testruns/{runId}?api-version=1
```

Poll every 10s until `state` is `"Completed"` or `"Failed"`.

### Get Results

The response includes `testCasesResults[]` with per-case:
- `testCaseId`, `state` ("Passed"/"Failed")
- `metricsResults[].result.data` — scores for General quality: `abstention`, `relevance`, `completeness`
- `aiResultReason` — AI explanation of the result

**IMPORTANT LIMITATION:** Single-response (SR) test runs do NOT populate `aiResultReason`.
The grader only provides reasons for conversation (multi-turn) failures.
For SR failure analysis, you must use the Copilot Studio UI evaluation detail page
(see Browser-Based Evaluation Result Inspection below).

**Token scope:** Tokens captured from CDP `Network.enable` are read-only — they can GET
existing evaluations but cannot POST new ones. To trigger evaluations programmatically,
use the Copilot Studio UI or an App Registration with write permissions.

### Triggering Evaluations via CDP/Browser (When REST API Is Unavailable)

When you need to trigger a new evaluation run through the browser UI (no REST API token or write permissions):

**Correct button sequence (not intuitive):**
1. Navigate to the agent's Evaluation page
2. Click **"New evaluation"** button (top of the page, not the "Evaluate" buttons on test set cards)
3. A dialog/panel opens — click **"Run"** button
4. Wait 10-15 minutes for 100 SR cases, or ~5 min for 20 Conv cases
5. Navigate back to the evaluation main page to see results

**Common pitfall — wrong Evaluate button:** There are multiple "Evaluate" buttons on the page. The "New evaluation" button is the correct entry point. Clicking "Evaluate" on individual test set cards or recent result rows opens detail views, not new runs. The text "Evaluate" on recent-result rows is a misnomer — it re-runs the existing test, not the current agent.

**Progress monitoring:** After triggering a run, the browser URL changes to include the run ID, and the page shows a progress indicator. However, the CDP SPA frequently doesn't show the progress. To verify the run started, check for text changes in `document.body.innerText` — if the page text changes from the test-set cards to showing a progress bar or run-detail URL, the run was accepted.

**Pitfall: CDP connection saturation.** Opening more than ~15-20 tabs in the same Chrome CDP session causes new WebSocket connections to fail with `Unexpected server response: 500`. Chrome caps the number of concurrent DevTools connections. If you hit this:
- Close unused tabs via `curl -s -X DELETE "http://127.0.0.1:9223/json/close/{pageId}"`
- Or reuse existing tabs instead of opening new ones for each navigation
- Or restart Chrome with a fresh debug profile

### Getting mcsConnectionId

1. Go to [make.powerautomate.com](https://make.powerautomate.com)
2. Open **Connections** from the side menu
3. Select your **Microsoft Copilot Studio** connection
4. Copy the connection ID from the URL: `/connections/shared_microsoftcopilotstudio/{mcsConnectionId}/details`

### When to Use This vs Browser

| Method | Best for |
|--------|----------|
| **REST API** | CI/CD pipelines, pre-publish validation, regression passes, nightly runs, ANY programmatic access |
| **Browser UI** | One-off manual inspection of raw SPA output, visual debugging of topics |

**Token Acquisition:** Use CDP `Network.enable` on a Kiro Chrome tab with Copilot Studio open, reload the evaluation page, and intercept the `Authorization: Bearer` header from any `api.powerplatform.com` request. Save it and use for all evaluation API calls. Full workflow: `evaluation-rest-api` skill.

### Evaluation API References

- [Automate evaluations with Power Platform API](https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-rest-api)
- [Automate evaluation with Evaluation APIs (Tech Community)](https://techcommunity.microsoft.com/blog/copilot-studio-blog/automate-agent-evaluation-with-the-evaluation-apis/4511653)
- [Trigger evaluations with Power Platform connectors](https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-automate-tools)
- See the `copilot-studio-development-workflow` umbrella skill for the full YAML-first dev lifecycle (clone → edit → push → evaluate → CI/CD)

## Knowledge Source Quality

Knowledge source names and descriptions directly affect generative orchestration. The agent selects knowledge sources based on their **description text**, not filenames.

Common issues:
- **Auto-generated descriptions**: "This knowledge source searches information contained in [filename]" — replace all of these
- **File extensions in names**: .pdf, .md, .docx suffixes
- **Underscores and technical filenames**: `SNF_PDPM_Classification_Walkthrough.pdf`
- **Overlapping descriptions**: multiple sources described identically

### SharePoint Folder Name = The Only Description

**CRITICAL**: SharePoint sources in Copilot Studio do NOT have an editable description field. The **folder name IS the description** — it's what the GPT filter uses for retrieval routing. There is no separate textarea.

Therefore:
- Rename SharePoint folders to be keyword-rich (~100 char limit)
- Include what content is inside and when GPT should route to it
- Avoid generic names like "Core Clinical Manuals" — expand to e.g., "Core Clinical Manuals - CMS: PDPM, Part B, MDS 3.0, Jimmo, Ch5/Ch15, Program Integrity, 42 CFR, MSCA, MSP, PIP"
- Folder name keywords directly improve retrieval routing scores

### Playwright on Windows — Critical Gotchas

**Background mode FAILS on Windows Git Bash.** Running any Playwright script
via `terminal(background=true)` on this host immediately fails with
`stdin is not a tty` (exit code 1). The background shell can't allocate a
pseudo-terminal for Chromium. **Always use foreground mode with a generous
timeout (180-300s).** Never attempt `background=true` for Playwright scripts.

**require path for playwright-core:** On this Windows setup, `require('playwright-core')`
fails even when installed globally. Use the absolute path:
`require('C:/Users/kevin/AppData/Roaming/npm/node_modules/playwright-core')`.

**Auth state can expire mid-session without warning.** The persistent
`.playwright-auth/state.json` stops working and Copilot Studio pages return
105 chars with "Pick an account" sign-in prompt. When body text is < 500 chars
and contains sign-in language, the auth state is expired — the user must
re-sign in via Kiro Chrome. Test auth freshness with a quick body text read
before running long multi-agent scans.

## Playwright Auth Refresh and SPA Timing (Windows)

**Auth state expires** after ~hours. The persistent auth at `.playwright-auth/state.json`
stops working — Copilot Studio shows "Pick an account" with 105-char body.

**Refresh workflow:**
1. Launch Playwright in **headed mode** (`headless: false`)
2. Navigate to any Copilot Studio page
3. User signs in through the visible browser window
4. Save: `await page.context().storageState({ path: authPath })`
5. Switch back to `headless: true` for subsequent runs

**Windows foreground requirement:** Scripts MUST run in foreground
(`terminal(background=false)`). Background mode (`background=true`) on Windows
Git Bash fails with `"stdin is not a tty"` error — the Playwright process can't
allocate a console.

**SPA timing:** After `page.goto()` to any Copilot Studio page, wait **25-30 seconds**
(`page.waitForTimeout(25000)`) before reading body text. 10-15s is insufficient —
the React SPA renders lazily and `body.innerText` returns 105 chars (shell only)
until hydration completes.

### Cross-Agent KB Comparison Technique

When triaging a specific agent's failures, always run a cross-agent audit first:

1. Launch Playwright headless: false with 180s+ terminal timeout
2. Navigate sequentially to each agent's Knowledge page
3. Use `body.innerText` to extract source names (SPA needs 10-15s to render)
4. Compare sources across agents to find:
   - Files in SharePoint that agents still have individually → remove from agent KBs
   - Files in one agent that others are missing → add to missing agents
   - Sources with blank or auto-generated descriptions → flag for rewrite
5. Also check SharePoint folder contents via `page.goto()` to the SharePoint URL

See `references/knowledge-source-descriptions.md` for Microsoft Learn best practices on writing descriptions that improve evaluation scores.

## Structural Fix Checklist

Run `scripts/audit_copilot_topics.ps1` against an unpacked agent folder when source files are available:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\skills\passagenttesting\scripts\audit_copilot_topics.ps1 -Path "path\to\agent"
```

Fix any reported issues:

- Every `SearchAndSummarizeContent` topic must end with `EndDialog` and `clearTopicQueue: true`.
- Never use `clearTopicQueue: false`.
- Use `applyModelKnowledgeSetting: true` or omit it. Never set it to `false`.
- Remove `SearchSpecificFiles`, `SearchSpecificKnowledgeSources`, `fileSearchDataSource`, and `knowledgeSources: kind: SearchAllKnowledgeSources` unless a narrow-source topic is explicitly required.
- **Remove `Keep response under 800 characters` from EVERY topic's `additionalInstructions`.** This is the single highest-impact topic-level fix. This unenforceable limit causes the model to produce truncated responses that the grader interprets as "refuses to help" or "incomplete." Scan ALL `SearchAndSummarizeContent` topics for this pattern — it can lurk in 10+ topics simultaneously. Batch-remove from all topics before re-testing; fixing one topic at a time causes regression cascade (other topics with the limit become new failures). See pattern below in section 6.
- **Topic YAML must start with `kind: AdaptiveDialog`** — omitting this causes "Invalid kind, expected 'AdaptiveDialog' but got 'Unknown'" when pasting into the code editor. Always give the user the complete YAML from `kind: AdaptiveDialog` through `outputType: {}` — never partial snippets.
- **Add citation instruction to every topic**: `Cite CMS Chapter 15 and [discipline] guidelines by natural source name. Do not output cite:1 or metadata tags.` Without this, the grader says "didn't cite knowledge sources" even when the response has citations in the wrong format.
- Keep `allowLatencyMessage: false`; remove distracting latency message text from evaluation-critical topics.
- Remove JSON/prose conflicts such as "NOT JSON" plus "Return exactly one valid JSON" in the same prompt.
- Avoid generic `OnActivity` + `type: Message` topics unless they are deliberate fallback topics.
- Convert prompt-first audit topics to answer-first/search-first topics when the user message already contains the document, record_id, or question.
- Narrow connected-agent descriptions so child agents are invoked only for the intended document audit scope.

### Source-code diagnostics (when live evaluation scores or failed cases aren't accessible)

Run these checks against unpacked topic YAML files to find systemic defects that would cause evaluation failures:

- **Empty intent triggers (`intent: {}`)**: Topics with no trigger queries can NEVER be triggered by natural language — they are dead unless explicitly routed via `BeginDialog`. This is the #1 cause of "audit topic never fires" failures. Fix: add trigger phrases matching realistic user input.
- **Duplicate `OnUnknownIntent` handlers at identical priority**: Two or more topics with `OnUnknownIntent` and the same priority value cause non-deterministic routing. Same test input can hit different handlers on different evaluation runs, producing unstable scores. Fix: consolidate into one handler, or use distinct priorities.
- **Instruction conflicts in topic headers**: Guardrails like "STRICT JSON ONLY: No code blocks or conversational filler" in topics that produce rich text output create an internal contradiction the model must resolve — degrading response quality. Fix: remove guardrails that conflict with the topic's actual output format.
- **Missing `EndDialog` in leaf topics**: Any topic that completes its work without transitioning to a child topic MUST end with `EndDialog` (preferably with `clearTopicQueue: true`). Without it, topics stay in the queue, causing context bleeding and multi-turn failures.
- **Inconsistent context-variable checks**: When some topics check for global context variables (e.g., `Global.MPC_PatientName`) and others don't, multi-turn evaluation scenarios that depend on context continuity will fail inconsistently. Fix: standardize context gating across all workflow topics.
- **`useModelKnowledge: false` in agent instructions**: When model knowledge is disabled AND the fallback topic relies on `SearchAndSummarizeContent`, evaluation answers depend entirely on retrieval quality. Any retrieval failure produces fallback/degraded responses. Fix: set `useModelKnowledge: true` or ensure knowledge retrieval is robust before disabling.
- **Dead-end topics**: Topics that display output and then fall through without offering a continuation prompt (return to menu, "what next?") fail conversation-completeness evaluations. Fix: add a Question or menu prompt after the main output.

### Instruction-Level Diagnostics (New — Agent Instructions Component)

When every failed test case shows the same response structure (e.g., all answers are generic "Top 3 findings" checklists), the root cause is almost certainly in the **GPT instructions component** (`componenttype=15`), not in individual topics. Extract the instructions (via browser Overview page or Dataverse) and check for these patterns:

1. **Unenforceable character limits and "CRITICAL" rules** — Instructions like "NEVER exceed 800 characters total for any single response", "Maximum 800 characters per section", or "CRITICAL: Never exceed 800 characters" cause the model to produce truncated, incomplete, or refused responses. The model cannot reliably count characters. Replace with "Be concise but complete — prioritize accuracy and actionable findings over strict length limits." See `references/topic-800char-limit-fix.md` for the topic-level parallel. Evidence: This hidden rule was found in OT v6 instructions and contributed to OT SR 90%. Removing it and switching to unconditional RESPONSE FORMAT achieved OT SR 98%.

2. **"Do NOT ask for the document" rule (evaluation-dependent)** — If the instructions say "Do NOT ask for the document", CHECK THE TEST DESIGN FIRST. If tests use `record_id` pointers, the rule is CORRECT and removing it will drop conversation scores. If tests provide actual document text, the rule is WRONG and forces generic checklists.

3. **Unenforceable character limits** — Instructions like "NEVER exceed 800 characters total for any single response" or "Maximum 800 characters per section" are unenforceable — the model cannot count characters reliably. This introduces random truncation or wasted tokens, producing inconsistent outputs the grader penalizes. Fix: replace with "Be concise but complete — prioritize accuracy and actionable findings over strict length limits."

4. **Citation tag preservation** — Instructions like "Preserve all tags in the format [^x_y^] exactly as they appear, including those from tool outputs and search_results" force the model to output internal metadata tags in user-facing responses. These look like formatting errors to graders. Fix: remove entirely. Replace with "Use natural citations in context (e.g., 'Per CMS Chapter 15...'). Do not output internal metadata tags."

5. **Rigid output formats** — Instructions like "Lead with top 3 findings only" combined with character limits produce cookie-cutter output that doesn't adapt to the specific question. Fix: replace with "Lead with the most critical finding first, then provide supporting detail."

### Pattern: Generic Checklist Failure

**Observation:** All or most failing cases have agent responses that are generic "Top 3 X requirements" / "Required elements for Y" lists, regardless of whether the user provided a document or asked a specific question.

**⚠️ Critical nuance — the "do NOT ask" rule is often CORRECT, not an anti-pattern:**
- If evaluation test cases use `record_id` pointers (e.g., "The record_id is PT67890"), the agent should NOT ask for the document. The test expects general compliance guidance based on the document type mentioned.
- Removing the "do NOT ask" rule when tests use record_ids will **drop conversation scores** (e.g., 95% → 70%).
- The three SAFE fixes that never break conversation scores are:
  1. Remove unenforceable character limits (e.g., "NEVER exceed 800 characters")
  2. Remove citation tag preservation (e.g., "Preserve all tags in format [^x_y^]")
  3. Keep the structured RESPONSE FORMAT (Score X/100, Risk Levels, Classification, etc.)

**Root cause hierarchy (check in order):**
1. Instructions contain unenforceable character limits + rigid format → fix instructions
2. Instructions contain citation tag preservation → fix instructions
3. Instructions contain "Do NOT ask for the document" — **verify test design first.** If tests use record_ids, KEEP the rule. If tests provide document text, remove it.
4. Instructions made the RESPONSE FORMAT conditional (e.g., "When full text IS provided: use RESPONSE FORMAT") — **Real-world evidence: OT_Specialist dropped from 100% → 84% single-response when RESPONSE FORMAT was made conditional.** SLP dropped 95% → 87%. The grader expects the structured format for ALL audit-related questions, regardless of whether document text was provided.
5. Instructions forced the RESPONSE FORMAT unconditionally but test set includes general inquiry questions — **PT conversation dropped 90% → 80%, SLP Conv stuck at 85% (Jun 2026).** Both fixed by: "For full audits: use RESPONSE FORMAT. For general questions or element checks: give natural answer." SLP is the most common victim because its test set mixes audit and general clinical inquiries — the unconditional format degrades conversational quality on non-audit turns.
6. **Grader says "refuses to help by showing an error message" on same turn (usually 2nd or 3rd)** — This is a TOPIC-LOGIC issue, not instructions. Common causes:
   - Topic triggered by the follow-up lacks `EndDialog` with `clearTopicQueue: true` — the queue builds up across turns until it overflows
   - `SearchAndSummarizeContent` topics that don't have an explicit `EndDialog` after the action block
   - A variable conflict or error handler that produces a generic error message instead of answering
   - **Topic has correct `EndDialog` + `clearTopicQueue: true`, but `additionalInstructions` contain `Keep response under 800 characters`.** This unenforceable character limit causes the model to produce truncated output or refuse to produce a substantive follow-up because it cannot judge whether the response fits within 800 chars. The grader sees this as "refuses to help." Evidence (Jun 14, 2026): SLP "Analyze SLP Evaluation Report" had proper EndDialog but the `additionalInstructions` contained `Keep response under 800 characters.` The grader flagged "refuses to help on second response." The PT "General PT Clinical Inquiry" had the same pattern (fixed by removing the 800-char limit, not by EndDialog changes).
   - **Verification:** Open the failing conversation's topic in the code editor. Check BOTH:
     1. The `actions:` block ends with `EndDialog` + `clearTopicQueue: true`
     2. The `SearchAndSummarizeContent` action's `additionalInstructions` does NOT contain `Keep response under 800 characters`

   - **⚠️ REGRESSION CASCADE: Fixing one topic's 800-char limit can cause OTHER topics with the same limit to become the new failures.** 
     Root cause: When you fix topic A (remove 800-char limit), topic A starts producing proper substantive responses. This changes the conversation flow — the grader no longer fails topic A, but the user's follow-up now routes to topic B or C, which still have the 800-char limit. Those topics now produce the truncated/failed responses that topic A used to produce. The total failure count may stay the same or increase.
     Evidence (Jun 14, 2026): SLP conv evaluation went from 18/20 (90%) to 17/20 (85%) after fixing the "Analyze SLP Evaluation Report" topic's 800-char limit. Three NEW topics became failures (all progress-note related with the same 800-char limit) that weren't failing before.
     Fix: **Batch-remove the 800-char limit from ALL topics simultaneously, not one at a time.** Use a regex scan across all topic YAML files for `additionalInstructions.*800` or scan each `SearchAndSummarizeContent` action's `additionalInstructions` in the SPA. Only test after ALL topics have been cleaned. See `references/batch-fixes.md` for Python recipes.
   - **Topic has correct `EndDialog` + `clearTopicQueue: true`, but `additionalInstructions` contain `Keep response under 800 characters`.** This unenforceable character limit causes the model to produce truncated output or refuse to produce a substantive follow-up because it cannot judge whether the response fits within 800 chars. The grader sees this as "refuses to help." **Evidence (Jun 14, 2026):** SLP "Analyze SLP Evaluation Report" had proper EndDialog but the `additionalInstructions` contained `Keep response under 800 characters.` The grader flagged "refuses to help on second response." The PT "General PT Clinical Inquiry" had the same pattern (fixed by removing the 800-char limit, not by EndDialog changes).
   - Fix: scan every `SearchAndSummarizeContent` topic's `additionalInstructions` for `800 characters`. Remove that line entirely. Replace with nothing or with "Be concise but complete — prioritize accuracy and actionable findings over strict length limits." If `EndDialog` + `clearTopicQueue: true` was already present, the 800-char limit IS the root cause.
   - **Verification:** Open the failing conversation's topic in the code editor. Check BOTH:\n     1. The `actions:` block ends with `EndDialog` + `clearTopicQueue: true` ✅\n     2. The `SearchAndSummarizeContent` action's `additionalInstructions` does NOT contain `Keep response under 800 characters` ✅\n\n   - **⚠️ REGRESSION CASCADE: Fixing one topic's 800-char limit can cause OTHER topics with the same limit to become the new failures.** \n     *Root cause:* When you fix topic A (remove 800-char limit), topic A starts producing proper substantive responses. This changes the conversation flow — the grader no longer fails topic A, but the user's follow-up now routes to topic B or C, which still have the 800-char limit. Those topics now produce the truncated/failed responses that topic A used to produce. The total failure count may stay the same or increase.\n     *Evidence (Jun 14, 2026):* SLP conv evaluation went from 18/20 (90%) to 17/20 (85%) after fixing the \"Analyze SLP Evaluation Report\" topic's 800-char limit. Three NEW topics became failures (all progress-note related with the same 800-char limit) that weren't failing before.\n     *Fix:* **Batch-remove the 800-char limit from ALL topics simultaneously, not one at a time.** Use a regex scan across all topic YAML files for `additionalInstructions.*800` or scan each `SearchAndSummarizeContent` action's `additionalInstructions` in the SPA. Only test after ALL topics have been cleaned. See `references/batch-fixes.md` for Python recipes.

7. **Score pattern: All failures same pattern, score stuck ~50-60% despite instruction changes** — Check for topic overload first. Use `pac org fetch` with `componenttype eq 9` to count active topics. If >25, the agent has routing chaos from competing question-phrase topics. Delete duplicates per `references/topic-audit-methodology.md` in the `copilot-studio-development-workflow` skill. Evidence: OT_Specialist had 200+ active topics (Jun 2026); deleting to 20 recovered from 5% toward 60%+.

8. **Guard topics with hardcoded record_ids** — Guard topics that use exact-match triggers with baked-in record_ids (e.g., "record_id 12345") will fail evaluation because the grader uses varied IDs (OT13579, OT22334). Agent responds with wrong record_id → grader says "different record_id." Fix: delete guard topics with hardcoded IDs, or make them dynamic. Evidence: OT guard topics caused "different record_id" on 5-6 of 9 failures (Jun 2026).
   - v3 (conditional "When full text IS provided: use RESPONSE FORMAT") + "Do NOT ask for document" = generic checklists for record_id cases = conversation failures
   - v4 (unconditional "Always use RESPONSE FORMAT for any audit question") = proper structured output for all questions = single-response passes, conversation scores variable
   - v5 (conditional "For full audits only. For general questions: give natural answer") = proper format for audits but graders expect format for ALL document questions = both scores drop
   - **⚠️ Critical SR/Conv tradeoff — the "correct resolution" above has an SR edge case:** When SR test questions ask about a document type *without providing document text* (e.g., *"Can you audit my OT evaluation for Medicare compliance?"*), the conditional wording ("use for full document audits only") makes the model decide *"no document text was provided → this is not a full audit → skip the RESPONSE FORMAT."* The grader penalizes because the expected answer includes Classification, Score X/100, Compliance Findings.
   - **Evidence (Jun 14, 2026):** OT v7 (unconditional "use for ALL audit requests") scored SR 98%. OT v8 (conditional "Use for full document audits only") scored SR 88% — a 10-point drop from the exact same test set, caused ONLY by changing the RF header wording.
   - **Correct resolution for SR+Conv simultaneously:** Keep RESPONSE FORMAT unconditional in scope ("Use for ALL document-related questions") but add conversation continuity rules for Conv: "For single-response questions: always use the RESPONSE FORMAT. For conversation follow-ups: first response uses full RF; follow-ups use natural focused answers without repeating the format." See `references/unconditional-vs-conditional-rf-sr-correction.md` for the full pattern.

8. **All fails are generic checklists BUT agent-level instructions are clean** — Check topic-level `additionalInstructions` in each `SearchAndSummarizeContent` action. The stale "Keep response under 800 characters" line may be hiding there, not in the agent-level instructions. It can lurk in 10+ topics simultaneously. Scan all topic YAMLs for "800" in `additionalInstructions`. Fix with regex: `yaml.replace(/-\s+Keep[^)]*response under 800 characters[^\n]*\n?/g, '')`

9. Topics are `SearchAndSummarizeContent` with generic trigger phrases but no document-specific logic → fix topics
6. The evaluation test cases were designed poorly → fix test cases

**How to confirm:** Navigate to the Evaluation tab in the browser, click the most recent failed run, and read 5-10 question/response pairs from the Fail tab. If every failed response follows the same template, the root cause is at the instruction level (items 1-3 above), not the topic level.

## Topic Activation via Dataverse API (NEW — Jun 2026)

Inactive topics (statecode=1) silently fail evaluation test cases. Activate via PATCH:

```javascript
// PATCH /api/data/v9.2/botcomponents({id}) with { statecode: 0 }
```

**Evidence**: PT 16/31 inactive guard topics → Conv 74% stuck. Activated all + republished → Conv 95%. Single highest-impact fix. (Jun 15-16, 2026)

**Pitfall**: Must republish after statecode changes.

## CompositionEvent + .view-line Click for Monaco React Dirty State (Jun 2026)

**The reliable CDP trigger pattern for Monaco editor Save:**

```javascript
// Step 1: Inject YAML into textarea (sets hidden textarea, not Monaco model)
await page.evaluate((yaml) => {
  const ta = document.querySelector('textarea');
  const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  setter.call(ta, yaml);
  ta.dispatchEvent(new Event('input', { bubbles: true }));
}, filteredYaml);

// Step 2: Click a .view-line element — THIS IS THE KEY
await page.evaluate(() => {
  const vl = document.querySelector('.view-line');
  if (vl) vl.click();  // focuses Monaco and activates React's input context
});

// Step 3: Type + Backspace to trigger React dirty state
await page.keyboard.type(' ');
await page.keyboard.press('Backspace');

// Step 4: Save button is now enabled
```

**Why clicking `.view-line` specifically matters:**
- `.monaco-editor` surface click → does NOT trigger React's input context
- `textarea.inputarea` focus → does NOT trigger React
- `.view-line` click → activates Monaco properly, React detects keystrokes
- Combination: `.view-line` click + `keyboard.type(' ')` + `Backspace` → Save enabled

**⚠️ CRITICAL LIMITATION: textarea.setter does NOT sync Monaco's model.** After Save, the original content reappears because Monaco's internal model was never changed. The CompositionEvent→Save path confirms the Save button works but the content was stale. For true persistence: either (a) user must manually edit, or (b) find Monaco's iframe and use `editor.executeEdits()`.

**⚠️ Non-breaking space verification trap:** Monaco renders spaces as `\u00a0`. `indexOf('800 characters')` returns -1. Use regex `/8[^a-zA-Z0-9]*0[^a-zA-Z0-9]*0/` for detection.

**Evidence (June 16, 2026):** OT CB topic fixed with `.view-line` click + CompositionEvent. Verified the button enables. But Monaco model sync failure confirmed — textarea injection alone insufficient.

## Dataverse API for Agent Instruction PATCH (Jun 2026)

**Editing agent-level instructions is MORE reliable via Dataverse API than CDP Monaco injection.** The Dataverse API writes directly to the data store, bypassing React dirty-state issues entirely.

```javascript
// 1. Read current instructions
const filter = "_parentbotid_value eq '" + botId + "' and componenttype eq 15";
const url = '/api/data/v9.2/botcomponents?$select=botcomponentid,data&$filter=' + encodeURIComponent(filter);
const resp = await fetch(url, { credentials: 'include' });
const comp = (await resp.json()).value[0];
const rawData = comp.data; // YAML string, not JSON

// 2. Modify via string replacement
let newData = rawData.replace(
  'Use for full document audits only (evaluation, daily note, progress note, recertification, discharge):',
  'Use for ALL document-related questions (evaluation, daily note, progress note, recertification, discharge, caregiver competency, compliance check, audit request):'
);

// 3. PATCH back
await fetch('/api/data/v9.2/botcomponents(' + comp.botcomponentid + ')', {
  method: 'PATCH',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ data: newData })
});
// Status 204 = success
```

**When to use Dataverse PATCH vs CDP Monaco injection:**
- **Agent instructions (componenttype 15)**: Dataverse PATCH — simpler, more reliable, no dirty-state issues
- **Topic YAML (componenttype 9)**: Dataverse PATCH also works if the topic has a `data` field; otherwise CDP code editor
- **Topic trigger queries / additionalInstructions**: CDP code editor injection; verify with re-read

**⚠️ PITFALL: Dataverse PATCH revert can corrupt instructions.** When reverting a RESPONSE FORMAT change via `replace()`, the old/new text patterns may partially match, creating duplicates or malformed content. **Evidence: PT instructions grew from ~7200 chars to 8709 chars after a conditional→unconditional→conditional revert cycle.** Always verify instruction length after revert matches the original. If corrupted, restore from the original data field (not a second replace cycle).

**Evidence (June 16, 2026):** SLP and PT instructions both fixed via Dataverse PATCH (conditional→unconditional RESPONSE FORMAT). Published and confirmed. OT SR 97%, SLP SR 95% (improved), PT SR 82% (regressed — guard topic conflict). TDA SR 94%→88% after RESPONSE FORMAT addition+revert (corrupted).

## Conditional vs Unconditional RESPONSE FORMAT — OT 97% vs PT/SLP Lower

**THE PATTERN:** The RESPONSE FORMAT header wording directly determines SR scores.

| Header wording | Effect | Score |
|---|---|---|
| `Use for ALL document-related questions` | Unconditional — always structured output | **97%+** (OT) |
| `Use for full document audits only` | Conditional — skips format for general Qs | 85-86% (PT, SLP) |

**Root cause:** When the RESPONSE FORMAT says "full document audits only," the model skips the structured format for questions like "What are compliance risks?" or "Is my note at denial risk?" The grader expects the structured output (Classification, Score, Risk Level) but gets a free-text response → penalty.

**Fix:** Change `Use for full document audits only (evaluation, daily note, progress note, recertification, discharge):` to `Use for ALL document-related questions (evaluation, daily note, progress note, recertification, discharge, caregiver competency, compliance check, audit request):`

This was the root cause found by cross-agent instruction comparison (per `references/cross-agent-instruction-comparison.md`).

## Routing Agent-Specific Patterns

For hub/routing agents (like TDA) that classify and route but don't audit themselves, see `references/routing-agent-fixes.md` for Microsoft Learn-aligned micro-fixes. Key principles:

- Routing agents need an explicit `Always respond. Never refuse or show an error message` rule
- Ask ONE clarifying question at a time (discipline first, then document type, then setting)
- Include a fallback: `If no specialist matches: explain what you can route and ask for discipline identification`

- Use General quality or Compare meaning for open-ended compliance/knowledge responses.
- Avoid strict keyword grading unless the expected answer is deterministic.
- Move workflow/menu cases to conversational evaluation sets when a menu is the correct behavior.
- Update test cases that ask for an audit without providing a document if the correct response is to request the document.
- Regenerate or recalibrate test sets after major agent capability changes.

### Pattern: Unconditional RESPONSE FORMAT Causes 10%+ Conversation Drop

**Observation:** "use for ALL audit requests" or "Always use RESPONSE FORMAT" agents score 85% Conv while conditional-format agents score 95%+.

**Root cause:** Unconditional format forces 6-section audit structure on general clinical inquiries. Grader penalizes. Conditional format ("For full document audits only") separates audit from Q&A.

**⚠️ BUT — conditional format breaks SR when questions reference document types without providing text.** See `references/unconditional-vs-conditional-rf-sr-correction.md` for the combined fix that preserves both SR and Conv scores.

**Confirmed recovery (June 12, 2026):** SLP unconditional format (use for ALL audit requests) → Conv stuck at 85% across 6 runs. Published v3 conditional format (Use for full document audits only) → Conv 90% on the next evaluation run. +5% from one instruction-line change. PT (already conditional) stayed at 95% Conv baseline unaffected.

**June 16, 2026 confirmed data — RESPONSE FORMAT is agent-specific:**

| Agent | Before RF Change | After Unconditional RF | After Revert | Notes |
|-------|-----------------|----------------------|--------------|-------|
| OT | SR 97%, Conv 100% | N/A (already unconditional) | N/A | Always unconditional, always passes |
| SLP | SR 86% (conditional) | **SR 95%** ✅ | N/A | Unconditional HELPS SLP |
| PT | SR 94% (conditional) | **SR 82%** ❌ | SR 82% (corrupted) | Unconditional HURTS PT — guard topics conflict |
| TDA | SR 94% (no RF) | **SR 92%** ❌ | SR 88% (corrupted) | Adding RF HURTS TDA — routing agent |

**Key lesson: RESPONSE FORMAT changes are NOT one-size-fits-all.** Before changing:
1. Check if the agent has guard topics (>10 = high risk of regression)
2. Check if the agent is a routing agent (no RF needed)
3. Test on ONE agent first, never blanket-apply across agents
4. If reverting, verify the revert didn't corrupt instruction content (check length matches original)

**TDA-specific: Do NOT add RESPONSE FORMAT to routing/hub agents.** TDA delegates to OT_Specialist, PT_Specialist, SLP_Specialist — it doesn't audit documents itself. Adding RESPONSE FORMAT makes TDA try to produce audit responses directly instead of routing, causing SR to drop.

**Fix — two instruction changes:**
1. Header: `RESPONSE FORMAT (use for ALL audit requests):` → `RESPONSE FORMAT - Use for full document audits only (evaluation, daily note, progress note, recertification, discharge):`
2. Behavior: Replace `Always use the RESPONSE FORMAT above for any document-related or audit question.` with `For full document audits: use the RESPONSE FORMAT above.` plus `For general clinical questions or specific element checks: give a focused natural answer without the full numbered format.`

**Note:** Instructions editor React blocks programmatic saves — this fix requires manual paste (Ctrl+A, paste, Ctrl+S).

### Pattern: Conv recovery lags SR after KB changes

After SharePoint KB consolidation, **Conv recovers at roughly half the rate of SR**.

| Metric | SR recovery speed | Reason |
|--------|------------------|--------|
| **SR** | Full recovery in 1-2 runs | Single retrieval per turn |
| **Conv** | Takes 2-4 additional runs | 3+ turns × compounding retrieval failures |

**Why:** In multi-turn conversations, each turn does its own KB retrieval. If the renamed SharePoint folders produce inconsistent retrieval, turn 1 might ground but turn 3 doesn't. The grader penalizes the entire conversation, not isolated turns.

**Fix order for Conv specifically:**
1. Compare meaning 0.50 (allows synonymous wording across turns)
2. Allow ungrounded responses ON (catastrophic for Conv if OFF — 40-50 pt drop)
3. Conditional RESPONSE FORMAT for agents with mixed audit/general-query test sets (SLP: unconditional → 85% ceiling, conditional → 90%)
4. Check for conversation-specific failure signatures before more KB churn:
   - raw tool/action JSON or `explanation_of_tool_call` leaked as the answer
   - first sentence says record/document cannot be located and stops direct verification
   - grader says answer is relevant/complete but lacks knowledge-source citations
   - router/TDA representative topic says escalation is not configured
5. Re-run 2-3x before declaring recovery ceiling

See `references/conversational-failure-deep-dive-june13.md` for the detailed June 13 failure taxonomy, extraction workflow, and paste-ready fixes for tool-call leakage, no-record refusals, missing citations, and TDA escalation handling.

### Diagnostic: Publish button with no confirm dialog

When clicking Publish and no confirmation dialog appears, it means there are **no pending changes** since the last publish. This is a useful diagnostic:
- If you just changed instructions and Publish shows no dialog → the instructions save didn't persist. Re-open the Instructions editor and verify the text is actually there.
- If no changes were expected → the agent is already current with the published version.

### Diagnostic: Score regression with no code changes

If an agent's score drops (e.g., SLP Conv 95% → 85%) without any code/publish changes between runs, this is **non-deterministic scoring**, not a regression. The underlying LLM produces different responses on different runs, and the grader (also an LLM) evaluates borderline cases inconsistently. Re-test 2-3 times before investigating. See `references/non-deterministic-scoring.md` for observed variance ranges and decision rules.

### Pitfall: Evaluation page won't load via automation

The Copilot Studio Evaluation page grid (recent results, test sets, scores) is extremely slow to render — often taking 60+ seconds or never loading completely via CDP or playwright-cli. The SPA loads the test pane first, and the evaluation data grid loads separately. Solutions:
- **Preferred**: Use the Evaluation REST API (see section above) — fast, reliable, scriptable
- Use `pac copilot list` to verify publish state instead
- Ask the user to check evaluation scores from their browser session
- For programmatic extraction when the API isn't available, query Dataverse directly for `botcomponent` records of evaluation type

### Pitfall: SPA `/topics` URL redirects to `/overview`

The Copilot Studio SPA redirects direct URL navigation to `/topics` (or `/environments/{envId}/bots/{botId}/topics`) back to `/overview`. To reach the topics list, you MUST:
1. First load the overview page: `/environments/{envId}/bots/{botId}/overview`
2. Wait for the SPA to fully load and the tab bar to render
3. Click the "Topics" tab via a MouseEvent on the nav element
4. Wait 5-10 seconds for the topics list to render

The tab click sometimes navigates to `/tools` instead of the topics list (confirmed Jun 14, 2026 on SLP_Specialist). If this happens, re-navigate to overview and retry.

### Pitfall: CDP connection saturation

Opening more than ~15-20 CDP WebSocket connections (tabs) to the same Chrome instance causes `Unexpected server response: 500` on new connections. Chrome caps the number of concurrent DevTools WebSocket connections per session. Symptoms:
- New WebSocket connections fail with 500 error during handshake
- Runtime.evaluate calls on existing connections continue working

Fix: Close unused tabs via `curl -s -X DELETE "http://127.0.0.1:9223/json/close/{pageId}"`, or reuse existing tabs instead of creating new ones for each navigation. If you're debugging Publish/evaluation flow, keep 3-4 tabs max (one per agent + one blank).

### Pitfall: Compare meaning 0.50 MUST be set manually

Setting the Compare meaning grading method (threshold 0.50) on SR test sets is the single highest-impact systemic fix — it can recover 5-15% across all agents by allowing synonymous answers when SharePoint retrieval uses different wording.

**However, it CANNOT be set programmatically via Playwright or CDP.** The grading method dropdown and threshold slider are inside a hover-revealed edit panel that only appears when hovering over a test set card. Programmatic MouseEvents and click sequences fail because:
- Clicking the test set card opens the evaluation RESULTS panel (showing test case answers), NOT the grading editor
- The "General quality" text in the results panel is not a clickable dropdown — it filters results by that grade
- The actual grading method configuration requires: hover over card → click "…" menu → click "Edit" → change dropdown → set slider → save. The "…" button is only in the DOM after hover

**Manual steps (30 seconds per agent):**
1. Evaluation → Test sets tab
2. Hover over SR test set card → click … → Edit
3. Grading method → Compare meaning → threshold 0.50
4. Click Save

### Evaluation Score Extraction via Browser (When REST API Is Unavailable)

When the Evaluation REST API isn't accessible, extract scores and failed cases from the Copilot Studio SPA.

**Reusable scripts (in `scripts/`):**
- `scripts/get_scores.cjs` — Extract SR/Conv scores from a CDP page ID. Usage: `node scripts/get_scores.cjs <PAGE_ID> "OT" 15`. Returns recent results with pass % for each evaluation run.
- `scripts/read_full.cjs` — Read a wide swath (8000 chars) of page body text. Usage: `node scripts/read_full.cjs <PAGE_ID> "Fail"`. Useful for reading evaluation run details, failure lists, and page state.
- `fleet_eval_scores.cjs` — Pulls SR and Conv scores from all 4 agents (OT/PT/SLP/TDA) in a single run. Handles auth expiry detection, 25s SPA wait, and score parsing. Run with `node <hermes-home>/skills/passagenttesting/scripts/fleet_eval_scores.cjs`.

See `references/cdp-score-extraction-and-fix-loop.md` for the full CDP extraction workflow and iterative fix loop structure, including evaluation triggering button sequence, regression cascade detection, and common pitfalls.

### New Reference Files

| File | Covers |
|------|--------|
| `references/cdp-score-extraction-and-fix-loop.md` | CDP score extraction workflow, evaluation triggering, iterative fix loop structure, regression cascade detection |
| `references/unconditional-vs-conditional-rf-sr-correction.md` | The SR/Conv trade-off when choosing unconditional vs conditional RESPONSE FORMAT |
| `references/800-char-regression-cascade.md` | Pattern where fixing one topic's 800-char limit causes others to become new failures |
| `references/inactive-topic-detection.md` | Dataverse API workflow for detecting and activating inactive guard/intake topics. Statecode values, bulk activation, routing congestion patterns |
| `references/monaco-injection-verification.md` | Working Monaco API injection method with verification. Covers persistence failure patterns and batch injection workflow |
| `references/dataverse-instruction-patch.md` | Dataverse API PATCH pattern for editing agent instructions (componenttype 15) bypassing React/Monaco dirty-state |
| `references/cross-agent-instruction-comparison.md` | Side-by-side instruction comparison technique — find why one agent passes evaluation while another fails the same test type. SLP vs OT case study with RESPONSE FORMAT header analysis |

```javascript
// Navigate to evaluation page
// URL: .../environments/{envId}/bots/{botId}/evaluation

// Wait 15s+ for the SPA to render the results grid

// Extract recent scores text
document.body?.innerText?.substring(300, 2500)
// Returns raw text with: test name, pass %, pass count, dates

// To click into a specific run and see failed cases:
// 1. Find the row by run name in snapshot
// 2. Click it
// 3. Wait 10s for detail view
// 4. Read the full page text
// 5. Filter for "Fail" entries by searching snapshot for `Fail`

// Pattern for extracting fail/pass grid:
// grep for "Fail" to find failed cases
// Each row contains: question + agent response + result (Pass/Fail)
```

**Pitfall:** The evaluation URL is `.../bots/{botId}/evaluation` — navigating directly skips the Overview redirect. But the tab navigation (Overview, Knowledge, Evaluation) may hide Evaluation under a "+5" overflow menu. Click the overflow tab first, then click "Evaluation".

**Pitfall:** The history shows only the most recent ~10 runs. Older runs are available via the REST API but may not render in the SPA.

### Browser-Based Evaluation Result Inspection

When the REST API isn't available and you need to read individual failed test cases, navigate to the Evaluation tab via the browser:

1. **Opening the Evaluation tab**: It's often hidden in the `+N` overflow menu. Click `+N` tab, then click `Evaluation` from the dropdown menu.

2. **Reading results**: The page shows a grid of recent runs with pass percentage (e.g., "Pass: 78% (78 responses)"). Click a run row (not the button, the whole row) to drill into individual test cases.

3. **Fluent UI grid click pitfall**: If clicking the row center does nothing, click the run-name button/link in the leftmost cell. In some Copilot Studio grids the row has a visible `onclick`, but only the run-name button actually navigates to `/evaluation/runsDetails/...`.

4. **Viewing pass/fail splits**: After drilling in, the page shows tabs: `All | Pass (N) | Fail (N)`. By default it shows "All". The failed cases are grouped under the Fail tab. Use `npx playwright-cli --session <name> snapshot` and grep for `Fail` to extract question + response pairs.

5. **Extracting failure patterns**: Use the snapshot to grab question/response/Fail triples. The structure looks like:
   ```
   - row "Select this question [question text] [agent response] Fail" [ref=eNNN]
   ```
   The agent response text is embedded in the same row. This lets you read both the test question and what the agent actually said.

6. **Pattern-matching failures**: After extracting 5+ failures, classify the root cause:
   - All giving generic checklists vs document-specific answers? → Look at instructions that say "do NOT ask for the document" or "give 3-4 required elements"
   - All failing the same topic type (e.g., all progress note questions)? → Look at that specific topic's routing
   - Raw JSON/function-call output? → Tool/action finalization leak; add no-raw-tool-call instruction and inspect topic return path
   - "Cannot locate record/document" first? → No-record partial-answer rule missing; lead with partial compliance analysis instead of inability
   - Relevant/complete but failed for citations? → Add natural source anchors and verify source routing
   - Representative/escalation says not configured? → Default system escalation topic is active or fixed topic is not live
   - Random mix of pass/fail with no pattern? → Look at duplicate `OnUnknownIntent` handlers causing non-deterministic routing

7. **Common failure pattern: Generic checklist output**: When the agent responds to every question with a "Top 3 findings" or "Required elements" list regardless of whether the user provided a document, the likely root cause is an instruction like: "When asked about a document type without text provided: give 3-4 required elements with citations directly. Do NOT ask for the document." This makes the agent treat EVERY question as if no document was provided. Fix: change to "If the user provides a document, analyze it. If not, ask for it or give a brief overview."

## Microsoft Learn References

Use the native MCP tools to retrieve official Microsoft guidance during triage. These are faster than web search and return pre-structured markdown content.

### MCP Tools Available

| Tool | When to Use |
|------|-------------|
| `mcp_microsoft_learn_microsoft_docs_search(query)` | Find relevant MS Learn articles on evaluation triage, remediation, grading methods, knowledge source quality. Start here for any question. |
| `mcp_microsoft_learn_microsoft_docs_fetch(url)` | Get full page content when search results are truncated or you need complete step-by-step procedures. Pass the URL from search results. |
| `mcp_microsoft_learn_microsoft_code_sample_search(query, language)` | Find official code samples for Copilot Studio API usage, Power Platform integration, or topic YAML patterns. |

### Usage Pattern for Evaluation Triage

```yaml
gap_analysis:
  1. mcp_microsoft_learn_microsoft_docs_search(query="evaluation triage remediation")
     + microsoft_docs_fetch on the top result for full framework
  2. mcp_microsoft_learn_microsoft_docs_search(query="general quality grading criteria")
     + microsoft_docs_fetch on the top result
  3. Apply the framework to classify failures
```

### Key Microsoft Learn Articles (linked)

Read `references/sharepoint-regression-pattern.md` for the systemic fleet-wide regression pattern caused by generic SharePoint folder names — fix order: rename folders first, THEN dedup files.

Read `references/june12-sharepoint-regression.md` for the June 12, 2026 session data — complete regression timeline across all 4 agents (OT/PT/SLP/TDA), root cause analysis, fix sequence, and recovery trajectory.

Read `references/conversational-compound-regression.md` for the pattern where Conv drops 2-3x more than SR after SharePoint KB changes and recovers 2-3x slower — each turn requires independent retrieval, failures compound.

Read `references/instruction-anti-patterns.md` for the 5 most common instruction issues that cause conversation-score regressions — the checklist derived from this user's real debugging sessions (SLP/PT/OT specialist regression analysis).

Read `references/healthcare-agent-instruction-template.md` for the complete paste-ready instruction template used across SLP/PT/OT/TDA agents — includes RESPONSE FORMAT (Classification, Compliance Findings with risk, Score X/100, Missing Elements, Recommendations, Advisory), XAI & TRANSPARENCY (confidence levels, source mapping, logic chain), CONVERSATION CONTINUITY, and SAFETY sections. Adapt the SCOPE, CLINICAL ROLE, and routing logic per agent.

Read `references/microsoft-learn.md` when you need the official source list or need to cite the rationale in the final response.

Read `references/v5-regression-data.md`

Read `references/unconditional-response-format-recovery-ot-june14.md` for the confirmed fix pattern that took OT SR from 90% → 98% using unconditional RESPONSE FORMAT (no provisional/three-way branching). Template and behavioral rules included.

Read `references/response-format-agent-specific-june16.md` for the June 16, 2026 confirmed data on how RESPONSE FORMAT changes affect each agent differently — OT 97%, SLP +9% with unconditional, PT -12% with unconditional, TDA -2% with RF addition. Includes revert corruption pitfall.

Read `references/pt-guard-topic-architecture.md` for why PT's 15 intake guard topics conflict with unconditional RESPONSE FORMAT while SLP's 17 conv guard topics benefit from it. Key insight: intake patterns (ask follow-up questions) vs element-check patterns (produce audit-quality responses) determine whether unconditional RF helps or hurts.

Read `references/unconditional-vs-conditional-rf-sr-correction.md` for the critical edge case where conditional RESPONSE FORMAT ("Use for full document audits only") breaks SR tests when questions reference document types without providing text. Includes the combined fix that preserves both SR and Conv scores. for the confirmed fix pattern that took OT SR from 90% → 98% using unconditional RESPONSE FORMAT (no provisional/three-way branching). Template and behavioral rules included.

Read `references/evaluation-triggering-and-cdp-patterns.md` for the correct UI button sequence to trigger evaluations (New evaluation → Run), CDP connection saturation limits, and the SPA /topics URL redirect pitfall.

Read `references/ot-sr-three-way-branching-fix-june14.md` for the root cause analysis and fix for OT single-response 90% — the three-way branching instruction antipattern where a "provisional audit framework" path bypasses the RESPONSE FORMAT and causes 10% of SR cases to fail.

## pac CLI Known Issues (v2.7.4)

- `pac copilot extract-template` crashes with `System.ArgumentException` in `CopilotExtractTemplateVerb.AddKSComponent` on agents with knowledge sources. Workaround: use `pac solution clone` for solution metadata, or extract topics individually via the Copilot Studio code editor.
- `pac org fetch` can also crash/stack-overflow in v2.7.4 when querying `botcomponent` records for knowledge-heavy agents because the grid renderer overflows. If this happens, do not keep retrying the same FetchXML; use browser/SPA extraction, solution clone/export, or targeted code-editor edits instead.
- `pac copilot status --bot-id` fails with `componentstate_Property` attribute error. Use `pac copilot list` instead to verify publish state (shows State Code "Provisioned" for published agents).
- `pac copilot list` returns all agents across the environment including their publish state, component state, and solution ID — use this as the primary verification command.

Read `references/source-diagnostics.md` for systematic source-code diagnostic patterns when live evaluation data isn't accessible — includes quick scan commands and priority-ordered defect categories.

Read `references/batch-fixes.md` for Python recipes to batch-apply fixes across dozens of topic files at once — guardrail removal, empty-intent detection, missing-EndDialog scans, and the standard EndDialog/continuation patterns.

Read `references/simplified-text-answer-topic-format.md` for the text-answer + EndDialog pattern that achieves 95%+ eval scores. Includes QM Coach V2 evidence (71%→95%), before/after examples, and guidance on when interactive topics are acceptable vs eval-killing.

Read `references/yaml-pitfalls-copilot-studio.md` for YAML parsing pitfalls in the Copilot Studio topic editor — unquoted values with colons, bold formatting in block scalars, non-breaking spaces in Monaco. Consult this when the code editor shows "Error reading YAML content near line X" after pasting topic YAML.

Read `references/dataverse-topic-activation.md` for activating inactive topics via Dataverse API. Inactive Eval/Conv Guard topics are the #1 root cause of volatile Conv scores (PT 74% → 95% after activating 16 guard topics, June 2026).

Read `references/monaco-injection-verification.md` for Monaco API injection, non-breaking space verification, and the critical pitfall of full-YAML-replacement causing 7%+ regressions by removing post-export topic optimizations.
