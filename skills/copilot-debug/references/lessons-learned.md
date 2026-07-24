# Copilot Studio Lessons Learned

Appended after each retrospective (Phase 2 of /copilotdebug).
Auto-loaded when `copilot-debug` skill is active.

---

## Architecture

- **Hub-and-spoke:** Orchestrator hubs route to specialist agents via BeginDialog. Proven for SNF Command Center → PT/OT/SLP, TheraDoc, QM Coach.
- **Topics: 10-15 per agent. 10 is ideal.** Documentation hubs (TheraDoc) can exceed if routing stays clean.
- **≥10 trigger phrases per NLU-topic.** Short, varied, complete. Covers edge cases, prevents wrong-topic routing.
- **Delete redundant/overlapping topics.** Fewer well-defined > many overlapping.
- **Card-based doc pattern (TheraDoc):** AdaptiveCard → SearchAndSummarizeContent → SendActivity(DRAFT) → BeginDialog(AuditExistingNote) → EndDialog(clearTopicQueue:true). Replaced 28 free-text Question nodes.
- **Purpose alignment first:** Classify topics as ALIGNED/PARTIALLY/MISALIGNED/ORPHAN before deep-diving. Confirm with user.
- **Every leaf topic: EndDialog + clearTopicQueue:true.** Falling through = context bleeding = Conv failures.

## Routing

- **Child/parent pattern:** Router → BeginDialog to Topic_Child for multi-step flows.
- **Router triggers on NLU only, NOT OnActivity type:Message.** Broad OnActivity hijacks all input.
- **Pasted text routing:** Include "pasted content" alongside "uploaded file" in trigger descriptions. Otherwise pasted text bypasses audit workflow.
- **Routing integrity:** Trace every BeginDialog to a real topic. Flag duplicate routers. Flag Card topics with no SearchAndSummarizeContent or EndDialog — data sinks.

## Instructions (GPT)

- **Target ≤5,500 chars.** OT 3,700 → 100%. PT 5,200 → 90%. Over 8,000 = errors.
- **Always replace full instructions.** Never partial-paste in UI. Select All → Delete → Paste.
- **Highest-priority rules first.** Short direct sentences. Separate response style from workflow.
- **Put durable rules in agent instructions** (not scattered across topic prompts).
- **Conditional RESPONSE FORMAT (validated Jun 2026):** "For full audits: use FORMAT. For general questions: natural answer." Unconditional "ALWAYS use FORMAT" causes 10%+ Conv drops. PT 80%→95%.
- **Remove 800-char limits from topics (validated Jun 2026):** Truncates mid-sentence. Replace with "Be concise but complete. Prioritize accuracy over strict limits." Root cause of OT/PT/SLP Conv failures.
- **Citation rules:** Remove "preserve [^x_y^] tags" — internal tracking tags in output cause eval failures. Replace with "Cite sources by natural name." Do NOT suppress Microsoft's built-in citations (tracking tags ≠ auto-citations).
- **Prefer General quality** for open-ended evals. Use Compare only when expected answer is required.

## Knowledge Sources

- **KB quality is triage layer #1.** Audit KBs before touching config. Most failures are KB gaps, not logic bugs.
- **SharePoint folder = the description.** No editable description field exists. Use ~100 keyword-rich chars for GPT routing.
- **NEVER dedup before renaming SP folders (validated Jun 2026):** Consolidating files into generically-named folders breaks retrieval for ALL sharing agents. PT SR 95%→75%, SLP 96%→92%. Fix: rename FIRST, then dedup.
- **Naming pattern:** "Provides [source]. Use when [query intent]. Covers [key topics]."
- **Keep each source narrow and purpose-specific.**
- **Use file groups** for role/region/workflow-specific subsets.
- **Uploaded files appear under Files tab only**, not "All" view.

## Topic YAML

- **kind varies by env:** Production → `kind: AdaptiveDialog`. Dev (a944fdf0) → may require `kind: TaskDialog`. Check existing topic first.
- **2-space indentation.** Monaco rejects wrong levels. Full blocks for paste (complete `kind:` through `outputType: {}`).
- **DynamicClosedListEntity routing:** `Text(Topic.ChoiceVar) = "OptionValue"`. NOT `.Value =` and NOT direct string comparison.
- **Canvas-first** → YAML for inspect/refine, not raw creation.

## Evaluation

- **Run 3x for stable measurement.** ±10% variance per run.
- **Publish + wait 90s before eval.**
- **REST API (preferred over SPA):** `https://api.powerplatform.com/copilotstudio/environments/{envId}/bots/{botId}/api/makerevaluation?api-version=1`
- **Platform failure:** ALL agents 0%/Error simultaneously = NOT config. Run untouched agent to confirm. Check Microsoft outages.

## Publish & Deploy

**Primary:** `Open agent` → `Get changes` → `Preview changes` → `Apply changes` → publish
**Secondary:** `pac copilot publish` + `pac copilot list` to verify
**Fallback:** CDP batch-patch via Kiro Chrome for YAML-only fixes

