# Cross-Agent Knowledge Source Comparison Workflow

## Use Case
You need to audit knowledge sources across multiple Copilot Studio agents to find duplicates, gaps, and incorrectly named sources. This workflow extracts KB sources from all agents programmatically and compares them.

## Prerequisites
- Playwright persistent auth (storageState with Power Platform cookies)
- Bot IDs for all agents (Overview page URL)
- Headless Chrome with terminal(timeout=120) or GUI Chrome with terminal(timeout=180)

## Workflow

### Step 1: Extract All Agents' KB Sources

```javascript
const { chromium } = require('playwright-core');
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ storageState: 'path/to/auth.json' });
const page = await ctx.newPage();

const agents = [
  ['OT', '73b45e98-af7a-443a-aa12-6d8a05118530'],
  ['PT', '593407f3-539b-490f-84ac-d74e13216c81'],
  ['SLP', '6e437a77-a5dc-4984-90eb-4924eab10006'],
  ['TDA', '4d0ed0d3-30f6-f011-8406-000d3a37eba2'],
];

const envId = 'Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f';

for (const [name, botId] of agents) {
  await page.goto(`https://copilotstudio.microsoft.com/environments/${envId}/bots/${botId}/knowledge`, { timeout: 30000 });
  await page.waitForTimeout(10000);

  // Dismiss all popups
  for (let i = 0; i < 5; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(200); }
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      const t = (b.textContent || '').trim();
      if (['Got it', 'Skip', 'Dismiss', 'Close', 'OK', 'Confirm'].includes(t)) b.click();
    }
  });
  await page.waitForTimeout(3000);

  const text = await page.evaluate(() => document.body?.innerText || '');
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 10 && l.length < 100);
  const keywords = ['AOTA', 'APTA', 'ASHA', 'CMS', 'Medicare', 'Medicaid', 'PDPM', 'MDS',
    'CPG', 'NINDS', 'CDC', 'AM-PAC', 'Pacific Coast', 'Core Clinical', 'Therapy',
    'Documentation', 'Scope', 'Standards', 'Practice', 'NOMS', 'Dysphagia', 'Common',
    'Compliance', 'Ensign', 'Joint Consensus', 'Section GG', 'Fall', 'Patterns'];

  const sources = lines.filter(l => keywords.some(k => l.includes(k)));
  console.log(`\n${name} (${sources.length} sources):`);
  sources.forEach((s, i) => console.log(`  ${i + 1}. ${s}`));
}
```

### Step 2: Compare Across Agents

Look for these patterns:

| Pattern | Example | Action |
|---------|---------|--------|
| Exact duplicate (same file in multiple agents) | Joint Consensus in PT + TDA | Keep in one, add to SharePoint if shared |
| Content duplicate (file + SharePoint) | CMS MDS uploaded + Core Clinical Manuals SP | Remove file, keep SharePoint |
| Content duplicate (website + file) | ASHA Practice Portal + scraped ASHA text | Remove scraped files, keep website |
| Missing source | Joint Consensus in PT/TDA but not OT | Add to OT |
| Unique useful source | Ensign 7 Habits (TDA only) | Keep in that agent only |
| Stale/low-quality source | Old guidance, orphan refs | Remove if better SP version exists |

### Step 3: Verify Against SharePoint

SharePoint sources show the folder path. Navigate to the SharePoint folder to list what's actually inside:

```javascript
// Use the SharePoint URL from the agent's knowledge source details
await page.goto('https://ensignservices.sharepoint.com/teams/{site}/Shared%20Documents/{folder}', { timeout: 30000 });
await page.waitForTimeout(10000);

const spText = await page.evaluate(() => document.body?.innerText || '');
```

The SPA typically requires the `:f:/r/` URL format:
`https://ensignservices.sharepoint.com/:f:/r/sites/{site}/{library}/{folder}`

When Playwright opens the folder, the file listing appears as a table with Name, Modified columns.

### SPA Rendering Issues

- The Knowledge page SPA sometimes renders the **test chat panel** instead of the source list. If body.innerText shows test conversation text ("Bot said: ...", "Connectivity Status: Connected"), navigate to `/knowledge` URL specifically and dismiss all popups.
- Sidebar tabs have DOUBLED text (e.g., "Knowledge   +7Knowledge") — use `.includes()` for matching.
- SharePoint site may redirect to login. The persistent auth may not include SharePoint cookies (only Power Platform). Workaround: navigate via the Copilot Studio knowledge source details panel which uses the authenticated session.

## Agent Status Reference (current as of June 2026)

| Agent | Sources | Type Count |
|-------|---------|------------|
| OT | 12 | 10 Public websites + 2 SharePoint |
| PT | 11 | Files + websites + SharePoint |
| SLP | 7 | Websites + SharePoint + Lean unique files |
| TDA | 10+ | Mostly files + 2 SharePoint |

OT has no uploaded files — all sources are either public websites or SharePoint. This means OT's dedup issues are minimal.

## Detecting Generic Descriptions

Microsoft auto-generates descriptions like: "This knowledge source searches information contained in [filename].txt"

Flag text patterns:
- `searches information contained in` — generic
- `searches the` — generic
- Empty or < 5 chars — blank

Per MS Learn: descriptions are the retrieval router when >25 sources. But even under 25, specific descriptions improve routing quality.
