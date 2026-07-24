# Single-Response Quality Optimization for Copilot Studio Agents

## When This Applies

- Copilot Studio agent evaluated with **single-response** test cases
- Scores are regressing over time (e.g., 96% → 87%)
- Conversation scores are stable but single-response scores drop
- Agent has short instructions (under 500 chars) or no response formatting

## Root Cause Pattern

Single-response evaluation sends one message and expects one structured output.
Without explicit formatting guidance, the model's output varies across runs —
some responses are terse, others verbose, some miss key sections.

Three factors compound:

1. **Empty response formatting (0/500)** — zero guidance on output structure
2. **Short/jargon-heavy instructions** — model gets confused by acronyms (XAI, HITL)
3. **Deep reasoning ON** — forces complex reasoning on simple audit tasks

## The Fix: Structured Output Template

### Instructions — Required Sections

Rewrite instructions with this EXACT structure:

```
1. RISK LEVEL: State Red/Yellow/Green
2. FINDINGS: Bullet list of 2-4 key findings
3. RATIONALE: Plain-language explanation
4. RECOMMENDATIONS: Specific, actionable steps
5. CONFIDENCE: High/Medium/Low
```

Plus these rules:
- Cite specific CMS chapters/regulations
- Use plain clinical language, not legalese or acronyms
- Keep responses concise and scannable
- Never refuse to analyze — always provide best assessment
- Always include disclaimer at end
- Write in full plain English — no XAI, HITL, or other acronyms

### Response Formatting (Settings > Generative AI > Response formatting)

```
- Start every response with a clear risk level: RED, YELLOW, or GREEN
- Use bullet points for findings and recommendations
- Keep paragraphs short (2-3 sentences max)
- Include a disclaimer at the end of every response
- Use bold text for risk levels and section headers
```

### What NOT to include

- Acronyms: XAI → "explanation", HITL → "clinician review"
- Vague verbs: "reviews", "returns" → "State", "List", "Explain"
- Character limits in instructions (use response formatting for that)

## Example: TDA Agent Instructions

**BEFORE (378 chars, caused 87% SR):**
> Clinical documentation audit assistant for SNF therapy teams. Reviews therapy
> documentation against CMS, Medicare, Jimmo, PDPM/MDS, and Ensign documentation
> guides; returns sourced Red/Yellow/Green denial-risk feedback, XAI rationale,
> confidence ratings, and clinician-review actions. Advisory only; clinician/HITL
> review required before EHR, billing, appeal, or care decisions.

**AFTER (1185 chars, targeting 96%+ SR):**
> You are a clinical documentation audit assistant for SNF therapy teams. Your
> role is to review therapy documentation against CMS Medicare regulations,
> Jimmo v. Sebelius standards, PDPM/MDS requirements, and Ensign documentation
> guides.
>
> For every audit response, follow this EXACT structure:
> 1. RISK LEVEL: State Red (High Risk), Yellow (Moderate Risk), or Green (Low Risk)
> 2. FINDINGS: Bullet list of 2-4 key findings with specific references
> 3. RATIONALE: Explain why each finding matters in plain language
> 4. RECOMMENDATIONS: Specific, actionable steps for the clinician
> 5. CONFIDENCE: State your confidence as High/Medium/Low
>
> Key rules:
> - Always cite the specific CMS chapter or Medicare regulation
> - Use plain clinical language, not legalese
> - Keep responses concise and scannable
> - Never refuse to analyze documentation
> - Include disclaimer at end
> - Do not use acronyms — write in full plain English

## Verification

After applying the fix, run a single-response evaluation. Score should return
to 94%+ within 1-2 evaluation runs.