- `.mcs` = extension cache, NOT source. Never copy between projects. Never check in (except `.gitkeep` + `conn.json`). If corrupted: keep `conn.json`, clear rest, reload, `Open agent` → `Get changes`.
- `Apply changes` is extension-owned, not headless-substitutable.
- **PAC v2.7.4 bugs:** `status --bot-id` fails. `extract-template` crashes on agents with KB. Publish can false-report parser errors — verify with `pac copilot list`.
- Verify: `synchronizationstatus.lastFinishedPublishOperation.status == "Succeeded"`.

## Debugging

**Pattern analysis (≥5 failures needed):**
- 80%+ same root cause → fix category, not cases
- Score flat after fix → wrong root cause, re-triage
- One up, another down → instruction conflicts or topic routing
- SR fails, Conv passes → prompt-first topics, strict graders, ambiguous expected answers
- Conv fails, SR passes → context retention, topic stacking, ref conversation design

**Without eval data, these predict failures:**
- Instruction self-contradictions (e.g., "STRICT JSON ONLY" in conversational agent)
- Unenforceable constraints (e.g., "never exceed 800 chars")
- Child agent cascading failure
- Disabled features (Topics Off, Web Search off, model knowledge off)
- Upload-vs-paste routing gaps
- Missing EndDialog = context bleeding
- Unconditional RESPONSE FORMAT

## Automation

- **Instructions editor resists ALL programmatic manipulation** — fill(), paste, execCommand all report success but don't persist. Only CDP `Input.insertText` works. When CDP unavailable, provide text file for manual paste.
- **CDP:** Launch Chrome with `--remote-debugging-port=N`. Set `CUA_DRIVER_CDP_PORT=N`.
- **Browser lifecycle:** Terminal timeout kills Node → kills Chrome. Use `headless:false` with 180-300s timeout. Never `browser.close()` unless asked.
- **Headless works for data collection** (no UI interaction).
- **Copilot Studio SPA:** 15-45s load. Use polling. Popups block everything — dismiss after EVERY goto.
- **US News:** Blocks headless Playwright and curl. Use playwright-cli `--headed` or user's Chrome.

## Dataverse (Therapy AI Dev)

- Env: `https://orgbd048f00.crm.dynamics.com` | Tenant: `03cc92c3-986c-4cf4-ae27-1478cf99d17f`
- Component types: 9=topics, 14=files, 15=GPT, 16=web/SP, 19=triggers
- Query: `_parentbotid_value eq '<botId>'`
- Auth: `az account get-access-token --resource <org_url>/ --tenant <tenant_id>`
- `content` PATCH blocked for complex YAML → use `data` PATCH instead
- **NEVER touch Ensign Default / `org3353a370.crm.dynamics.com`** while in Therapy mode.

## Agent Registry (Therapy AI Dev)

| Agent | Bot ID | Role |
|-------|--------|------|
| SNF Command Center V2 | `9f3e370c-a747-f111-bec6-0022480b6bd9` | Orchestrator |
| SNF AI Dashboard V2 | `bd570423-cf47-f111-bec5-70a8a5b1c3a3` | Dashboard |
| TheraDoc Workbench | `e09954e1-4af8-47c6-8ef4-d1d9335bf2e6` | Documentation |
| Pacific Coast Case Historian | `ad635500-cf47-f111-bec5-70a8a5b1c3a3` | Case History |
| Pacific Coast QM Coach V2 | `ea52ad9c-8233-f111-88b3-6045bd09a824` | QM |
| Pacific Coast Denial Defense V2 | `6d7815b4-ce47-f111-bec5-70a8a5b1c3a3` | Denial Mgmt |
| Therapy Report Prep V2 | `fd1bce12-cf47-f111-bec5-70a8a5b1c3a3` | Reports |
| Pacific Coast Compliance Analyzer | `19779839-7b6e-4362-925b-8ddf03979f7d` | Compliance |
| Pacific-Coast Regulatory Hub V2 | `ea901efc-d043-4023-88a6-8ac4c561a4d5` | Regulatory |
| PacCoast Medicare Meeting | `ee72fe1a-0882-4dec-9959-ace1fbb74280` | Meetings |
| Pacific-Coast Clinical Synthesis Lab V2 | `89c7415d-df73-490c-9d78-4829cfbc2f84` | Clinical |
| POSTette_Compliance_Agent | `03b08692-aa24-4159-986b-cfad8fed6865` | Compliance |

---

## Validated Lessons (add newest first)

