# Causal Audit of Historical Crypto Derivatives Archives

Use this reference before admitting funding, open interest, premium, liquidation, or basis data into a historical strategy.

## Core distinction: six clocks

Record these separately for every source:

1. **Measurement period** — interval summarized by the row.
2. **Event time** — settlement, snapshot timestamp, or candle close.
3. **Emission/publication time** — when a live consumer could first observe it.
4. **Archive availability** — when the daily/monthly file appeared.
5. **Retrieval time** — when the current archive was downloaded.
6. **Ingestion/available-at time** — when the simulator permits use.

A currently downloadable archive proves current retrievability, not historical observability or immutability. Require `available_at < decision_time`; same-timestamp joins are not conservative enough.

## Source-audit workflow

1. Freeze the development window and keep validation/holdout paths unopened.
2. Use official documentation to identify endpoint retention, archive start dates, field semantics, and publication cadence.
3. Enumerate the exchange-hosted archive rather than assuming that a landing-page start date fully describes file-level coverage.
4. Inventory every expected day/month in development scope. Record `ok`, `missing`, and `error` separately.
5. Validate every found ZIP: HTTP success, ZIP integrity, exactly expected CSV members, headers/schema, parseability, UTC timestamp order, duplicates, gaps, and target-symbol presence.
6. Verify distributed current checksums, but state that they prove only agreement with the current exchange checksum.
7. Inspect the venue's revision policy and update log. Snapshot current ZIP/checksum identities for reproducibility.
8. Generate machine-readable coverage/quality artifacts plus tests that assert totals, scope boundaries, zero hidden errors, and exclusion rules.
9. Classify each feature independently as `conditional` or `exclude`; a partial pass for one feature does not rescue another.
10. Freeze joins, staleness, missingness, and naming rules before strategy implementation.

## Important archive lesson

Direct exchange-hosted files may predate the start date advertised on a historical-data page, and those early files may be discontinuous. Inventory them, but do not silently promote undocumented or gapped coverage to guaranteed full-period support. Report both:

- documented coverage; and
- observed current file-level coverage.

## Duplicate and gap rules

- Distinguish duplicate timestamps from duplicate payloads.
- Byte/value-identical duplicates may be deterministically collapsed.
- If same-timestamp values conflict, invalidate that timestamp; never select an arbitrary winner.
- Never interpolate funding, OI, premium, or liquidation gaps.
- Before pair-specific inception, the feature is unavailable—not zero.
- A missing or stale feature disables dependent conditions; it must not synthesize a neutral pass.

For data normalized archive-by-archive, conflict invalidation must be represented explicitly—not merely by dropping the row. Return an immutable batch containing normalized rows, conflict tombstones, source identity, and duplicate counts. Merge batches so a tombstone always dominates a row at the same timestamp; an A/B/A payload sequence must remain conflicted permanently. The latest eligible identity includes tombstones, so a conflict at the newest eligible time returns unavailable rather than falling back to an older valid row. Reject conflicting lineage entries that reuse one canonical archive URL.

Canonical raw-payload identity should preserve exact string values, including decimal strings that collide after float conversion, while ignoring mapping insertion order. Require string keys and values before fingerprinting. Use the parsed timestamp as the identity key and a sorted raw field/value tuple as payload identity.

Test exact duplicates, key-order permutations, A/B/A conflicts, tombstone-plus-row cross-batch merges in both orders, conflicting source lineage, and future tombstones before running the full audit.

## Exact 5-minute OI contract

For Binance USD-M daily metrics OI:

- measurement time is the UTC five-minute-grid `create_time`;
- `event_time` is absent/`None` unless the source documents a distinct event clock;
- conservative availability is exactly `create_time + 5 minutes`;
- selection requires `available_at < decision_time` and current measurement age `<= 10 minutes`;
- choose the latest eligible row-or-tombstone identity, not the latest valid row only;
- the lag endpoint is exactly `current.measurement_time - 288 * 5 minutes`—never row position, nearest match, fill, interpolation, or an archive timestamp;
- a missing/conflicting lag or nonpositive endpoint makes the feature unavailable;
- expose immutable endpoint evidence plus stable `log(current) - log(lag)` and a separately validated exact Boolean `current > lag`;
- apply pair-specific inception during normalization, not only at selection;
- validate but omit observations whose conservative availability crosses the authorized development boundary.

