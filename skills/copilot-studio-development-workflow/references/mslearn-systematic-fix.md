# MS Learn Systematic Eval Fix Workflow

Per [Microsoft Learn evaluation triage](https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-failure):

## Layers (Execute in Order)

### Layer 1: Interpret Scores
- Run 3x to establish baseline
- ≤5% variance is normal
- If single-response shows 100% but conversation is low: agent config is fine, eval setup is the issue

### Layer 1.5: KB Quality (MANDATORY FIRST CHECK)
- Check knowledge source descriptions are populated
- Sources marked official/authoritative
- Content is fresh and covers test domains
- Most failures come from KB gaps, not agent logic

### Layer 2: Fix Evaluation Setup BEFORE Agent Config
- **record_id test cases**: The eval channel cannot resolve Dataverse lookups. Agent asks for record_id → grader says "irrelevant". These are evaluation limitations, not agent issues.
  - Fix: Switch failing test cases from "Keyword match" to "Compare meaning" at 50% threshold
  - OR accept as known platform limitation
- **"refuses to help" failures**: Usually CB fallback problem. Fix CB YAML.
- **"incomplete" + "ungrounded" without refusal**: Test cases likely lack inline clinical text. Agent has nothing to audit.

### Layer 3: Agent Config Fixes
- CB additionalInstructions: cite when natural, never demand citations
- Fallback message: contain real compliance info, not "I can help with X"
- Never set `applyModelKnowledgeSetting: false`

### Layer 4: Document Patterns
- Track iterations, identify trends
- Note what broke when you changed X → Y

## Common Failure → Fix Map

| Grader Says | Root Cause | Fix |
|-------------|-----------|-----|
| "agent refuses to help" | CB fallback is flat refusal | Improve CB activity + additionalInstructions |
| "agent repeats request for record_id" | Test case uses record_id (can't resolve) | Compare meaning OR accept limitation |
| "incomplete" + "ungrounded" (no refusal) | KB retrieval miss OR test case has no text | Improve additionalInstructions OR rewrite test case |
| "agent explains tool instead of answering" | Non-deterministic grader variance | Compare meaning |
| Score drops after CB change | additionalInstructions too aggressive | Remove "must cite" mandate |
