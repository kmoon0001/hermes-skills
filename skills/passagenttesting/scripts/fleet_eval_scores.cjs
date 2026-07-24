/**
 * fleet_eval_scores.cjs
 *
 * Extract evaluation scores from all Copilot Studio agents via Playwright.
 * Pulls latest SR and Conv scores for OT, SLP, PT, TDA.
 *
 * Usage:
 *   node <hermes-home>/skills/passagenttesting/scripts/fleet_eval_scores.cjs
 *
 * Output: per-agent score table with run name, type, score, running status.
 * Saves to fleet_scores.txt in the current directory.
 *
 * Dependencies: playwright-core installed globally
 *   require('C:/Users/kevin/AppData/Roaming/npm/node_modules/playwright-core')
 *
 * Auth: .playwright-auth/state.json (expires ~hours; refresh via headed mode)
 */

const { chromium } = require('C:/Users/kevin/AppData/Roaming/npm/node_modules/playwright-core');
const fs = require('fs');
const authPath = ['D:', 'my agents copilot studio', '.playwright-auth', 'state.json'].join('/');
const envId = 'Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f';

const AGENTS = [
  { name: 'OT', id: '73b45e98-af7a-443a-aa12-6d8a05118530' },
  { name: 'SLP', id: '6e437a77-a5dc-4984-90eb-4924eab10006' },
  { name: 'PT', id: '593407f3-539b-490f-84ac-d74e13216c81' },
  { name: 'TDA', id: '4d0ed0d3-30f6-f011-8406-000d3a37eba2' },
];

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function getScores(page, botId, name) {
  await page.goto(`https://copilotstudio.microsoft.com/environments/${envId}/bots/${botId}/evaluation`, {
    timeout: 60000, waitUntil: 'domcontentloaded',
  });
  await sleep(25000);
  for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await sleep(300); }

  const body = await page.evaluate(() => document.body?.innerText || '');
  const lines = body.split('\n');

  // Detect auth failure: body < 500 chars with sign-in language
  if (body.length < 500 && body.toLowerCase().includes('sign in')) {
    console.log(`  ⚠ AUTH EXPIRED — body only ${body.length} chars`);
    return [];
  }

  const runs = [];
  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(/^(Evaluate\s+\S+)\s+(\d{6}_\d{4})$/);
    if (!match) continue;
    const runName = match[2];

    // Look ahead ~8 lines for data type and score
    let dataType = '';
    let score = '?';
    let running = false;
    for (let j = i + 1; j < Math.min(i + 10, lines.length); j++) {
      const nl = lines[j].trim().toLowerCase();
      if (nl.includes('conversation')) dataType = 'Conv';
      if (nl.includes('single response')) dataType = 'SR';
      if (nl === 'running') running = true;
      if (/^\d+%$/.test(nl)) score = nl;
    }

    // Verify type from surrounding context
    if (!dataType) {
      const ctx = body.substring(body.indexOf(runName), body.indexOf(runName) + 300).toLowerCase();
      if (ctx.includes('conversation')) dataType = 'Conv';
      else if (ctx.includes('single response')) dataType = 'SR';
    }

    if (dataType) {
      runs.push({ name: runName, type: dataType, score, running });
    }
  }
  return runs;
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--no-sandbox'],
  });
  const ctx = await browser.newContext({ storageState: authPath });
  const page = await ctx.newPage();

  const output = [];
  for (const agent of AGENTS) {
    console.log(`\n=== ${agent.name} ===`);
    const runs = await getScores(page, agent.id, agent.name);
    if (runs.length === 0) {
      output.push(`${agent.name}: NO DATA`);
      continue;
    }
    for (const r of runs.slice(0, 8)) {
      output.push(`${agent.name} | ${r.name} | ${r.type} | ${r.score}${r.running ? ' | RUNNING' : ''}`);
    }
  }

  console.log('\n--- FLEET SCORES ---');
  output.forEach(l => console.log(l));

  fs.writeFileSync('./fleet_scores.txt', output.join('\n'));
  console.log('\nSaved to fleet_scores.txt');
  await browser.close();
})();
