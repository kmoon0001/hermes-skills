# Fleet Evaluation Score Extraction

Fast patterns for pulling evaluation scores from Copilot Studio SPA snapshots without screenshots or visual analysis.

## Quick Score Grab (single agent)

Navigate to agent evaluation page and extract scores:

```bash
# Navigate
npx playwright-cli --session cs goto ".../bots/<botId>/evaluation"
sleep 12

# Extract scores + data types
npx playwright-cli --session cs snapshot 2>/dev/null | grep -oP 'interactive chart\. [0-9]+%' | head -10

# Extract with data type context
npx playwright-cli --session cs snapshot 2>/dev/null | grep -oP '(Evaluate [A-Z_]+[^"]*|Data type: (conversation|single response))' | head -20
```

## Full Table Extraction (JS)

```bash
npx playwright-cli --session cs eval "(function(){
  var rows = document.querySelectorAll('[role=rowgroup] [role=row]');
  var results = [];
  var count=0;
  rows.forEach(function(r){
    var cells = r.querySelectorAll('[role=gridcell]');
    if(cells.length>=4 && count<10){
      results.push({
        name: cells[0].innerText.substring(0,50),
        score: cells[3].innerText.replace(/\\n/g,' ').substring(0,100)
      });
      count++;
    }
  });
  return JSON.stringify(results);
})()"
```

## Environment URL Quick Reference

Therapy AI Dev environment: `Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f`

Agent bot IDs (Therapy AI Dev):
- TDA: `4d0ed0d3-30f6-f011-8406-000d3a37eba2`
- OT: `73b45e98-af7a-443a-aa12-6d8a05118530`
- SLP: `6e437a77-a5dc-4984-90eb-4924eab10006`
- PT: `593407f3-539b-490f-84ac-d74e13216c81`

## Fleet Score Dashboard Pattern

```bash
for agent in tda ot slp pt; do
  case $agent in
    tda) bid="4d0ed0d3-30f6-f011-8406-000d3a37eba2" ;;
    ot)  bid="73b45e98-af7a-443a-aa12-6d8a05118530" ;;
    slp) bid="6e437a77-a5dc-4984-90eb-4924eab10006" ;;
    pt)  bid="593407f3-539b-490f-84ac-d74e13216c81" ;;
  esac
  echo "=== $agent ==="
  npx playwright-cli --session cs goto "https://copilotstudio.microsoft.com/environments/Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f/bots/$bid/evaluation" 2>&1 | tail -1
  sleep 10
  npx playwright-cli --session cs snapshot 2>/dev/null | grep -oP 'interactive chart\. [0-9]+%' | head -4
done
```

## Interpreting the Score Pattern

Each score appears twice in the snapshot (chart img alt text + text label). Deduplicate:

```bash
npx playwright-cli --session cs snapshot 2>/dev/null | grep -oP 'interactive chart\. [0-9]+%' | sed 's/interactive chart\. //' | sort -u
```

## Auth Refresh Before Fleet Scan

If auth is stale, refresh from Kiro Chrome CDP before scanning:

```bash
node scripts/refresh_auth.cjs
npx playwright-cli --session cs open https://example.com
npx playwright-cli --session cs state-load "C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/home/fresh_auth.json"
```
