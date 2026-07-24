## OT Agent Session Lessons - July 2, 2026

### Incident
On July 2, 2026, during evaluation score improvement attempts:
- OT SR dropped from 90% to 53% after instruction/topic changes
- Rolling back to pre-change state (via Dataverse PATCH of botcomponents) restored partial function (67% SR) but not full 90%
- Root cause analysis indicated multiple factors:
  1. Applied conditional RESPONSE FORMAT to OT, but historical data shows OT performs best with UNCONDITIONAL RESPONSE FORMAT ("Use for ALL document-related questions")
  2. Possible incomplete rollback of topic configurations (800-char limits may not have been fully removed)
  3. Citation handling may not have been verified (should cite by natural name, not preserve internal tags)

### Key Learnings
1. **Agent-Specific RESPONSE FORMAT**: Always consult historical performance data before changing RESPONSE FORMAT. For OT, unconditional RESPONSE FORMAT is optimal (97% SR). Applying conditional format ("Use for full document audits only") likely contributed to the regression.
2. **Verify Rollback Completeness**: After reverting agent components via Dataverse API, always re-fetch and verify the exact content matches the known-good state. Incomplete reversion can leave residual misconfigurations.
3. **Incremental Validation**: Make one change at a time (e.g., fix RESPONSE FORMAT, publish, evaluate; then fix 800-char limits, publish, evaluate) to isolate impact.
4. **Citation Hygiene**: Ensure instructions include "Cite sources by natural name" and explicitly remove any language about preserving internal tracking tags like [^x_y^].

### Recommended Recovery Procedure for OT
1. Reset to known-good baseline (confirm via session history or backup)
2. Set instructions to: Unconditional RESPONSE FORMAT + natural citation guidance
3. Scan ALL topics for and remove: "Keep response under 800 characters" or similar unenforceable length limits
4. Verify every SearchAndSummarizeContent topic ends with EndDialog and clearTopicQueue: true
5. Publish and evaluate single-response before attempting conversation tests

### Supporting Evidence
- From copilot-debug/references/lessons-learned.md (June 16, 2026): OT SR 97% with unconditional RESPONSE FORMAT
- From same source: "Remove 800-char limits from topics (validated Jun 2026)" improved OT Conv 85%->90%
- From same source: "Citation rules: Remove 'preserve [^x_y^] tags' — internal tracking tags in output cause eval failures. Replace with 'Cite sources by natural name.'"