# Topic Deletion Replacement Pattern

## When This Applies

Deleting corrupted, stub, or duplicate topics improves single-response eval scores but breaks conversation eval because test phrases now route to deleted topics, producing empty responses and "Something went wrong while evaluating this test case" errors.

## Evidence (June 19, 2026 — QM Coach V2)

- Pre-cleanup: 62 topics, SR 71%, Conv 50%
- Deleted 31 topics (duplicates, stubs, corrupted with Fallback content)
- Post-cleanup: 15 topics, SR 95%, Conv 0% (all errors)
- Root cause: Conversation test cases asked "Start a QM intake workflow", "Show me a summary of our DoR", "Latest resident submissions" — all routed to deleted topics

## The Pattern

| Eval Type | Impact of Topic Deletion |
|-----------|------------------------|
| Single-response | Improves (+20-25 pts typical) — fewer competing triggers, cleaner routing |
| Conversation | Breaks (0% possible) — multi-turn flow hits missing topics, agent returns empty |

Single-response eval tests individual questions. Deleting topics removes competing triggers, so questions route to the correct remaining topic. 

Conversation eval tests multi-turn flows. If Topic A in the flow was deleted, the conversation breaks at that turn — the agent returns nothing, the grader errors, and ALL conversation cases fail.

## Detection

1. After topic deletion + publish, conversation eval shows:
   - All cases failed (not just reduced pass rate)
   - Agent response column shows `--` or empty
   - Error message: "Something went wrong while evaluating this test case"

2. Check the failing test phrases — do they match topics you deleted?
   - "Start a QM intake workflow" → QM Intake topic (deleted)
   - "Show me a summary of our DoR" → WORKFLOW MENU topic (deleted)
   - "Latest resident submissions" → LATEST RESIDENT SUBMISSION ROUTER (was broken, now deleted)

## Fix Options

### Option A: Re-add the Topics (Recommended if they have value)

Create a replacement list documenting what was deleted and how to restore it:

```
CONNECTED AGENTS (Agents tab → Add agent)
1. SNF AI Dashboard V2 — routes monitoring queries
2. Pacific Coast Case Historian V2 — routes documentation audits
3. Pacific-Coast Regulatory Hub V2 — routes regulatory questions
4. SNF Command Center V2 — routes command center queries

CUSTOM TOPICS (Topics → Add topic → From blank)
5-12. Escalate QM Concern, QM Driver Analysis, QM Action Plan, etc.
   - Use simple text answers (not interactive menus) to preserve SR scores
   - Add trigger phrases matching the original deleted topics

TOOLS (Tools tab → Add tool)
13-14. Work IQ Copilot/User — MCP connections
```

### Option B: Redistribute Triggers to Remaining Topics

If you want to keep the cleaned topic count:

1. Update remaining topics' trigger phrases to absorb deleted topics' phrases
2. Examples:
   - "Start a QM intake" → add to "SNF - Clinical Intake Handoff Router" triggers
   - "DoR summary" → add to "DoR Summary" topic triggers
   - "Start over" → add to "Reset Conversation" triggers

3. Verify agent instructions have: "Route to available topics even if original topic was deleted"

### Option C: Republish and Let Generative AI Handle It

Sometimes the agent's generative AI can recover if:
- Remaining topics have broad, generic trigger phrases
- Agent instructions include routing fallbacks
- But this is unreliable for exact-match test cases

## Best Practice

Always create a replacement list BEFORE deleting topics. The list should include:
1. Topic name (as it appeared)
2. Type (connected agent, custom topic, system topic, tool)
3. Purpose/value of that topic
4. Steps to re-add if needed

Save this list to Desktop with a clear filename: `{agent_name}_replacement_list.txt`

## Key Insight

The 85%+ SR threshold requires topic discipline. The 95% Conv threshold requires the conversation flow to survive intact. You cannot sacrifice conversation flow for SR points — both need attention.

When deleting topics: verify conversation eval test cases don't depend on them, OR restore the topics, OR redistribute their triggers.