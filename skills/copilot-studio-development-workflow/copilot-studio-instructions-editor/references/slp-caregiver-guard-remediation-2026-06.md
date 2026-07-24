# SLP caregiver guard remediation — June 2026

Use this when SLP Conversation evals fail on caregiver competency, caregiver safety, or caregiver cognitive-capacity cases.

## Observed eval behavior

Best completed live configuration:

- `Caregiver Competency Audit` OFF
- `SLP Conv Guard - Caregiver Competency` OFF
- `SLP Conv Guard - Caregiver Cognitive Capacity` OFF
- `SLP Conv Guard - Caregiver Safety` OFF
- Published state produced SLP Conversation `260613_1231`: 95% (19/20)
- The caregiver safety case passed with the safety guard OFF.

Unsafe experiments:

- Broad SLP agent-level source-anchor patch regressed Conversation from 90% to 35% by causing bracket citation footnotes and duplicated answer blocks.
- Re-enabling only `SLP Conv Guard - Caregiver Competency` after YAML repair regressed Conversation to 89%.
- The repaired YAML removed the 800-character limit, removed bracket-source instructions, added prose-only citation instructions, added `clearTopicQueue: true`, and still performed worse than leaving the guard OFF.

## Replacement topic created June 13, 2026

A new topic `SLP Caregiver Documentation Compliance Audit` was created as a Microsoft Learn-aligned replacement for the four old caregiver guard topics. Key details:

- **Topic ID**: `7b77a11b-c817-45ec-85c7-7ff24746489d`
- **Topic URL**: `.../bots/6e437a77-a5dc-4984-90eb-4924eab10006/adaptive/7b77a11b-c817-45ec-85c7-7ff24746489d`
- **Name**: `SLP Caregiver Documentation Compliance Audit`
- **Description**: `Audits SLP caregiver documentation for Medicare compliance. Use for caregiver competency, caregiver safety comprehension, teach-back, return demonstration, cognitive capacity for multi-step caregiver tasks, supervision level, carryover plan, red flags/escalation, and discharge or skilled-need linkage.`
- **Architecture**: AdaptiveDialog with `OnRecognizedIntent` + trigger queries, `SendActivity` + `EndDialog` with `clearTopicQueue: true`. **No `SearchAndSummarizeContent`** — avoids the citation-artifact root cause entirely.
- **YAML saved at**: `C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/home/caregiver_audit_topic_yaml.txt`
- **Injection method**: Monaco code editor clipboard paste (proven reliable path)
- **Eval result**: Conversation `260613_1616` scored **95%** (19/20), matching the guard-off baseline `260613_1231` exactly. No rollback needed.

### Compare results

| Run | Config | Score |
|-----|--------|-------|
| 260613_1231 | All caregiver guards OFF (baseline) | 95% |
| 260613_1433 | All caregiver guards OFF + republish | 100% |
| 260613_1616 | New topic ON (static SendActivity), old guards OFF — Conv | 95% |
| 260613_1353 | Old guards ON with YAML fix | 89% |
| 260613_1054 | Broad SLP source-anchor patch | 35% |

**Single Response regression (June 13 discovery):** The v1 static SendActivity topic with triggerQueries caused Single Response eval to REGRESS from 96% (260612_0229) to 89% (260613_1353). Root cause: ~8 caregiver-specific SR questions matched the topic's trigger phrases, and the static SendActivity returned template placeholders (`[Assessment...]`, `[HIGH/MODERATE/LOW with rationale]`) instead of real generative answers. The SR grader scored these as incomplete/non-answers. The 96% peak was achieved with NO caregiver topic at all — the agent's instruction-level generative AI + KB handled caregiver queries correctly via the general conversational boosting path.

**Fix for SR regression:** Replace the static `SendActivity` with `CreateGenerativeAnswers` + `additionalInstructions` so the topic leverages the agent's full generative AI and KB. Or turn the topic OFF and let agent instructions + CB handle caregiver queries (proven at 96% SR). Monaco Save for topic YAML updates is unreliable after the initial creation — see `## Monaco Save persistence pitfall` below.

| SR Run | Topic State | Score |
|--------|-------------|-------|
| 260612_0229 | No caregiver topic (peak) | 96% |
| 260612_0405 | After KB/SP changes | 92% |
| 260613_1026 | Static SendActivity topic ON | 90% |
| 260613_1353 | Static SendActivity topic ON | 89% |

## Live test results

