# Knowledge Source Description Best Practices

Source: Microsoft Learn — "Orchestrate agent behavior with generative AI"
URL: https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-generative-actions

## Why Descriptions Matter

In generative orchestration, the agent selects knowledge sources based on their **description** (not trigger phrases). A good description directly improves:
- Knowledge source selection accuracy
- Response grounding quality
- Evaluation scores for knowledge-grounded answers

## Writing Style

- Use **simple, direct language**; avoid jargon
- Write in **active voice, present tense** (e.g., "Provides CMS MDS 3.0 RAI Manual content")
- **1-2 sentences** — what it does and its benefit
- Include **keywords** that match user intent (e.g., "PDPM", "skilled therapy", "Section GG")

## Pattern

```
[Source name] provides [content]. Use when [query intent / user scenario]. Covers [key topics].
```

### Good Example

Name: **Medicare Benefit Policy Manual, Chapter 15**
> Provides CMS Medicare Benefit Policy Manual Chapter 15 on covered medical services. Use when auditing for skilled therapy criteria, reasonable and necessary services, or Medicare coverage determinations. Covers skilled PT, OT, and SLP documentation requirements.

### Bad Example (auto-generated)

> This knowledge source searches information contained in Medicare Benefits Policy Manual Chapter 15.pdf

## Additional Examples

### Medicare Program Integrity Manual, Chapter 3

Name: **Medicare Program Integrity Manual, Chapter 3: Medical Review & Program Integrity**

> Provides CMS Medicare Program Integrity Manual Chapter 3 on verifying potential fraud and abuse under Medicare. Use when auditing documentation for medical review policies, overpayment identification, provider compliance, or integrity program requirements. Covers prepayment review, postpayment review, provider enrollment screening, Medicare Secondary Payer verification, and recovery audit contractor processes.

### Medicare Program Integrity Manual, Chapter 5

Name: **Medicare Program Integrity Manual, Chapter 5: Provider Enrollment**

> Provides CMS Medicare Program Integrity Manual Chapter 5 on provider enrollment and screening. Use when auditing provider enrollment applications, verifying provider eligibility, or assessing compliance with Medicare enrollment requirements. Covers provider enrollment screening levels, provider disclosure requirements, reporting of adverse actions, re-enrollment bar policies, and revocation or deactivation of provider billing privileges.

## Disambiguation

For similar sources (e.g., two Jimmo-related sources), describe what each covers that the other does NOT:

Name: **Jimmo v. Sebelius Settlement Agreement (Filed 2013)**
> Provides the Jimmo v. Sebelius settlement agreement. Use when defending maintenance therapy coverage, challenging the improvement standard, or justifying skilled care to prevent decline. Covers the legal basis that Medicare covers maintenance therapy.

Name: **Jimmo v. Sebelius — CMS FAQs**
> Provides official CMS Frequently Asked Questions on Jimmo v. Sebelius. Use when answering questions about maintenance therapy coverage, the improvement standard, or skilled care definitions under Medicare. Covers SNF and outpatient settings.

Name: **Jimmo v. Sebelius — Program Manual Clarifications (2014)**
> Provides CMS Program Manual updates following the Jimmo settlement. Use when auditing documentation for post-Jimmo coverage criteria or regulatory compliance since 2014. Covers CMS policy changes, not the original settlement text.

## What to Avoid

- **Too vague**: "Answer Question" / "This tool can answer questions"
- **Auto-generated pattern**: "This knowledge source searches information contained in [filename]" — replace ALL of these
- **File extensions in name or description**: Remove ".pdf", ".md", ".docx" from display names
- **Jargon**: "Get EPS" instead of "Get Earnings Per Share"
- **Overlapping descriptions** for similar sources — make each one unique

### Worked Example: Microsoft Learn as a Knowledge Source

Name: **Microsoft Learn Documentation**
> Provides the official Microsoft Learn documentation library. Use when answering questions about Microsoft Copilot Studio agent configuration, Power Platform administration, or Microsoft product documentation. Covers product guides, tutorials, API references, compliance certifications, and troubleshooting for Microsoft 365, Azure, Dynamics 365, and Power Platform.

