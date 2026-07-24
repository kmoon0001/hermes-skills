# Topic Audit Methodology

## Quick Audit via pac CLI

### Preferred method — extract-template (works for agents that pac org fetch crashes on)

```bash
# Export entire agent as YAML template (48-63 components, works for agents with knowledge sources)
pac copilot extract-template --bot "<botId>" --templateFileName "agent_template.yaml" --overwrite
```

This outputs a ~40-50KB YAML file containing ALL topics as `displayName: ...` blocks with their full `dialog:` YAML. Use Python to search/analyze (see Batch Topic Analysis below).

**Known to work (June 2026):** PT_Specialist (48 components, 990 lines).  
**Known to crash:** SLP_Specialist (63 components — crashes with `System.ArgumentException` after loading all components, before writing file). PT and OT typically succeed.

### Fallback — pac org fetch (often crashes)

```bash
# Ensure correct environment
pac org select --environment "https://org3353a370.crm.dynamics.com/"

# Query botcomponent topics — NOTE: correct attribute names are case-sensitive
# Common errors: 'parentbotid' attribute not found, stack overflow on knowledge agents
pac org fetch --xml "
<fetch><entity name='botcomponent'>
  <attribute name='botcomponentid'/>
  <attribute name='name'/>
  <attribute name='componenttype'/>
  <filter>
    <condition attribute='botid' operator='eq' value='<botId>'/>
    <condition attribute='componenttype' operator='eq' value='9'/>
  </filter>
</entity></fetch>"
```

**Pitfall:** `botcomponent` entity attribute names are case-sensitive. The FK attribute to bot is `botid` (not `parentbotid`). `pac org fetch` frequently crashes on knowledge-heavy agents with `System.ArgumentException` — prefer `extract-template` when available.

## Batch Topic Analysis via Python

After running `pac copilot extract-template`, analyze the exported YAML with Python to find systemic issues across all topics at once:

```python
import re

with open("agent_template.yaml") as f:
    content = f.read()

# Split by topic blocks (each starts with displayName:)
blocks = re.split(r'(?=^\s+displayName:)', content, flags=re.MULTILINE)

for block in blocks:
    dn = re.search(r'displayName:\s*(.+)$', block, re.MULTILINE)
    if not dn:
        continue
    name = dn.group(1).strip()
    
    # Only check topics with actions (skip knowledge sources)
    has_actions = 'actions:' in block
    has_enddialog = 'EndDialog' in block
    has_cancelall = 'CancelAllDialogs' in block
    has_800 = '800' in block
    has_citation = 'cite:' in block.lower() or 'citation' in block.lower() or 'source' in block.lower()
    
    if has_actions and not has_enddialog:
        print(f"❌ No EndDialog: {name}")
    if has_cancelall:
        print(f"⚠️ Has CancelAllDialogs (use EndDialog instead): {name}")
    if has_800:
        print(f"📏 800-char limit: {name}")
    if has_actions and not has_citation:
        print(f"📝 No citation rule: {name}")
```

Common issues found by this analysis:
- **Missing EndDialog** — causes "refuses to help" on conversation turns 2-3
- **CancelAllDialogs instead of EndDialog** — same symptom, different keyword
- **"Keep response under 800 characters"** — causes truncation, grader marks "incomplete"
- **No citation instruction** — causes `cite:1` placeholder output, grader marks "knowledge sources not cited"

## Diagnostic Thresholds

| Topic Count | Diagnosis | Action |
|------------|-----------|--------|
| < 25 | Healthy | Check EndDialog on SearchAndSummarizeContent topics |
| 25-50 | Warning | Review for duplicates |
| 50+ | Overloaded | Routing conflicts likely |
| 200+ | Critical | Delete 80%+ of question-phrase duplicates |

## Topic Classification

After fetching, classify each topic:

1. **System topics** (keep): Conversation Start, Fallback, Escalate, End of Conversation, On Error, Sign in, Multiple Topics Matched, Reset Conversation, Conversational boosting
2. **Named audit topics** (keep): "Analyze [Discipline] [DocType]", "Insurance Denial Risk Prompt", "[Discipline] Clinical Documentation Standards", "[Discipline] General Knowledge"
3. **Guard/Intake topics** (assess): "Eval Guard - *" or "Conv Guard - *" — check for hardcoded record_ids in YAML
4. **Question-phrase duplicates** (delete): "How do I document...", "Can you analyze...", "What are the requirements..." — these compete with generative AI routing

## Guard Topic Assessment

Before deleting guard topics, open one in the code editor and check:
- Does it have hardcoded record_ids ("12345", "67890") in SendMessage text? → DELETE
- Does it use variables for record_id? → KEEP
- Is it an exact-match trigger for evaluation test phrases? → KEEP if needed, DELETE if generative AI handles it

## Case Studies

### OT_Specialist (June 2026)

- Pre-cleanup: 200+ topics, 12 guard topics with hardcoded "12345" IDs
- Post-cleanup: 20 topics (12 named + 8 system), 0 guard topics
- Score improvement: 5% → 60%+ (partial cleanup), target 85%+

### PT_Specialist (June 2026)

- 48 components extracted via `pac copilot extract-template` (990 lines)
- All 5 audit topics had `Keep response under 800 characters` in additionalInstructions — same 800-char truncation pattern found in SLP/OT
- None of the 5 audit topics had natural source citation instructions
- Conv score: 85% → target 95%+
- Fix: remove 800-char limit, add natural citation instruction to each topic's additionalInstructions

## Topic YAML Fix Pattern (SearchAndSummarizeContent)

When fixing a SearchAndSummarizeContent topic, the `additionalInstructions:` block typically needs:

**Remove these:** `Keep response under X characters.`, `Max X characters per section.`, any arbitrary length limit.

**Replace with:** `Be concise but complete. Prioritize accuracy over strict length limits.`

**Add:** Natural source citation instruction: `Cite [applicable sources] by natural source name (e.g., Per CMS Chapter 15...). Do not output cite:1 or metadata tags.`

**Persistence caveat:** After editing the Monaco code editor, the Save button stays `disabled=true`. The user must type any character + Backspace to trigger React's onChange before clicking Save. No programmatic workaround exists.
