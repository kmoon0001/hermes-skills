# SharePoint KB Dedup Regression — Fleet-Wide Failure Pattern

## The Pattern

When you consolidate individual knowledge source files into SharePoint folders, the SharePoint folder name becomes the ONLY retrieval routing text for GPT. If the folder name is generic ("Core Clinical Manuals"), GPT cannot route queries to the right content. This causes ALL agents sharing that folder to regress — not just the one you were fixing.

## Root Cause

Per Microsoft Learn: "If >25 sources, GPT filters by description." SharePoint sources have NO editable description field — the folder name IS the description. A generic folder name like "Core Clinical Manuals for Medicare A, PDPM vs. Part B, LTC Rehabilitation" tells GPT very little vs a keyword-rich name like "Core Clinical Manuals - CMS PDPM Part B MDS 3.0 Jimmo Ch5 Ch15 Program Integrity MSCA MSP PIP 42 CFR".

## Evidence (June 2026 — Ensign Services Fleet)

| Agent | Pre-Dedup SR | Post-Dedup SR | Drop | Pre-Dedup Conv | Post-Dedup Conv |
|-------|-------------|---------------|------|----------------|-----------------|
| PT | 95% | 75% | -20% | 95% | 94% |
| SLP | 96% | 92% | -4% | 85% | 85% |
| OT | 91% | Running | ? | 90% | ? |

PT was hardest hit because it relies most heavily on SharePoint content. SR (knowledge-grounded) dropped 20% while Conv (conversational) stayed stable — the grader was failing on grounding quality, confirming retrieval routing failure.

## Prevention

**Golden rule: Rename SharePoint folders BEFORE removing duplicates from agent KBs.** Never dedup before renaming.

Folder naming target: ~100 chars, comma-separated keywords covering:
- Content types (CMS, PDPM, Part B, MDS 3.0, Jimmo, etc.)
- Intended use (Medicare compliance, therapy documentation, audit standards)
- Disciplines covered (OT, PT, SLP)

## Recovery Steps

1. Rename SharePoint folders to keyword-rich names (~100 chars)
2. Verify folder names propagate to Copilot Studio (auto-syncs, no publish needed)
3. Remove duplicate individual files from agent KBs
4. Rewrite remaining KB source descriptions (non-SharePoint sources)
5. Set SR test sets to Compare meaning at 0.50 threshold
6. Re-run evaluations to verify recovery

## Related

- `sharepoint-folder-naming.md` — naming patterns and before/after examples
- `knowledge-source-descriptions.md` — description writing best practices
- `kb-dedup.md` — full 4-agent KB inventory and duplicate list