### 2026-07-01 | Therapy Documentation Feedback Agent (PROD) | Round 1: 16% → 83%. Round 2: Removed remaining SearchSpecificKnowledgeSources
- **Root cause (Round 2):** Despite removing SearchSpecificFiles in Round 1, 4/6 audit topics (Discharge Summary, Progress Report, Eval Plan of Care Copy, Episode of Care) still had `knowledgeSources: SearchSpecificKnowledgeSources` restricting KBs to 8 specific sources. The Dataverse `data` PATCH worked but local YAML was stale.
- **Fix (Round 2):** PATCHed `botcomponent.data` via Dataverse Web API with az token to remove the `knowledgeSources` block from 4 topics. Published via `pac copilot publish` — succeeded. Synced live YAML → local files (11 topics updated).
- **Delta:** Round 1: 16% → 83% on 25-case. Round 2: KnowledgeSources fix published and verified live.
- **Lessons:** (1) SearchSpecificFiles removal is NOT enough — must also remove `knowledgeSources: SearchSpecificKnowledgeSources` block. (2) Dataverse PATCH on `botcomponent.data` works for `content` when the YAML is valid (the `data→content` sync issue applies to broken YAML only). (3) PPAPI token ≠ Dataverse token — use `az account get-access-token --resource "https://{org}.crm.dynamics.com"` for Dataverse API. (4) Local YAML gets stale — always pull live after live edits. (5) CDP capture on port 9223 works for PPAPI tokens; Copilot Studio SPA needs 15-20s load time per page.

### 2026-07-01 | Therapy Documentation Feedback Agent (PROD) | SearchSpecificFiles on 6 audit topics
- **Root cause:** All 6 audit topics used SearchSpecificFiles + SearchSpecificKnowledgeSources, restricting KB retrieval to 5 files + 8 knowledge sources instead of searching all. Episode of Care had unconditional 800-char limit.
- **Fix:** Removed fileSearchDataSource and knowledgeSources blocks from Discharge Summary, Progress Report, Eval Plan of Care (Copy), Episode of Care, Recertification/UPOT, and Treatment Encounter Note Review. Removed 800-char limit from Episode of Care. Made GPT instructions RESPONSE FORMAT conditional (structured for audits, natural for general Qs).
- **Delta:** N/A — baseline evals not yet run.
- **Lesson:** All audit topics should use `applyModelKnowledgeSetting: true` (or omit) instead of SearchSpecificFiles. Unconditional RESPONSE FORMAT causes systematic Conv drops (per PT/OT/SLP validation). Monaco editors render YAML as single-line with \\u00a0 instead of \\n — CDP scripts must use the hidden textarea for proper YAML reads.

### 2026-07-01 | Therapy Documentation Feedback Agent | US News blocked tooling
- **Root cause:** health.usnews.com blocks headless Playwright and curl.
- **Fix:** playwright-cli --headed or user's Chrome. Batched at 4 AM via scheduled Node.js script.
- **Lesson:** US News blocks headless. Use headed mode.

### 2026-06-30 | TheraDoc Workbench | 56 topics, 35 out of scope
- **Root cause:** Purpose misalignment — treated as general workbench, not focused documentation assistant.
- **Fix:** 27 kept + 17 Card topics. Free-text Intake → click-button Card capture.
- **Lesson:** Purpose alignment step BEFORE topic analysis. ALIGNED/PARTIALLY/MISALIGNED/ORPHAN. Confirm with user.

### 2026-06-30 | PT/OT/SLP | 800-char limits killed Conv
- **Root cause:** "Keep under 800 chars" in topic additionalInstructions truncated audit responses.
- **Fix:** "Be concise but complete. Prioritize accuracy over strict limits."
- **Delta:** OT Conv 85%→90%. Root cause of all Conv failures.
- **Lesson:** Remove 800-char limits from ALL topic additionalInstructions.

### 2026-06-30 | PT/OT/SLP | Unconditional RESPONSE FORMAT
- **Root cause:** "ALWAYS use FORMAT for ALL audits" forced structured output on general questions.
- **Fix:** Conditional — structured for full audits, natural for general questions.
- **Delta:** PT Conv 80%→95%.
- **Lesson:** Unconditional FORMAT kills Conv 10%+. Use conditional routing.

### 2026-06-20 | Fleet | SharePoint KB dedup regression
- **Root cause:** Consolidated KB files into folders without renaming folders first.
- **Fix:** Rename folders to keyword-rich ~100-char names, THEN dedup.
- **Delta:** PT SR 95%→75%, SLP 96%→92%. Recovered after rename.
- **Lesson:** Never dedup KB before renaming folders. Folder name = GPT routing signal.

### 2026-06-11 | Fleet | Platform eval failure
- **Root cause:** Microsoft deployment broke eval auth — ALL agents 0%.
- **Fix:** Waited for Microsoft remediation.
- **Lesson:** When ALL fail together, check platform first. Not config.

### 2026-06-10 | General | Instructions paste wall
- **Root cause:** React contentEditable rejects all programmatic DOM manipulation.
- **Fix:** CDP `Input.insertText` only proven path. Otherwise, text file for manual paste.
- **Lesson:** Playwright cannot inject instructions. CDP or manual only.
