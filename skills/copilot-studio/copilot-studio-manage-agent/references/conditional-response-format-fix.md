# Instructions Fix: Conditional RESPONSE FORMAT

## The Rule

When agent instructions force a strict compliance scoring format (e.g., "Missing = noncompliant", 5-section audit output) on ALL queries, it kills both SR and Conv scores on coaching/how-to questions. The fix is purely additive — no content removed.

## The Fix Pattern

Insert a conditional routing block BEFORE the existing format definitions. Example:

```yaml
### FORMAT SELECTION RULES (CRITICAL)
Route A — Document Uploaded/Provided: Apply the full DOCUMENT REVIEW FORMAT below (5-section audit + compliance table + scoring).
Route B — General Compliance Question (no document): Use GENERAL COMPLIANCE QUESTION FORMAT (2-3 bullets, no tables, no emojis).
Route C — Coaching/How-to Question: Give a focused natural coaching answer. Do NOT force the compliance scoring format. Answer directly from knowledge sources with inline citations.
```

## What It Changes

- **Document reviews (Route A):** Still get the full structured audit output — no loss of existing behavior.
- **General questions (Route B):** Get 2-3 bullets with citations — cleaner than forcing a 5-section table.
- **Coaching questions (Route C):** The agent gives helpful natural answers instead of a compliance matrix.

## Verified Delta

| Agent | Before | After | Change |
|-------|--------|-------|--------|
| Medicare Part B Compliance Agent (2026-07-09) | 71% SR | 81% SR | **+10 pts** |

## How to Apply

1. Read current instructions from Dataverse: `GET botcomponents where componenttype eq 15`
2. Insert the FORMAT SELECTION RULES block BEFORE the existing format sections
3. PATCH the `data` field via Dataverse API
4. Publish agent
5. Run eval to measure impact