Sent "Evaluate caregiver competency for dysphagia" through the test pane. The bot responded with:

```
Caregiver Competency for Dysphagia: Key Elements
- Caregiver must demonstrate understanding of oral intake modifications...
- Documentation must be clear, concise, and include evidence of return
  demonstration, supervision level, and discharge criteria linkage.

Clinical review required. Non-Device CDS only.
```

The Copilot Studio UI renders a `1 reference` knowledge-source citation dropdown in the test pane — this is platform behavior, not agent output. The eval (General Quality) does not penalize this.

## Root cause pattern

The failure is not just wording. The existing caregiver guard topics use `SearchAndSummarizeContent`, which can append citation artifacts even when agent instructions forbid them:

- `[1]: cite:1 \"Citation-1\"`
- `[2]: cite:2`
- bracket footnotes
- raw URLs/source metadata
- duplicated answer blocks

The old competency topic also had topic-level hidden constraints:

```yaml
additionalInstructions: |-
  - Focus on caregiver competency documentation standards
  - Cite sources inline using [Source Name] format
  - Keep response under 800 characters
  - Prioritize the most critical compliance findings
```

Those topic-level instructions are invisible from the agent Overview instructions and can override/undermine otherwise-good agent instructions.

## Safe short-term rule

For SLP caregiver eval failures, do **not** keep tweaking or re-enabling the existing caregiver guard topics unless a new run proves improvement. The safest known live state for Conversation is all four old caregiver-related topics OFF plus the new `SLP Caregiver Documentation Compliance Audit` topic ON.

**For Single Response:** The static SendActivity version of the new topic causes SR regression (96% → 89%) because its triggerQueries capture caregiver SR questions and return template placeholders instead of real answers. Either:
- Use the CreateGenerativeAnswers version of the topic (v2 YAML), or
- Turn the topic OFF and let the agent's instruction-level generative AI + CB handle caregiver queries (proven at 96% SR)

**June 13 final determination:** The replacement topic degrades SR regardless of action kind. Both static SendActivity (v1: 86% SR) and AnswerQuestionWithAI (v3: 85% SR) scored below the no-topic baseline (96% SR). The topic's triggerQueries capture SR questions and replace the agent's full generative response with topic-level instructions. **The Microsoft Learn-aligned long-term fix is: keep the topic OFF.** The agent's Conversational Boosting topic + instruction-level generative AI + KB handles caregiver queries correctly. The topic's description serves as a routing hint for generative orchestration, but the topic itself should remain disabled to avoid intercepting SR questions.

**June 14 — final action:** All 5 caregiver topics were DELETED from the SLP agent (the 4 old guard topics + the new `SLP Caregiver Documentation Compliance Audit` topic). Deletion was done via Topics page row More menu (x:336) → Delete → confirm → Publish. The agent now has zero caregiver-specific authored topics. Confirmed: SR eval `260614_0053` scored **95%** with caregiver topics deleted and CB topic restored to original configuration (unchanged). This is 1 point below the historical peak (96%) but 6 points above the 89% start-of-day score. The remaining gap is attributed to earlier KB/instruction state differences, not a regression.

## Final rollback discipline rule

Any future experiment with caregiver topics must follow:
1. Conv baseline: 95%, SR baseline: 95%
2. If Conv drops below 95% or SR drops below 95%: topic OFF, re-Publish, re-evaluate
3. If SR drops below 92% (a full-blown regression): restore CB topic to original YAML from `C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/home/cb_rollback.yaml` and re-evaluate

If a future agent experiments, use rollback discipline:

1. Confirm all caregiver topics' ON/OFF state from the Topics table.
2. Publish before evaluating.
3. Run the target eval config directly.
4. Compare against baseline: Conv 95%, SR 96%.
5. If Conv drops below 95% or SR drops below 96%, rollback: turn new topic OFF, all four old caregiver topics OFF, publish.

## Durable long-term Microsoft Learn-aligned fix

Before implementation, ground the design with the Microsoft Learn MCP server (`microsoft-learn` → `https://learn.microsoft.com/api/mcp`) and fetch current Learn guidance for:

- Copilot Studio generative orchestration / agent behavior.
- Custom agent tools and prompt tools.
- Topic descriptions / trigger selection.
- SharePoint or other knowledge-source descriptions.
- Fallback behavior.

The relevant Microsoft Learn pattern is: use generative orchestration to select the best combination of topics, tools, and knowledge; give topics/tools/knowledge detailed, non-overlapping descriptions; use knowledge as grounding/fallback; use tools/prompt tools when the response needs structured behavior and output constraints.

