# Power BI Connector for Copilot Studio (Healthcare AI)

## Architecture

```
Copilot Studio Agent
  -> Power BI Connector Action (Power Platform)
    -> Power BI REST API (Execute Queries)
      -> Semantic Model (Power BI dataset)
        -> DAX Query -> JSON Response
```

## Auth: Service Principal (Recommended for Healthcare)

Per Microsoft Learn, service principal auth is preferred for healthcare AI agents because:
- No user credential delegation (HIPAA-compliant)
- Scoped access to specific datasets
- Auditable via Azure AD logs

### Prerequisites (User Must Do in Azure Portal)

1. **Register app in entra.microsoft.com**
   - App registrations → New registration
   - Name: descriptive (e.g., "QM Coach V2 Power BI Connector")
   - Save Application (client) ID and Tenant ID

2. **Create client secret**
   - Certificates & secrets → New client secret
   - Save the secret value (shown only once)

3. **Add Power BI API permissions**
   - API permissions → Power BI Service
   - Select: `Dataset.Read.All`, `Workspace.Read.All`
   - Grant admin consent

4. **Enable tenant settings** (Power BI Admin Portal)
   - Developer settings → "Allow service principals to use Power BI APIs" = ON
   - Developer settings → "Dataset Execute Queries REST API" = ON
   - Integration settings → "Allow XMLA endpoints" = ON (for Arrow API)

5. **Add service principal to workspace**
   - Open Power BI workspace → Access → Add people
   - Paste the app registration name
   - Role: Contributor (minimum)

6. **Get Workspace ID and Dataset ID**
   - From the Fabric URL or semantic model settings

### Copilot Studio Configuration (Agent Can Do)

Once the user provides Client ID, Secret, Tenant ID, and Workspace/Dataset IDs:
1. Create Power Platform connection in the environment
2. Configure the Power BI connector action in the topic
3. Set up DAX queries for each query level
4. Add input filters to stay under 500KB response limit

## Connector Response Limit (500KB)

Per Microsoft Learn: connector responses over 500KB return HTTP 400.
Fix: Configure connector action inputs to filter data:
- Use DAX `TOPN()` to limit rows
- Use `SUMMARIZE()` to reduce columns
- Set `Limit` input parameter on the connector

## Query Levels (Multi-Level Dashboard Access)

For agents that need facility-level, patient-level, and general QM data:

| Level | Purpose | DAX Pattern | HIPAA Notes |
|-------|---------|-------------|-------------|
| Facility QMs | Declining measures | `FILTER(SUMMARIZE(...), CurrentRate < PriorRate)` | Aggregate OK |
| Patient Detail | Individuals driving decline | `TOPN(20, FILTER(...), TotalDeclined, DESC)` | Mask names |
| General Trends | National benchmarks | `SUMMARIZE(..., MeasureName, NationalAvg, FacilityRate)` | Public data |

## Dashboard Pages

A single semantic model may contain multiple report pages:
- Clinical Outcomes - Current Patients
- ADLs and Ambulation
- Quality Measures Summary
- etc.

Each page can be queried independently via DAX.

## Key Pitfalls

1. **500KB response limit** — Filter aggressively. Use TOPN and SUMMARIZE.
2. **Premium/Fabric capacity required** — Execute Queries API needs Premium or Fabric capacity. Pro/PPU workspaces don't support it.
3. **Service principal must be workspace member** — Without Contributor+ role, API calls return 403.
4. **Tenant settings require admin** — "Allow service principals to use Power BI APIs" can only be enabled by Power BI admins.
5. **HIPAA: Use aggregate data in chat** — Patient-level data should use approved secure workflows, not free-text chat responses.
6. **DAX not SQL** — Power BI uses DAX (Data Analysis Expressions), not SQL. Queries use EVALUATE, FILTER, SUMMARIZE, TOPN.

## References

- https://learn.microsoft.com/power-bi/developer/execute-dax-queries-arrow/overview
- https://learn.microsoft.com/troubleshoot/power-platform/copilot-studio/actions/connector-request-failure
- https://learn.microsoft.com/training/modules/extend-declarative-agents-connector-actions-copilot-studio/
