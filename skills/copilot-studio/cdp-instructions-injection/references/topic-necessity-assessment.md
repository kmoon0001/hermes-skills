# Topic Necessity Assessment (Before Re-Adding)

When rebuilding topics after cleanup, assess whether each replacement topic is truly needed.

## Assessment Framework

1. **Dependency Check**: Does this topic reference other deleted topics (BeginDialog calls)?
2. **Infrastructure Check**: Does required data infrastructure exist (flows, connectors, other agents)?
3. **Coverage Check**: Does an existing topic already cover this area adequately?
4. **Eval Impact**: Will adding this topic destabilize current eval scores?

## Red Flags — Likely Extraneous Topics

- Topics routing to non-existent downstream topics
- Complex routing without supporting infrastructure
- Outlier-analysis topics in facility-focused QM agents
- Email generators when summary topics exist

## Case Study: QM Coach V2 (Jun 19, 2026)

**LATEST RESIDENT SUBMISSION ROUTER** — ASSESSED EXTRANEOUS

- Routes to RESIDENT OUTLIER ANALYSIS (topic deletion broke this chain)
- Requires resident insight submission flow infrastructure
- Core QM workflows already covered by QM Data Upload & Decline Detection
- Would drop single-response eval from 95%
- NOT re-added to preserve stability

**VERDICT PATTERN**: If downstream topic + infrastructure missing, and core workflows covered, mark as extraneous.

## Decision Matrix

| Topic | Depends On | Infrastructure | Coverage Exists | Eval Risk | Verdict |
|-------|------------|----------------|-----------------|-----------|----------|
| LATEST RESIDENT SUBMISSION ROUTER | RESIDENT OUTLIER ANALYSIS | Resident insight flow | QM Data Upload & Decline Detection | High | Extraneous |
| SNF - Quality Measure Email Generator | None | Simple text answer | DoR Summary | Low | Optional |
| Conversational boosting | System topic behavior | Knowledge sources | Fallback (exists) | High | Skip |

## Recommendation

Preserve 95% eval stable state. Add only if specific user workflow requires missing capability.