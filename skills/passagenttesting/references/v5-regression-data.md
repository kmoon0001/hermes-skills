# v5 Conditional Format: Regression Data

## Ensign Services Fleet (June 9, 2026)

Real-world regression scores when switching from v4 "Always use RESPONSE FORMAT" to v5 "Use for full document audits only":

| Agent | Metric | v4 (Always) | v5 (Conditional) | Delta |
|-------|--------|-------------|------------------|-------|
| **SLP** | Single-response | 95% | 87% | **-8%** |
| **SLP** | Conversation | 95% | 95% | 0 |
| **PT** | Single-response | 90% | 90% | 0 |
| **PT** | Conversation | 80% | 80% | 0 |
| **OT** | Single-response | 84% | 84% | 0 |
| **OT** | Conversation | 80% | 65% | **-15%** |
| **TDA** | Single-response | 99% | 88% | **-11%** |
| **TDA** | Conversation | 80% | 94% | +14% |

## Key Findings

1. **Single-response universally suffers** under conditional format. The grader expects the structured RESPONSE FORMAT for ALL audit-related questions, regardless of whether document text was provided.

2. **Conversation scores are mixed** — TDA conversation improved (routing agent, less format-dependent), while OT conversation dropped hard.

3. **The "Always use" format (v4/v6) is the safest default.** It prevents single-response regressions across all agent types.

4. **Conditional format (v5) only makes sense for routing agents** (TDA) where the expected output is a classification/route, not a full audit.

## What Did NOT Cause the Regression

- Knowledge source changes
- Topic structure changes  
- Test set changes
- Model or provider changes

All regressions were caused SOLELY by changing the RESPONSE FORMAT directive from unconditional to conditional.

## Post-SharePoint Regression (June 12, 2026)

After SharePoint folder renaming caused fleet-wide KB retrieval degradation, the v5/v4 dynamic reversed for **conversational** scores:

| Agent | Pre-KB-change Conv (v4) | Post-KB-change Conv (v4) | Post-KB-change Conv (v5) | Recovery |
|-------|------------------------|------------------------|------------------------|----------|
| **SLP** | 85% (stuck) | 85% (stuck) | **90%** (v3 fix) | +5% after conditional fix |
| **PT** | 95% (v5 conditional) | 75% (KB broke) | 85% (KB refresh) | Still recovering |
| **OT** | 90% (v5 conditional) | 50% (KB broke) | 75% (KB refresh) | Still recovering |

**Key insight:** When KB retrieval is DEGRADED (SharePoint rename broke GPT routing), unconditional RESPONSE FORMAT amplifies the problem. The rigid format + poor retrieval = grader penalizes harder. Conditional format gives the agent flexibility to fall back to natural answers when retrieval is inconsistent.

**Actionable rule:**
- KB healthy → unconditional format (v4) for SR, conditional (v5) for Conv with mixed test sets
- KB degraded → conditional format (v5) for Conv immediately, fix KB first before switching back to unconditional
