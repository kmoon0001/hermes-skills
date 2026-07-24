# Dataverse Knowledge Source Schema (Undocumented)

This documents the reverse-engineered schema for knowledge source tracking in Dataverse's `botcomponent` table, discovered during Copilot Studio agent development.

## Where Uploaded Files Are Stored

**Uploaded files (PDFs, DOCXs) are NOT stored in `botcomponents` with `componenttype=16`.** That type is for Public Website and SharePoint *definitions*. The actual uploaded files are stored as:

- **componenttype=14** — Bot File Attachment (the actual file blob stored in Dataverse FileAttachment table)
- The file metadata (name, description) is in `botcomponent` with `componenttype=14`, but `pac org fetch` crashes on memo fields

**Alternative storage:** Many therapy agents reference files stored in **SharePoint document libraries**, linked via a SharePoint knowledge source (`componenttype=16` with `knowledgeSourceType: SharePoint`).

## Querying Knowledge Source Definitions

```bash
# List Public Website and SharePoint definitions only (NOT uploaded files)
pac org fetch --environment <env> --xml "
<fetch>
  <entity name='botcomponent'>
    <attribute name='botcomponentid'/>
    <attribute name='name'/>
    <filter>
      <condition attribute='componenttype' operator='eq' value='16'/>
      <condition attribute='parentbotid' operator='eq' value='<botId>'/>
    </filter>
  </entity>
</fetch>"
```

## Why Local Clone Commands Fail

- `pac copilot clone` — not available in v2.7.4 (only `list`, `extract-template`, `publish`, etc.)
- `pac copilot extract-template` — crashes with `System.ArgumentException` on agents with knowledge sources
- `pac org fetch` with the `content` field — crashes with `System.ArgumentOutOfRangeException` (known v2.7.4 bug with memo fields)

## Finding Uploaded Files via the Browser

Uploaded files appear ONLY in the **Files tab** of the Copilot Studio Knowledge page — NOT in the "All" view. The "All" view only shows Public Website and SharePoint sources.

Browser-based discovery URL pattern:
```
/files/knowledge/<componentId>/details
```

## Sources Found in Real Agent Inspections

### OT_Specialist (Ensign Services, 73b45e98)
Files tab shows 9 uploaded files (PDFs):
- Medicare Program Integrity Manual, Ch 3 & 5
- AOTA/APTA/ASHA Consensus Statement
- Medicare Secondary Payer Manual
- CMS Medicare Therapy Learning Network
- Medicare Benefits Policy Manual Ch 15
- 42 CFR Section 424.24
- 2025 Part B MSCA Audit Worksheet
- OT Documentation Patterns

### PT_Specialist (Ensign Services, 593407f3)
Files tab shows 7 uploaded files (PDFs):
- Medicare Benefits Policy Manual Ch 15
- Neurologic Outcome Measures CPG
- PLATINUM PT Documentation Patterns
- Medicare Claims Processing Manual Ch 5
- Medicare Secondary Payer Manual
- 2025 Part B MSCA Audit Worksheet
- Medicare Program Integrity Manual Ch 3

### Dataverse Query for Public/SharePoint Sources (PT_Specialist)
```
componenttype=16, parentbotid=593407f3-...:
  4 sources found: https://learn.microsoft.com, APTA CPG, CMS MLN, Pacific Coast SharePoint
```
