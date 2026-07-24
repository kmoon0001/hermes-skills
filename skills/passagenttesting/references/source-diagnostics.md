# Copilot Studio Source-Code Diagnostic Patterns

When live evaluation scores or failed cases aren't accessible (browser busy, API down, no Dataverse access), perform a source-code audit of the unpacked agent's topic YAML files. The patterns below were validated against a real-world Copilot Studio agent with 69+ topics.

## Quick Scan Commands

```bash
# Find topics with empty intent triggers (dead topics)
rg -l 'intent: \{\}' topics/

# Find topics without EndDialog (causes context bleeding)
rg -L 'EndDialog|EndConversation' topics/*.mcs.yml | wc -l

# Find duplicate OnUnknownIntent handlers
rg -l 'OnUnknownIntent' topics/

# Find topics with clearTopicQueue: true (the ones doing it right)
rg -l 'clearTopicQueue: true' topics/
```

## Diagnostic Priority Order

### 1. DEAD TOPICS — `intent: {}`

**What**: Topic defines `kind: OnRecognizedIntent` with `intent: {}` — no trigger queries.

**Impact**: Topic can NEVER fire from user text. Can only be reached via explicit `BeginDialog` from another topic. This is the #1 cause of "the audit/compliance/review topic doesn't trigger when users ask for it."

**Example** (from real agent):
```yaml
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent: {}          # <-- DEAD: no triggers
```

**Fix**: Add 5-10 trigger phrases matching realistic user input for that topic's purpose.

### 2. DUPLICATE UNKNOWN-INTENT HANDLERS

**What**: Two or more topics with `OnUnknownIntent` at the same priority value.

**Impact**: Non-deterministic routing. Same input can hit different handlers on different runs → unstable evaluation scores.

**Fix**: Consolidate into one handler or use distinct priorities (higher priority = checked first).

### 3. INSTRUCTION CONFLICTS

**What**: Topic header guardrails that contradict the topic's actual output format.

**Pattern**: "STRICT JSON ONLY: No code blocks or conversational filler" in topics that produce rich-text clinical/conversational output.

**Impact**: Model has to resolve contradictory instructions → degraded response quality across all runs.

**Fix**: Remove guardrails that don't match the topic's output format. JSON-only guardrails belong in API/backend integration topics, not in conversational/documentation topics.

### 4. MISSING TOPIC TERMINATION

**What**: Topics that complete their work without `EndDialog` (ideally with `clearTopicQueue: true`).

**Impact**: Topic stays in the active queue → context bleeding between turns → multi-turn evaluation failures.

**Expected Count**: In a well-structured agent, ~80%+ of leaf topics should have explicit `EndDialog`. If the count is under 20%, this is a systemic defect.

### 5. KNOWLEDGE RETRIEVAL GAP

**What**: `useModelKnowledge: false` in agent instructions + `SearchAndSummarizeContent` as the fallback.

**Impact**: When model knowledge is disabled, ALL domain answers depend on retrieval. If retrieval fails or times out, the response degrades to the Fallback message. In evaluation, this produces inconsistent scores depending on retrieval availability.

**Fix**: Either set `useModelKnowledge: true` or ensure all knowledge sources are indexed and reliable before disabling model knowledge.

### 6. BROKEN CONVERSATION FLOW

**What**: Topics that display output and then end silently — no return to menu, no "what next?" prompt, no conversation handoff.

**Impact**: Conversation completeness evaluations fail. Multi-turn test cases that expect a follow-up or menu redisplay score zero on the continuation turn.

**Fix**: Add a Question or menu prompt after the main output before EndDialog.

### 7. HIDDEN CHARACTER LIMITS IN `additionalInstructions` (SearchAndSummarizeContent)

**What**: `SearchAndSummarizeContent` topics with `Keep response under 800 characters.` (or any unenforceable length limit) buried in the `additionalInstructions:` YAML block.

**Impact**: The model cannot reliably count characters, so this instruction causes random truncation or refusal on follow-up turns. The grader sees "agent refuses to help" or "incomplete response" — identical symptoms to a missing EndDialog. **Evidence (Jun 14, 2026):** SLP "Analyze SLP Evaluation Report" topic had this line, producing a "refuses to help on second response" conversation failure. Removing it and adding a citation instruction eliminated the pattern.

**Scan command:**
```bash
rg -n "additionalInstructions" topics/*.mcs.yml -A 10 | rg -B2 "800|under.*characters|keep.*response.*under"
```

**Fix**: Replace `Keep response under NNN characters.` with `Be concise but complete — prioritize accuracy over strict length limits.` Or remove entirely and rely on the agent-level instructions for length guidance.

**Why this hides**: The line is inside a YAML heredoc (`|-`) in the `additionalInstructions` of a `SearchAndSummarizeContent` action. Not visible on the topic card — requires opening the code editor. Agents with 10+ SSC topics can have this in every one.

### 8. PROVISIONAL/FALLBACK RESPONSE PATHS THAT OVERRIDE RESPONSE FORMAT

**What**: Instructions that tell the agent to use a DIFFERENT response structure when "document text is not provided" — e.g., "answer with a provisional documentation audit framework."

**Impact**: The grader expects the full RESPONSE FORMAT (Classification, Score X/100, Compliance Findings) for every audit question. A "provisional" response omitting the score is graded as a failure. **Evidence (Jun 14, 2026):** OT_Specialist SR stuck at 90% because 10/100 test cases hit the provisional path. Removing the provisional fallback and making the RESPONSE FORMAT unconditional recovered to **98%**.

**Fix**: Eliminate conditional response paths. Use a SINGLE RESPONSE FORMAT for all audit-related questions. When document text isn't available, still populate Classification, Score ("Preliminary assessment pending source text"), and Compliance Findings. Never replace the RESPONSE FORMAT structure.

## Systemic vs Individual Fixes

When a pattern appears in 80%+ of topics, fix the category (e.g., add EndDialog to all leaf topics via script or bulk edit), not individual topics one by one. The effort-to-impact ratio flips at scale.