Use difference-of-logs rather than `log(current / lag)` so extreme positive finite endpoints do not overflow or underflow during division.

### Public-boundary validation and adversarial proof

Do not trust a public immutable batch/result constructor merely because the normalizer usually produces valid rows. Validate the evidence again at every selector-facing boundary. For five-minute OI, both rows and conflict tombstones must satisfy `minute % 5 == 0`, `second == 0`, and `microsecond == 0`; source month/date, symbol, inception, availability geometry, and development bounds must also remain valid. A manually constructed row must not bypass causal invariants.

When one canonical source URL appears more than once, compare the complete immutable manifest entry—not only the digest. Independently test conflicts in digest, retrieval time, and byte count so a partial lineage comparison cannot survive. Endpoint positivity tests must include negative values as well as zero at both lag and current positions; this kills the common `<= 0` to `== 0` weakening.

After a reviewer finds a missing invariant, add a focused mutation probe for the exact weakening before rerunning the broad suite. Useful probes include deleting row-grid validation, deleting microsecond validation, weakening `<= 0`, and omitting one lineage field. Run each mutant in an isolated copy so the authoritative worktree and staged snapshot stay untouched.

### Protocol transcription corrections

Treat a mismatch between authoritative prose and machine-readable protocol nomenclature as a protocol defect, not an implementation convenience. Prove the mismatch RED with a contract test, change only the label/field name, verify that timing, age, source, threshold, and economic meaning are byte-for-byte unchanged, independently review the tiny exact snapshot, and commit it before implementing the affected feature. This preserves the frozen research boundary while allowing non-economic transcription corrections.

## Binance USD-M archive implementation notes

When using Binance Vision USD-M archives, do not infer value-column semantics from a synthetic fixture or a newer schema. Verify representative files at both ends of the development window and, where possible, reconcile a sample against the official live-history API.

Development-era schemas encountered in practice include:

- funding monthly CSV: `calc_time,funding_interval_hours,last_funding_rate`; use `last_funding_rate` as the realized settled value and reject the file if that column is absent rather than guessing a substitute;
- metrics daily CSV: `create_time,symbol,sum_open_interest,...`; use `sum_open_interest` for position growth, not the price-contaminated `sum_open_interest_value`;
- premium-index 1h klines: older files may be headerless while newer files are headered; the canonical field order is exactly `open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore`; use `close` as `premium_pressure`, never silently alias it to basis or carry, and make the row usable only when the decision is strictly after raw `close_time`.

For premium-index monthly ZIP normalization, freeze these parser invariants:

- require the canonical URL and sole member `<SYMBOL>-1h-YYYY-MM.csv` for an authorized symbol/month;
- bind the exact input bytes to manifest byte count and SHA-256 before opening the ZIP;
- accept only the exact 12-field legacy headerless order or the exact 12-field headed schema above—do not infer shifted columns from partial name matches;
- require `open_time` on an exact UTC-hour boundary and raw `close_time = open_time + 1 hour - 1 millisecond`;
- preserve `measurement_time=open_time`, `event_time=None`, `available_at=close_time`, and immutable source lineage;
- reject malformed ZIP/UTF-8/CSV, source/member/month mismatches, lossy decimal conversion, and conflicting same-availability rows;
- select the latest row with `available_at < decision_time`, enforce the frozen maximum age, and return unavailable for missing/stale/conflicted data rather than interpolation or fallback aliases.

Before freezing a parser, exercise representative allowed archives from both schema eras across every frozen symbol, in memory when possible. Record mode and row count, but treat this as source-compatibility evidence—not a substitute for deterministic fixtures, RED→GREEN tests, or archive lineage.

