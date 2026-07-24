# Therapy Report Prep V2 — Audit + Fix (2026-07-17)

**Bot:** `fd1bce12-cf47-f111-bec5-70a8a5b1c3a3`  
**Schema prefix:** `auto_agent_aaamq`  
**Env:** Therapy AI Dev (`orgbd048f00`)  
**Publish after fix:** 2026-07-17T10:41:08Z (03:41 AM PT) — Succeeded, no diagnostics

## Inventory (live Web API)
- Topics 21 | Instr 1 | KBs 3 | Bot Files 7 | Settings 2 | External trigger 1 | Eval ~600 rows
- Connected TaskDialogs: Case Historian V2, SNF Dashboard V2, Command Center V2
- Get Therapy Notes + Mock: workflows were **Inactive** at audit

## Architecture killer (pre-fix) — Pattern P
`Conversational boosting` schemaname = `auto_agent_aaamq.topic.Search`.

Live **analysis topic `data`**:
```
SendActivity intro → Question(String) → BeginDialog topic.Search
→ SendActivity "Analysis complete" → EndConversation
```
No local SASC. Question gate + silent Search = eval-hollow.

Live **boosting `data`** (OnUnknownIntent priority -1):
```
SASC variable Topic.Answer   # no FullResponse
→ EndDialog clear            # NO SendActivity → notextresponse
```
Fallback (priority -2): rephrase-only.

## content trap
Richer SASC in `content` still lacked FullResponse/EndDialog and BeginDialog into stale `pcca_agent39xn69.topic.*`. Never restore content as-is. Rewrite live `data` only.

## Fix applied (all 204 + re-GET PASS)
1. Instructions: GPT5Chat, EVAL CTX, compress, typos fixed  
2. Boosting Pattern L (+ else capability message)  
3. Progress / Recert / Discharge / Eval / ManualIntake → Pattern L leaves  
4. Suggested Actions menu + EndDialog  
5. Conversation Start + Fallback Pattern J  
6. On Error: strip inactive flow  
7. OIG KB description + isOfficial  

**Artifacts:** `REPORTPREP_AUDIT_REPORT.md`, `REPORTPREP_FIX_PASS_2026-07-17.md`, `scripts/fix_reportprep_v2.py`  
**Backups:** `backups/reportprep_v2_20260717_034037/`

## Contrast: QM Coach V2 same night
QM Coach = sound leaves missing package flags (surgical Pattern L).  
Report Prep = hollow Search handoff until leaves became Pattern L.
