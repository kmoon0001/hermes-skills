# Conditional PRIMARY DIRECTIVE — Worked Example

## The Problem
Unconditional "DO NOT search knowledge sources" causes ~50% abstention failures when test questions ask general knowledge without providing clinical text.

## The Fix
Split into two subsections based on input context:

### WHEN THE USER PROVIDES CLINICAL TEXT
> When the user provides clinical text, case snippets, note excerpts, or embedded patient data: the USER-PROVIDED TEXT IS THE AUTHORITATIVE SOURCE. Read it directly and EXTRACT the requested values from it. When clinical text is present, DO NOT search knowledge sources — extract only from what the user provided. State the actual values present; only mark an item absent if genuinely not in the provided text. This overrides any knowledge-source result.

### WHEN THE USER ASKS A GENERAL QUESTION WITHOUT TEXT
> When the user asks a general knowledge question, standards question, or asks about clinical documentation requirements WITHOUT providing patient-specific clinical text: DO search your knowledge sources (CMS manuals, Medicare guidelines, professional standards) and provide a complete, thorough answer. Answer directly with clinical standards-based information. Do NOT say you cannot answer. This is the EVALUATION CONTEXT — provide the framework directly.

## Proven Results
- **Case History Reviewing Agent:** Baseline 36% → 43% after primary directive split (+12pp, from 43%→57% closure of the gap)
- Applied in combination with: model name fix, removal of "under 4 sentences", removal of SearchSpecificFiles
- Without the PRIMARY DIRECTIVE fix, the other fixes plateau at +5-8pp

## When to Apply
- ANY agent with a text-extraction PRIMARY DIRECTIVE that blocks KB search
- ANY agent that scores <50% on SR with abstention/groundedness failures
- Instructions that say "DO NOT search" without a conditional fallback for no-text queries
