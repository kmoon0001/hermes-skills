# Topic YAML 800-Char Limit Fix Pattern

## Root Cause

Audit-type Copilot Studio topics (SearchAndSummarizeContent actions) frequently have `Keep response under 800 characters.` in their `additionalInstructions`. This causes the model to truncate audit responses, making the grader mark them "incomplete" — even when the response is otherwise accurate.

This pattern was validated across **PT (all 5 audit topics → contributed to 75% Conv)** and **SLP (3+ topics)**.

## Scanning for the Problem

Use `pac copilot extract-template` to dump the agent's full YAML, then scan:

```bash
pac copilot extract-template --bot "<BOT_ID>" --templateFileName "agent_template.yaml" --overwrite
```

For agents where pac crashes (knowledge-heavy like SLP), use the CDP approach instead — navigate to each topic's code editor and read `.view-lines.textContent`.

### Python Scanner Pattern

```python
import re

with open("agent_template.yaml") as f:
    content = f.read()

blocks = re.split(r'(?=^\s+displayName:)', content, flags=re.MULTILINE)

for block in blocks:
    if 'actions:' in block and 'SearchAndSummarizeContent' in block:
        dn = re.search(r'displayName:\s*(.+)$', block, re.MULTILINE)
        name = dn.group(1).strip() if dn else "?"
        
        has_800 = '800' in block
        has_citation = any(x in block.lower() for x in ['cite:', 'citation', 'natural source'])
        has_enddialog = 'EndDialog' in block
        
        issues = []
        if has_800: issues.append('800-char limit ❌')
        if not has_citation: issues.append('no citation rule ❌')
        if not has_enddialog: issues.append('no EndDialog ❌')
        
        status = ', '.join(issues) if issues else '✅ clean'
        print(f"{name}: {status}")
```

## The Fix

Replace the `additionalInstructions` block. Remove ALL of these:
- `Keep response under 800 characters.`
- `Max 800 characters per section. Total response max 2400 chars.`
- Any character/word count constraint

Add:
- `Be concise but complete.`
- `Cite [CMS Chapter 15, discipline-specific guidelines] by natural source name. Do not output cite:1 or metadata tags.`

### Complete YAML Structure (paste-ready)

The code editor requires `kind: AdaptiveDialog` as the VERY FIRST LINE. Omitting it causes: `Invalid kind, expected 'AdaptiveDialog' but got 'Unknown'.`

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Analyze [Discipline] [Document Type]
    triggerQueries:
      - query 1
      - query 2

  actions:
    - kind: SearchAndSummarizeContent
      id: search_[TopicName]
      latencyMessageSettings:
        allowLatencyMessage: false

      userInput: =System.Activity.Text
      additionalInstructions: |-
        [Audit instructions without 800-char limit]
        Use risk levels (High/Moderate/Low). Be concise but complete.
        Cite CMS Chapter 15 and [discipline] guidelines by natural source name. Do not output cite:1 or metadata tags.
      applyModelKnowledgeSetting: true

    - kind: EndDialog
      id: end-topic
      clearTopicQueue: true

inputType: {}
outputType: {}
```

## Applying the Fix

1. Open the topic in Copilot Studio
2. **More → Open code editor**
3. **Ctrl+A → Delete** (clear editor entirely)
4. **Paste** the complete YAML (from `kind: AdaptiveDialog` through `outputType: {}`)
5. Type any character → **Backspace** (unlocks Save button)
6. Click **Save**

## Known Limitation: `pac` Crashes on Knowledge-Heavy Agents

`pac copilot extract-template` succeeds for simpler agents (PT: 48 components, ~43KB YAML) but **crashes** with `System.ArgumentException` for knowledge-heavy agents (SLP: 63+ components). The error occurs during `AddKSComponent` when processing knowledge sources. When pac fails, fall back to CDP topic-by-topic reading of the code editor.

## Cross-Agent Validation

This 800-char limit pattern was found in ALL audit topics across:
- **PT_Specialist**: 5/5 audit topics (Daily Note, Progress Note, Discharge, Evaluation, Recertification Note)
- **SLP_Specialist**: 3/6 audit topics (Daily Therapy Note, Evaluation Report, others)
- **OT_Specialist**: Was fixed earlier in instruction-level changes (v7-v9)

The fix is the same for every agent. When an agent's Conv score is stuck below 90%, scan all topics for 800-char limits first — it's the highest-yield fix.
