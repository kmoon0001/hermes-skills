# Microsoft Learn Evaluation Triage Framework

Key excerpts from Microsoft Learn for Copilot Studio agent evaluation.

## General Quality Grading Criteria
The grader evaluates on 4 criteria — ALL must pass:
1. **Relevance** — Does the response address the question?
2. **Groundedness** — Is the response based on provided context?
3. **Completeness** — Does the response cover all aspects? (800-char limits FAIL this)
4. **Abstention** — Did the agent attempt to answer?

## Non-Determinism Rules
- "Up to 5% variance between runs is normal for language model graders"
- "If runs vary by more than 10%, investigate grader reliability before diagnosing agent problems"
- "For evaluation sets with fewer than 30 test cases, a single test case changing from fail to pass changes the score by 3% or more"
- "Run the full evaluation set at least three times before treating any score as a baseline"

## Thresholds (MS Learn)
| Quality signal | Blocking threshold |
|---|---|
| Safety and personal data | < 95% blocks shipping |
| Compliance and verbatim content | < 95% blocks shipping |
| Factual accuracy | < 80% blocks shipping |
| Knowledge grounding | < 80% blocks shipping |

## Iteration Completion Criteria
"Reruns produce consistent scores with less than 5% variance between runs"

## Source
- https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-readiness
- https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-overview
- https://learn.microsoft.com/microsoft-copilot-studio/guidance/optimize-prompts-custom-instructions
