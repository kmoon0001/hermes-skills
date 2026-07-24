# DeepSeek API Key Discovery (Windows)

## Problem

On Windows, API keys are often stored as user-level environment variables
(set via System Properties or `setx`) rather than in shell config files.
Shell sessions (git-bash, MSYS) may not inherit these variables, so
`echo $DEEPSEEK_API_KEY` returns empty even though the key exists.

## Extraction

```bash
# Get from Windows user env
DEEPSEEK_KEY=$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')" 2>/dev/null | tr -d '\r\n')
export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
```

The `tr -d '\r\n'` is critical — PowerShell output on Windows includes
carriage returns that corrupt the key.

## Verification

```bash
# Check key format (DeepSeek keys start with sk-)
echo "Key: ${DEEPSEEK_API_KEY:0:10}... (len: ${#DEEPSEEK_API_KEY})"

# Test API access
curl -s "https://api.deepseek.com/v1/models" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

Expected output: `{"object":"list","data":[{"id":"deepseek-v4-flash",...},{"id":"deepseek-v4-pro",...}]}`

## Alternative Locations

Check these if the PowerShell method returns empty:
- `hermes auth list | grep deepseek` — Hermes may have the credential
- `~/.bashrc`, `~/.bash_profile` — shell configs
- `.env` files in project roots
- `~/.hermes/auth.json` credential pool

## Known Models

| Model | Best For | Speed |
|-------|----------|-------|
| `deepseek-v4-flash` | Code review, bug fixes, test gen | Fast |
| `deepseek-v4-pro` | Complex refactors, architecture | Slower, better reasoning |
