---
name: copilot-studio-create-eval-set
description: "Create a test set CSV file for import into Copilot Studio Evaluate tab. Reads agent topics, instructions, and knowledge sources to generate meaningful test cases with appropriate graders."
category: copilot-studio
---

# Create Evaluation Test Set

Create a test set CSV file that can be imported into Copilot Studio's Evaluate tab for in-product agent evaluation.

## Phase 1: Understand the Agent
1. Glob for `**/agent.mcs.yml` — find the agent
2. Read agent.mcs.yml — instructions, description, capabilities
3. Read settings.mcs.yml — orchestration mode
4. Glob for `**/topics/*.mcs.yml` — list all topics
5. Read key topics — trigger phrases, flows, expected behaviors

## Phase 2: Design Test Cases
Cover: Core functionality, Knowledge/generative, System topics, Edge cases, Boundary. Aim for 10-25 cases.

## Phase 3: CSV Format
```csv
"question","expectedResponse"
"User question","Expected response or rubric"
```
Max 100 questions, 1000 chars each. expectedResponse optional. Test methods configured in UI after import.

## Phase 4: User Instructions
Import via: Evaluate tab > New evaluation > Single response > drag CSV file.