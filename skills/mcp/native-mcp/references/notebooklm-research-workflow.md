# NotebookLM Research Knowledge Base Workflow

A repeatable pattern for building topic-specific research notebooks in NotebookLM via the `nlm` CLI, then querying them for grounded, citation-backed insights.

## When to Use

- You need to research a topic deeply and get structured, grounded answers
- You want a searchable knowledge base with citations from curated + auto-discovered sources
- You're building a reference corpus for agent development, compliance, or domain learning

## Step 1: Create the Notebook

```bash
nlm notebook create "Topic Name"
```

Returns JSON with `notebook_id` and `url`. Save the notebook_id for subsequent operations.

## Step 2: Add Curated Sources (Direct URLs)

Add sources in batches of ~7 URLs per call (rate limit). Use repeatable `-u` flags:

```bash
nlm source add <notebook-id> \
  -u "https://docs.example.com/page1" \
  -u "https://docs.example.com/page2" \
  --wait
```

`--wait` blocks until all sources finish processing. Omit it for fire-and-forget and check later with `nlm notebook get <notebook-id>`.

**Source types supported:** URLs (web pages, docs, GitHub, PDFs), pasted text, Google Drive documents, local files (PDF, TXT, MD, DOCX, CSV, EPUB, audio, video, images).

## Step 3: Run Deep Web Research

Deep research (~5 min, ~40-90 sources) automatically discovers relevant sources:

```bash
# Auto-import (recommended — waits + imports)
nlm research start "research query about topic" -n <notebook-id> --mode deep --auto-import
```

Without `--auto-import`, check status and import manually:
```bash
nlm research start "query" -n <notebook-id> --mode deep
nlm research status <notebook-id>
nlm research import <notebook-id> <task-id>
```

The deep mode searches the web, finds 40-90 sources, and imports them into the notebook. Fast mode (~30s, ~10 sources) is for quick drafts.

## Step 4: Check Progress

```bash
nlm notebook get <notebook-id>
```

Returns `source_count` and list of all source titles. Useful for spotting 404s or irrelevant sources that should be cleaned up.

## Step 5: Query for Insights

Query the notebook with targeted questions. Each query returns grounded answers with citations back to specific sources:

```bash
nlm notebook query <notebook-id> "Specific question about the topic"
```

**For comprehensive analysis, fire multiple parallel queries** covering different sub-topics. Each query operates independently and returns structured JSON with `answer`, `sources_used`, `citations`, and `references` arrays.

Good query strategy:
- One query per subtopic / dimension
- Ask for specific lists, comparisons, or how-to steps
- Use the answers to inform decisions, not just for information gathering

## Step 6: Create Slide Deck

Generate a presentation from the notebook's sources:

```bash
nlm slides create <notebook-id> --confirm
```

Returns an `artifact_id` (e.g., `48e1a537-9bd1-43f5-8763-7c488126c73b`). Generation takes ~1-2 minutes — check status:

```bash
nlm studio status <notebook-id> --artifact-id <artifact-id>
```

Once status is `"completed"`, download the deck:

```bash
nlm download slide_deck <notebook-id> <artifact-id> --output "~/Desktop/topic-deck.pptx"
```

## Step 7: Extract and Act

The query response includes:
- `answer` — the grounded response text
- `sources_used` — which source IDs were referenced
- `citations` — numbered citation map
- `references` — full per-source cited text excerpts with source titles

Use these to build action plans, presentations, or configuration decisions.

## Practical Tips

- **Target 100+ sources** for comprehensive coverage. Use direct URLs for core docs + deep research for discovery.
- **Separate notebooks by domain.** One notebook per major topic (e.g., "Hermes Advanced Setups" and "Copilot Studio Tactics").
- **Delete broken sources** (404s, etc.): `nlm source delete <notebook-id> <source-id-1> <source-id-2> --confirm` — source IDs are positional args, NOT `--source-ids` flag. The `--confirm` flag is required and prompts per-source.
- **Deep research is async.** The `--auto-import` flag makes it synchronous. Without it, run `research status` then `research import` in a background process.
- **Citations are per-query.** Each query independently selects the most relevant sources from the notebook. Asking the same question twice may cite different reference texts.

## Example: Two-Notebook Split

Used in production to research Hermes Agent setups AND Copilot Studio in parallel:

| Notebook | Sources | Topics Queried |
|---|---|---|
| "Crazy Hermes Setups" | 140 | MCP servers, free LLMs, automations, connectivity, GUI |
| "Microsoft Copilot Studio Advanced Tactics" | 112 | Skills, MCP connectors, Power Fx, Power Automate, HIPAA, FHIR |
