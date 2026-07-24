# Simplified Text-Answer Topic Format for 95%+ Eval Scores

## Problem

Interactive menu topics (ClosedListEntity, AdaptiveCardPrompt, multi-step wizards, SearchAndSummarizeContent) consistently fail single-response eval because the grader expects a direct text answer, not a menu prompt.

## Solution: Text-Answer + EndDialog Pattern

Use the simplest possible topic structure — comprehensive text answer followed immediately by EndDialog:

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    triggerQueries:
      - trigger phrase 1
      - trigger phrase 2
      - trigger phrase 3
  actions:
    - kind: SendActivity
      id: answer_id
      activity: |
        [Comprehensive text answer with specific clinical/regulatory content]
        
        [Bullet points or numbered lists as appropriate]
        
        [Reference ONE Clinical protocols or CMS standards where applicable]
        
        [End with a continuation prompt]
    - kind: EndDialog
      id: end_id
```

## QM Coach V2 Evidence (Jun 2026)

- **Before**: 29 topics with interactive menus, SearchAndSummarizeContent, ClosedListEntity
- **Result**: 71% single-response eval (20 of 29 failures from interactive topics)
- **After**: 20 topics converted to simplified text-answer format
- **Result**: 95% single-response eval

## What NOT to Use in Eval-Critical Topics

| Pattern | Why It Fails |
|---------|-------------|
| `ClosedListEntity` menus | Returns menu prompt, not answer |
| `AdaptiveCardPrompt` | Returns card with buttons |
| Multi-step `Question` wizards | Returns first question, not answer |
| `SearchAndSummarizeContent` | Variable output length/format |
| `BeginDialog` chains | Returns intermediate prompt |

## What WORKS

| Pattern | Why It Works |
|---------|-------------|
| `SendActivity` with full text | Returns complete answer |
| `EndDialog` immediately after | Clean topic completion |
| Multiple `triggerQueries` | Better intent matching |
| Direct clinical content in `activity` | Grounded, specific answer |
| Continuation prompt at end | Guides user to next step |

## Example: Converting Interactive to Text-Answer

**Before (fails eval):**
```yaml
actions:
  - kind: Question
    variable: Topic.CoachingCategory
    prompt: "Choose: Process, Team, or Systems?"
    entity:
      kind: ClosedListEntity
      items:
        - id: Process
        - id: Team
        - id: Systems
  - kind: ConditionGroup
    conditions:
      - condition: =Topic.CoachingCategory = "Process"
        actions:
          - kind: SearchAndSummarizeContent
            userInput: "Provide coaching for..."
```

**After (passes eval):**
```yaml
actions:
  - kind: SendActivity
    id: coaching_answer
    activity: |
      Coaching for QM Measures:
      
      Falls Prevention:
      - Emphasize safe mobility protocols
      - Review bed alarm compliance
      - Reference ONE Clinical Protocol for Fall Risk Assessment
      
      Mobility ADL Decline:
      - Reference ONE Clinical Protocol for Activity Tolerance
      - Focus on GG coding accuracy (Section GG)
      - Coach on restorative nursing program engagement
      
      [Continue with Pain Management, Antipsychotics, Pressure Ulcers...]
      
      Which QM measure needs coaching?
  - kind: EndDialog
    id: end_coaching
```

## When Interactive Topics Are Acceptable

Interactive topics are acceptable when:
- They're NOT in the evaluation test set
- They serve as navigation menus (user explicitly requests menu)
- They're used for data collection workflows (not eval-facing)
- They're system topics (Fallback, Conversational boosting)

## Rule of Thumb

If a topic's primary output is a menu/card/prompt rather than a text answer, it will hurt single-response eval scores. Convert to text-answer format for any topic that might be triggered during evaluation.
