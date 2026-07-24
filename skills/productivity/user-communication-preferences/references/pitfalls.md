## Pitfalls for Communication

- **No markdown** – All user‑facing messages must be plain text. Avoid markdown syntax like `*bold*`, `- lists`, or code fences unless explicitly required for code snippets.
- **Keep it short** – Users have asked for concise answers. Limit explanations to one‑sentence summaries unless deeper detail is requested.
- **ALL CAPS for casual** – When a casual tone is appropriate, use ALL CAPS as per Kevin's style preference.
- **Don't duplicate skill content in memory** – If a memory entry is essentially the same info that's already in a skill, replace it with a one-liner pointer. Memory is 2,200 chars; skills are unlimited. Kevin noticed memory was 100% full and asked to see/compact it — proactively keep it under 30%.
- **Explain system constraints early** – When a limit becomes relevant (memory cap, tool timeout, etc.), mention it before it causes a problem, not after the user asks why something broke.
- **"env" = `.env` file, NOT Copilot Studio environment** – When Kevin says "env", "enfv", or ".env", he means the dot-env configuration file where he stores API keys (e.g. `~/.hermes/.env`). Do NOT interpret this as a Copilot Studio / Dataverse / Power Platform environment unless the surrounding conversation is explicitly about agents, bots, publishing, or agent management. If unsure, just show him the `.env` file(s) rather than guessing.
