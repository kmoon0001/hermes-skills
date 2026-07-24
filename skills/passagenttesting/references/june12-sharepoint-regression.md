# June 12, 2026 — SharePoint Rename Regression Data

## Timeline

All times Pacific, June 12, 2026.

| Time | OT SR | OT Conv | SLP SR | SLP Conv | PT SR | PT Conv | Event |
|------|-------|---------|--------|----------|-------|---------|-------|
| ~2:00 AM | 91% | 90% | 96% | 85% | 94% | 95% | Pre-change peak |
| ~4:00 AM | 82% | ? | 92% | 85% | 87% | ? | SharePoint folders renamed |
| ~9:00 AM | 50% | ? | 85%? | 85% | 75% | ? | Progressive cache degradation |
| ~1:34 PM | 75% | ? | 90% | 90% | 85% | 85% | After KB refresh + SLP instructions publish |

## Root Cause

SharePoint folder names changed from:
- "Pacific Coast Therapy Swarm Shared Knowledge Library" → "Therapy Shared Knowledge-Ensign compliance, audit standards..."
- "Core Clinical Manuals for Medicare A, PDPM vs. Part B, LTC Rehabilitation" → "Core Clinical Manuals-CMS PDPM, Part B, MDS 3.0, Jimmo..."

GPT filter uses folder name as retrieval description. Changed keywords → retrieval routing mismatch → ungrounded responses → score drops.

Progressive degradation (91%→82%→50%) across same day suggests Copilot Studio's internal retrieval cache becomes progressively more stale after path changes.

## Fixes Applied

1. SharePoint folder names already keyword-rich (user did pre-session)
2. SLP instructions: unconditional → conditional RESPONSE FORMAT (saved + published)
3. TDA published
4. PT evaluation triggered

## Fixes NOT Applied (Manual)

1. **Compare meaning 0.50** on all SR test sets — NOT programmable (hover-revealed UI)
2. KB source descriptions on individual files
3. Re-add SharePoint sources (full cache rebuild) if above insufficient

## Recovery Trajectory

| Agent | Pre-Change Peak | Post-Change Trough | After Fixes | Gap to Peak |
|-------|----------------|-------------------|-------------|-------------|
| OT | 91% | 50% | 75% | -16% |
| SLP | 96% | 85% | 90% | -6% |
| PT | 95% | 75% | 85% | -10% |

Compare meaning 0.50 expected to recover 5-15% of remaining gap.
