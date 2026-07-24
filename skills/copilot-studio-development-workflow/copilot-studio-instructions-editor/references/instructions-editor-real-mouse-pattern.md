# Instructions Editor Real-Mouse Save Pattern

Use this when Copilot Studio agent-level Instructions need to be edited programmatically and `fill`, CDP `Input.insertText`, or synthetic DOM clicks fail silently.

## Why previous approaches fail

The Instructions editor is a React/Lexical controlled `div[role="textbox"]`. It starts as read-only and only becomes editable after the true Instructions `Edit` button is activated. Synthetic `dispatchEvent` clicks may hit nested spans/divs or the wrong Edit button; Playwright `fill` can report success without updating Lexical state.

## Working Playwright pattern

1. Launch Playwright with saved Copilot Studio auth and a large viewport.
2. Navigate to `https://copilotstudio.microsoft.com/environments/{envId}/bots/{botId}/overview`.
3. Wait 25-30 seconds for SPA hydration.
4. Dismiss onboarding/What's New overlays (`Skip`, `Got it`, `Dismiss`, `Close`, `OK`, `Next`, `Done`, plus Escape). The Welcome overlay can intercept pointer events while the page appears usable.
5. Find the actual Instructions `button`/`[role="button"]` whose text is `Edit`, usually with top coordinate around 550-900. Avoid:
   - Details Edit near the top (`y` around 100-250)
   - Suggested prompts Edit much lower (`y` often > 2400)
   - non-button spans/divs with text `Edit`
6. **Click the button center with CDP `Input.dispatchMouseEvent`** — Playwright's `page.mouse.click()` silently fails on most agents (June 2026: failed on PT, SLP; only worked on TDA). Use:
   ```javascript
   const client = await p.context().newCDPSession(p);
   await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
   await sleep(50);
   await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
   ```
7. Verify the editor is active:
   - selector: `[aria-label="Describe what you want this agent to do, its tone, and rules."]`
   - `contenteditable="true"`
   - `aria-readonly` absent/null
8. Click the editor with `force:true`, press `Control+A`, then use `page.keyboard.insertText(instructions)`.
9. Read back `innerText`/`textContent` and confirm a unique marker exists before saving.
10. Click the enabled `Save` button with real mouse click.
11. Wait, reload, and verify the marker persists in the Overview body.
12. Publish and confirm.

## Observed limits

- An approximately 8k TDA instruction body failed to insert/persist; a shortened approximately 4.4k body worked. If insertion fails despite correct edit mode, shorten the instruction block rather than retrying the same body repeatedly.

## Success markers used

- `Never display internal tool JSON`
- `Conversation evaluation behavior`
- For TDA: `ESCALATION / REPRESENTATIVE REQUESTS`
