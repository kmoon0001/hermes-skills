# KB Duplicate Audit — Diagnosing "Knowledge Sources Not Cited" Failures

## The Problem

Evaluation failures showing `completeness: "No"` + `groundedness: "No"` with no `aiResultReason` = "Knowledge sources not cited" false negative. The response IS relevant and complete but the grader flags missing citations.

**Root cause is often DUPLICATE knowledge sources, not missing citations.** When the same content exists in both SharePoint AND as individually uploaded files, the retrieval system:
1. Wastes slots in the 25-source limit
2. Returns the same content twice → crowds context window
3. Pushes citations out of the response window → "not cited" failure

## Audit Steps

### 1. Check Copilot Studio Knowledge tab
Navigate to each agent's Knowledge page. Note:
- All sources with their type (SharePoint, website, file)
- Whether descriptions are populated (blank = retrieval filter can't distinguish)
- Whether sources are marked "Official"

### 2. Open the SharePoint folder(s)
Get the SharePoint URL from the agent's knowledge source and open it. Compare listed files against uploaded files.

### 3. Identify duplicates
Common duplication patterns:
- Same CMS PDF uploaded individually AND present in a "Core Clinical Manuals" SharePoint
- ASHA Practice Portal website + individually scraped ASHA text files
- Same content added via both SharePoint URL AND individual file uploads

### 4. Fix
- Remove individually uploaded files that exist in SharePoint
- Keep UNIQUE files not in SharePoint (e.g., AOTA-APTA-ASHA Joint Consensus, ASHA NOMS)
- Give each remaining source a SPECIFIC description (not blank) so the GPT filter can select correctly
- MS Learn: "If more than 25 knowledge sources, the agent filters by using an internal GPT model based on the description"

### 5. Expected improvement
- Fewer sources = less retrieval noise
- Better descriptions = better source selection
- No duplicates = no citation crowding
- TDA SR typically improves from 91% → 95%+
- SLP conversation typically improves from 90% → 93%+
