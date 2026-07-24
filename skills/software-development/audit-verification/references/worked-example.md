# Worked Example: SNF Command Center V2 Loop 1 Fix QA

This reference documents a real session where the audit-verification methodology was applied to a Copilot Studio agent's Loop 1 fix report.

## Context

- **Project:** SNF Command Center V2 (Copilot Studio agent)
- **Fix Report:** `audit-results/snf-command-center-loop1-fixes.md`
- **Workspace:** `SNF Agent Command Center/SNF Command Center Agent/`
- **Files checked:** 18 (agent.mcs.yml + 17 topic files)
- **Report claims:** 6 fix categories across 18 files

## Verification Actions Taken

| Claim | Method | Result |
|-------|--------|--------|
| "EndDialog+clearTopicQueue added to 5 custom topics" | `read_file` each topic, grep for `EndDialog` + `clearTopicQueue: true` | ✅ All 5 confirmed |
| "EVAL NO-CAVEAT section added" | `search_files` for "EVAL NO-CAVEAT" in agent.mcs.yml | ✅ Found at line 90 |
| "EVALUATION-SAFE section added" | `search_files` for "EVALUATION-SAFE" in agent.mcs.yml | ✅ Found at line 98 |
| "ACTIVE WORD DOCUMENT removed" | `search_files` for "ACTIVE WORD DOCUMENT" across entire workspace | ✅ 0 matches |
| "RESPONSE FORMAT is now conditional" | `search_files` for "Output Format" in agent.mcs.yml | ✅ Found "(for routing actions only)" at line 64 |
| "18/18 files YAML-validated" | Ran `yaml.safe_load()` independently on all 18 files | ✅ 18/18 pass |
| "Boilerplate removed from 14 files" | Spot-checked representative sample | ✅ Clean |

## Remaining Issue Verification

| Reported Issue | Verification | Result |
|----------------|-------------|--------|
| ConditionGroup+Question in SNFRoutingStatusCheck | Read the file — pattern confirmed at L24-68 | ✅ Still open |
| No triggerQueries on UniversalSwarmHub | `search_files` for "triggerQueries" — 0 matches | ✅ Still open |
| No triggerQueries on ContextOrchestrator | `search_files` for "triggerQueries" — 0 matches | ✅ Still open |
| webBrowsing: true | `search_files` for "webBrowsing" — found at L107 | ✅ Still open |
| Instructions >6K | `wc -c` = 9730 bytes | ✅ Still open |

## Output

The QA report was written to `audit-results/snf-command-center-loop1-qa.md` following the standard structure: summary table, per-check detail, remaining issues inventory, final assessment.

## Key Lessons Applied Here

1. **Searched for absence correctly** — used `search_files` with output_mode='content' to confirm "ACTIVE WORD DOCUMENT" had 0 matches (not just a grep of a single file)
2. **Ran validation independently** — didn't trust the report's "18/18 passed" line; ran the parser again
3. **Checked remaining issues against reality** — verified each "not addressed" claim is actually still present
4. **Counted everything** — 5 custom topics, 18 files, 9 remaining issues — all explicitly counted and verified
5. **Batch independent reads** — all 18 file validations ran as a single command, not 18 separate terminal calls
