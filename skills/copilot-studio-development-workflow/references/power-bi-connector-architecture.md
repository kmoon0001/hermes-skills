# Power BI Connector Architecture for Copilot Studio Agents

## Overview

Connecting Power BI dashboards to Copilot Studio agents enables natural-language
queries against live clinical/operational data. Per Microsoft Learn, this uses
the Power Platform connector framework with the Power BI REST API.

## Architecture

```
Copilot Studio Agent
  -> Power BI Connector Action (Power Platform connector)
    -> Power BI REST API (Execute Queries endpoint)
      -> Semantic Model (hosted on Fabric/Premium capacity)
        -> DAX Query -> JSON Response (max 500KB)
```

## Authentication: Service Principal (Option A — recommended for healthcare)

Per MS Learn: service principal auth is the correct approach for healthcare AI
agents because it avoids per-user OAuth flows and provides consistent access.

### Prerequisites

1. **Azure AD App Registration** (Microsoft Entra ID)
   - Name: descriptive (e.g., "QM Coach V2 Power BI Connector")
   - Save: Application (client) ID, Tenant ID

2. **Client Secret**
   - Certificates & secrets -> New secret
   - Save the value immediately (shown only once)

3. **API Permissions**
   - Power BI Service -> Dataset.Read.All, Workspace.Read.All
   - Grant admin consent

4. **Tenant Settings** (Power BI Admin Portal at admin.power.microsoft.com)
   - Developer settings: "Allow service principals to use Power BI APIs" = ON
   - Developer settings: "Dataset Execute Queries REST API" = ON
   - Integration settings: "Allow XMLA endpoints" = ON (for Arrow API)

5. **Workspace Access**
   - Add service principal to the workspace as Contributor (minimum)
   - This grants access to semantic models in that workspace

### Copilot Studio Connection Setup

1. Navigate to Power Apps (make.powerapps.com) — NOT Copilot Studio
   (Per MS Learn: "If you're using Copilot Studio, the connector must be
   defined using Power Apps or Power Automate. Then it can be used in
   Copilot Studio.")
2. Connections -> + New connection -> Search "Power BI"
3. Select authentication type: Service Principal
4. Enter: Client ID, Client Secret, Tenant ID
5. Create the connection

### Adding to Copilot Studio Agent

1. In Copilot Studio -> Agent -> Tools -> Add tool
2. Select the Power BI connection
3. Choose action: "Run a query against a dataset" (or similar)
4. Configure inputs: Workspace ID, Dataset ID, DAX Query
5. Map to a topic or use as agent-wide action

## Connector Response Limit (500KB)

Per MS Learn:
> "The connector request to the service returns more than 500 KB of data.
> This amount exceeds the Copilot Studio connector response limit."

**Fix:** Configure connector action inputs to filter data:
- Use DAX `TOPN()` to limit rows
- Use `SUMMARIZE()` to reduce columns
- Use `FILTER()` to narrow results
- Set `Limit` input parameter on the connector

## DAX Query Patterns for Healthcare QM

### Level 1: Facility QMs (declining measures)
```dax
EVALUATE
FILTER(
  SUMMARIZE(
    'QualityMeasures',
    'QualityMeasures'[MeasureName],
    'QualityMeasures'[CurrentRate],
    'QualityMeasures'[PriorRate],
    'QualityMeasures'[Trend]
  ),
  'QualityMeasures'[CurrentRate] < 'QualityMeasures'[PriorRate]
)
```

### Level 2: Patient-level (individuals driving declines)
```dax
EVALUATE
TOPN(
  20,
  FILTER(
    'PatientOutcomes',
    'PatientOutcomes'[TotalDeclined] > 0
  ),
  'PatientOutcomes'[TotalDeclined], DESC
)
```

### Level 3: General QM trends vs benchmarks
```dax
EVALUATE
SUMMARIZE(
  'QualityMeasures',
  'QualityMeasures'[MeasureName],
  'QualityMeasures'[NationalAvg],
  'QualityMeasures'[FacilityRate],
  'QualityMeasures'[StarRating]
)
```

## Two REST API Endpoints

| Endpoint | Format | Capacity | Best For |
|----------|--------|----------|----------|
| Execute Queries | JSON | Pro, PPU, Premium/Fabric | Small queries, Power Automate, Copilot Studio |
| Execute DAX Queries | Arrow IPC | Premium/Fabric only | Large results, analytics pipelines |

For Copilot Studio connector actions, use the **Execute Queries (JSON)**
endpoint. It works on all capacity types and returns JSON that the connector
can parse directly.

## HIPAA Compliance for Data Connectors

Per healthcare AI guidelines:
- Use aggregate facility data in general responses
- Patient-level data only through approved secure workflow
- Minimum necessary principle — filter DAX queries to return only needed data
- Mask patient names in responses (initials + ID only)
- Limit patient-level queries to 20 rows max
- Log all data access for audit trail
- Require facility confirmation before patient-level queries
- Include "DRAFT - CLINICAL REVIEW REQUIRED" on clinical recommendations

## Cross-Referencing with Clinical Protocols

When the agent detects declining QMs via Power BI data, it should cross-reference
with clinical protocol knowledge sources already in the agent's knowledge base:

| Declining QM | Clinical Protocol to Reference |
|--------------|-------------------------------|
| Functional decline (GG) | Low Vision, Contracture Management, Sensory Integration |
| Pressure ulcers | Wound care protocols |
| Antipsychotic use | Sensory Integration |
| Falls with injury | Low Vision, Contracture Management |
| Walking ability decline | Contracture Management |
| Nutrition/hydration | Nutrition and Hydration protocol |

The agent should:
1. Identify declining QM from Power BI data
2. Match to relevant clinical protocol
3. Provide specific intervention recommendations
4. Structure as actionable therapy plan

## Common Pitfalls

1. **Creating connector in Copilot Studio directly** — MS Learn says to create
   in Power Apps first, then use in Copilot Studio
2. **Forgetting workspace access** — Service principal must be added to the
   workspace, not just have API permissions
3. **Not filtering responses** — 500KB limit causes 400 errors on large datasets
4. **Using Arrow API for Copilot Studio** — Use JSON endpoint (Execute Queries),
   not Arrow (Execute DAX Queries)
5. **Missing tenant settings** — "Allow service principals to use Power BI APIs"
   must be enabled at the tenant level
6. **Patient data in chat** — Always mask PHI, use aggregate data when possible

## References

- MS Learn: Fix connector request failure (500KB limit)
  https://learn.microsoft.com/troubleshoot/power-platform/copilot-studio/actions/connector-request-failure
- MS Learn: Execute Queries REST API
  https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries
- MS Learn: Execute DAX Queries REST API
  https://learn.microsoft.com/power-bi/developer/execute-dax-queries-arrow/overview
- MS Learn: Service principal for Power BI
  https://learn.microsoft.com/power-bi/developer/embedded/service-principal-profile-sdk
- MS Learn: Connector actions in Copilot Studio
  https://learn.microsoft.com/training/modules/extend-declarative-agents-connector-actions-copilot-studio/
