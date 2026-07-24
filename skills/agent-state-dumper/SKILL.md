---
name: agent-state-dumper
description: "Dump full state of any Copilot Studio agent via Dataverse API: instructions, topics, knowledge, model, publish status."
category: copilot-studio
---

# Agent State Dumper

**Purpose:** Bypass the Copilot Studio SPA entirely. Single command to inspect any agent's full state via the Dataverse API. Used when the UI is slow, non-responsive, or when you need diffable snapshots.

**Script:** `D:/my agents copilot studio/pipeline/scripts/dump_agent_full.cjs`

---

## Usage

```
node dump_agent_full.cjs <botId> [label]
```

### Known bot IDs (Dev / Default org)

| Agent | Bot ID |
|-------|--------|
| OT    | `73b45e98-af7a-443a-aa12-6d8a05118530` |
| PT    | `593407f3-539b-490f-84ac-d74e13216c81` |
| SLP   | `6e437a77-a5dc-4984-90eb-4924eab10006` |
| TDA   | `4d0ed0d3-30f6-f011-8406-000d3a37eba2` |

### Output files (all in `live_agent_dump/`)

| File | Content |
|------|---------|
| `<label>_agent_dump_<timestamp>.json` | Full structured dump |
| `<label>_instructions_live.txt` | Instructions as readable YAML |
| `key_agent_info.txt` | Cumulative summary of all dumps |

### Summary fields

- `displayName` — agent name
- `model` — GPT5Chat / Sonnet46
- `instructionChars` — total instruction length
- `hasResponseFormat` — true if RESPONSE FORMAT section found
- `hasNoCaveat` — true if NO-CAVEAT STANDARDS CHECK found
- `hasEvalSafe` — true if EVALUATION-SAFE ORCHESTRATION found
- `conversationStarters` — present/missing
- `topicCount` / `knowledgeCount` — component counts

---

## Limitations

- API pagination caps at 5000 components (some bots have more topics)
- Currently targets org3353a370 (default org); Prod org needs `--org` flag (not yet implemented)

## Pitfalls

- Token from `az account get-access-token` expires after ~1 hour
- **Trailing-slash requirement:** The resource URL passed to `az account get-access-token` MUST have a trailing slash (e.g., `"https://org3353a370.crm.dynamics.com/"`). Without it, the token silently returns 401 on all Dataverse API calls. Always verify with a `WhoAmI` probe.
- **Claims challenge (`insufficient_claims`):** Even with a valid, non-expired token, Dataverse may reject every request with HTTP 401 and `error="insufficient_claims"` in the `WWW-Authenticate` header. The token is missing required claims — typically `xms_rp_ipaddr` (client IP address). The `az` CLI (tested through v2.84.0) does **not** support the `--claims` parameter needed to pass the claims challenge back to Entra ID. **Workaround:** use MSAL Python with device-code flow and `claims_challenge` parameter (see `references/dataverse-claims-challenge.md`). **Quick detection:** probe `WhoAmI` with the token — if you get 401 + a `claims="ey..."` value in the header, you have this problem.
- Large bots (OT) may exceed 5000 components; topics list will be truncated
- The instructions extraction regex for `responseInstructions` is fragile for multi-line values

## Related patterns

- **CDP Chrome fix:** Start Chrome with `--remote-debugging-port=9223 --user-data-dir="<profile>"` before scripts that need Playwright
- **Headless bypass:** For sites blocking headless Playwright, see `references/headless-bypass.md` — Chrome Canary + `--headless=new` technique
- **Component IDs (instructions):** OT=`28c4402c-2a2b-45d7-888d-e3ef81b2f401`, PT=`a6575469-8269-41ae-9e6e-dabd14e8ca63`, SLP=`9a5e1289-baf3-44be-bb76-ce9d410c91dc`, TDA=`ff00b80a-321b-44be-80a4-40c78072ffe3`
- **Patching instructions:** Use `patchDV()` function pattern — HTTPS PATCH to `botcomponents(<id>)` with `{data: <newYaml>}`. Returns 204 on success. See `references/instruction-patching.md` for full template.
- **No‑caveat pattern:** Inject a `NO-CAVEAT STANDARDS CHECK` block into instructions that tells the model: "For eval questions without note text, give a direct standards screen. NEVER ask for the note. Just audit it." This addresses the "ask-for-document" failure pattern. See `references/no-caveat-pattern.md`.
- **Merge pattern:** When user says they've reworked an agent, fetch live instructions first, then add only what's missing (conversation starters, gptCapabilities, no-caveat). Do NOT overwrite their work. Keep the best of both worlds.
- **Verification-before-action:** Verify agent state (dump) → assess gaps → get user confirmation → execute. See `references/verify-decide-execute.md`.
