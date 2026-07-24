# Timestamp + inject preferences (Kevin)

## Local time
- Always convert Dataverse/`pac` UTC (`publishedon`, "Succeeded […]", sync times) to **Pacific local** before reporting.
- Never present bare UTC as the time the user should use.

## Inject vs paste
- When the user asks for agent instructions or Generative AI Responses formatting and the agent is live: **PATCH + publish** (type-15 `data` / `responseInstructions`), do not only dump paste blocks.
- Draft text only if they explicitly want review-before-inject.
