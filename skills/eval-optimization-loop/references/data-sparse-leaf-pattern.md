# Data-Sparse Leaf Instructions Pattern

## Problem

Global anti-abstention instructions in agent GPT metadata, Conversational boosting,
and Fallback are **not enough** when a specialized leaf topic (ProgressAnalysis,
RecertAnalysis, EvalAnalysis, etc.) contains only:

```
Extract only from user-provided text when present. End with CLINICAL REVIEW REQUIRED.
```

On a direct-intent hit, the leaf's instruction set wins. If no clinical text is present
(record IDs only, a date + discipline, partial metrics), the model defaults to one of:

- **"No notes found"** / "no documentation provided" — incorrectly claims the EHR was searched
- **"What type of document?"** — routing failure into generic clarification
- **"No prior quarter found"** — treats absent data as a stop signal instead of providing template

## Verified Fix: Three-Mode Leaf Instructions

Replace the leaf `additionalInstructions:` in each `SearchAndSummarizeContent` node with
explicit three-mode handling:

```yaml
      additionalInstructions: |-
        Provide a structured [REPORT_TYPE] review for SNF rehab.

        ## DATA RICH — When the user provides full clinical text or notes
        Extract and analyze only from what was provided. Do NOT invent findings,
        scores, diagnoses, patient facts, or facility metrics.

        ## DATA SPARSE — When the user gives only record IDs, date, discipline,
        or a partial request WITHOUT clinical text
        Do NOT say "No notes found", "no documentation provided", or
        "the notes are not included". The agent does NOT have EHR retrieval —
        do not claim records were searched or unavailable.
        Instead: deliver a complete pre-review package:
        - Full CMS compliance checklist for this report type
        - Required evidence and documentation elements
        - Placeholder language for missing clinical fields
        - Missing-fields table with "To complete from your facility data"
        - Do NOT ask "what document type" — use the topic context to infer.

        ## PARTIAL DATA — When the user supplies metrics, counts, or one period
        but asks for comparison
        Format and analyze the provided values. Create blank comparator columns
        for missing periods. Mark missing values as "To complete from your facility
        data", not as unavailable. Do NOT claim any data was searched for or not found.

        ## REPORT TYPE SPECIFIC
        [Type-specific instructions here]

        End with CLINICAL REVIEW REQUIRED.
```

## When to Apply

1. You've confirmed the agent has global anti-abstention (instructions + boosting + fallback)
2. But Conv failures still show abstention on record-ID-only or partial-metric turns
3. The agent's leaf topics say only "extract from user-provided text"

## Evaluation

- **Therapy Report Prep V2 (2026-07-17):** Conv improved +10pts (45% → 55%) after applying
  three-mode instructions to ProgressAnalysis, RecertAnalysis, DischargeAnalysis,
  EvalAnalysis, and ManualIntakeFallback
- Remaining Conv failures were facility-metric questions requiring facility-specific data
  the agent cannot have — these are eval-setup issues (Pattern E5), not agent refusal
