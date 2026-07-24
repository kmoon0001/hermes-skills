# Sealed-data codebase and experiment audits

Use this reference when inspecting research or backtest code while validation/holdout periods must remain unopened.

## Scope lock before inspection

1. Write down the permitted periods, prohibited periods, allowed artifact classes, and prohibited actions.
2. Inventory names and Git state before opening content. Treat raw data, cached panels, generated results, notebooks, reports, and logs as separate exposure classes.
3. Do not run experiment runners, downloaders, notebooks, or commands that may transitively load data unless their boundary behavior has first been inspected.
4. Keep a read ledger: source/docs/tests opened, commands run, and confirmation that no raw or result-bearing sealed artifact was accessed.

## The mixed-file trap

A date filter does not prove sealed-data isolation. Code like this reads every row before slicing:

```python
frame = pd.read_feather(path)
frame = frame.loc[start:end]
```

If `path` contains holdout rows, the holdout was accessed even if it never appears in output. The same hazard applies to CSV, Parquet/Feather, database queries without predicates, and helper functions that load first and filter later.

Preferred controls, in order:

1. Physically segregated development-only files produced by an authorized data-custodian step.
2. A storage/query format with verifiable predicate pushdown, plus a manifest proving the allowed partitions.
3. A dedicated development snapshot with hashes, min/max timestamps, source identity, and generation provenance.

Do not “verify” a mixed file is safe by reading it in the restricted session; that inspection itself defeats the gate.

## Tiered verification of an allowed generated cache

When the engagement explicitly permits one local development cache but forbids sealed periods and result-bearing artifacts, verify in increasing exposure order:

1. Inspect only the staged source, tests, manifest, quality summary, and Git metadata first. Derive the permitted archive universe independently from the frozen requirements; do not trust counts copied into the prompt or implementation.
2. Reconcile manifest and quality claims programmatically from exact index blobs (`git show :path`): canonical ordering, unique URL set, full lineage fields, family/symbol/period counts, row-count totals, duplicate/conflict/nonpositive/outside-window aggregates, and hashes of staged evidence files.
3. Hash and size-check the explicitly allowed cache as opaque bytes before decoding it. This proves artifact identity without exposing row values or dates.
4. Inspect the focused artifact test before execution and confirm every transitive read is limited to allowed source/configuration/synthetic fixtures and the explicitly allowed cache. Do not run a broad suite whose data reads are unknown.
5. Only when the cache is explicitly authorized for semantic verification, run that single focused test with bytecode and pytest caches disabled. Immediately recheck staged identity and full Git status afterward.

A hash-only check proves identity, not causal semantics; a focused decode test proves the assertions it contains, not the safety of unrelated runners. Report these as separate evidence classes.

## Safe architecture inspection

Safe evidence usually includes source code, schemas, protocol documents, synthetic tests, Git metadata, and development-only audit manifests. Be cautious with reports and notebooks: prose, charts, or cached outputs can reveal sealed outcomes even when no raw dataset is opened.

For a minimal causal research engine, look for and recommend these boundaries:

- **snapshot/ingest:** obtains only authorized data and records hashes;
- **normalization/alignment:** emits `event_at`, `available_at`, validity, and staleness without strategy thresholds;
- **pure signal/target engine:** builds all matched variants through one code path;
- **runner:** freezes universe, periods, costs, and output metadata;
- **synthetic tests:** exercise causality without opening research data.

Avoid putting the first implementation directly into a trading strategy when callbacks, protections, ROI rules, capital competition, or framework state would add dimensions not present in the preregistered experiment.

## Point-in-time join review

Require separate concepts for measurement interval, event time, publication/availability time, and decision time. For strict delayed use, a robust pandas pattern is:

```python
pd.merge_asof(
    decisions.sort_values("decision_at"),
    observations.sort_values("available_at"),
    left_on="decision_at",
    right_on="available_at",
    direction="backward",
    allow_exact_matches=False,
)
```

Then apply independently frozen staleness and inception masks. Never interpolate, pre-inception backfill, or replace missing dependent features with a synthetic neutral value unless the protocol explicitly defines that behavior.

Minimum synthetic checks:

- an observation available exactly at a decision timestamp is deferred;
- future truncation leaves all earlier signals bit-identical;
- stale and missing observations disable dependent conditions;
- conflicting duplicate timestamps become invalid;
- pair/instrument inception is respected;
- actual candle close times are used instead of assuming `open + interval`;
- excluded feature families are absent from the schema, not merely disabled by a flag.

## Matched-variant attribution

All variants should share one simulator, price signal, timestamps, universe, costs, and execution rule. Express variants as compositional switches, for example base signal, then volatility control, then an additional data filter. Compare adjacent variants to isolate each layer.

When an added data source starts later or has intermittent gaps, freeze the estimand before running:

- primary comparison on a common-support mask applied to every variant; or
- full-window comparison where reduced eligibility is intentionally part of the treatment.

Without this choice, data availability can be mistaken for filter value.

## Closeout verification

- Run only synthetic/unit tests known not to load prohibited data.
- Re-check Git status and ensure no caches, result files, or snapshots were created unexpectedly.
- Report exactly what was and was not opened; distinguish “no raw holdout data” from the stronger claim “no artifact containing holdout outcomes.”
