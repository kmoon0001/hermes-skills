# Copilot Studio Instructions Editor Live Remediation

Session learning: Copilot Studio's agent-level Instructions editor can be updated programmatically if automation clicks the real Fluent `button` with a real mouse event. Earlier CDP/synthetic dispatch attempts failed because they clicked nested text/span elements, the wrong `Edit` button, or left the editor in read-only Lexical mode.

## Working pattern

1. Navigate to the agent Overview page and wait long enough for the SPA to hydrate (about 25-30s).
2. Dismiss onboarding/What's New overlays first. The Welcome overlay can intercept clicks even when the target editor is visible. Click `Skip`, `Got it`, `Dismiss`, `Close`, etc., and press Escape several times.
3. Find the Instructions section `Edit` button as an actual `button` or `[role="button"]`, not a `span`/`div` with text `Edit`.
   - Details Edit is near the top (`y` around 100-250).
   - Instructions Edit is mid-page (`y` often 550-900, depending on scroll/viewport).
   - Suggested prompts Edit is much lower (`y` often > 2400).
4. Use Playwright real mouse click on the button center:
   - `await page.mouse.click(x, y)`
   - Avoid synthetic `dispatchEvent` clicks for this editor.
5. Verify the Instructions Lexical editor changed from read-only to editable:
   - selector: `[aria-label="Describe what you want this agent to do, its tone, and rules."]`
   - `contenteditable="true"`
   - `aria-readonly` absent/null
6. Click the editor with `force:true`, press `Control+A`, and insert text with `page.keyboard.insertText(...)`.
7. Verify the inserted marker appears in `innerText` before saving.
8. Click the enabled `Save` button with real mouse click, wait, reload, and verify the marker persisted in Overview body text.
9. Publish the agent and confirm the publish dialog.

## Pitfalls

- If editor text length does not change after insertion, you probably clicked the wrong `Edit` button or the editor is still `contenteditable="false"`.
- If Save is not found/enabled, you are probably not in Instructions edit mode.
- If Playwright reports a DialogSurface/backdrop or WelcomeStep image intercepting pointer events, dismiss the onboarding overlay before interacting with the editor.
- Do not conclude Instructions editor is manual-only until the real-button/real-mouse path has been tried.
- Very long instruction bodies may fail to insert or persist. In the observed session, an ~8k TDA instruction draft failed, while a shortened ~4.4k draft inserted and persisted.

## Verification markers used successfully

- `Never display internal tool JSON`
- `Conversation evaluation behavior`
- For TDA, a different uppercase heading may be used; verify substantive markers such as `Never display internal tool JSON` and `ESCALATION / REPRESENTATIVE REQUESTS`.
