# Topic-Level Pitfalls

## The "Third Turn Error" Pattern (Missing EndDialog)

### Symptom
The grader says: *"In the third response, the agent refuses to help by showing an error message."* The agent handles turns 1-2 correctly but fails on turn 3.

### Root Cause
The topic uses `SearchAndSummarizeContent` but has NO `EndDialog` after it. Without an explicit `EndDialog`, Copilot Studio does NOT clear the topic queue after the topic finishes. This causes:

1. **Turn 1**: Topic fires → answers correctly → ends implicitly (no queue cleanup)
2. **Turn 2**: User follow-up → a different topic or Fallback triggers → answer quality degrades
3. **Turn 3**: Topic queue becomes inconsistent → Copilot Studio throws an internal error → agent shows "refuses to help" message

### Fix
Add `EndDialog` with `clearTopicQueue: true` after EVERY `SearchAndSummarizeContent`:

```yaml
  actions:
    - kind: SearchAndSummarizeContent
      id: answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Be concise with top 3 findings by severity
    - kind: EndDialog
      id: done
      clearTopicQueue: true
```

### Verification
After fixing, check that the topic YAML contains both:
- `kind: EndDialog`
- `clearTopicQueue: true`

Each is independently checked. Missing `clearTopicQueue` is equivalent to `clearTopicQueue: false`.

## The Hidden 800-Char Limit

### Symptom
Agent-level instructions are clean (no 800-char limit), but responses are still truncated. The grader reports responses are "too short" or "lack detail."

### Root Cause
Each `SearchAndSummarizeContent` topic has its own `additionalInstructions` field that may contain a stale `- Keep response under 800 characters` constraint. This is invisible when you only check the agent-level instructions on the Overview page.

### How to Find
Every `SearchAndSummarizeContent` topic YAML needs to be inspected. Look for patterns like:
- `- Keep response under 800 characters with top X findings by severity`
- `- Limit responses to 800 characters`
- `- 800 characters max`

### Fix
Replace with:
```
- Be concise with top 3 findings by severity
```
Or any phrasing that communicates conciseness without a numeric constraint.

### Scope
In this user's fleet (PT_Specialist), a full sweep of all 18 leaf topics found that ALL of them had this stale 800-char limit. Fixing agent-level instructions does NOT cascade to topics.

## Batch Fixing — Why Browser UI Automation Fails

Attempting to batch-fix 17+ topic YAMLs via playwright-cli browser automation is UNRELIABLE:

| Failure Mode | Cause |
|-------------|-------|
| Ref IDs change per navigation | Every `goto` invalidates ALL prior element refs |
| SPA load time varies | `sleep 10` is too short for some topics, too long for others |
| Save button detection fails | Save ref only appears after code editor opens asynchronously |
| YAML extraction via view-line | Content escaping differs per editor state |
| fill with multi-line content | Shell escaping converts actual newlines to literal `\\\\n` sequences |

## Reliable Individual Topic Fix: Code Editor Approach

For fixing ONE topic at a time (not batch), the **More > Open code editor**
flow is reliable via Playwright:

1. Click the topic name in the topics list
2. **More** > **Open code editor** (opens Monaco YAML editor)
3. `Ctrl+A`, paste corrected YAML via `navigator.clipboard.writeText()`
4. Save button is ENABLED (Monaco triggers CS's save tracker correctly)

This bypasses the React Save-button bug that plagues the visual canvas editor
where `fill()`/`type()` fail to trigger React's `onChange`. See the main
`copilot-studio-development-workflow` skill's Common Pitfalls section and
`references/cdp-code-editor-workflow.md`.

Key difference from visual editor: Monaco is a real text editor, not a
React-controlled contenteditable. It properly triggers Copilot Studio's
internal dirty-state tracking, so Save works reliably.

## Better Approach: Dataverse Web API PATCH

Use the Dataverse Web API with a Bearer token (extracted from the browser's MSAL cache):

```python
import requests

# token from page localStorage.getItem('cacheLocation') or pac auth
headers = {
    "Authorization": f"Bearer {bearer_token}",
    "Content-Type": "application/json",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0"
}

# Query all topic botcomponents for an agent
api = "https://orgXXXXX.crm.dynamics.com/api/data/v9.2"
params = f"?$filter=parentbotid eq {bot_id} and componenttype eq 9&$select=botcomponentid,name,content"
resp = requests.get(f"{api}/botcomponents{params}", headers={**headers, "Accept": "application/json"})

for bc in resp.json().get("value", []):
    yaml = json.loads(bc["content"])  # content is JSON-encoded YAML
    if "800" in yaml or "Keep response" in yaml:
        fixed = yaml.replace("Keep response under 800 characters", "Be concise")
        fixed = fixed.replace("800 characters", "concise")
        requests.patch(f"{api}/botcomponents({bc['botcomponentid']})", headers=headers, json={"content": fixed})
```

**CORS limitation**: You CANNOT do this from a browser `fetch()` in the Copilot Studio page context — the Dynamics API doesn't return CORS headers for the `copilotstudio.microsoft.com` origin. You need a server-side HTTP client or a Bearer token outside the browser.
