# Doc Defense post-migrate fix pass (Therapy AI Dev)

Bot: `2e08ac68-bdef-481e-9c04-6a349c79d6c0`  
Published clean: Thu Jul 16, 2026 ~11:05 PM Pacific · Succeeded · 0 diagnostics

## P0/P1 applied
1. Instructions: GPT5Chat; soften only-sources; drop under-900 Route B; restore responseInstructions (~480 chars, routes A–E)
2. All SASC: responseCaptureType FullResponse + allowLatencyMessage false
3. Fallback: full SASC → has-answer / FallbackCount guidance / final (Pattern J)
4. Conversational boosting: RCT + =Topic.Answer + empty redirect
5. System topics: EndDialog + clearTopicQueue
6. Thank you hollow topic: real SendActivity + EndDialog
7. modelDescription on core audit/MAC/managed care/Medicare Q topics
8. LCR KB human description

## Publish failures encountered mid-pass
- Silence detection: EndDialog with clearTopicQueue before id
- Conversational boosting: SendActivity missing Activity; double-inserted send_answer
- Fallback: prepended SASC broke ConditionGroup indent

**Fix:** restore from pre-edit backups under `docdef_migrate/backups/`, rewrite clean YAML, re-publish. Always backup before bulk PATCHes.

## Scripts/artifacts
- `C:/Users/kevin/Desktop/docdef_migrate/apply_all_fixes.py` (initial bulk; may need Pattern J repair after)
- Backups: `C:/Users/kevin/Desktop/docdef_migrate/backups/`
