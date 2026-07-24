# Causal Historical Derivatives-Data Audit

Use this before building a strategy from funding, open interest, premium/basis, positioning, or liquidation data. A value that is queryable today is not proof it was observable at the simulated decision time.

## Required timestamp model

Record these separately for every feature:

1. Exchange event or snapshot time.
2. Measurement-period open and close.
3. Funding settlement time, if applicable.
4. Exchange publication time or conservative publication assumption.
5. Collector ingestion time, when available.
6. Archive publication/retrieval time.
7. Earliest strategy decision allowed to consume the value.

Never merge on a generic `timestamp` until its semantics are identified. Execute on the next tradable bar after the conservative availability time.

## Source hierarchy

1. Immutable point-in-time captures produced by the live collector.
2. Official exchange archives with checksums and documented timestamp semantics.
3. Official historical API endpoints with independently verified retention and completeness.
4. Reputable vendors only after provenance, collection method, revisions, and missingness are documented.
5. Reject present-day reconstructed values whose historical availability cannot be established.

## Binance public-archive procedure

The official `data.binance.vision` S3 bucket can be catalogued without guessing URLs. Query the bucket XML by exact pair/year prefix so daily metric listings remain below the 1,000-key page limit. Relevant USD-M paths include:

- Monthly funding: `data/futures/um/monthly/fundingRate/{SYMBOL}/`
- Daily derivatives metrics: `data/futures/um/daily/metrics/{SYMBOL}/`
- Monthly premium-index klines: `data/futures/um/monthly/premiumIndexKlines/{SYMBOL}/{INTERVAL}/`

For each pair, family, and year:

1. Enumerate expected calendar labels independently.
2. Compare expected labels with ZIP keys; ignore `.CHECKSUM` keys when counting archives.
3. Verify representative ZIPs against their adjacent SHA-256 checksum files.
4. Parse every archive for the final quality gate; sample checks are not enough.
5. Report rows, unique timestamps, exact duplicates, descending steps, large gaps, and estimated missing intervals.
6. Preserve retrieval time and current checksums in the experiment manifest.

Binance states that daily files appear the following day, monthly files on the first Monday of the next month, and archived files may later be replaced after discovered issues. Present checksums establish current integrity, not historical immutability.

## Known schema eras to support

Do not assume one CSV timestamp representation across the archive:

- Funding archives use a `calc_time` field and may exhibit millisecond settlement jitter.
- Metrics archives use `create_time`; historical files can encode it as UTC text such as `YYYY-MM-DD HH:MM:SS`, not milliseconds.
- Older premium-index kline files can be headerless; newer files can include an `open_time` header.

Add regression fixtures for every encountered schema era. Normalize timestamps to UTC milliseconds only after recognizing the source format.

## Gap and duplicate rules

- Do not classify tiny funding settlement jitter as a missing interval. A practical detector should require a gap substantially larger than the expected cadence (for example, at least 1.5×) and estimate missing observations by rounded cadence multiples.
- Exact duplicate timestamps must be investigated at the full-row level. If duplicate rows are byte/value-identical, deterministic deduplication is permissible and must be reported.
- Never interpolate a missing derivative observation for a trading signal.
- Never forward-fill through a known outage. Mark the feature stale/unavailable and suppress any signal requiring it.
- Measure coverage from pair-specific feature inception; do not infer that all members of a fixed universe started simultaneously.

## Feature-specific causal treatment

### Funding

Treat the realized rate as unknown until its settlement event. A conservative rule is settlement time plus a small ingestion delay, followed by execution on the next bar. Distinguish predicted funding from realized funding.

### Open interest and positioning metrics

A snapshot timestamp does not prove it was published at the start of the labeled interval. Conservatively make a five-minute snapshot available only after the interval closes plus ingestion delay. If archival coverage starts late for a pair, either shorten the common research period ex ante or make the feature unavailable before inception; never backfill it.

### Premium and basis

A premium-index candle is an input to the funding mechanism, not automatically a conventional spot-futures basis. Label it `premium_index`, not `basis`. A true basis feature requires synchronized, causally closed spot and futures/index prices with matching instrument definitions. One-hour kline information becomes usable only after close plus ingestion delay.

### Liquidations

A live liquidation snapshot stream is not a complete liquidation ledger. If the exchange documents that only one event per symbol per interval is emitted, do not reinterpret it as total liquidation volume. Without an official historical archive or independently verified point-in-time collector, classify historical liquidation pressure as unusable.

## Go/no-go gate

A data family passes only when all are explicit:

- Instrument and pair coverage.
- Earliest usable timestamp per pair.
- Event/period/publication semantics.
- Missingness and duplicate policy.
- Archive/API retention and revision policy.
- Conservative availability lag.
- Staleness behavior in the strategy.
- Provenance manifest and reproducible audit output.

Approve signal implementation only for the families that pass independently. A partial pass must narrow the hypothesis; it must not be used to justify unverifiable auxiliary features.
