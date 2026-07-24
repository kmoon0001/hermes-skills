# QM Coach V2 Agent Details

## Identity
- **Name:** SimpleLTC QM Coach V2
- **Bot ID:** ea52ad9c-8233-f111-88b3-6045bd09a824
- **Environment:** Therapy AI Agents Dev (a944fdf0-0d2e-e14d-8a73-0f5ffae23315)
- **Org URL:** https://orgbd048f00.crm.dynamics.com/
- **Model:** GPT-5 Chat
- **Published:** 6/19/2026 (instructions updated)

## Purpose
Quality measure analysis and clinical coaching for SNF therapy services. Part of Pacific Coast SNF Clinical AI Fleet.

## Instructions (cleaned, injected via CDP June 19, 2026)
- 5591 chars (well under 8K limit)
- Sections: CONTENT SAFETY, ROLE, SCOPE, KNOWLEDGE SOURCES, INSTRUCTIONS, RESPONSE FORMAT, CONSTRAINTS, ERROR HANDLING, PROMPT INJECTION DEFENSE, TOPIC ROUTING, RESPONSE QUALITY
- Key improvements over original:
  - Removed CRITICAL/NEVER language
  - Consolidated duplicate error handling sections
  - Updated knowledge source list to match actual 15 sources
  - Made response format conditional (full analysis vs general questions)
  - Added MDS-specific guidance (Section GG/K/O/C/D)
  - Soft citation language
- File: D:/my agents copilot studio/qm_coach_v2_instructions_clean.md

## Knowledge Sources (15)
1. CMS Five-Star Quality Rating System
2. CMS Nursing Home Quality Measures
3. CMS Nursing Home Quality Measure Technical Specifications
4. CMS SNF QRP Measures and Technical Info
5. CMS MDS 3.0 RAI Manual
6. CMS Medicare Benefit Policy Manual Chapter 15
7. CMS Skilled Nursing Facility Prospective Payment System
8. CMS QAPI Quality Assurance and Performance Improvement
9. CMS Nursing Home Data Dictionary
10. AAPACN MDS Coordinator Resources
11. Data Dictionary for Upload and Query Workflows
12. ONE Clinical Protocol Low Vision
13. ONE Clinical Protocol Contracture Management
14. ONE Clinical Protocol Sensory Integration
15. DoR Summary Email Template and Examples

## Connected Agents
1. Pacific Coast Case Historian V2
2. Pacific-Coast Regulatory Hub V2
3. SNF AI Dashboard V2

## Topics (5 actual, 48 shown in UI from connected agents)
- DoR Summary
- QM - Accountability Matrix
- QM - Publish Output
- Sign in
- Greeting
- Power BI - Run a Query Against a Dataset (updated with TaskDialog YAML)

## Tools/Actions
- No tools connected (as of June 2026)
- Web Search: Disabled
- Work IQ: Disabled
- Power BI connector pending (user needs to add manually)

## Power BI Dashboards Available
1. CMS QM Scorecard
2. One Clinical Outcomes Dashboard
3. Therapy Margin Comparison
4. PDPM CMI Dashboard
5. Therapy Financials Overview
6. DON Daily Operations Dashboard
7. Clinical Dashboard

## Dataverse Component Counts
- Type 19 (Testing/Evaluation): 181 items
- Type 9 (Topics): 5 items
- Type 14 (Knowledge Sources): 12 items
- Type 15 (Instructions): 1 item
- Type 11 (Connected Agent): 1 item

## Known Issues
- Tools page SPA doesn't load via `/tools` URL (use overflow menu)
- Topic YAML requires `kind: TaskDialog` (not `AdaptiveDialog`) in this environment
- Power BI connector not yet added (pending user action)
- 1 Warning on agent (unknown cause)

## Last Updated
June 19, 2026
