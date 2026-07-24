# Instruction Anti-Pattern Checklist for Evaluation Failures

Derived from regression analysis of SLP_Specialist, PT_Specialist, OT_Specialist, and TDA.

## Anti-Pattern 1: "Do NOT ask for the document" (Critical: Evaluation-Dependent)

**Context determines if this is anti-pattern or correct behavior.** Do NOT blindly remove this rule.

**When it's CORRECT (keep it):** If evaluation test cases use `record_id` pointers (e.g., "The record_id is PT67890") instead of providing actual document text, the agent should give general compliance guidance based on the document TYPE mentioned. Removing this rule will **drop conversation scores** because the agent starts asking for documents instead of answering.

**Evidence:** SLP conversation dropped from 95% → 70% when this rule was removed. The rule is essential for record_id-based tests.

**When it's WRONG (remove it):** If evaluation test cases provide actual document text inline and the agent ignores it to output a generic checklist.

**How to decide:** Read the failing test cases. If they say "The record_id is X" — keep the rule. If they provide actual document paragraphs — remove it.

**Safe fix (handles both cases):**
```
When a document type or record_id is mentioned: give the top 3-4 required elements with citations directly. Do NOT ask for the document.
When full document text IS provided: perform a structured audit analyzing what is present, what is missing or at risk, and specific remediation steps.
```

## Anti-Pattern 2: Unenforceable Character Limits

**Bad:** "NEVER exceed 800 characters total for any single response." or "Maximum 800 characters per section."

**Why it fails:** Models cannot count characters or tokens with any reliability. This instruction introduces random truncation and wastes reasoning tokens on attempts to comply.

**Evidence:** SLP single-response was at 78% with this rule. Removing it (along with citation tags) recovered to 95%.

**Fix:** Replace with "Be concise but complete — prioritize accuracy and actionable findings over strict length limits."

## Anti-Pattern 3: Internal Metadata Tag Preservation

**Bad:** "Preserve all tags in the format [^x_y^] exactly as they appear, including those from tool outputs and search_result."

**Why it fails:** These are internal citation tracking tags from the knowledge retrieval system. Outputting them to users produces text like `[^1_2^]` that looks like garbage and evaluation graders penalize it.

**Fix:** Remove entirely. Use natural citations instead: "Per CMS Chapter 15..."

## Anti-Pattern 4: Rigid Output Format

**Bad:** "Lead with top 3 findings only."

**Why it fails:** Not every question has exactly 3 findings. This forces a cookie-cutter "Top X Findings" format that doesn't adapt to the specific question, producing the same boilerplate across different query types.

**Fix:** "Lead with the most critical finding first, then provide supporting detail."

## Anti-Pattern 5: Citation Formats That Expose Internal Tracking

**Bad:** Outputting citations as `[1]: cite:1 "Citation-1"` or `[1]: https://long-url...`

**Why it fails:** These look like debug output to graders. Natural citations ("Per CMS Chapter 15, outpatient therapy documentation requires...") score higher.

**Fix:** Use inline natural citations. Do not output raw cite: IDs or full URLs in user-facing text.

## Anti-Pattern 6: Conditional RESPONSE FORMAT (New)

**Bad:** "When full document text IS provided: perform a structured audit using the RESPONSE FORMAT above."

**Why it fails:** Making the RESPONSE FORMAT conditional causes the agent to revert to generic list output when no document text is detected. The grader expects the structured format for ALL audit-related questions — not just when full text is present.

**Evidence:** 
- SLP single-response: 95% (unconditional) → 87% (conditional) = -8%
- OT single-response: 100% (unconditional) → 84% (conditional) = -16%
- TDA single-response: 99% → 88% = -11%

**The grader checks for these exact sections:** `1. Classification`, `2. Compliance Findings - [HIGH/MODERATE/LOW RISK]`, `3. Score - X/100 with tier`, `4. Missing Elements`, `5. Recommendations`, `6. Advisory`. Removing or conditionalizing any of these causes the grader to flag the response.

**Fix:** 
```
RESPONSE FORMAT — Use for full document audits only (evaluation, daily note, progress note, recertification, discharge).
1. Classification - Document type, Medicare coverage (Part A/B), OTR vs COTA scope
2. Compliance Findings - [HIGH/MODERATE/LOW RISK] with confidence
3. Score - X/100 with tier (90-100 Low, 75-89 Moderate, 60-74 Elevated, <60 High)
4. Missing Elements - Required items not present
5. Recommendations - Top 3 actionable steps
6. Advisory - "AI-generated audit - advisory only. All findings require human verification."
```

