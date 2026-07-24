---
name: copilot-debug
description: Full debug, evaluation repair, and deployment-prep workflow for Microsoft Copilot Studio agents. Use when a user invokes /copilotdebug or /copilot-debug, or asks to prepare an agent for deployment, improve evaluation scores, run debug loops with retrospective analysis, apply lessons learned, or gather agent context and specs from a production environment.
---

# Copilot Debug

Use this workflow for any Microsoft Copilot Studio agent. Treat the live Copilot Studio UI and live Dataverse records as source of truth unless the user says otherwise.

## Ground Truth

**PITFALL — Wrong agent**: Always verbally confirm the agent name, bot ID, and environment with the user before starting analysis. Do not assume a local repo or a previously opened agent matches the one the user is asking about. Copilot Studio tenants often have multiple agents with similar-sounding names (e.g., "TheraDoc Workbench" vs "Therapy Documentation Audit Agent"). If the user corrects you, stop immediately, find the right agent via the Copilot Studio agents list, and restart the analysis from scratch.

This skill plugs into the `copilot-studio-development-workflow` umbrella skill (step 6: debug loop). Use that skill for the full YAML-first development lifecycle.

## Phase 0: /full-agent-audit — Deep Context & Baseline

Before any debug loop, run a comprehensive agent audit as defined by the `therapy-fleet-agent-audit` skill:

1. **Purpose alignment** — Write a one-sentence core-function statement. Classify every topic as ALIGNED, PARTIALLY ALIGNED, MISALIGNED, or ORPHAN. Present to user for confirmation before deep-diving.
2. **Discovery** — Query environment, bot ID, schema name, publish status. Pull live bot components via Dataverse. Categorize: 9 topics/connections, 14 file knowledge, 15 GPT/metadata, 16 web/SharePoint knowledge, 19 trigger phrases.
3. **Audit all dimensions:**
   - Overview: name, description, role clarity
   - Instructions: size, corruption, contradictions, JSON/prose conflicts, citation issues, response-format guardrails
   - Knowledge: source quality, dedup, SharePoint folder naming, description uniqueness
   - Topics: YAML validity, EndDialog/clearTopicQueue, trigger phrases, routing integrity, orphan detection, Card-vs-Intake gaps, duplicate conditions, 800-char limits
   - Settings: moderation, auth, web/code interpreter
   - Evaluation: test set coverage, single-response + conversational scenarios
4. **Fix priority** — Security/compliance → environment/settings → YAML validity → routing/triggers → knowledge → instructions
5. **Baseline metrics** — Record current evaluation scores, topic count, instruction size, KB count, publish status before any changes.

## Phase 1: Debug Loop

After Phase 0 context is gathered, enter the iterative debug loop:

1. Get evaluation results programmatically via Power Platform Evaluation REST API
2. For every failed case, follow Microsoft Learn triage order:

**Layer 1.5 — KB quality FIRST.** Always audit knowledge sources before touching agent config. Most failures are KB gaps, not logic bugs.

1. If the agent response is acceptable, fix the evaluation case or grader.
2. If the expected answer is wrong or stale, fix the evaluation case.
3. If a concrete configuration defect exists, fix the agent.
4. If a fix does not persist or cannot be configured, document it as a platform limitation.
### Cross-Agent KB Comparison

When troubleshooting a specific agent, compare its knowledge sources against all other agents. See `references/lessons-learned.md` (Knowledge Sources section) for the dedup order and naming rules.

**⚠️ Tools page SPA issue**: The `/tools` URL sometimes loads the Topics page instead. Navigate via the overflow menu (+N) → Tools, or click the Tools tab from within the Topics page.

**⚠️ Platform-level failure diagnosis**: When ALL agents return "Error" simultaneously (including untouched ones), it's NOT agent config — it's the evaluation service. See `references/lessons-learned.md` (Debugging section) for full diagnostic steps.

**⚠️ Playwright CANNOT inject Copilot Studio instructions**: The Overview page's contentEditable editor resists all programmatic approaches. See `references/lessons-learned.md` (Automation section) for the only working method.

See `references/sharepoint-folder-naming.md` for folder naming patterns, `references/knowledge-source-descriptions.md` for individual file descriptions, `references/sharepoint-kb-regression.md` for the full regression case study, `references/power-bi-integration.md` for Power BI connector setup, and `references/qm-coach-v2-agent.md` for QM Coach V2 agent details.

**Browser lifecycle on Windows**: Terminal timeout kills Node process → kills Chrome. Use headless: false with 180-300s terminal timeout. Never call browser.close() unless user asks. Background mode doesn't keep processes alive on Windows Git Bash.

Then pattern-analyze at least five failures:

- `80%+ same root cause`: fix the category, not individual cases.
- `score flat after fix`: re-triage; the root cause was probably wrong.
- `one score improves while another regresses`: inspect instruction conflicts and topic routing.
- `single response fails but conversation passes`: check prompt-first topics, strict graders, and ambiguous expected answers.
- `conversation fails but single response passes`: check context retention, topic stacking, and reference conversation design.

## Phase 2: Retrospective & Lessons Learned

