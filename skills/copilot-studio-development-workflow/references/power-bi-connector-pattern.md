# Power BI Connector for Copilot Studio Agents

Session: June 19, 2026 — QM Coach V2
Dashboard: "One Clinical Outcomes Dashboard" on Microsoft Fabric

## Architecture (per Microsoft Learn)

```
Copilot Studio Agent
  -> Power BI Connector Action (Power Platform)
    -> Power BI REST API (Execute Queries)
      -> Semantic Model
        -> DAX Query -> JSON Response
```

## Auth: Service Principal (Option A — recommended for healthcare)

Per MS Learn: "Allow service principals to use Power BI APIs" must be enabled in tenant Developer settings.

### Steps (user must do):
1. Register app in entra.microsoft.com → save Client ID + Tenant ID
2. Create client secret → save the value
3. Add API permissions: Dataset.Read.All, Workspace.Read.All → grant admin consent
4. Power BI Admin Portal → Tenant settings:
   - "Allow service principals to use Power BI APIs" = ON
   - "Dataset Execute Queries REST API" = ON
5. Add service principal to workspace as Contributor (minimum)
6. Get Workspace ID and Dataset ID from Fabric URL or semantic model settings

### Steps (agent does):
1. Create Power Platform connection in the environment
2. Configure connector action in topic
3. Set up DAX queries for each query level
4. Add HIPAA guardrails to responses
5. Test connection

## Connector Response Limit

Per MS Learn: "The connector request to the service returns more than 500 KB of data. This amount exceeds the Copilot Studio connector response limit."

**Fix:** Configure connector action inputs to filter data:
- Use DAX TOPN() to limit rows
- Filter to only relevant measures
- Use SUMMARIZE() to reduce columns
- Set Limit input parameter on the connector

## Multi-Level Query Pattern

For agents that need facility-level, patient-level, and general QM data:

**Level 1: Facility QMs (dropping measures)**
```dax
EVALUATE FILTER(SUMMARIZE('QualityMeasures', ...), [CurrentRate] < [PriorRate])
```

**Level 2: Patient-level (individuals driving declines)**
```dax
EVALUATE TOPN(20, FILTER('PatientOutcomes', [TotalDeclined] > 0), [TotalDeclined], DESC)
```

**Level 3: General QM trends**
```dax
EVALUATE SUMMARIZE('QualityMeasures', [MeasureName], [NationalAvg], [FacilityRate], [StarRating])
```

## Healthcare Compliance

- Use aggregate facility data in general responses
- Patient-level data only through approved secure workflow
- Minimum necessary principle
- No PHI in chat responses
- DRAFT label on all clinical recommendations
- Limit patient-level queries to 20 rows max
- Mask patient names (use initials + ID only)

## Power BI API Endpoints

- **Execute Queries (JSON):** `POST /v1.0/myorg/groups/{workspaceId}/datasets/{datasetId}/executeQueries`
  - Works on Pro, PPU, Premium/Fabric
  - Hard limit: 100,000 rows, 1,000,000 values
  - Response: JSON

- **Execute DAX Queries (Arrow):** `POST /v1.0/myorg/groups/{workspaceId}/datasets/{datasetId}/executeDaxQueries`
  - Premium or Fabric capacity only
  - No fixed row limit (use resultsetRowcountLimit)
  - Response: Apache Arrow IPC (needs pyarrow to deserialize)

## References

- https://learn.microsoft.com/power-bi/developer/execute-dax-queries-arrow/overview
- https://learn.microsoft.com/troubleshoot/power-platform/copilot-studio/actions/connector-request-failure
- https://learn.microsoft.com/training/modules/extend-declarative-agents-connector-actions-copilot-studio/
