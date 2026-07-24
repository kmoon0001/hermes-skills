# MiniMax M3 (Free) – NVIDIA NIM

- **Model identifier**: `minimaxai/minimax-m3`
- **Endpoint**: `https://integrate.api.nvidia.com/v1/chat/completions`
- **Free tier**: Unlimited usage for the preview model (subject to NVIDIA's trial terms).
- **Typical request payload**:
```json
{
  "model": "minimaxai/minimax-m3",
  "messages": [{"role": "user", "content": "Your prompt here"}],
  "max_tokens": 8192,
  "temperature": 1.0,
  "top_p": 0.95
}
```
- **Headers** (replace `$NVIDIA_API_KEY`):
```
Authorization: Bearer $NVIDIA_API_KEY
Accept: application/json
```
- **Notes**:
  - Multimodal: you can send images or video URLs via the `content` list (see NVIDIA docs).
  - Pricing: free tier, but higher‑tier usage incurs per‑token fees.
  - Logging: requests are logged per NVIDIA's trial policy; avoid sending confidential data.
