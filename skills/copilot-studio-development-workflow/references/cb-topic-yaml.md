# Conversational Boosting Topic YAML

## Location
System topic on Topics page → System (9) tab (x:336, y:198). URL pattern: `.../adaptive/2960a8e1-ca2b-4eeb-8d9d-c749a9127dcc` (SLP agent).

## YAML Structure
Uses `SearchAndSummarizeContent` (NOT `CreateGenerativeAnswers` — that's for internal system use only).

### Original (known-good, 95% Conv / 96% SR):
```yaml
actions:
  - kind: SearchAndSummarizeContent
    id: search-content
    additionalInstructions: |-
      Keep response under 600 characters. Give the most relevant 2-3 points only.
      - Always cite knowledge sources using [Source Name] format in every response
    webBrowsing: false
    applyModelKnowledgeSetting: true
```

### Key properties:
- `applyModelKnowledgeSetting: true` — uses agent-level model knowledge toggle
- `webBrowsing: false` — no web search fallback
- `latencyMessageSettings.allowLatencyMessage: false` — no "thinking" messages

## Editing
1. Navigate to topic URL
2. More (topic toolbar, x:1024, y:138) → Open code editor
3. See Monaco code-editor-workflow for save persistence

## Citation behavior
The 600-char limit + "Always cite" instruction is the Microsoft Learn-aligned pattern. SR was 96% with this config. The citation artifacts (`[1]: cite:1`) are platform rendering, not instruction-controllable. Do NOT remove the cite instruction — doing so drops SR to 35%.

## Pitfalls
- Removing the 600-char limit causes 30+ min eval times and 35% SR regression
- Removing "Always cite" doesn't eliminate platform citation rendering
- CB is a SYSTEM topic — its YAML schema is different from authored topics
