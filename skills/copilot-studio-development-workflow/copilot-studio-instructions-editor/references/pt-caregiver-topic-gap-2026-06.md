# PT Caregiver Topic Gap Analysis (June 17, 2026)

## Hypothesis

PT Conv stuck at 85% with 2/20 caregiver failures. PT has caregiver topics ("PT Eval Guard - Caregiver Competency Intake", "PT Eval Guard - Caregiver Education Intake") that are ACTIVE (statecode:0) with correct YAML (no 800-char limits, no Question nodes, soft citation ban). But the score doesn't improve.

## What We Tried

| Fix | Conv Score | Result |
|-----|-----------|--------|
| Original baseline | 90% | 2 caregiver failures |
| CRITICAL citation ban | 85% | Regressed |
| Stacked fixes (hedge+cite+concise) | 80% | Regressed further |
| Soft citation + hedging removed | 85% | No change |
| MANDATORY caregiver checklist | 85% | Regressed |
| Caregiver topic YAML update | 85% | No change |
| Restored to baseline (Original) | 90% | Back to 90% |

## Theory: Response Quality, Not Triggering

The caregiver topics exist and are ON. Updating their YAML doesn't change the score. This means:
1. The topics ARE being triggered by caregiver questions
2. The agent's RESPONSE to caregiver questions doesn't meet the grader standard
3. This is a content quality issue, not a triggering or routing issue

## Why OT's Caregiver Topics Work (100% Conv)

OT has dedicated caregiver topics ("Caregiver competency verification", "Caregiver Competency") that route through OT_Specialist. OT's instructions may have stronger caregiver-specific response guidance, or the topics may have different YAML content (possibly using different action kinds or additionalInstructions).

## Investigation Path

1. Read OT's caregiver topic YAML via code editor
2. Compare to PT's caregiver topic YAML
3. If different, copy OT's YAML structure to PT
4. If same, the issue is in agent-level instructions or response format

## Direct Test Pane Testing

To see what PT actually says for caregiver questions:
1. Open PT in Copilot Studio → click Test button
2. Send: "Can you assess caregiver competency documentation in the PT evaluation for completeness and compliance?"
3. Inspect the bot response for missing elements, missing citations, or quality issues
4. Compare to OT's response for the same question

## Playwright Test Pane Interaction Pattern

```javascript
// Click Test button to open pane
await page.mouse.click(1094, 53);
await sleep(5000);

// Find chat input 
const chatInput = await page.evaluate(() => {
    const all = document.querySelectorAll('textarea, [role="textbox"]');
    for (const el of all) {
        const r = el.getBoundingClientRect();
        if (r.x > 1000 && r.width > 50) return { x: r.x, y: r.y };
    }
    return null;
});

if (chatInput) {
    await page.mouse.click(chatInput.x + 20, chatInput.y + 20);
    await page.keyboard.type('question text here', { delay: 10 });
    await page.keyboard.press('Enter');
    await sleep(20000);
    
    // Read response via innerText
    const text = await page.evaluate(() => (document.body?.innerText || ''));
}
```

**Note:** The test pane uses a Web Chat component rendered in an iframe/React portal. Direct DOM selector queries consistently return null. The mouse click + keyboard approach is the only reliable path found so far. Bot responses can be read from `document.body.innerText` by searching for the question text and extracting subsequent content.
