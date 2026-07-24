# Auto Eval Script

Triggers evaluation runs and monitors them until complete. Handles the full Copilot Studio eval workflow.

## Usage

```bash
node auto_eval.cjs
```

Triggers SLP Conv and PT Conv sequentially, monitoring each (~10 min per eval, ~20 min total).

## How It Works

1. Navigates to agent evaluation page
2. Clicks the 20/100 test cases link
3. Clicks Evaluate → Run
4. Polls every 30s for completion
5. Returns the score when done

## Pitfalls

- Must run in FOREGROUND on Windows (background fails with `stdin is not a tty`)
- Only 1 eval can run at a time across all agents
- Timeout after 20 min per eval (40 x 30s polls)
- Requires Chrome on port 9223 with authenticated Copilot Studio session

## Location

`C:/Users/kevin/AppData/Local/hermes/profiles/coding-profile/home/auto_eval.cjs`
