/**
 * Batch Instructions Injector — Playwright fill() auto-save approach
 * 
 * Injects consolidated instructions into PT, SLP, and TDA agents via CDP.
 * Uses Playwright's fill() on the contenteditable instructions editor which
 * auto-saves without needing Space+Backspace (pitfall 0b.1 in SKILL.md).
 * 
 * Prerequisites:
 *   - Chrome running with --remote-debugging-port=9223
 *   - Authenticated session on copilotstudio.microsoft.com
 *   - playwright-core installed: npm install playwright-core
 *   - Instruction files in D:/my agents copilot studio/
 * 
 * Usage:
 *   NODE_PATH="C:/Users/kevin/AppData/Roaming/npm/node_modules" node batch_inject_instructions.cjs
 *   NODE_PATH="C:/Users/kevin/AppData/Roaming/npm/node_modules" node batch_inject_instructions.cjs PT
 *   NODE_PATH="C:/Users/kevin/AppData/Roaming/npm/node_modules" node batch_inject_instructions.cjs SLP TDA
 */

const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const ENV = 'Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f';
const BASE = 'https://copilotstudio.microsoft.com/environments/' + ENV + '/bots';

const AGENTS = {
    PT: {
        id: '593407f3-539b-490f-84ac-d74e13216c81',
        file: 'D:/my agents copilot studio/pt_instructions_consolidated.txt',
        name: 'PT_Specialist',
        editYRange: [750, 950],  // Instructions Edit button y-coordinate range
    },
    SLP: {
        id: '6e437a77-a5dc-4984-90eb-4924eab10006',
        file: 'D:/my agents copilot studio/slp_instructions_consolidated.txt',
        name: 'SLP_Specialist',
        editYRange: [850, 950],
    },
    TDA: {
        id: '4d0ed0d3-30f6-f011-8406-000d3a37eba2',
        file: 'D:/my agents copilot studio/tda_instructions_consolidated.txt',
        name: 'TDA_Specialist',
        editYRange: [750, 950],
    },
    OT: {
        id: '73b45e98-af7a-443a-aa12-6d8a05118530',
        file: 'D:/my agents copilot studio/ot_instructions_v9_final.txt',
        name: 'OT_Specialist',
        editYRange: [850, 950],
    },
};