After each debug iteration, before moving to the next:

1. **What was fixed?** — Document the change and the specific score delta.
2. **What was the root cause?** — Categorize: KB gap, topic logic, instruction conflict, routing issue, platform limitation, evaluation case error.
3. **What was learned?** — One-sentence reusable lesson. Example: "Unconditional RESPONSE FORMAT in instructions causes 10%+ conversational score drops — use conditional formatting tied to audit triggers instead."
4. **Update the Lessons Learned registry** — Append to the skill's `references/lessons-learned.md` with format:
   ```
   ## [YYYY-MM-DD] Agent: <name> | Issue: <brief>
   Root cause: <category> — <specific>
   Fix: <what was changed>
   Delta: <before%> → <after%> on <metric>
   Lesson: <one-sentence reusable>
   ```
   This file is loaded when the `copilot-debug` skill is active — the agent sees accumulated lessons from all prior debug sessions, enabling cross-agent pattern detection in Phase 3.
5. **Check for regression** — Rerun all previously passing evaluation cases. If any regressed, revert or adjust.

## Phase 3: Lessons-Learned Reloop

After the retrospective, check the accumulated lessons-learned registry against the current agent state:

1. **Scan for recurring patterns** — Are the same root causes appearing across multiple agents? (e.g., missing EndDialog, 800-char limits, unconditional RESPONSE FORMAT)
2. **Apply systemic fixes** — If a pattern appears in 3+ agents, fix it fleet-wide rather than agent-by-agent.
3. **Re-evaluate** — After systemic fix, rerun evaluations. If scores plateau, drill into the remaining failure cases — they're likely from a different root cause layer.
4. **Loop exit criteria** — Both Single Response and Conversational scores >95%, no failed cases from the same root cause category, and no regressions. Until then, repeat Phase 1 → Phase 2 → Phase 3.

## System Analysis from Agent Instructions (No Evaluation Access)

When evaluation data is unavailable, check the agent against patterns that predict failures. These are documented in `references/lessons-learned.md` under the `## Debugging` section. Key triggers:

1. **Instruction self-contradictions:** e.g., "STRICT JSON ONLY" in a conversational text agent, or citation tag `[^x_y^]` preservation.
2. **Unenforceable constraints:** e.g., "never exceeding 800 characters per section".
3. **Upload-vs-paste routing gaps:** If primary audit topic triggers "ONLY when the user uploads", pasted text bypasses routing.
4. **Missing EndDialog:** Topics without EndDialog + clearTopicQueue cause context bleeding.
5. **Unconditional RESPONSE FORMAT:** Forces structured output on general inquiries, causing 10%+ Conv drops.

## Agent Fix Checklist

Apply the smallest live UI/API-supported change that resolves the proven root cause.

See `references/lessons-learned.md` for the full reference on validated fixes, known traps, and design rules. Key items checked on every fix pass:

- Every `SearchAndSummarizeContent` topic ends with `EndDialog` and `clearTopicQueue: true`.
- Never use `clearTopicQueue: false`.
- Use `applyModelKnowledgeSetting: true` or omit it; never set it to `false`.
- Remove `SearchSpecificFiles`, `fileSearchDataSource`, and `SearchSpecificKnowledgeSources` unless explicitly needed.
- Avoid broad `OnActivity type: Message` or generic trigger phrases that hijack all input.
- Convert prompt-first audit/help topics to answer-first search when the user's message already contains enough context.
- Topic YAML `kind` varies by environment — check existing topic before pasting.
- YAML indentation: 2-space, strict. Always provide full blocks for paste.
- **Editing instructions on the Overview page**: Uses a `div[contenteditable]` inside a `[role=textbox]`. Click Edit, Ctrl+A, paste, Ctrl+S. See `playwright-hermes` for automation.

## Publish, Test, And Sync

1. Publish the agent from Copilot Studio or `pac copilot publish`.
2. Wait for publish and retrieval propagation.
3. Verify `synchronizationstatus.lastFinishedPublishOperation.status == "Succeeded"`.
4. Rerun evaluations using the **Power Platform Evaluation REST API** (see `passagenttesting` skill for full API reference). List test sets, trigger a run, poll for completion, then get per-case results. This is faster and more reliable than waiting for the SPA evaluation grid.
5. If either score is below threshold, export failures and repeat the root-cause loop.
6. If thresholds are met, run a regression pass against previously passing cases.
7. Sync live back to local:
   - Pull live topics, knowledge metadata, GPT instructions, and active evaluation cases.
   - Remove stale local components only inside the target agent's managed local folders.
   - Write a manifest with environment, bot ID, component IDs, component types, modified timestamps, and output files.

## Microsoft References

- Evaluation triage overview: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-overview
- Triage agent failures: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-failure
- Pattern analysis: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-pattern
- Remediation strategies: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-remediation
- Edit test cases: https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-edit-cases
- Evaluation methods: https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-overview
- Evaluation REST API: https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-rest-api
- Automate evaluation with Evaluation APIs: https://techcommunity.microsoft.com/blog/copilot-studio-blog/automate-agent-evaluation-with-the-evaluation-apis/4511653
