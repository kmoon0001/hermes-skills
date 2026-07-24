# Medicare Part B Compliance Agent — Baseline Snapshot 2026-07-09

**Bot:** Medicare Part B Compliance Agent
**Bot ID:** b0346795-4876-f111-ab0e-70a8a5b1b8cc
**Schema:** cr917_CopyTherapyDocuementationFeedbackAg
**Environment:** a944fdf0 (Therapy AI Agents Dev)
**Org:** orgbd048f00.crm.dynamics.com
**Tenant:** 03cc92c3
**Gateway:** powervamg.us-il106

**Last Publish:** Succeeded 2026-07-09T18:21:40Z

## Topics (23 total, 17 active)

### Active document audit topics (7) — all have ED+CTQ+SAS+FLW+FILE
- Evaluation/Assessment and Plan of Care (8645ch)
- Treatment Encounter Note Review (8160ch)
- Progress Report Review (7379ch) — **has auto-poll retry loop injected 2026-07-09**
- Discharge Summary (8277ch)
- Recertification/UPOC Review (8267ch)
- Episode of Care (8915ch)
- Large Document OCR Extraction (6673ch)

### Active system topics
- Document Upload Intake (15198ch) — main router with 7 BeginDialogs
- Check OCR Status (5548ch) — manual polling, no FILE
- Greeting (998ch) — has ED+CTQ
- Goodbye (1752ch) — has BD→EndOfConvo, no ED
- Fallback (1746ch) — has ED+CTQ
- End of Conversation (755ch) — **now has ED+CTQ** (fixed in prior cleanup)
- Multiple Topics Matched — has ED+CTQ
- Start Over — has BD, no ED
- Thank you (829ch) — has ED
- On Error (3115ch) — has BD, no ED
- Reset Conversation (637ch) — has BD, no ED
- Escalate (2359ch) — **no ED, no CTQ**

### Inactive topics (statecode=1)
- Conversation Start (5880ch) — **has 6 BeginDialogs** to all audit topics. DEACTIVATED — biggest single score lever
- Check Async OCR Job Status (3333ch) — has ED+CTQ+SAS+FLW
- Sign In — irrelevant
- Work IQ Teams MCP — irrelevant

## Instructions
- Name: Copy Therapy Docuementation Feedback Ag
- Length: 6673ch
- **Key issue:** Unconditional strict scoring format. Lines 10-14 say "Apply the strictest reasonable CMS interpretation" and "Missing = noncompliant" for ALL queries, including general coaching questions. Same pattern that caused 10%+ Conv drops across PT/OT/SLP.

## Knowledge Sources (12)
7 Ensign Habits (1-7), CMS Ch.15, Jimmo FAQ, 2026 MSCA Tool, 2026 LCR Form, Safe Transition DC Planning

## Evaluation Configuration
- **SR test set:** 544233b7 (100 cases, ResponseQualityGeneral grader, SingleTurn)
- **Conv test set:** fcfea569 (20 cases, ResponseQualityGeneral grader, MultiTurn)

### Recent scores
- Jul 6 "SR PostFix Round1": 82% (18/100 failed)
- Jul 6 "SR PostPublish SendActivity": 71% (29/100 failed) — regressed after publish
- Jul 6 "Fix Loop 1 Conv": 8 passed / 6 failed / 2 errors out of 20

### Failure Patterns Identified
1. **Conversation Start deactivated** — breaks routing for all 6 audit topics. Estimated 10-15pt lift to re-activate.
2. **Unconditional strict format in instructions** — forces compliance scoring on coaching questions. Same pattern killed PT Conv (80%→95% after fix).
3. **3 topics missing EndDialog** — Escalate, On Error, Reset Conversation. Causes Conv topic queue bleed.
4. **Duplicate Progress Report topics** — "Progress Report Review" and "Progress Report Review - Text Paste". The Text Paste variant still uses FilePrebuiltEntity instead of text input.

## Files
Snapshot directory: `C:\Users\kevin\Desktop\feedback_b_snapshot_2026-07-09\` (36 component YAML files)
Checklist: `C:\Users\kevin\Desktop\feedback_b_FIX_CHECKLIST.md`