async function injectAgent(page, agentKey) {
    const agent = AGENTS[agentKey];
    if (!agent) {
        console.error(`Unknown agent: ${agentKey}`);
        return false;
    }

    // Read instructions file
    if (!fs.existsSync(agent.file)) {
        console.error(`[${agentKey}] File not found: ${agent.file}`);
        return false;
    }
    const instructions = fs.readFileSync(agent.file, 'utf8').replace(/\r\n/g, '\n').trim();
    console.log(`[${agentKey}] Loaded ${instructions.length} chars from ${path.basename(agent.file)}`);

    // Navigate to Overview
    const url = `${BASE}/${agent.id}/overview`;
    console.log(`[${agentKey}] Navigating to Overview...`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(15000);  // SPA needs time

    // Dismiss any overlays (What's New, onboarding)
    await page.evaluate(() => {
        const closeBtns = Array.from(document.querySelectorAll('button'))
            .filter(b => {
                const t = b.textContent?.trim()?.toLowerCase() || '';
                const r = b.getBoundingClientRect();
                return (t === 'close' || t === 'dismiss' || t === 'got it' || t === 'skip') 
                    && r.width > 0 && r.width < 100;
            });
        closeBtns.forEach(b => b.click());
    }).catch(() => {});
    await sleep(2000);

    // Find and click the Instructions Edit button (by y-coordinate range)
    console.log(`[${agentKey}] Clicking Instructions Edit button...`);
    const clicked = await page.evaluate((yRange) => {
        const btns = Array.from(document.querySelectorAll('button'));
        const editBtns = btns
            .filter(b => b.textContent?.trim() === 'Edit' && b.getBoundingClientRect().width > 0)
            .map((b, i) => ({ 
                i, 
                y: Math.round(b.getBoundingClientRect().y),
                yCenter: b.getBoundingClientRect().y + b.getBoundingClientRect().height / 2
            }));
        
        // Find Edit button in the y-coordinate range for instructions
        const target = editBtns.find(b => b.y >= yRange[0] && b.y <= yRange[1]);
        if (target) {
            btns.filter(b => b.textContent?.trim() === 'Edit')[target.i].click();
            return { clicked: true, y: target.y, index: target.i };
        }
        
        // Fallback: try Edit #1 (2nd Edit button)
        if (editBtns.length >= 2) {
            btns.filter(b => b.textContent?.trim() === 'Edit')[editBtns[1].i].click();
            return { clicked: true, y: editBtns[1].y, index: editBtns[1].i, fallback: true };
        }
        
        return { clicked: false, editBtns };
    }, agent.editYRange);

    if (!clicked.clicked) {
        console.error(`[${agentKey}] Could not find Instructions Edit button. Buttons found:`, JSON.stringify(clicked.editBtns));
        return false;
    }
    console.log(`[${agentKey}] Clicked Edit button at y=${clicked.y}${clicked.fallback ? ' (fallback)' : ''}`);

    await sleep(4000);  // Wait for React to activate editor

    // Verify editor is active (contenteditable=true or role=textbox)
    const editorActive = await page.evaluate(() => {
        const ce = document.querySelector('[contenteditable="true"]');
        const tb = document.querySelector('[role="textbox"]:not([aria-readonly="true"])');
        if (ce && ce.innerText.length > 100) return { active: true, type: 'contenteditable', length: ce.innerText.length };
        if (tb && tb.innerText.length > 100) return { active: true, type: 'textbox', length: tb.innerText.length };
        return { active: false };
    });

    if (!editorActive.active) {
        console.error(`[${agentKey}] Editor not active after click. Trying ALL-EDITS iteration...`);
        
        // Brute force: try each Edit button
        for (let i = 0; i < 4; i++) {
            await page.evaluate(idx => {
                const e = Array.from(document.querySelectorAll('button'))
                    .filter(b => b.textContent?.trim() === 'Edit')[idx];
                if (e) e.click();
            }, i);
            await sleep(3000);
            
            const check = await page.evaluate(() => {
                const ce = document.querySelector('[contenteditable="true"]');
                const tb = document.querySelector('[role="textbox"]:not([aria-readonly="true"])');
                if (ce && ce.innerText.length > 100) return true;
                if (tb && tb.innerText.length > 100) return true;
                return false;
            });
            
            if (check) {
                console.log(`[${agentKey}] Editor activated via Edit #${i}`);
                break;
            }
            
            // Cancel and try next
            await page.evaluate(() => {
                const b = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent?.trim() === 'Cancel');
                if (b) b.click();
            });
            await sleep(1500);
        }
    }

    // Set unique ID on the editor for reliable targeting
    await page.evaluate(() => {
        const divs = document.querySelectorAll('[contenteditable="true"], div[role="textbox"]');
        for (const div of divs) {
            if (div.innerText.length > 100) {
                div.id = 'agent-instructions-editor';
                return true;
            }
        }
        return false;
    });

    // Fill instructions — this auto-saves!
    const locator = page.locator('#agent-instructions-editor');
    try {
        await locator.fill(instructions);
        console.log(`[${agentKey}] fill() completed`);
    } catch (e) {
        console.error(`[${agentKey}] fill() failed: ${e.message}`);
        return false;
    }

    await sleep(2000);

    // Verify content persisted
    const verifyResult = await page.evaluate(() => {
        const editor = document.querySelector('#agent-instructions-editor');
        if (!editor) return { verified: false, reason: 'editor not found' };
        const text = editor.innerText || '';
        return { 
            verified: text.length > 200,
            length: text.length,
            snippet: text.substring(0, 100)
        };
    });

    if (!verifyResult.verified) {
        console.error(`[${agentKey}] Verification failed:`, JSON.stringify(verifyResult));
        return false;
    }
    console.log(`[${agentKey}] Verified: ${verifyResult.length} chars in editor`);
    console.log(`[${agentKey}] Preview: ${verifyResult.snippet.substring(0, 80)}...`);

    // Click Cancel to close edit mode (changes already saved via fill())
    await page.evaluate(() => {
        const b = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent?.trim() === 'Cancel');
        if (b) b.click();
    });
    await sleep(2000);

    // Now publish
    console.log(`[${agentKey}] Publishing...`);
    const published = await page.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent?.trim() === 'Publish' && b.getBoundingClientRect().width > 0);
        if (btn) { btn.click(); return true; }
        return false;
    });

    if (!published) {
        console.log(`[${agentKey}] Publish button not found (may already be published)`);
    } else {
        await sleep(8000);
        const publishCheck = await page.evaluate(() => {
            return (document.body?.innerText || '').includes('Published');
        });
        console.log(`[${agentKey}] Publish ${publishCheck ? 'confirmed' : 'uncertain'}`);
    }

    console.log(`[${agentKey}] DONE ✓`);
    return true;
}

async function main() {
    // Parse CLI args for specific agents
    const args = process.argv.slice(2).map(a => a.toUpperCase());
    const targets = args.length > 0 ? args.filter(a => AGENTS[a]) : ['PT', 'SLP', 'TDA'];

    console.log(`Target agents: ${targets.join(', ')}`);
    console.log(`Connecting to CDP on port 9223...`);

    let browser;
    try {
        browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
    } catch (e) {
        console.error('CDP connection failed:', e.message);
        console.error('Make sure Chrome is running with --remote-debugging-port=9223');
        process.exit(1);
    }

    const context = browser.contexts()[0];
    const page = context.pages()[0];

    if (!page) {
        console.error('No pages open in Chrome. Open copilotstudio.microsoft.com first.');
        process.exit(1);
    }

    // Check if we're on Copilot Studio
    const currentUrl = page.url();
    console.log(`Current page: ${currentUrl}`);

    const results = {};
    for (const agent of targets) {
        console.log(`\n${'='.repeat(50)}`);
        console.log(`INJECTING: ${agent}`);
        console.log(`${'='.repeat(50)}`);
        results[agent] = await injectAgent(page, agent);
    }

    // Summary
    console.log(`\n${'='.repeat(50)}`);
    console.log('SUMMARY');
    console.log(`${'='.repeat(50)}`);
    for (const [agent, ok] of Object.entries(results)) {
        console.log(`  ${agent}: ${ok ? '✓ SUCCESS' : '✗ FAILED'}`);
    }

    // NOTE: Do NOT close browser — keeps MSAL auth alive
    process.exit(0);
}

main().catch(e => {
    console.error('Fatal:', e.message);
    process.exit(1);
});