**Pitfall**: Microsoft Learn has no clinical therapy content. If the agent also has clinical knowledge sources, the description should steer MS Learn toward platform/compliance queries. Use the description to disambiguate what this source contains that other sources do NOT.

### Worked Example: Medicare Chapter 15 (Refined)

Name: **Medicare Benefit Policy Manual, Chapter 15**
> Provides CMS Medicare Benefit Policy Manual Chapter 15 on covered medical services. Use when auditing skilled therapy documentation for Medicare Part B coverage, determining reasonable and necessary criteria, or verifying qualifying service definitions. Covers skilled PT, OT, and SLP services, outpatient therapy thresholds, the therapy cap exceptions process, and supervision requirements.

**Why better than the generic version**: Specifies Part B vs Part A, adds concrete keyword phrases the orchestration engine can match ("therapy cap exceptions", "supervision requirements"), and names the three therapy disciplines explicitly.

### Worked Example: 42 CFR Section 424.24

Name: **42 CFR Section 424.24 — Therapy Services Conditions of Payment**

> Provides the Code of Federal Regulations Title 42, Volume 3, Section 424.24 governing conditions of payment for outpatient therapy services. Use when verifying regulatory compliance for Medicare Part B therapy claims, auditing signature requirements, or confirming that documentation meets conditions for payment. Covers plan of care requirements, certification and recertification periods, and physician signature rules.

**Handling technical filenames:** When the source file has a name like `CFR-2022-title42-vol3-sec424-24.pdf`, strip the year, volume prefix, and file extension. The title should read like a document name, not a file path.

### Worked Example: Interorganizational Consensus Statement

Name: **AOTA/APTA/ASHA Consensus Statement on Therapy Documentation**

> Provides the interorganizational consensus statement from AOTA, APTA, and ASHA on documentation standards for occupational, physical, and speech therapy services. Use when auditing for compliance with professional documentation standards across disciplines. Covers documentation content requirements, signature policies, frequency-of-treatment justification, and interprofessional communication standards.

**Handling acronym-heavy names:** Replace hyphens and underscores with proper spacing. Use the full organization names in the description but a shortened form in the title for readability.

### Worked Example: Medicare Secondary Payer Manual

Name: **Medicare Secondary Payer Manual — Therapy**

> Provides CMS Medicare Secondary Payer (MSP) rules as they apply to therapy services. Use when determining whether Medicare is primary or secondary payer for therapy claims, verifying coordination of benefits, or auditing MSP compliance in outpatient and SNF settings. Covers billing order requirements, conditional payments, and recovery processes for therapy services.

**Pitfall: Losing scope in the title.** The original filename `Medicare Secondary Payer Manual - therapy.pdf` correctly scoped the document to therapy services. When removing `.pdf`, preserve the scope qualifier.

## Naming Convention: "Document Name: Subtitle"

Names and descriptions are separate in Copilot Studio, but they work together. The
name determines what generative orchestration sees first; the description provides
context for selection.

### Name Pattern

```
Authority Name: Specific Topic
```

| ✅ Good | ❌ Bad |
|---------|--------|
| Medicare Program Integrity Manual, Chapter 3: Medical Review | Ch3_Medicare_Program_Integrity_Manual.pdf |
| Medicare Benefit Policy Manual, Chapter 15: Covered Medical Services | Chapter 15.pdf |
| AOTA Occupational Therapy Practice Framework | AOTA_OT_Framework_4th_Edition.pdf |
| CMS Medicare Learning Network: Therapy | MLN_Therapy_Fact_Sheet_2024.pdf |

### Cleanup Checklist

1. [ ] Name has no `.pdf`, `.docx`, `.md` file extension
2. [ ] Name has no underscores or hyphens (replace with spaces)
3. [ ] Name uses consistent "Document Name: Subtitle" format
4. [ ] Description is 1-2 sentences, active voice
3. [ ] Description includes when to use this source
4. [ ] Description includes key topic keywords
5. [ ] Description is unique (not identical to other sources)
6. [ ] File extensions removed from display name
