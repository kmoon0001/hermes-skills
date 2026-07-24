# Therapy AI Dev Environment (orgbd048f00)

## Gateway API Details

| Property | Value |
|----------|-------|
| Org URL | `https://orgbd048f00.crm.dynamics.com` |
| Environment ID | `a944fdf0-0d2e-e14d-8a73-0f5ffae23315` |
| Gateway host | `https://powervamg.us-il106.gateway.prod.island.powerapps.com` |
| Gateway API base | `/api/botmanagement/v2/environments/{env}/bots/{bot}` |
| Tenant ID | `03cc92c3-986c-4cf4-ae27-1478cf99d17f` |
| Token resource | `https://orgbd048f00.crm.dynamics.com` |
| Eva token scope | `api://96ff4394-9197-43aa-b393-6a41652e21f8` |

## Refresh Eval Token

```bash
cd ~/skills-for-copilot-studio/scripts
node refresh_eval_token.cjs    # writes to ~/.copilot-studio-cli/test-agent-token.txt
```

Token expires ~85 min. Verify: `head -c 30 ~/.copilot-studio-cli/test-agent-token.txt` should start with `eyJ`.

## Bot IDs in This Environment

| Agent | Bot ID |
|-------|--------|
| SNF Command Center V2 | `9f3e370c-a747-f111-bec6-0022480b6bd9` |
| SNF AI Dashboard V2 | `bd570423-cf47-f111-bec5-70a8a5b1c3a3` |
| Pacific Coast QM Tracker and Coach | `ea52ad9c-8233-f111-88b3-6045bd09a824` |
| Pacific Coast Denial Defense V2 | `6d7815b4-ce47-f111-bec5-70a8a5b1c3a3` |
| Therapy Report Prep V2 | `fd1bce12-cf47-f111-bec5-70a8a5b1c3a3` |
| Pacific Coast Case Historian | `ad635500-cf47-f111-bec5-70a8a5b1c3a3` |
| Copy Therapy Doc Feedback | `b0346795-4876-f111-ab0e-70a8a5b1b8cc` |

## Conv Eval Test Sets (QM Tracker and Coach - MultiTurn 20-case)

| Test Set ID | Name |
|-------------|------|
| `6a864a10-b8d2-49c9-a8a0-2f88dea58603` | Evaluate Pacific Coast QM Tracker and Coach |

## SR Eval Test Sets (QM Tracker and Coach - SingleTurn 100-case)

| Test Set ID | Name |
|-------------|------|
| `fcf19677-240e-45a1-ad44-03374afa460b` | Evaluate Pacific Coast QM Tracker and Coach |
