# Conversation evaluation remediation notes

Use this when Copilot Studio Conversation test sets regress or plateau after KB/source work.

## FIRST CHECK: "Allow ungrounded responses" setting

**Before any instruction or topic changes**, verify the **"Allow ungrounded responses"** setting is ON. This is the #1 cause of conversation eval failures and the easiest to miss.

**Location**: Agent > Settings > Generative AI > Knowledge > "Allow ungrounded responses"

**MS Learn source**: https://learn.microsoft.com/microsoft-copilot-studio/knowledge-copilot-studio#allow-ungrounded-responses

> "When you turn off this setting, the agent blocks any response generated in a turn where it didn't use a knowledge source or tool. The response is blocked and the fallback topic triggers."

> "If the Allow ungrounded responses setting is disabled, follow-up questions don't work. The orchestrator considers clarifying questions that don't have a citation ungrounded and suppresses them. The agent defaults to: 'I'm sorry, I'm not sure how to help with that. Can you try rephrasing?'"

**Symptoms when OFF:**
- Conversational introductions (e.g., "My name is Sarah Chen") trigger Fallback
- Follow-up questions answered from conversation context get blocked
- Agent says "I'm sorry, I cannot help with that request" on non-KB queries
- Conversation eval scores plateau at 80-85% while SR is fine (95%+)
- Agent blocks conversational follow-ups even when it has enough context from prior turns

**Fix**: Toggle ON. This is a UI-only setting (not accessible via Dataverse API). Must be done manually or via Playwright UI automation.

**When to check this FIRST**: Before any instruction changes, topic modifications, or CB topic adjustments. If Conv failures show "I'm sorry, I cannot help" or "I'm not sure how to help" on conversational/non-clinical inputs, this setting is the most likely cause.

**When to NOT toggle ON**: If the grader says "One or more answers seem incomplete", "One or more questions not answered", or "didn't cite knowledge sources", these are INSTRUCTION-LEVEL problems (hedging language, cite:1 format, truncation). Toggling ON in these cases actually makes things WORSE by enabling lower-quality ungrounded responses. **Evidence (June 2026):** SLP Conv was 90% with toggle OFF. Toggling ON dropped to 85% because ungrounded responses scored even lower on completeness. The real fix was removing hedging language from instructions. See pitfall 22 in SKILL.md.

**Decision tree for Conv failures:**
- Grader says "refuses to help" / "error message" / "I'm sorry" → toggle ON
- Grader says "incomplete" / "not answered" / "didn't cite" → fix instructions (see hedging/citation pitfalls 22-23)
- Response cut off mid-sentence → add conciseness instruction ("limit each section to 2-3 sentences max")

Also per MS Learn (generative-mode-guidance): "If you notice your agent blocks normal behavior by using content filtering, update your agent instructions to indicate the behavior is expected to work."

## CRITICAL: Check "Allow ungrounded responses" setting FIRST

Before investigating instruction or topic issues for Conversation eval failures, verify this setting:

**Settings > Generative AI > Knowledge > "Allow ungrounded responses"**

If OFF, the platform BLOCKS any response where the agent didn't use a knowledge source or tool. Conversational inputs (greetings, introductions, follow-ups answered from context) get blocked and the Fallback topic fires with "I'm sorry, I cannot help with that request." This is a platform-level override that supersedes agent instructions.

June 2026 evidence: SLP Conv 80% failure — agent instructions said "never refuse" but platform blocked conversational responses anyway. Toggle ON + Publish improved Conv to 90%+.

See `references/ungrounded-responses-setting.md` for full MS Learn sources.

## CRITICAL: DO NOT modify the Conversational Boosting (CB) system topic

The CB system topic uses SearchAndSummarizeContent with a 600-character limit and "Always cite knowledge sources using [Source Name] format" instructions. This configuration is the correct Microsoft Learn-aligned setup and must NOT be changed.

Changing the CB topic caused a 35% SR regression (from 92% to 35%) — the identical regression pattern seen from broad instruction patches. The original CB config achieves 95% Conv / 96% SR.

- CB topic URL (SLP): .../adaptive/2960a8e1-ca2b-4eeb-8d9d-c749a9127dcc
- How to verify: Topics → System (9) filter tab → Conversational boosting → Open code editor
- Expected content: 600-char limit, "Always cite" instructions, applyModelKnowledgeSetting: true
- If accidentally changed, rollback to original YAML at: C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/home/cb_rollback.yaml

## SR Single Response evaluation grading

