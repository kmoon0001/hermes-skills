# Gateway API Eval Scripts (created July 2026)

## Scripts
All at `D:\my agents copilot studio\pipeline\scripts\`:

| Script | Purpose |
|--------|---------|
| `check_medicare_eval.cjs` | Query recent eval runs for any bot by bot ID. Fetches runs, scores, failure details |
| `run_conv_eval.cjs` | Launch a Conv eval via gateway API, poll until complete, report score |
| `poll_eval.cjs` | Poll an active eval run for progress |
| `check_conv_detail.cjs` | Dump full case-by-case Conv results with per-turn queries, answers, and grader scores |

## Auth
All scripts use the manage-agent MSAL cache at `~/.copilot-studio-cli/manage-agent.cache.json`.
Run with `cd "D:/my agents copilot studio/pipeline" && node scripts/<name>.cjs`

## Key Constants (edit per bot)
```javascript
const TENANT='03cc92c3-986c-4cf4-ae27-1478cf99d17f';
const CLIENT='51f81489-12ee-4a9e-aaae-a2591f45987d';
const GW='https://powervamg.us-il106.gateway.prod.island.powerapps.com';
const ENV='a944fdf0-0d2e-e14d-8a73-0f5ffae23315';  // Raw GUID, NOT Default- prefixed
const BOT_ID='b0346795-4876-f111-ab0e-70a8a5b1b8cc';
```

## Debugging Token Issues
- MSAL cache is DPAPI-encrypted, run with same Windows user
- Install msal deps: `npm install @azure/msal-node @azure/msal-node-extensions`
- Run from pipeline dir (has node_modules/)
- `echo "" |` prefix NOT needed when running directly (only for MSYS stdin workaround)

## Failure Pattern Detection
```javascript
// Conv eval loop detection
for (const c of cases) {
  for (const q of c.queries) {
    if (q.answer.includes('upload') && (q.query.includes('here is') || q.query.includes('attached'))) {
      // Loop B: FilePrebuiltEntity re-prompt loop
    }
  }
}
```