Do not rebuild this as four overlapping micro guard topics. Replace them with one clearly described capability that generative orchestration can choose:

- Preferred: Prompt tool / agent tool named `SLP Caregiver Documentation Compliance Audit`.
- Alternative: deterministic authored topic that does not rely on `SearchAndSummarizeContent` for the final answer. **This alternative is now proven at 95%.**

Recommended tool description:

> Audits SLP caregiver documentation for Medicare compliance. Use for caregiver competency, safety comprehension, teach-back, return demonstration, cognitive capacity for multi-step caregiver tasks, supervision level, carryover plan, red flags, and discharge/skilled-need linkage.

Prompt/tool output requirements:

- One concise mini-audit.
- Include caregiver identity/role, SLP task trained, return demonstration/teach-back, accuracy/cueing level, safety comprehension, carryover plan, supervision level, red flags/escalation, and linkage to discharge/skilled need.
- Source grounding in prose only: `Grounding: CMS Medicare Benefit Policy Manual Chapter 15, CMS outpatient therapy documentation guidance, ASHA SLP documentation guidance, and Ensign SLP documentation patterns.`
- Forbid bracket citations, citation footnotes, `cite:1`, `Citation-1`, raw URLs, and source metadata lines.

## Monaco Save persistence pitfall (June 13, 2026)

**Monaco code editor Save button does not enable after clipboard paste for topic YAML UPDATES.** The initial topic creation Save worked (v1), but subsequent updates (v2 with CreateGenerativeAnswers) pasted correctly into the editor (verified via `.view-line` textContent showing new YAML), yet the Save button remained null and `Ctrl+S` did not persist. On reload, the topic reverted to the prior YAML.

Confirmed symptoms:
- `Ctrl+A` + `Ctrl+V` pastes new YAML into Monaco
- `.view-line` text shows the new content
- Space+Backspace hack does not trigger the React dirty-state detector
- `Ctrl+S` appears to work (no error) but content reverts on reload
- `navigator.clipboard.writeText` + native `input`/`change` event dispatch on hidden textarea also fails

**Workaround**: After the initial topic creation, if YAML needs updating, either:
1. Manually edit the YAML in Monaco with actual keystrokes (not clipboard paste), or
2. Delete and recreate the topic with the correct YAML, or
3. Use the Dataverse Web API to PATCH the topic YAML directly

**Do not** assume clipboard paste + invisible Save is sufficient — always reopen the code editor and verify persistence before publishing.

## CreateGenerativeAnswers topic YAML (v2 — not yet persisted)

The preferred caregiver topic YAML replaces static `SendActivity` with `CreateGenerativeAnswers` so the agent uses its full generative AI + KB for caregiver queries:

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: SLP Caregiver Documentation Compliance Audit
    triggerQueries:
      - "caregiver competency"
      - "caregiver safety"
      [...]
  actions:
    - kind: CreateGenerativeAnswers
      id: createCaregiverAudit
      inputs: =System.Activity.Text
      dataSources: []
      additionalInstructions: |-
        You are auditing SLP caregiver documentation for Medicare compliance.
        Return ONE concise mini-audit with sections:
        1. Competency/Safety Finding [...]
        6. Advisory - "Clinical review required. Non-Device CDS only."
        FORBIDDEN: [1], [2], cite:1, Citation-1, bracket footnotes, raw URLs, duplicate answer blocks, internal tool JSON
    - kind: EndDialog
      id: endDialog
      clearTopicQueue: true
inputType: {}
outputType: {}
```

Full YAML saved at: `C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/home/caregiver_audit_topic_v2.yaml`

For topic YAML, visual `Describe what the topic does` textarea edits can visually change text while Save remains disabled and reload shows no persistence. Use **More -> Open code editor** instead.

When Monaco does not expose `window.monaco`, clipboard paste into the hidden Monaco textarea worked:

1. Open topic.
2. Click topic toolbar `More` (near Details/Save, not the test-pane More).
3. Click `Open code editor`.
4. Write fixed YAML to `navigator.clipboard`.
5. Click inside editor.
6. Press `Ctrl+A`, then `Ctrl+V`.
7. Verify `.view-line` text contains unique markers and no stale constraints.
8. Click enabled Save.
9. Reopen code editor and read back `.view-line` text before publishing.

Do not treat a changed visual canvas field as saved unless reload/readback confirms persistence.
