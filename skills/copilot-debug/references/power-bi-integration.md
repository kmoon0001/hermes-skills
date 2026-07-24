# Power BI Integration with Copilot Studio

## Overview

Copilot Studio has a built-in Power BI connector for live data queries. No Power Automate flow needed.

## Two Approaches

### Option A: Knowledge Source (simple)
- Add Power BI reports as knowledge sources
- Static snapshot, not live queries

### Option B: Tool/Action (recommended)
- Built-in Power BI connector
- Live DAX queries against datasets

## Adding Power BI Connector

1. Agent → Tools page
2. "Add a tool" → "Connector"
3. Search "Power BI"
4. Select "Run a query against a dataset"
5. "Add and configure"
6. Create connection (maker credentials)
7. Select dataset(s)
8. Submit

## Tools Page SPA Issue

The `/tools` URL sometimes loads Topics instead. Workaround:
- Navigate via overflow menu (+N) → Tools

## Dataset Discovery

1. Navigate to app.powerbi.com
2. Check My Workspace, Apps, shared dashboards
3. Dataset IDs in report URLs

## Required Permissions

- Power BI: viewer access to datasets
- Copilot Studio: Bot Author + Bot Contributor

## References

- https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-connectors
- https://learn.microsoft.com/en-us/connectors/powerbi/