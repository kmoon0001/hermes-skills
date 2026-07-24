# Habit Quick Reference — Names and Descriptions

These 8 files are Dataverse `botcomponents` on the Therapy Documentation Audit Agent (TDA)
that exist in Dataverse but do NOT surface in the Copilot Studio Knowledge UI tabs.
They can only be renamed via Dataverse Web API PATCH.

## Target Names and Descriptions

| Component ID | New Name | Description |
|-------------|----------|-------------|
| `5b300971-...` | Habit 1 Quick Reference | Foundational clinical documentation habits for therapy compliance. Use when training clinicians on basic documentation best practices. |
| `37de7941-...` | Habit 2 Quick Reference | Structured note organization for compliant therapy documentation. Use for guidance on note framework and sequencing. |
| `de1e8675-...` | Habit 3 Quick Reference | Objective measurement and functional outcome documentation. Use when documenting standardized assessments and progress data. |
| `6c69fe45-...` | Habit 4 Quick Reference | Skilled service justification and medical necessity language. Use when validating skilled intervention rationale. |
| `e2b7933e-...` | Habit 5 Quick Reference | Denial risk reduction strategies and documentation red flags. Use for pre-submission compliance checks. |
| `bb3b1aef-...` | Habit 6 Quick Reference | Interdisciplinary communication and care coordination documentation. Use for team-based documentation scenarios. |
| `1044ff57-...` | Habit 7 Quick Reference | Ongoing compliance monitoring and audit readiness. Use for maintaining continuous documentation improvement. |
| `e9cdf189-...` | Medicare Benefits Policy Manual, Chapter 15 | Covered medical and other health services for therapy providers. Use when verifying Medicare Part B therapy coverage, medical necessity, and benefit limitations. |

## Dataverse Web API PATCH Template

```javascript
// Requires an OAuth token for the Dataverse org (e.g., org3353a370.crm.dynamics.com)
// Token can be obtained from MSAL.js localStorage or pac auth

const files = [
  {id: "5b300971-...", name: "Habit 1 Quick Reference", desc: "Foundational clinical documentation habits..."},
  // ... add all 8 files
];

const apiUrl = "https://org3353a370.crm.dynamics.com/api/data/v9.2/botcomponents";

async function patchFile(idx) {
  if (idx >= files.length) return "DONE";
  const f = files[idx];
  const res = await fetch(apiUrl + "(" + f.id + ")", {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'OData-MaxVersion': '4.0',
      'OData-Version': '4.0'
    },
    body: JSON.stringify({name: f.name, description: f.desc})
  });
  console.log(f.name + (res.ok ? ' ✅' : ' ❌'));
  return patchFile(idx + 1);
}
patchFile(0);
```

## How to Get the Token

The token must be fetched from the MSAL cache in a page that has authenticated against the
target Dataverse org. Navigate to a Copilot Studio page in a browser session that's logged in,
then extract from localStorage:

```javascript
// In the browser console:
for (let i = 0; i < localStorage.length; i++) {
  let k = localStorage.key(i);
  if (k.includes('org3353a370') && k.includes('accesstoken')) {
    let entry = JSON.parse(localStorage.getItem(k));
    console.log(entry.secret); // This is the Bearer token
  }
}
```