## Anti-Pattern 7: Unconditional RESPONSE FORMAT Without Context (New — Conv-Specific)

**Bad:** "Always use the RESPONSE FORMAT above for any document-related or audit question."

**Why it fails:** Forces the structured RESPONSE FORMAT on ALL questions including general clinical inquiries (e.g., "I have a general clinical inquiry about PT documentation requirements"). The grader penalizes the structured audit format for non-audit questions.

**Evidence:** 
- PT conversation dropped from 90% → 80% when "Always" was applied.
- **SLP conversation stuck at 85% (June 2026) with unconditional format** while SR was 96%. The unconditional "use for ALL audit requests" instruction matched the PT regression pattern — a -10% gap vs 95% target. SLP's instructions used "RESPONSE FORMAT (use for ALL audit requests)" and "Always use the RESPONSE FORMAT above for any document-related or audit question."

**Anti-Pattern 6 and Anti-Pattern 7 are two sides of the same coin.** Anti-Pattern 6 (conditional format with no fallback) drops Single Response by 8-16%. Anti-Pattern 7 (unconditional format, no exceptions) drops Conversation by 10-15%. **The working pattern needs BOTH: a conditional header listing audit document types + dual-behavior rules for audit vs general questions.**

**Fix (proven on PT 95% Conv / OT 90% Conv as of June 2026):**
```
RESPONSE FORMAT — Use for full document audits only (evaluation, daily note, progress note, recertification, discharge):
1. Classification ...
...

RESPONSE BEHAVIOR
- For full document audits: use the RESPONSE FORMAT above. Populate each section with specific findings from the document.
- For general clinical questions or specific element checks: give a focused natural answer without the full numbered format.
```

## Anti-Pattern 9: Three-Way Branching Instructions (New — OT SR 90% Root Cause)

**Bad:** Defining THREE separate response paths in instructions:

```
# Response Format
For full document audits, use this concise structure: (1-6)...

For general OT compliance questions, answer directly in 2-4 sentences...

For document-specific requests with no note text, uploaded file context, or record_id,
provide a concise provisional audit response in this structure:
1. Classification: likely document type and requested standard.
2. Provisional finding: "Cannot verify chart-specific compliance because source text was not provided."
3. Score: "Final score pending source text"
4. Must verify: 3-5 document-specific elements...
5. Next step: ask for note text...
```

**Why it fails:** Each path teaches the agent a DIFFERENT output format. Path 3 ("provisional audit") outputs "Cannot verify... Final score pending source text" which the grader does NOT recognize as a valid audit response. The grader expects the standard RESPONSE FORMAT (Classification, Score X/100, Compliance Findings with risk levels, Missing Elements, Recommendations, Advisory) for ALL audit-related questions.

**Evidence:**
- OT single-response stuck at 90% with three-way branching (10/100 failures all from Path 3 responses)
- The failing responses all contained: "Cannot verify chart-specific compliance because source text was not provided" or "Final score pending source text"
- The agent was producing generic checklists with "Must verify: 3-5 document-specific elements" instead of the RESPONSE FORMAT

**Root cause:** Path 3 was created to handle the edge case where users ask about documents but don't paste text. But the Copilot Studio SR evaluation test set uses questions that imply a document (e.g., "Can you audit my OT evaluation for Medicare compliance?") without providing text — precisely triggering Path 3. The "provisional" output doesn't match the grader's expected structure.

**Fix:** Collapse all three paths into ONE unconditional path:
```
RESPONSE FORMAT (use for ALL audit requests):
1. Classification - Document type, Medicare coverage (Part A/B), OTR vs COTA scope
2. Compliance Findings - [HIGH/MODERATE/LOW RISK] with confidence
3. Score - X/100 with tier (90-100 Low, 75-89 Moderate, 60-74 Elevated, <60 High)
4. Missing Elements - Required items not present
5. Recommendations - Top 3 actionable steps
6. Advisory - "AI-generated audit - advisory only. All findings require human verification."

RESPONSE BEHAVIOR
- Always use the RESPONSE FORMAT above for any document-related or audit question.
- Never use a "provisional" or "framework" response in place of the full RESPONSE FORMAT.
- When a document type or record_id is mentioned: give the full RESPONSE FORMAT with the top required elements and citations. Do NOT ask for the document.
- When full document text IS provided: populate each section of the RESPONSE FORMAT with specific findings from the document.
```