### Source-verified numeric serialization adapters

Exchange archives can contain valid venue-generated decimal text that a deliberately strict record-level parser rejects. Handle this at the archive boundary without weakening the reusable normalizer:

1. Stop on the first unknown lexical form and report the canonical source URL in the exception.
2. Audit the complete authorized archive set for every noncanonical form before changing code; do not generalize from one row.
3. Add a RED fixture using the exact observed archive schema and token.
4. Canonicalize only the audited forms to exact fixed-point decimal text, then pass them through the unchanged strict record normalizer.
5. Keep unaudited exponent scales, lowercase variants, `NaN`, infinities, whitespace variants, and nonnumeric tokens fail-closed.

Concrete Binance USD-M examples observed in development archives:

- daily metrics can serialize zero OI as `0E-8`; canonicalize only zero-with-negative-scale forms to zero at the archive adapter;
- monthly funding rates use finite uppercase scientific notation at audited scales `E-7` and `E-8`; parse with `Decimal` and format to fixed-point before strict float/precision validation.

A nonpositive OI observation is source evidence, but it is not a valid logarithmic endpoint. Preserve it in the immutable raw-feature cache, count it in the quality artifact, and make downstream OI state unavailable when either endpoint is nonpositive. Do not silently drop it and allow fallback to an older row.

## Immutable development feature-cache build

For a large one-time development cache, freeze an auditable artifact contract before the download:

- enumerate the complete canonical URL set deterministically and assert exact counts by source family;
- reject any requested start/end other than the frozen development window;
- validate canonical host/path, exact ZIP member, UTF-8/CSV schema, source date/symbol, byte count, and SHA-256 before normalization;
- use bounded download concurrency and bounded retries, but preserve one manifest entry per exact archive;
- include the source URL in every retrieval/parser exception so late failures remain diagnosable;
- sort normalized rows deterministically and rerun all lineage, timestamp, conflict, and finite-value validation before writing;
- refuse to overwrite any completed cache, manifest, or quality artifact;
- write through same-directory temporary files and atomic replacement; write the manifest last as the completion marker and remove partial outputs on failure.

Use three artifacts with different tracking rules:

1. **Ignored local cache** (Feather/Arrow/Parquet): normalized rows plus complete per-row lineage.
2. **Tracked JSON manifest**: frozen window, source count, every source URL/retrieval time/byte count/SHA-256, protocol hash, builder hash, cache path/size/hash/row count, and quality path/size/hash.
3. **Tracked compact quality CSV**: one row per symbol/family with row and archive counts, first/last measurement times, exact duplicates collapsed, conflict tombstones, conflicting rows used, nonpositive OI count, outside-window count, and monotonicity.

The artifact integration gate should independently:

- recompute protocol, builder, cache, quality, and every source-lineage hash/identity;
- assert the manifest URL set equals the frozen enumerator exactly;
- assert every source produced cache lineage and every cache lineage appears in the manifest;
- require every expected symbol/family, unique measurement keys, monotonic ordering, and zero outside-window rows;
- require zero conflicting OI rows used while allowing exact duplicates to be deterministically collapsed and reported;
- compare quality counts and first/last times to the cache rather than trusting the CSV.

Do not edit the builder while a long cache build is running: the manifest's builder hash must identify the code that actually produced the artifact. After the artifact gate and full suite pass, stage only builder/tests/tracked metadata, verify the large cache remains ignored, freeze HEAD/tree/binary-patch identities, and obtain independent requirements/causality plus code-quality approvals before commit.

Binance checksum payloads use the shape `<64-hex-sha256>  <filename>`. Verify both the digest and filename, retain the ZIP digest, checksum payload identity, retrieval time, byte count, and URL in the source manifest, and fail closed on malformed or missing checksum metadata.

For daily decision systems, prefer a small decision-time cache over carrying millions of raw event rows into the backtest. A useful wide row records, per symbol and decision:

