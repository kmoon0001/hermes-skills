/**
 * US News NOT FOUND retry script.
 *
 * Reads a facility file (row|name|city|state[|rating]) and retries up to 5 times
 * per facility, trying the PRIMARY search name first, then any ALT names.
 * This catches common scraper misses where US News indexes by CMS provider name
 * rather than the operational name in the spreadsheet.
 *
 * Usage:
 *   node scripts/not-found-retry-with-alt-names.cjs [input_file]
 *
 * Input format (pipe-delimited, one facility per line):
 *   371|Heritage Park Rehabilitation and Healthcare Center|Roy|Utah|As Expected
 *
 * The script auto-resumes via state file. Tries up to 5 retries per search name.
 * If the primary name gets 0 matches, it falls through to each alt name.
 * If all names + retries fail, final rating is "NOT FOUND" (genuinely unlisted).
 *
 * Paths are hardcoded for the desktop workflow. Adjust CANARY_PATH, RESULTS_FILE,
 * LOG_FILE, and STATE_FILE as needed.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const CANARY_PATH = 'C:\\Users\\kevin\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe';
const RESULTS_FILE = 'C:\\Users\\kevin\\Desktop\\usnews_retry_notfound_results.csv';
const LOG_FILE = 'C:\\Users\\kevin\\Desktop\\usnews_retry_notfound_log.txt';
const STATE_FILE = 'C:\\Users\\kevin\\Desktop\\usnews_retry_notfound_state.json';

const stateAbbr = {
  'Alabama':'AL','Alaska':'AK','Arizona':'AZ','California':'CA','Colorado':'CO',
  'Idaho':'ID','Iowa':'IA','Kansas':'KS','Nebraska':'NE','Nevada':'NV',
  'Oregon':'OR','South Carolina':'SC','Tennessee':'TN','Texas':'TX',
  'Utah':'UT','Washington':'WA','Wisconsin':'WI'
};

// --- Example facility list with alt names ---
// Replace with your own data. The 'alt' array holds CMS provider names or alternative
// search names if the primary operational name doesn't match.
const facilities = [
  { row:'371', name:'Heritage Park Rehabilitation and Healthcare Center', alt:['Heritage Park Healthcare and Rehabilitation'], city:'Roy', state:'Utah' },
  { row:'434', name:'The Health Center of Eastview', alt:['The Healthcare Center of Eastview'], city:'Birmingham', state:'Alabama' },
];

function log(m) {
  const l = `[${new Date().toISOString()}] ${m}`;
  console.log(l);
  fs.appendFileSync(LOG_FILE, l + '\n');
}

log(`Loaded ${facilities.length} facilities for retry`);

let startIdx = 0;
if (fs.existsSync(STATE_FILE)) {
  try { startIdx = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8')).lastIndex + 1; log(`Resuming from ${startIdx}`); }
  catch(e) { log('State corrupt, starting fresh'); }
}

(async () => {
  const browser = await chromium.launch({
    executablePath: CANARY_PATH, headless: false,
    args: ['--headless=new', '--no-sandbox', '--disable-blink-features=AutomationControlled',
      '--disable-http2',
      '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36']
  });
  const page = await browser.newPage();
  await page.addInitScript(() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); });

  try { await page.goto('https://health.usnews.com/best-nursing-homes', { waitUntil:'domcontentloaded', timeout:15000 }); await page.waitForTimeout(3000); }
  catch(e) { log(`Warm-up: ${e.message.substring(0,60)}`); }

  if (startIdx === 0) fs.writeFileSync(RESULTS_FILE, 'row|name|city|state|rating|searched_as\n');

  for (let i = startIdx; i < facilities.length; i++) {
    const f = facilities[i];
    const st = stateAbbr[f.state] || f.state.slice(0,2).toUpperCase();
    let finalRating = 'NOT FOUND', foundVia = '';
    const searchNames = [f.name, ...(f.alt || [])];

    for (const searchName of searchNames) {
      if (finalRating !== 'NOT FOUND' && finalRating !== 'ERROR') break;
      const url = `https://health.usnews.com/best-nursing-homes/search?name=${encodeURIComponent(searchName)}&location=${encodeURIComponent(f.city)},+${st}`;
      for (let retry = 0; retry < 5; retry++) {
        try {
          log(`[${i+1}/${facilities.length}] (try ${retry+1}) "${searchName}" for ${f.row}`);
          const resp = await page.goto(url, { waitUntil:'domcontentloaded', timeout:30000 });
          if (!resp) throw new Error('No response');
          await page.waitForTimeout(4000);
          const text = await page.evaluate(() => document.body.innerText);
          if (text.includes('0 match') || text.includes('0 nursing homes')) {
            log(`  -> 0 matches for "${searchName}"`);
            break; // try next alt name
          } else if (text.includes('High Performing')) { finalRating = 'High Performing'; foundVia = searchName; break; }
          else if (text.includes('As Expected')) { finalRating = 'As Expected'; foundVia = searchName; break; }
          else if (text.includes('not rated') || text.includes('insufficient resident outcomes')) { finalRating = 'NOT RATED'; foundVia = searchName; break; }
          else { finalRating = 'NOT FOUND'; foundVia = searchName; break; }
        } catch(err) {
          log(`  RETRY ${retry+1}: ${err.message.substring(0,80)}`);
          await page.waitForTimeout(5000 * (retry+1));
        }
      }
    }

    log(`  -> ${finalRating}${foundVia ? ` (found as "${foundVia}")` : ''}`);
    fs.appendFileSync(RESULTS_FILE, `${f.row}|${f.name}|${f.city}|${f.state}|${finalRating}|${foundVia}\n`);
    fs.writeFileSync(STATE_FILE, JSON.stringify({ lastIndex: i, ts: new Date().toISOString() }));
    await page.waitForTimeout(4000 + Math.random() * 4000);
  }

  await browser.close();
  if (fs.existsSync(STATE_FILE)) fs.unlinkSync(STATE_FILE);
  log('\nDone.');
})().catch(e => { console.error(e); process.exit(1); });
