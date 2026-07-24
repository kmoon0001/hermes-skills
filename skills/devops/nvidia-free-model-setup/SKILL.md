---
name: nvidia-free-model-setup
description: "Configure Hermes Agent to use NVIDIA free Minimax M3 model via NIM APIs."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# NVIDIA Free Model Setup for Hermes

This skill captures the reusable steps to add a free NVIDIA model (currently **MiniMax M3 Preview**) to Hermes Agent.

## Prerequisites
- Have a **NVIDIA API key**. Obtain it from the NVIDIA NIM console (https://build.nvidia.com/).
- Hermes Agent installed and a functional profile (e.g., `coding-profile`).

## Steps
1. **Add the NVIDIA provider** (if not already present):
   ```bash
   hermes config set model.provider nvidia
   ```
2. **Set the default model** to the free MiniMax M3 preview:
   ```bash
   hermes config set model.default minimaxai/minimax-m3
   ```
3. **Add the API key** to the environment file:
   - Open `~/.hermes/.env` in an editor (e.g., `notepad %USERPROFILE%\.hermes\.env`).
   - Append the line (replace `<YOUR_KEY>` with the actual key):
     ```
     NVIDIA_API_KEY=<YOUR_KEY>
     ```
   - Save the file.
4. **Restart or start a fresh session** so the new config takes effect (`/reset` inside a chat or relaunch the CLI).
5. **Verify** by checking the active model:
   ```bash
   /model
   ```
   You should see `nvidia` as the provider and `minimaxai/minimax-m3` as the selected model.

## Pitfalls & Tips
- **Missing API key** – Hermes will silently fail to call the model. Ensure the key is present and has no surrounding spaces.
- **Session caching** – Config changes only apply to new sessions. Use `/reset` after editing `.env`.
- **Rate limits** – The free tier has generous limits, but a sudden surge of requests may hit temporary throttling. If you see `429 Too Many Requests`, back‑off and retry.
- **Model name spelling** – The correct identifier is `minimaxai/minimax-m3`. Typos will cause an “model not found” error.

## References
- See `references/minimax-m3.md` for the official NVIDIA endpoint snippet and usage example.

---

**When to use**: Any time you need to quickly configure Hermes to use a free NVIDIA model for coding, reasoning, or multimodal tasks.
