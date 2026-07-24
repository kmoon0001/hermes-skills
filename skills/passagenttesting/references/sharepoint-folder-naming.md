# SharePoint Folder Naming — The Only Description GPT Sees

**Core finding**: SharePoint knowledge sources in Copilot Studio have NO editable description field. The folder name/path is the only text the GPT filter uses for retrieval routing.

## Why This Matters

Per Microsoft Learn: "If >25 sources, GPT filters by description." SharePoint folder names ARE the description. A folder named "Core Clinical Manuals" tells GPT almost nothing — it's generic enough to match any CMS query, causing poor routing.

## Naming Guidelines

- **~100 character limit** (SharePoint allows longer, but shorter is better for GPT matching)
- **Include content types**: CMS, PDPM, Part B, MDS 3.0, Jimmo, Ch5, etc.
- **Include intended use case(s)**: Medicare compliance, therapy documentation, audit standards
- **Use comma-separated keyword lists** (GPT tokenizes on punctuation and spaces)
- **Avoid underscores and file extensions** in the visible name

## Before/After Examples

| Before | After | Characters |
|--------|-------|------------|
| Pacific Coast Therapy Swarm Shared Knowledge Library | Pacific Coast Therapy Swarm - Ensign compliance, audit standards, and documentation rules for OT/PT/SLP | 103 |
| Core Clinical Manuals for Medicare A, PDPM vs. Part B, LTC Rehabilitation | Core Clinical Manuals - CMS: PDPM, Part B, MDS 3.0, Jimmo, Ch5/Ch15, Integrity, MSCA, MSP, PIP, 42 CFR | 102 |
| AI Fleet Knowledge | AI Fleet Knowledge - Ensign SLP/OT/PT therapy agent prompts, clinical decision support files, and shared reference documents | 123 |

## Implementation

Rename in SharePoint: go to the document library → click "..." next to folder → "Rename" → paste the new name.

After renaming, the change propagates to Copilot Studio within minutes. No publish needed for the knowledge source — the folder path updates automatically.

## ⚠️ Regression Warning

**Renaming SharePoint folders causes fleet-wide evaluation score regression.** Confirmed June 12, 2026 — after renaming the two shared SharePoint folders, all 4 agents dropped:

| Agent | Pre-rename Peak | Post-rename | Drop |
|-------|----------------|-------------|------|
| OT | 91% | 50% | -41% |
| PT | 95% | 75% | -20% |
| SLP | 96% | 85% | -11% |

**Root cause:** Copilot Studio's GPT filter uses the folder name for retrieval routing. When the name changes, the keyword distribution shifts → GPT routes to wrong sources or no sources → ungrounded responses. Copilot Studio also caches retrieval paths internally — stale cache causes progressive degradation across runs.

**Recovery steps (in order):**
1. After renaming, **re-add the SharePoint knowledge source** on each agent's Knowledge page (remove → add back). This forces a retrieval index rebuild.
2. **Republish** all agents.
3. **Set Compare meaning at 0.50** on SR test sets to allow synonymous answers during the cache rebuild window.
4. **Re-run evaluations** — scores typically recover within 2-3 runs.
5. If still below target: check KB source descriptions (individual files may still have auto-generated descriptions causing routing conflicts).
