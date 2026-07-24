# SharePoint KB Regression Pattern

## Symptom

All agents (OT, PT, SLP, TDA) regress simultaneously after SharePoint knowledge base
consolidation. Scores drop 10-30% fleet-wide.

## Root Cause

Individual files were moved from agent KBs into shared SharePoint folders, but:
1. **SharePoint folder names stayed generic** — GPT can't route retrieval
2. **Auto-generated descriptions weren't rewritten** — random routing
3. **Compare meaning grading not set** — citation false negatives

## Fix Checklist (apply in order)

### 1. SharePoint Folder Renaming
- Navigate to SharePoint document library
- Rename each folder to keyword-rich ~100 char paths
- Pattern: `[Name] - [Keywords]: PDPM, Part B, MDS 3.0, Jimmo, Ch5/Ch15, etc.`
- See `sharepoint-folder-naming.md` for examples

### 2. Force KB Cache Refresh (CRITICAL — missing this causes progressive degradation)
After renaming SharePoint folders, Copilot Studio caches old retrieval paths internally.
The agent still finds the source (status shows "Ready") but GPT filter routing is
broken because the folder name IS the description, and the cached index has the old name.

**For each agent:** Knowledge page → remove SharePoint source → re-add it pointing to
the renamed folder. Then republish. Scores degrade progressively (91%→82%→50% over
6 hours) without this step.

### 3. Remove Duplicates
- Files individually uploaded to agents that exist in SharePoint
- Check: anything with "searches information contained in [filename]" as description
- SLP: MDS 3.0 Section GG, 42 CFR 424.24
- TDA: Medicare Benefits Policy Manual, PDPM files, Clinical Decision Support

### 3. Rewrite KB Descriptions
- Every source needs a specific 1-2 sentence description
- Pattern: "[Source] provides [content]. Use when [scenario]. Covers [topics]."
- See `knowledge-source-descriptions.md` for examples
- NEVER: "searches information contained in [filename]"

### 4. Cross-Agent Audit
- Check which sources exist in some agents but not others
- Example: AOTA-APTA-ASHA Joint Consensus in PT+TDA but missing from OT
- Add missing consensus/standards docs to agents that lack them

### 5. Compare Meaning Grading
- Set Compare meaning at 0.50 on ALL Single Response test sets
- Set in Test Sets editor, NOT in evaluation runs
- Fixes citation false negatives where valid answers fail on wording

### 6. SLP Conditional Format
- If SLP Conv below 90%: check RESPONSE FORMAT
- Unconditional ("for ALL audit requests") → change to conditional
- Match PT pattern: "For full document audits only... For general questions: natural answer"

## Conv Recovery Lags SR

After KB cache refresh, Conv takes 2-4 additional evaluation runs to reach the same recovery level as SR. This is expected — don't declare a fix ineffective until both SR and Conv have settled.

| Metric | Conv recovery | Reason |
|--------|--------------|--------|
| SR | 1-2 runs | Single retrieval per question |
| Conv | 3-5 runs | 3+ turns × compounding retrieval failures |

**If SR recovers but Conv doesn't after 3 runs:**
1. Verify "Allow ungrounded responses" is ON (catastrophic for Conv)
2. Check if RESPONSE FORMAT is unconditional in a degraded-KB context (switch to conditional)
3. Set Compare meaning 0.50 on Conv test sets too (not just SR)

## Cross-Agent Pattern: All regress together

When ALL agents in a fleet regress simultaneously and the only shared change was SharePoint, the root cause is the SharePoint KB, not individual agent configs. Don't debug OT independently when PT and SLP also dropped. Fix SharePoint once → publish all → re-run evaluations.

## Verification: Publish Button Diagnostic

- If Publish shows no confirm dialog → no pending changes
- This means: if you thought you changed instructions and Publish doesn't confirm, the instructions save didn't persist
- Publishing an already-published agent wastes time: check if there's a dialog before waiting for a publish cycle


**June 12, 2026 — SharePoint consolidation without cache refresh:**
- OT: SR 91% → 82% → 50% (progressive degradation over 6 hours)
- PT: SR 94% → 87% → 75% (progressive degradation)
- SLP: SR 96% → 92% (moderate, KB had fewer sources to lose)
- Root cause: GPT lost retrieval routing because SharePoint folder names changed.
  Copilot Studio cached old folder-name-based retrieval index. Removing and re-adding
  sources forces cache rebuild.

**June 10, 2026 — Earlier regression from KB dedup without folder renaming:**
- OT: 5% (12/20 Guard topics OFF + ungrounded OFF + KB chaos)
