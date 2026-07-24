# KB-First Triage & Compare Meaning Pre-Conditions

## Rule (enforced across all four agents — SLP/OT/PT/TDA)

KB quality → Compare meaning (SR only) → Instructions

Do NOT change agent instructions before confirming KB quality.

## KB Description Audit Checklist

KB descriptions act as retrieval router hints for GPT. Blank or keyword-poor descriptions cause ungrounded/random retrieval.

1. Navigate to agent Knowledge page: `.../bots/<botId>/knowledge`
2. List all sources; for each check detail page: `.../knowledge/<sourceId>/details`
3. Verify each source has a populated description (>50 chars, keyword-rich)
4. Rename SharePoint source folder names — the folder name IS the description
5. Remove duplicate sources — duplicates waste the 25-slot limit and confuse retrieval
6. Target: 15-20 keyword-rich, non-overlapping sources per agent

## Compare Meaning (SR Test Sets Only)

SR (Single Response) test sets can use Compare meaning grading:
- Pass score: 50/100 (0.50 similarity threshold)
- Requires expected responses in test cases
- Not available for Conversation data type (Conversation uses General quality only)

To set:
1. Go to evaluation config: `.../evaluation/configsDetails/<configId>`
2. Scroll to "Configure test set" → "Add test method"
3. Select "Compare meaning" → OK
4. Set Pass score to 50 → OK
5. Save

## Whole-Agent Status (June 13, 2026)

| Agent | Conv | SR | Status |
|-------|------|-----|--------|
| TDA | 95% | 95% | ALL PASS |
| SLP | 95% | 85% | SR needs Compare meaning |
| PT | 92% | 92% | Both below 95% |
| OT | 85% | 82% | Both need KB+instruction work |

SLP Conversation baseline: 95% with all caregiver guard topics OFF + new Caregiver Documentation Compliance Audit topic ON.
