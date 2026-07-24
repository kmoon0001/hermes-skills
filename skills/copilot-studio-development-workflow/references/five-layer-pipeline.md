# 5-Layer Reproducible Pipeline (June 21, 2026)

Long-term architecture for shipping Copilot Studio agents without
re-discovering the same failure modes every week. Born out of the
June 19-21 QM Coach V2 loop (re-discover → reinvent → hand-publish →
time out at 600s on the Evaluation SPA → re-do).

## The five layers

1.  **AUTHOR**     `topic_templates/*.yaml` (single source of truth, git-tracked)
2.  **LINT**       `pipeline/topic_lint.cjs` — guard all publish attempts
3.  **DEPLOY**     `pipeline/publish_pipeline.cjs` — Dataverse API upsert + `pac copilot publish`
4.  **EVAL**       `pipeline/eval_bot.cjs` — REST API trigger + poll + log
5.  **HISTORY**    `pipeline/eval_history.jsonl` — append-only score ledger + delta vs last 3

Plus one supporting artifact per topic: `routing_matrix.json` (intent,
triggers, keywords, expected output shape) so eval can grade "right topic
fired" vs "right answer given" separately instead of conflating them.

**Default threshold gate:** pipeline exits 1 if SR <85% or Conv <70%.
Configurable per bot in `pipeline/config.json`. The gate is the piece
that stops regressions staying alive for weeks — without it the same
failure mode re-emerges every publish.

## Why this beats the SPA/CDP loop

- The Evaluation page SPA kept bouncing to Overview via CDP across four
  consecutive attempts. Power Platform REST API returns the same data as
  structured JSON without rendering. See the `evaluation-rest-api` skill
  for the full endpoint reference.
- "I published, did it ship?" → deploy returns the publish version ID.
- "Did the eval finish?" → eval_bot polls until state=Completed or fails.
- "What was last week's score?" → `tail -20 eval_history.jsonl`.
- Each failure mode (Question-without-EndDialog, OnUnknownIntent override,
  topic dedup, duplicate trigger phrases) becomes one lint rule. New
  agents inherit those rules for free.

## Working folder convention

All five deliverables live in `D:/my agents copilot studio/pipeline/`
alongside the existing `topic_templates/` folder.

| Path                                  | Purpose                                |
|---------------------------------------|----------------------------------------|
| `pipeline/topic_lint.cjs`             | Layer 2 — pre-publish guard            |
| `pipeline/publish_pipeline.cjs`       | Layer 3 — Dataverse upsert + PAC publish |
| `pipeline/eval_bot.cjs`               | Layer 4 — REST eval trigger + poll     |
| `pipeline/eval_history.jsonl`         | Layer 5 — append-only score ledger     |
| `pipeline/routing_matrix.json`        | Per-topic intent/keyword metadata      |
| `pipeline/config.json`                | bot IDs, env IDs, Entra client_id, threshold gate |

Existing parent-folder `*.cjs` scripts (verify_topics, goto_topics,
check_ui_topics, create_topics_via_api, patch_empty_topics_batch,
check_qm_live_topics) stay where they are. They are demos / one-shots,
not part of the pipeline. Do not relocate them as part of the
pipeline build.

## Auth model

Enter via **Entra ID client credentials** with Power Platform API scope:

- `MakerOperations.Write` — for POST /testsets/{id}/run
- `/.default` — for Dataverse topic upsert botcomponent

**Do NOT reuse SPA-captured Bearers** for the pipeline. They are READ-only.
GET works, POST fails. They are scoped to the agent whose page you are on.
They will not resolve Dataverse tokens against `org*.crm.dynamics.com`
either (different audience).

Token acquisition lives in `pipeline/get_pp_token.cjs` — Entra ID
`POST /{tenant}/oauth2/v2.0/token` with `client_credentials`, cache to
disk with TTL, refresh once on 401.

## Order of build (don't try to do all five at once)

| # | Piece                           | Effort  | Leverage                          |
|---|---------------------------------|---------|-----------------------------------|
| 1 | `topic_lint.cjs`                | <=1 day  | Eliminates the 5 most common publish blockers (empty AdaptiveDialog, missing EndDialog, OnUnknownIntent override, period in name, duplicate triggers) |
| 2 | `eval_history.jsonl` writer     | <=half day  | Captures score deltas so "why did we drop" questions become answerable |
| 3 | `eval_bot.cjs`                  | 2-3 days| Replaces CDP/SPA eval extraction entirely |
| 4 | `routing_matrix.json`           | 1 day   | Stops trigger-overlap bugs (the cause of the 71->95% slam-dunks) |
| 5 | `publish_pipeline.cjs`          | 1 day   | Orchestrator — only worth doing after 1-4 are stable |

Layer 5 is purely orchestration. Layers 1-4 each have independent value;
you can run any of them manually today.

## MS Learn citations

- Eval REST API + Entra ID prerequisites:
  https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-rest-api
- pac copilot commands:
  https://learn.microsoft.com/power-platform/developer/cli/reference/copilot
- botcomponent / bot Dataverse schema (componenttype, schemaname, parentbotid):
  https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/botcomponent
- Topic YAML authoring rules + period-in-name export block:
  https://learn.microsoft.com/microsoft-copilot-studio/authoring-create-edit-topics

## Pitfalls observed while designing this

- **ComponentState in botcomponent**: 0=Published, 1=Unpublished,
  2=Deleted, 3=Deleted Unpublished. PATCH `statecode` to control
  which layer a topic lives on. Topic authoring canvas works on
  Unpublished (1); publish freezes; the eval runs against the
  published version.
- **Using "OnUnknownIntent" as a topic's beginDialog kind is a system
  poison**. We removed Conversational Boosting once already because it
  crashed publish. The lint must hard-fail on it.
- **Period in topic name** blocks `pac copilot export` to a solution.
  The lint must hard-fail on it even before getting to deploy.
- **SPA Eval page RouteNotFound**: as of June 2026 the URL
  `api.powerplatform.com/copilotstudio/environments/.../api/makerevaluation`
  returns 404 for SPA-captured tokens because of tenant routing prefix
  injection. Entra-issued tokens with proper scope do not have this
  issue. This is a strong reason the pipeline must use Entra, not
  SPA capture.

## How this changes day-to-day workflow

**Before:**
1. Edit YAML in Notepad
2. Open CDP-connected Chrome
3. Click More -> Open code editor
4. Paste -> Space+Backspace -> Save (verify by re-opening)
5. Repeat for N topics
6. Click Publish in UI
7. Navigate to Evaluation tab
8. Click test set card -> Evaluate -> click Manage Profile -> Run
9. Wait 5-10 min polling for results
10. Parse score manually from SPA body text
11. Repeat until 95%

**After (one command, fully automated):**
```
node pipeline/publish_pipeline.cjs --bot <BOT_ID>
```

-> Lint passes / fails. Uploads new YAMLs via Dataverse. Publishes via
PAC. Triggers REST eval. Polls for completion. Appends to jsonl. Prints
delta vs last 3. Exits 0 or 1 based on gate.
