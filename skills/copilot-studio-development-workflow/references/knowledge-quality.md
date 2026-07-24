# Knowledge Source Quality — MS Learn Layer 1.5

## Why KB Quality is Layer 1.5

Per Microsoft Learn evaluation triage: **Audit knowledge source quality BEFORE investigating agent config.** Most failures come from KB gaps, not agent logic. An agent with perfect architecture will still fail without adequate KB content.

## The Retrieval Router: Descriptions

MS Learn: *"If there are more than 25 different knowledge sources, the agent filters the knowledge sources by using an internal GPT model based on the description given to the knowledge source."*

Descriptions directly control which sources get searched at query time.

| Description | Effect |
|-------------|--------|
| Blank or "SharePoint files" | GPT filter can't route → random/no retrieval |
| "CMS Ch.15 Section 220 — Skilled Therapy Documentation Requirements" | Filter routes CMS queries here specifically |

**Blank descriptions are the #1 cause of "Knowledge sources not cited" failures.** Even 2-3 descriptive words fix retrieval.

## SharePoint vs Uploaded Files — Duplicate Detection

Agents frequently have the same content from MULTIPLE sources:
1. **SharePoint folder** containing CMS PDFs (e.g., "Core Clinical Manuals for Medicare")
2. **Individually uploaded files** that are subsets of that SharePoint (e.g., "CMS MDS 3.0 Section GG", "Medicare Program Integrity Manual")
3. **Public website sources** covering the same domain (e.g., "ASHA Scope of Practice" website + scraped text files)
4. **Multiple SharePoint sources** from the same parent folder structure

### Consequences
- **Wasted source slots**: Agents max out at 25 sources in generative mode
- **Retrieval noise**: Same content from 3+ sources → context saturated → unique content doesn't fit
- **Groundedness false negatives**: Citations from the "wrong" copy get flagged
- **Score impact**: 10-15% drop from this alone

### Fix: One Canonical Source Per Content Type
1. Remove individually uploaded CMS files if SharePoint already has them
2. Remove scraped ASHA text files if ASHA Practice Portal website is added
3. Keep unique files NOT in any other source (e.g., AOTA-APTA-ASHA Joint Consensus)
4. Add descriptions to every remaining source

## Audit Checklist for All Agents

- [ ] Every source has a specific description (not blank)
- [ ] No duplicate coverage across SharePoint + files + websites
- [ ] CMS content in ONE canonical source (prefer SharePoint)
- [ ] ASHA/APTA/AOTA content in ONE canonical source (prefer website)
- [ ] Description accurately describes content (for GPT filtering)
- [ ] Official marking ON for authoritative sources (CMS, ASHA, 42 CFR)
- [ ] Total sources under 25 (generative mode limit)
- [ ] Web URLs are stable and still active

## Evaluation Score Correlation

| Eval Pattern | Likely KB Root Cause |
|--------------|---------------------|
| completeness:No + groundedness:No + no aiResultReason (SR) | "Knowledge sources not cited" — blank descriptions or duplicate sources flooding context |
| completeness:No + groundedness:No + aiResultReason mentions truncation | Multi-turn platform limit — not KB related |
| abstention:Yes | CB fallback refusal — fix CB activity string (not KB) |
| relevance:No | Wrong source being retrieved — fix description to narrow filter scope |
