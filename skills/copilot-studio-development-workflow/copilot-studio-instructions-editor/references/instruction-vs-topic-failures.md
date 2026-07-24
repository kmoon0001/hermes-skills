# Instruction vs Topic-Level Failure Diagnosis

When eval scores don't improve after instruction cleanup, the remaining failures are likely topic-level, not instruction-level.

## How to Tell the Difference

| Symptom | Cause | Fix |
|---------|-------|-----|
| Interactive menus/wizards as responses | Topic returns card/menu instead of text | Delete or restructure topic |
| "System error" responses | Broken topic action/connector | Fix action node or delete topic |
| "Something went wrong" with "--" response | Broken topic routing or platform issue | Check for references to deleted topics |
| Wrong but coherent answer | Instruction issue | Update instructions |
| Hedging language ("I'm not sure") | Instruction issue | Remove hedging from instructions |
| Citation artifacts (cite:1) | Instruction issue | Add citation format rules |

## Key Finding: QM Coach V2 Session

Instruction cleanup (removing CRITICAL/NEVER, consolidating sections, adding MDS references) had ZERO impact on eval score (stayed at 71%). The 29 failures were ALL topic-level:
- 20 interactive menu topics
- 7 system error topics  
- 2 misrouted topics

After deleting 31 topics (stubs + duplicates + interactive menus), eval jumped to 95% — without any further instruction changes.

## Rule of Thumb

Before changing instructions, check:
1. Are the failed test cases getting wrong answers or no answer?
2. Are the failures concentrated in specific topic areas?
3. Do the failed responses look like topic outputs (menus, cards, wizards) or instruction-guided outputs (text answers)?

If the failures look like topic outputs, fix the topics first. Instruction changes won't help.
