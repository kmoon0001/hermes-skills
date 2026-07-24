# Live Dataverse PATCH + Inline-Quote Recipe (Medicare Part B Compliance Agent)

Reproducible recipe used Jul 13 2026 to add the inline verbatim-quote + citation feature to the
Medicare Part B Compliance Agent (bot b0346795) in Therapy AI Agents Dev env (a944fdf0).

## 1. Component IDs (this agent)
- Instructions component (type 15): `1b6244b9-f417-4027-a601-0d94c9d3ef9c`
- Progress Report Review topic (type 9): `fcd7c66e-e6b0-40fc-84fe-59b16119027d`
Find any component id live from the agent's `components-core.json` (`value[]` array) by matching `displayName` + `componenttype`.

## 2. Token + PATCH (instructions component)
```bash
TOKEN=$(az account get-access-token --resource "https://orgbd048f00.crm.dynamics.com" --query accessToken -o tsv)
CID="1b6244b9-f417-4027-a601-0d94c9d3ef9c"
# body.json = {"data": "<full instructions text under the instructions: |- block>"}
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X PATCH \
  "https://orgbd048f00.api.crm.dynamics.com/api/data/v9.2/botcomponents($CID)" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "OData-MaxVersion: 4.0" -H "OData-Version: 4.0" \
  --data @body.json
# expect HTTP 204 (no body)
```

## 3. PATCH (topic — whole YAML as data)
```bash
CID="fcd7c66e-e6b0-40fc-84fe-59b16119027d"
# body.json = {"data": "<entire topic YAML file content>"}
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X PATCH \
  "https://orgbd048f00.api.crm.dynamics.com/api/data/v9.2/botcomponents($CID)" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "OData-MaxVersion: 4.0" -H "OData-Version: 4.0" --data @body.json
```

## 4. VERIFY readback (mandatory — do not trust 204)
```bash
curl -s "https://orgbd048f00.api.crm.dynamics.com/api/data/v9.2/botcomponents($CID)?\$select=data" \
  -H "Authorization: Bearer $TOKEN" -H "OData-Version: 4.0" \
  | python3 -c "import sys,json; t=json.load(sys.stdin).get('data',''); print('rule present:', 'G4a' in t)"
```

## 5. The inline-quote rule texts that were added

### 5a. Instructions guardrail (G4a)
```
G4a. Inline Quoted Evidence (MANDATORY for document reviews): For every finding on a submitted document, you MUST quote the EXACT flagged passage from the user's documentation inline, immediately followed by its regulation citation. Format: > "[exact verbatim phrase from the note]" — [Regulation citation, e.g. Medicare Benefit Policy Manual Chapter 15 Section 220]. The quote must be the literal text as written in the submitted note (not a paraphrase). If the phrase is missing entirely, write > "[Not documented in submitted note]" — [Regulation citation]. Always pair the quotation and the citation inline so the reader sees the flagged text next to the rule it violates.
```

### 5b. Topic SearchAndSummarizeContent userInput (appended to the Concatenate string)
```
MANDATORY INLINE QUOTE RULE: For EVERY finding, you MUST embed the EXACT verbatim phrase from the submitted Progress Report that triggered the finding, inside quotation marks, immediately followed by its regulation citation. Example: > "Patient tolerated treatment well and is making progress" — Medicare Benefit Policy Manual Chapter 15 Section 220 (lacks objective measurable progress). If a required element is absent, write > "[Not documented in submitted note]" — [Regulation citation]. Do NOT paraphrase the flagged text; quote it word-for-word from the OCR payload.
```

### 5c. Topic additionalInstructions (double-quoted — contains internal colon)
```
additionalInstructions: "Provide specific, source-grounded audit findings with inline citations AND inline verbatim quotations of the exact flagged text from the submitted document. For each finding, quote the literal phrase (or state [Not documented]) then the regulation citation, inline. Report what is present, what is missing, and what CMS requires. If OCR data is missing, state that clearly. Keep responses concise (under 900 characters). Never output raw citation tokens or metadata (cite:1, Citation-1, etc.). Reference sources by natural document name only."
```
**PITFALL:** the `additionalInstructions` value contains `For each finding,` — an internal colon. An UNQUOTED plain scalar with a mid-value `:` breaks YAML parse (`mapping values are not allowed here`). Always double-quote such values.

## 6. Scope note
Only the Progress Report Review topic was updated this pass. Other inline-review topics
(Treatment Encounter, Evaluation/Plan of Care, Discharge Summary, Recertification, Episode of Care)
still use the old citation-only prompt and need the same G4a rule applied for uniform behavior.
