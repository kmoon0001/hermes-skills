# OnConversationStart — Eval Impact Pattern

## The Pattern

Conversation Start topics using `kind: OnConversationStart` fire on **every new conversation**. This means the agent always shows the ConvStart's first action — typically a welcome message or document-type selection menu — before answering anything.

## Why This Affects Eval Scores

| Score Type | Impact | Mechanism |
|---|---|---|
| **Single-Response** | Minor (0-5 pts) | Welcome message doesn't interfere with single-turn evals |
| **Conversational** | Major (15-40+ pts) | Welcome message or menu at conversation start forces first response off-topic for the test case |

## Observed Behavior (Updated Jul 10 2026)

From Medicare Part B Feedback B agent (Therapy AI Dev environment):

| ConvStart State | Conv Score | Notes |
|---|---|---|
| **Deactivated (statecode=1)** | **10-15%** | Clean slate, no ConvStart interference |
| **OnRecognizedIntent + 15 trigger phrases** | **30%** | Best post-change result. Only fires when trigger phrases match. |
| **OnConversationStart + original menu + stale topic refs** | **0%** | Original YAML restored from snapshot, but topic dialog references were stale (topics reorganized) |
| **OnConversationStart + welcome message only (no menu)** | **5-15%** | Welcome message still interfering with first-turn eval expectations |
| **OnConversationStart + menu (baseline, active)** | **45%** | Original state before any changes. Menu question provided expected options. |

**Key insight:** The 45% baseline was achieved with ConvStart ACTIVE and offering a document-type menu. The 30% with OnRecognizedIntent was the best post-change result. But subsequent publishes dropped Conv to 10-15% due to other factors (instruction changes, Greeting/Fallback interceptors, topic reorganization).

## Deactivated vs OnRecognizedIntent — Which to Use?

**OnRecognizedIntent** is the better choice when:
- The ConvStart topic offers a document-type selection menu that routes to specific topics via BeginDialog
- The trigger phrases allow the topic to still fire for document upload flows
- You want it available but not forced on every conversation

**Deactivated** is the better choice when:
- The ConvStart YAML references stale/deprecated topic names that no longer exist
- The document upload routing is handled by individual topics' own trigger phrases
- You want zero interference with conversation flow

## CRITICAL: Snapshot Restoration with Stale References

**Restoring the original ConvStart YAML from a snapshot can break things** if the topics it references have been renamed or reorganized. The original ConvStart for Feedback B had `BeginDialog` references to topics like `EvaluationAssessmentandPlanofCare`, `TreatmentEncounterNoteReview`, etc. — but these topics were later split into individual intent-based topics with different schema names.

**Fix:** When restoring ConvStart from a snapshot:
1. Check all `dialog:` references in the YAML — verify they exist via Dataverse `botcomponents` query
2. If topics were renamed: either update the references, or deactivate ConvStart and let NLU routing handle it
3. If topics were removed: deactivate ConvStart, remove the routing conditions

## Verified Eval Pattern

When iterating on ConvStart changes:
1. Change → publish → run 20-case Conv eval (~3-5 min)
2. Each run costs one daily eval quota slot
3. Run SR eval (100 case, ~5-8 min) less frequently — SR is less sensitive to ConvStart changes
4. Track scores in a table to identify regressions across publishes
