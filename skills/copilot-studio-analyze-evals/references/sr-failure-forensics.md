# SR Failure Forensics — Connector Gate & No-Note Framework (Validated 2026-07-12)

## Run with exactly 9 SR failures (Feedback B, bot b0346795)
- File: `D:\my agents copilot studio\pipeline\eval_full_details\FeedbackB_run_00d93911_detail.json`
- Run id `00d93911-f96b-404a-b0af-1e255a9551b4`, startTime `2026-07-05T19:30:34Z`, 91 pass / 9 fail.
- User-premise: "failures ask about features (inline citations, color coding, 7 Habits)".
- ACTUAL classification (from grader `properties` + agent `answer`):
  - 5 of 9 = **connector/auth gate** — agent replied "Let's get you connected first… Open connection manager to verify your credentials" (sign-in demanded before answering a general knowledge question).
  - 4 of 9 = **no-note "review" questions** — "review my progress note" with no note pasted; agent gave a generic framework; grader marked completeness=No / abstention=Yes.
  - Only 1 of 9 touched 7 Habits; NONE asked about inline citations or color coding.
  - All 3 features (inline citations, 🔴🟡🟢 risk levels, 7 Habits knowledge) were PRESENT in live instructions `I_Copy Therapy Docuementation Feedback Ag.yml` and `K_Ensign Habit 1–7`.

## Connector-gate source
- Topic `T_Sign in .yml` (in `feedback_b_snapshot_<date>\`):
  ```yaml
  kind: AdaptiveDialog
  beginDialog:
    kind: OnSignIn
    actions:
      - kind: ConditionGroup
        condition: =System.SignInReason = SignInReason.SignInRequired
        actions:
          - kind: SendActivity
            activity: Hello! To be able to help you, I'll need you to sign in.
      - kind: OAuthInput
        title: Login
        text: To continue, please login
  ```
- This fires on general questions needing only knowledge-source grounding. The grader sees "connect and verify credentials" as an abstention/refusal → Fail.
- Impact across Feedback B SR runs (2026-07-05 batch): run 07dc0e61 = 67 of 69 fails connector-gate; 16263da5 = 46 of 47; 6331d6db = 12 of 23. **Dominant SR driver when present.**

## Fix — make general questions answerable WITHOUT sign-in (Validated 2026-07-12)

The failure is a bot-level auth posture, not a missing feature. All three features (inline citations, 🔴🟡🟢, 7 Habits) were present and working.

**PRE-CHECK (do first):** confirm no topic/connector needs delegated end-user auth.
- Scan `T_*.yml` for `connectionReference|OAuthInput|SignIn|delegat`. For each connector, check `mode:` — `Invoker` = agent identity (safe under None); delegated/OAuth-on-behalf-of = would need auth.
- In this agent the only connector was Work IQ Teams MCP in `Invoker` mode; OCR/doc-upload used shared agent-scoped connections. → global `None` is safe.

**THE CHANGE — settings.mcs.yml:**
```yaml
authenticationMode: None          # was: Integrated
authenticationTrigger: AsNeeded    # was: Always
```
- `None` = no user auth required; `Invoker` connectors + shared OCR still work (agent identity).
- `AsNeeded` → `OnSignIn` only fires if a topic needs it; under `None`, `SignInRequired` is never raised, so `T_Sign in .yml` goes dormant.
- ADDITIVE: keeps every feature. Do NOT delete `T_Sign in .yml` (preserve gate for any future delegated-auth connector).

**Apply:**
- UI (no token): Settings → Authentication → None + AsNeeded → Publish.
- API: PATCH bot `authenticationmode` via `manage-agent.bundle.js` + publish. Local tokens expired 2026-07-11; refresh via `node refresh_token.cjs`.

**Impact:** recovers the connector-gated share (5 of 9 in 00d93911; 67 of 69 in 07dc0e61). Does NOT fix the 4 no-note "review" failures — those need the DATA-SPARSE PROMPTS instruction block (copilot-studio-edit-agent skill).

## No-note "review" question → generic framework
- Agent output starts "Here is a preliminary standards-based… framework for data-sparse prompts."
- Grader pattern-matches the words "framework"/"preliminary" as abstention/refusal (same class of issue as the EVAL-instruction "framework" pitfall, but here it is the AGENT output wording).
- Fix direction: instruction to answer general/standard questions directly from knowledge (already in EVALUATION MODE of Feedback B instructions) AND avoid "framework"/"preliminary" preamble wording on no-note conceptual questions.

## Forensics recipe (reuse)
```python
import json, glob, os
base = "D:/my agents copilot studio/pipeline/eval_full_details"
for f in glob.glob(base + "/FeedbackB_run_*_detail.json"):
    try: d = json.load(open(f, encoding="utf-8"))
    except: continue
    tc = d["details"]["testCases"]
    if len(tc) != 100: continue   # SR runs = 100; skip Conv (10)
    nf = ngate = 0
    for c in tc:
        for m in (c.get("graderMetrics") or {}).get("queryResponseMetrics", []):
            if m.get("evaluationResult") == "Fail":
                nf += 1
                a = c["queries"][0].get("answer", "")
                if "connect" in a.lower() and "credential" in a.lower(): ngate += 1
    print(os.path.basename(f), "fails:", nf, "gate:", ngate)
```
