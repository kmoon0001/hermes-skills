# Cross-Agent Knowledge Sharing via Instructions

## Problem
Copilot Studio knowledge sources (type 19 file-based components) are per-agent — the `_parentbotid_value` links each knowledge file to exactly one bot. There is no Dataverse API to "share" or "copy" a knowledge file component across agents. The file blob reference (`data` field) is not directly cloneable.

## Solution: Instructions-Based Knowledge Grounding
Add the **same approved knowledge source descriptions and hierarchy** to the target agent's instructions component (type 15). The model reads the instructions and applies the same regulatory framework, even without the actual knowledge files attached to the agent.

## Recipe (validated Jul 13 2026)

### 1. Get the source agent's knowledge hierarchy
From the source agent's instructions, extract:
- `## APPROVED KNOWLEDGE SOURCES` — list of source names with descriptions
- `## KNOWLEDGE HIERARCHY` — numbered priority list

### 2. Get the target agent's instructions component ID
```bash
TOKEN=$(az account get-access-token --resource "https://{org}.crm.dynamics.com" --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
  "https://{org}.crm.dynamics.com/api/data/v9.2/botcomponents?\$filter=_parentbotid_value%20eq%20'{targetBotGuid}'%20and%20componenttype%20eq%2015&\$top=5" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['value'][0]['botcomponentid'])"
```

### 3. Read the full live instructions
```bash
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
  "https://{org}.crm.dynamics.com/api/data/v9.2/botcomponents({instructionsId})"
```

### 4. Inject knowledge sources into `instructions:` block
Insert before `# SAFETY` section (or the last instruction section before guardrails):
```yaml
  ## APPROVED KNOWLEDGE SOURCES
  Use these sources as the primary authority for Medicare Part B therapy documentation and denial risk assessment:
  - Medicare Benefit Policy Manual Chapter 15 (Section 220, Section 230) — Coverage text
  - Jimmo v. Sebelius CMS FAQ — Maintenance therapy standards
  - 2026 Medicare Part B LCR Form and Instructions — Denial risk criteria
  - Ensign 7 Habits Documentation Framework (Habits 1-7) — Clinical quality framework

  ## KNOWLEDGE HIERARCHY
  1. Medicare Benefit Policy Manual — Primary CMS authority
  2. CMS Jimmo v. Sebelius guidance — Maintenance therapy
  3. 2026 Medicare Part B LCR Form — Current scoring
  4. Ensign clinical standards — Internal quality
  If sources appear inconsistent, favor the highest-ranking authority.
```

### 5. PATCH and verify
```python
data_updated = original_data.replace('\n  # SAFETY', knowledge_block + '\n  # SAFETY')
# PATCH body: {"data": data_updated}
# Expect HTTP 204
# Verify readback: GET and assert "APPROVED KNOWLEDGE SOURCES" in data
```

## Limitations
- The model references sources described in instructions but does NOT have direct file access (no `fileSearchDataSource` or `SearchSpecificFiles`).
- For full file-grounded answers, the actual knowledge files must still be uploaded per-agent via Copilot Studio UI or Dataverse `botcomponents` create with componenttype=14/19.
- Instructions-based knowledge works best for: citation standards, regulation hierarchy, scoring methodology, framework descriptions.