The SR test set uses ONLY "General quality" grading (relevance + completeness). Compare meaning at 0.50 was NOT required for the 96% SR peak. The 96% SR peak was achieved with pure General quality grading on the original CB config + no caregiver topics. Focus on topic/KB issues, not grader threshold tuning.

## Caregiver topics degrade Single Response scores

Any caregiver topic that intercepts caregiver queries via triggerQueries will degrade SR scores. The agent's instruction-level generative AI + Conversational Boosting handles caregiver queries better. See references/slp-caregiver-guard-remediation-2026-06.md for the Final action. June 14 run 260614_0053: 95% SR with zero caregiver topics + original CB config.

## Topic deletion

To delete topics, use the Topics list page:
1. Topics tab → find the topic row (.fui-DataGridRow class)
2. Click the More button at x:336 on that row
3. Select "Delete" from the menu
4. Confirm deletion dialog
5. Publish
Note: row y positions shift after deletions. Always verify the correct row before deleting.

## Confirm the run type before acting

Recent results can show multiple test sets with the same display name. Do not trust position alone.

- Verify the row says `20 test cases • Data type: conversation` before treating it as a Conversation run.
- A same-timestamp `100 test cases • Data type: single response` row is a different test set and should not be used to judge conversation fixes.
- Starting a run from a known `/evaluation/configsDetails/{configId}` URL is safer than clicking whichever card appears first after test-set ordering changes.

## PT-style successful pattern

A broad but targeted agent-instruction hardening worked for PT when failures showed record_id hedging:

- Root cause: answers said source text was unavailable, offered to generate an audit, or ended with follow-up questions instead of completing the audit.
- Effective fix: treat `record_id` as sufficient evaluation context, require a complete preliminary audit, include risk/score/required-elements/checklist/corrective wording, and forbid `would you like me...` endings.
- Verify by read-back of the instructions body after Save/Publish before rerunning evaluation.

## SLP caution: broad source-anchor patches can regress badly

A broad SLP agent-level patch that required explicit `Source Anchors` sections caused a Conversation score regression from 90% to 35% because SLP guard topics amplified citation artifacts:

- Bad artifacts included `[1]: cite:1 "Citation-1"`, `[2]: cite:2`, bracket footnotes, and duplicate answer blocks.
- The problem was not lack of content; the grader penalized incomplete/relevance/citation behavior triggered by citation footnotes and topic duplication.
- Roll back broad SLP source-anchor/format patches if the score collapses, then inspect failed rows before trying a narrower fix.

For SLP caregiver-only failures, prefer topic-level remediation over broad Overview instruction rewrites:
For SLP caregiver-only failures, prefer topic-level remediation over broad Overview instruction rewrites:

- `Caregiver Competency Audit`
- `SLP Conv Guard - Caregiver Competency`
- `SLP Conv Guard - Caregiver Cognitive Capacity`
- `SLP Conv Guard - Caregiver Safety`

June 2026 result: turning all four SLP caregiver-related topics OFF, publishing, and rerunning the 20-case Conversation set improved SLP from 90% to 95%; the caregiver safety case passed with the safety guard OFF. Re-enabling only a YAML-fixed `SLP Conv Guard - Caregiver Competency` topic (removed 800-char limit and bracket-source rule, added prose-only citation instructions) regressed Conversation to 89%, so leave all caregiver guards OFF unless a new deterministic/non-SearchAndSummarize topic is built and verified.

Desired topic behavior if rebuilding: one concise mini-audit, prose-only source grounding such as `Per CMS Medicare Benefit Policy Manual Chapter 15 and ASHA documentation guidance...`, no bracket citations, no citation footnote definitions, no duplicated second answer, no `SearchAndSummarizeContent` auto-footnotes if possible.

## Topic textarea dirty-state pitfall

If durable topic YAML/code edits are not immediately available, disabling caregiver guard topics is a reversible diagnostic and can improve score by routing to the agent-level fallback instead of artifact-prone guard topics.

Observed SLP outcome (June 2026):

- Baseline Conversation score: 90%.
- Broad SLP source-anchor instruction patch regressed Conversation to 35% because guard topics amplified `[1]: cite:1`, `Citation-1`, bracket footnotes, and duplicate answer blocks.
- Rolling back instructions restored 90%.
- Turning OFF all four caregiver-related topics, publishing, and rerunning Conversation improved SLP to 95%:
  - `Caregiver Competency Audit` OFF
  - `SLP Conv Guard - Caregiver Competency` OFF
  - `SLP Conv Guard - Caregiver Cognitive Capacity` OFF
  - `SLP Conv Guard - Caregiver Safety` OFF