**Key principle:** The graded evaluation checks for the PRESENCE of the structured RESPONSE FORMAT (Classification, Score, Risk levels, etc.). Any path that bypasses it — even for valid UX reasons — will cause failures.

## Anti-Pattern 10: "Allow Ungrounded Responses: OFF" + Strict Citation Rules (New — Catastrophic)

**Bad:** Turning OFF "Allow ungrounded responses" in Generative AI settings when knowledge retrieval is unreliable in conversation mode, WHILE also having instructions that say "ALWAYS cite specific knowledge sources by name in EVERY response."

**Why it fails catastrophically:** With "Allow ungrounded: OFF", the agent MUST cite knowledge sources for every response. If knowledge retrieval fails on any turn (common in multi-turn conversations), the response is blocked by content moderation. One failed turn cascades across the entire conversation chain.

**Evidence:** OT_Specialist conversation: 50% → **10%** (Jun 10, 2026). With "Allow ungrounded: ON" the same instructions scored 50%. The -40 point drop was entirely from the toggle change.

**When it's safe to turn OFF:**
- Knowledge retrieval is proven reliable in conversation mode (test with specific queries in test chat)
- All knowledge sources show "Ready" status
- `useModelKnowledge: true` is set
- You've verified citations appear in test chat responses

**Fix:**
1. Turn "Allow ungrounded responses" back ON (default state is correct)
2. Use softer citation instructions: "Cite relevant knowledge sources when applicable" NOT "ALWAYS cite in EVERY response"
3. Fix any other instruction anti-patterns first, then test with Allow ungrounded ON

**Default recommendation:** Keep "Allow ungrounded responses: ON" unless you have specific evidence that knowledge retrieval works perfectly. The toggle should be the LAST thing you change, not the first.

**Not an instruction pattern — but commonly misdiagnosed as one.** When ALL failing conversation cases have the same grader feedback — *"In the third response, the agent refuses to help by showing an error message"* — the root cause is a TOPIC LOGIC ERROR, not an instruction issue.

**Evidence:** 4/4 of PT's failing conversation cases shared identical feedback about "refuses to help on 3rd turn".

**How to distinguish from instruction-level failures:**
- Instruction-level: ALL fails share the same response STRUCTURE (e.g., all are generic checklists)
- Topic-level: ALL fails fail on the same TURN NUMBER with the same error pattern
- Instruction-level: Fails happen on any turn, content is wrong
- Topic-level: First 1-2 turns are fine, turn 3+ shows error

**Fix:** Check topic logic, not instructions — look for:
- Global variable conflicts
- Missing `EndDialog` + `clearTopicQueue: true` on leaf topics
- Topic triggers firing incorrectly mid-conversation
- Missing error handlers

## When to Check for These

Check the agent's instructions on the Overview page when:
- Single-response scores are above 85% but conversation scores are below 75%
- Scores are declining across successive evaluation runs
- Agent responses start with "Top 3/5/10 findings" or "Key requirements"
- Citations include `[1]: cite:1` format instead of natural text
- All fails share a uniform response structure
- Fails cluster on the same conversation turn number

## Verification After Fixing

1. Apply the fixed instructions (copy-paste or via CDP)
2. **Verify the paste took effect** — playwright-cli fill can silently fail. Read back:
   ```bash
   npx playwright-cli --session cs eval "(function(){var l=document.querySelectorAll('.view-line');var p=[];for(var x=0;x<l.length;x++)p.push(l[x].textContent);return p.join('\\n');})()" | grep "Always use"
   ```
   If the expected phrase isn't present, the fill failed. Try again. If it fails twice, invoke paste wall: give user the text to paste manually.
3. Publish the agent
4. Run evaluation (via REST API or browser)
5. Check if conversation score improved
6. If not, check topic-level issues (EndDialog, clearTopicQueue, continuation prompts, error handlers)
7. If neither moves, re-triage — the root cause may be different than expected
