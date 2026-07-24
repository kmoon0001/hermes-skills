# Healthcare Agent "Allow Ungrounded Responses" Guidance

## Source: Microsoft Learn Copilot Studio Documentation

From the official FAQ for generative answers:

> "To enable agents to answer questions outside the scope of their configured
> knowledge sources, makers can turn on the Allow ungrounded responses feature.
> **To limit agents to only answer questions within the scope of their configured
> knowledge sources, makers should turn off this feature.**"

From the image input analysis page:

> "If you're having problems generating high-quality responses from files, turn on
> the Allow ungrounded responses setting in the Knowledge section of your agent's
> Generative AI settings. **This setting is required if there are no relevant
> knowledge sources configured.**"

## Healthcare Recommendation: KEEP OFF

For healthcare/therapy documentation agents, "Allow ungrounded responses"
should stay **OFF** because:

1. **Clinical safety**: With ungrounded OFF, the agent can ONLY answer from
   configured knowledge sources (CMS Chapter 15, AOTA guidelines, 42 CFR, etc.).
   This prevents hallucination of clinical facts from model weights alone.

2. **Microsoft's guidance**: The "limit agents to only answer questions within
   the scope of their configured knowledge sources" is the safe/conservative
   default for regulated domains.

3. **Compliance**: HIPAA and CMS don't want AI generating clinical content
   from model weights without knowledge grounding.

## The Refusal Cascade Problem

With ungrounded OFF, if the orchestrator can't find a matching knowledge source
OR a matching topic, the agent **refuses to answer**. This produces mass
abstention failures in evaluations (e.g., 35/44 SR failures as "refuses to help").

## The Refusal Cascade — TWO Refusal Paths

When ungrounded is OFF and Conversational boosting is ON, there are actually
**two separate refusal paths**, not one:

1. **Fallback topic** — fires when NO system or custom topic matches the query.
   Its default message is "I'm sorry, I can't help with that." Fix: replace
   with a helpful redirect.

2. **Conversational Boosting's own fallback** — fires when a topic DOES match
   but `CreateGenerativeAnswers` returns no answer (`IsBlank(Topic.Answer)`).
   The DEFAULT `elseActions` says: *"I don't have specific information on that
   in my knowledge sources. Could you rephrase...?"* — a SECOND refusal.

Both must be fixed. Fixing only the Fallback topic leaves the CB refusal path
active. See `templates/conversational-boosting-fixed.yaml` for the CB fix.

## The Healthcare-Safe Fix Path (NOT turning ungrounded ON)

1. **Coverage**: Ensure knowledge sources cover ALL test domains
2. **Fallback topic**: Replace "I can't help" with a helpful redirect listing
   what the agent CAN do
3. **Conversational boosting**: Turn ON AND replace its refusal `elseActions`
   message with the same helpful redirect as Fallback (see template)
4. **Instructions**: Add anti-refusal language ("NEVER refuse to help") but
   recognize instructions alone won't overcome missing knowledge coverage