- The caregiver safety test passed with `SLP Conv Guard - Caregiver Safety` OFF, so do not assume the safety guard must stay enabled.
- The remaining 95% failure was caregiver competency, still due to citation footnotes emitted by fallback knowledge citations (`[1]: cite:1`, `[2]: cite:2`, etc.).

Workflow rule: prefer OFF over DELETE for guard-topic experiments because OFF is reversible. Always publish after toggling, verify table state (`On`/`Off` rows), run a fresh 20-case Conversation eval from the known `configsDetails/{configId}` URL, and inspect the remaining failed row before deciding whether to keep or revert.

See `references/slp-caregiver-guard-toggle-experiment.md` for the detailed run evidence and exact topic list.

## 800-char limit in topic additionalInstructions (update June 2026)

The unenforceable "Keep response under X characters" constraint was found to be the main cause of Conv regressions in both SLP and OT (June 14, 2026). It is hidden in per-topic SearchAndSummarizeContent additionalInstructions and does NOT appear in the agent-level Overview. Every topic must be checked individually.

**Affected topics pattern:** Any SearchAndSummarizeContent action with `additionalInstructions: |-` that contains "Keep response under 800 characters" (or any arbitrary char limit) causes:
1. The model to stop mid-answer when it hits the limit
2. Incomplete responses that grade as "incomplete"
3. The grader hitting the "refuses to help by showing an error message" pattern on follow-up turns

**Fix:** Remove the line entirely. Replace with:
- "Be concise but complete. Prioritize accuracy over strict length limits."
- Add: "Use natural source citations (e.g., Per CMS Chapter 15...). Do not output cite:1 or metadata tags."

**The fix does NOT persist if the Save button stays disabled.** After editing the Monaco code editor, the user must type a character + Backspace to enable Save. Without this, the old YAML remains live despite appearing updated in the editor.

## OT Conv regression (June 2026) - unconditional format + topic bugs

OT Conv dropped from 100% to 85% after switching to unconditional RESPONSE FORMAT (v7). Root cause was NOT the instruction format:
- Topic SearchAndSummarizeContent had "Keep response under 800 characters" in additionalInstructions
- No conversation continuity rules to tell the model to adapt format on follow-up turns
- The model gave full 6-section RESPONSE FORMAT on every turn instead of focused follow-up answers

**Fix:** v9 hybrid approach - unconditional RESPONSE FORMAT for document-related SR questions + explicit conversation continuity rules:
- "For conversation follow-up turns: use the RESPONSE FORMAT for the first response, then provide focused follow-up answers referencing prior context without repeating the full format."
- "For single-response questions: always use the RESPONSE FORMAT."
- "If the user provides a record_id, document type, discipline, payer/setting, or case context, preserve it across turns and never ask for the same information again."

## Topic textarea dirty-state pitfall

On Copilot Studio topic pages, the `Describe what the topic does` textarea may visually change through Playwright `fill()` or keyboard insertion while the Save button remains disabled. Reload then shows the old text, so the edit did not persist.

Do not treat a changed textarea value as saved. Durable topic edits should use a proven topic-code path instead:

- More -> Open code editor / Monaco YAML path when available.
- Dataverse/PAC/API topic patch path when available.
- After any topic edit, reload the topic and verify the text/YAML persisted before publishing or evaluating.

## Response truncation causes "incomplete" failures

When the agent's response is cut off mid-word (e.g., "Documentation of Com..."), the grader marks "One or more answers seem incomplete." This happens when the response exceeds the model's output token limit.

**Fix:** Add to agent instructions: "Keep responses concise — limit each section to 2-3 sentences max. Prioritize accuracy and completeness over verbosity. NEVER let a response get cut off mid-sentence. If running long, abbreviate remaining sections."

**Evidence (June 2026):** SLP Conv had 2 failures from truncation after hedging fix improved score from 85% to 90%. The caregiver cognitive capacity assessment response was cut off at "Documentation of Com..." — the 6-section RESPONSE FORMAT generates very long responses for detailed clinical questions.

## Rollback discipline

If an instruction patch causes a regression:

1. Restore the last known-good instructions from a saved local copy.
2. Save, Publish, and read back the restored body.
3. Rerun a Conversation evaluation to confirm the baseline recovered.
4. Only then attempt a smaller topic-level or case-specific fix.
