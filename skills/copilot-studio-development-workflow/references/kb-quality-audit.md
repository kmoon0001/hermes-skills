# KB Quality Audit — Layer 1.5 of MS Learn Evaluation Triage

## MS Learn Priority

Per Microsoft Learn evaluation triage, **Layer 1.5 (KB quality) comes BEFORE Layer 3 (agent config).** Most ungrounded/incomplete failures come from KB gaps, not agent logic.

## What to Check

### 1. Descriptions (MOST IMPACTFUL)

Every knowledge source needs a description. MS Learn: "If there are more than 25 sources, the agent filters by using an internal GPT model based on the description given to the knowledge source." Blank descriptions = random filter selection = ungrounded failures.

**Good description format:**
- What the source contains (specific topics, doc types, regulatory references)
- When to use it (query patterns that should trigger this source)

**Bad:**
- Blank (0/2500 chars) — GPT filter ignores it
- "This knowledge source searches information contained in [filename].txt" — Microsoft auto-generated, too generic

### 2. Duplicate Sources

Individually uploaded files that also exist in SharePoint folders waste the 25-source limit and crowd retrieval context with identical content.

**Common duplicates found in Pacific Coast agents:**
- `Core Clinical Manuals for Medicare` SharePoint folder contains: MDS 3.0 RAI Manual, CMS Ch.15, PDPM docs, Jimmo docs, CFRs. Uploading the same files individually creates duplicates.
- ASHA Practice Portal website + individually uploaded ASHA text files = duplicate ASHA content
- CMS Medicare Learning Network website + individually uploaded CMS files = duplicate CMS content

**Fix:** Remove the individually uploaded files. Keep SharePoint as the single source. Run eval after each removal to check for regression.

### 3. Official Marking

Mark authoritative/government sources as "Official" (three dots → Official source → Yes). Note: this only works in classic orchestration mode, NOT generative mode.

## SharePoint Folder Structure (Ensign Services)

```
AI Fleet Knowledge/
├── Core Clinical Manuals for Medicare A, PDPM vs. Part B, LTC Rehabilitation/  ← CMS PDFs
├── Pacific Coast Therapy Swarm Shared Knowledge/  ← .md prompt files (clinical grounding, governance)
├── Compliance Analyzer/
├── QM Coach/
└── QM Coach v2/
```

Sources used across agents: `Pacific Coast Therapy Swarm Shared Knowledge` (prompt configs) and `Core Clinical Manuals for Medicare` (CMS manuals) are shared across SLP and TDA. Do not re-upload their contents as individual files.

## Detection Script

Run `scripts/detect_generic_descriptions.cjs` (under `evaluation-rest-api` skill) to auto-detect empty/generic descriptions across all 4 agents.

## Per-Agent Status (As of 6/11/26 Session)

| Agent | Sources | Empty | Generic | Notes |
|-------|---------|-------|---------|-------|
| SLP | 13 (after dedup) | 2 | 0 | FOIS Scoring Guide + 2025 Part B MSCA need descriptions |
| TDA | 6 (after dedup) | 0 | 0 | All good. Med Program Integrity, 42 CFR 424.24, Secondary Payer re-added. |
| OT | ~10 | Not checked yet | — | Needs audit |
| PT | ~10 | Not checked yet | — | Needs audit |
