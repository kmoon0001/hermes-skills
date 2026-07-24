---
name: powerautomate-office-scripts
description: Create Power Automate flows that use Office Scripts (TypeScript) for custom logic — PHI scrubbing, data transformation, SBAR formatting. Zero cold start, free with M365 license, HIPAA in-tenant.
category: productivity
---

# Power Automate — Office Scripts Pattern

## When to Use
- Any Power Automate flow step that needs custom code (string manipulation, regex, JSON transform, date logic)
- PHI scrubbing before clinical payloads cross agent boundaries
- Replacing Azure Function cold-start latency with M365-native execution

## Why Office Scripts (Not Azure Functions, Not C# Actions)
- **Zero cold start** — runs inside M365 shared pool, always warm
- **Free** — included in corporate M365 license
- **In-tenant HIPAA boundary** — data never leaves the Entra ID tenant
- **TypeScript** — same language as repo tooling

## Authoring Pattern

### 1. Write Script
```typescript
function main(workbook: ExcelScript.Workbook, inputJson: string): string {
  const payload = JSON.parse(inputJson);
  // ... transform ...
  return JSON.stringify({ result: payload });
}
```

### 2. Upload via Excel Online
Automate → Code editor → paste content → save

### 3. Connect in Power Automate
Add **Excel Online (Business) → Run script** action → map `inputJson` parameter → use `result` output

### 4. PHI Scrubbing Reference
```
scratch/ScrubPHI.ts
```
Redacts: Names, Dates, Phone, Email, SSN, MRN, Address (HIPAA Safe Harbor identifiers)

## Flow Creation via Playwright (Hermes browser tool)

Use `browser` tool to automate flow creation in Power Automate portal:
1. Navigate to flow.microsoft.com
2. Create new flow with manual trigger
3. Add Excel Online → Run script step
4. Configure input/output mapping

## Validation Gate

After flow creation, manually trigger in Power Automate portal:
```
https://flow.microsoft.com/manage/environments/{envId}/flows
```
Confirm run history shows **Succeeded**.

## Hard Rules
- Script must not log or persist PHI; only return redacted output
- Always use `try/catch` and return `{ error: "...", details: "..." }` on failure
- Flow must write audit trail row after each run (Dataverse or SharePoint)
- Never hardcode credentials in scripts — use environment variables or Key Vault