- each component's measurement/event time;
- its conservative `available_at` time;
- the value used;
- the 24-hour OI comparison timestamp/value;
- validity and staleness flags;
- source lineage and manifest hash.

Build this cache by causal as-of selection only. Do not interpolate. Test that future truncation leaves every earlier cache row byte-identical.

## Conservative availability defaults

Defaults must be justified per source and frozen in the protocol. Common conservative patterns:

- realized funding: first decision bar strictly after settlement time;
- interval statistics such as 5-minute OI: first decision bar strictly after timestamp plus one complete measurement interval;
- premium-index candle: first decision bar strictly after candle close.

Define explicit maximum ages. A backward/as-of join without a staleness cap can silently propagate old observations.

## Naming and feature boundaries

A premium-index candle is **premium pressure**, not automatically true basis or tradable carry.

True basis or annualized dated-futures carry requires a separate audit of:

- causally aligned spot/index and futures prices;
- exact historical contract identity/type;
- listing, expiry, settlement, and specification changes;
- deterministic roll logic;
- missingness and revisions for every component.

Exclude true basis until every component passes.

## Liquidation rejection test

A live stream is not a historical ledger. Reject liquidation features when:

- the stream emits only a latest event/snapshot per interval;
- the venue says the feed is not total or complete;
- the REST endpoint has short retention; or
- no complete official archive exists for the development period.

Do not substitute third-party liquidation history without a separate provenance, completeness, and point-in-time audit.

## Publication and revision semantics

If daily archives appear the next day or monthly archives later, archive timestamps must never be treated as live event timestamps. If archives may be revised:

- preserve current ZIP/checksum identities;
- check the official update log before reproduction;
- label results conditional on the archived revision;
- never claim that a current checksum proves original publication contents.

## Gate outcome language

Keep three decisions separate:

- **Data engineering gate:** may be `pass with exclusions`.
- **Permission to freeze/test a protocol:** allowed only for explicitly eligible features.
- **Evidence of trading edge or deployment permission:** remains no until later experiments pass.

A valid first engine should be price-led, with derivatives used only as filters. Require matched controls such as price trend only, trend plus volatility control, and trend plus volatility plus eligible derivatives filters. This isolates derivatives contribution instead of crediting them for reduced exposure.

## Physical isolation of sealed periods

Before opening any local market-data file, inspect a committed metadata-only audit or sidecar catalog for its first/last timestamps. A later dataframe slice is not a seal: if one Feather/Parquet/CSV file physically spans development and reserved years, loading the file and then filtering has already opened the holdout.

For a sealed research cycle:

1. Verify file date ranges from metadata without reading market values.
2. Reject a mixed-period source as a development input when the protocol forbids loading reserved timestamps.
3. Build or download a physically separate development-only cache into an ignored directory, with an explicit inclusive start and exclusive end boundary.
4. Assert the resulting file's minimum/maximum timestamps and row grid before strategy code can read it.
5. Record source identity, retrieval time, byte count, digest, requested timerange, and the exclusive end boundary in the lineage manifest.
6. Keep validation and holdout paths absent or mechanically inaccessible until their gates authorize opening.

Do not rely on lazy slicing unless the storage format and reader provide verified predicate pushdown that demonstrably avoids reading reserved row groups. When uncertain, fail closed and create a separate cache.

## Minimum executable quality checks

- expected archive-cell count and exact development years;
- every loaded source is physically bounded to the authorized interval, not merely filtered after load;
- no query or output outside the development window;
- current checksum sample count and zero failures;
- zero unreported download/parser errors;
- archive and observation totals reconcile;
- duplicate payload conflict count is zero for conditionally eligible data;
- documented inception masks are enforced;
- liquidation and true-basis classifications remain hard exclusions;
- source-semantics file names every official reference and causal join rule;
- future truncation leaves all earlier `available_at`, features, decisions, and returns unchanged.
