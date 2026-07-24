# Microsoft Learn References

Use these official references during Copilot Studio evaluation repair:

- Evaluation triage quick reference: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-quick-reference
- Triage agent failures: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-failure
- Pattern analysis: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-pattern
- Remediation strategies: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-remediation
- Evaluation overview and methods: https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-overview
- Edit evaluation test cases: https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-edit-cases
- Generative orchestration instructions: https://learn.microsoft.com/microsoft-copilot-studio/guidance/generative-mode-guidance
- Prompt modification best practices: https://learn.microsoft.com/microsoft-copilot-studio/nlu-generative-answers-prompt-modification
- Generative answers in topics: https://learn.microsoft.com/microsoft-copilot-studio/nlu-boost-node
- Generative orchestration best practices: https://learn.microsoft.com/microsoft-copilot-studio/advanced-generative-actions#best-practices

Key official guidance to preserve:

- Triage failures before changing the agent. If the response is acceptable or the expected answer is wrong, fix the evaluation first.
- Use pattern analysis after at least five failures. If one root cause is 80% or more of failures, fix that category.
- Treat flat scores after remediation as a sign that the root cause was likely misclassified.
- Keep instructions grounded in available tools and knowledge. Instructions cannot make unavailable tools or sources usable.
- Use concise, specific instructions with clear response format and an alternative path when the agent cannot complete the task.
- Topic, tool, agent, and knowledge descriptions affect generative orchestration. Make names and descriptions specific and non-overlapping.
