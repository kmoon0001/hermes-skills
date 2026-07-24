# Binance 2024 OI Data Format Changes

Investigation performed 2026-07-19 when extending the Cycle 5 feature cache from 2021-2023 to include 2024.

## Discovery Method

The `--build --start 2024-01-01 --end 2024-12-31` command failed during parallel archive retrieval. Each error surfaced from `_retrieve_and_normalize_archive` and propagated through the thread pool executor. Root cause was not immediately obvious — needed direct archive inspection.

**Diagnostic pattern (repeatable for future data-source issues):**
1. Download individual archives directly from Binance (via `urllib.request`)
2. Parse CSV manually with Python stdlib (no framework involvement)
3. Check all rows systematically for constraint violations
4. Test same-date archives across all 5 frozen symbols to scope the issue
5. Check adjacent dates and prior years to characterize "changed vs. always-broken"
6. After fixing each issue, scan broadly for remaining failures by re-running the full build — each run may surface a new format variant

## Root Cause 1: Timestamp Seconds Drift

**Affected:** ~9% of daily OI archives across all 5 symbols (BTC, ETH, SOL, XRP, ADA), starting from approximately September 2024.

**Symptom:** `_parse_metrics_create_time` raised `ValueError("create_time must align to a five-minute boundary")`

**Sampled failures (ADAUSDT):**
| Date | Bad rows | Sample timestamp |
|------|----------|-----------------|
| 2024-09-01 | 6 | 02:10:01 |
| 2024-09-02 | 18 | 02:10:01 |
| 2024-09-15 | 20 | 02:55:03 |
| 2024-10-01 | 21 | 01:55:01 |
| 2024-11-01 | 12 | 02:30:05 |
| 2024-11-15 | 11 | 02:45:02 |
| 2024-12-01 | 19 | 01:00:01 |
| 2024-12-15 | 0 (clean) | — |

**All failures were seconds-only drift (1-5 seconds, never minutes).**
Minutes were always divisible by 5. This means the truncation approach (set second=0, microsecond=0) is safe.

**Cross-symbol check (2024-09-01):**
| Symbol | Bad rows | Type |
|--------|----------|------|
| BTCUSDT | 2 | sec-only |
| ETHUSDT | 9 | sec-only |
| SOLUSDT | 2 | sec-only |
| XRPUSDT | 6 | sec-only |
| ADAUSDT | 6 | sec-only |

## Root Cause 2: Cross-Date Records in Daily Archives

**Affected:** Same set of archives as Root Cause 1 (2024-only).

**Symptom:** `normalize_open_interest_records` raised `ValueError("metrics observation is outside the source archive date")` because records from the next calendar day appear in the current day's archive.

**Example:** The `ADAUSDT-metrics-2024-09-01.zip` archive contained records with `create_time` of `2024-09-02`. The `2023-09-01` archive had zero cross-date records — this is a 2024-only behavior change by Binance.

## Root Cause 3: Zero-Value Exponent Format Change

**Affected:** At least 2 archives (ADAUSDT 2024-07-12 had 2 rows). Other symbols/dates likely similar — the `0E-16` pattern appears sporadically.

**Symptom:** `_parse_open_interest` raised `ValueError("sum_open_interest must be a finite decimal string")` on value `0E-16`. The code had an exact-string check `value != "0E-8"` that rejected any other zero-exponent notation.

**Sample data:**
```
2024-07-12 03:25:00,ADAUSDT,0E-16,0E-16,...
2024-07-12 14:30:00,ADAUSDT,0E-16,0E-16,...
```

Binance uses `0E-8` as their standard zero placeholder. In 2024, some records use `0E-16` instead — same semantic (zero OI/value), different exponent. Both `Decimal("0E-16")` and `float("0E-16")` produce `0.0` correctly.

**Fix:** Switched from exact match to regex `not re.fullmatch(r"0E-\d+", value)`, accepting any zero-exponent notation.

**Verification:** All five frozen symbols (BTC, ETH, SOL, XRP, ADA) have at least some 2024 archives with `0E-16` values. Historical 2021-2023 data always uses `0E-8`.

## Root Cause 4: Year-Boundary Validation Ordering

**Affected:** Any archive whose date bounds cross a year boundary. Triggered on the last day of 2024 (`ADAUSDT-metrics-2024-12-31.zip`).

**Symptom:** `_require_development_timestamp("measurement_time", measurement_time)` raised `ValueError("measurement_time year must be within 2021-2024")` because the archive's final record had `create_time = 2025-01-01 00:00:01` — a next-day cross-date bleed.

**Root cause:** The cross-date skip check (measurement_time.date != source_archive_date → continue) was placed AFTER `_require_development_timestamp`. A 2025 record never reached the skip — the year check rejected it first.

**Fix:** Swapped the two checks so the date-boundary skip runs first:
```python
measurement_time = _parse_metrics_create_time(record["create_time"])
# Date boundary skip FIRST
if (measurement_time.year, measurement_time.month, measurement_time.day) != (source_year, source_month, source_day):
    continue
# Year/timestamp validation SECOND — only runs on in-boundary records
_require_development_timestamp("measurement_time", measurement_time)
```

This pattern should be followed for any new parser that handles daily archives with potential cross-date bleed.

## Fix Applied

### File: `research/cycle5_feature_cache.py`

1. **`_parse_metrics_create_time` (line ~532):** Changed from strict rejection to gentle truncation:
   ```python
   # Before:
   if parsed.minute % 5 != 0 or parsed.second != 0:
       raise ValueError("create_time must align to a five-minute boundary")

   # After:
   if parsed.second != 0 or parsed.microsecond != 0:
       parsed = parsed.replace(second=0, microsecond=0)
   ```
   Kept minute % 5 check implicit — if a future format change causes non-5-min minutes, the downstream `OINormalizationBatch.__post_init__` validation will catch it.

2. **`normalize_open_interest_records` (line ~596):** Cross-date records now skipped instead of error:
   ```python
   # Before:
   raise ValueError("metrics observation is outside the source archive date")

   # After:
   continue  # correct archive will produce identical row
   ```

3. **`normalize_open_interest_records` (line ~615):** Added 2024 to year filter.

4. **`_parse_open_interest` (line ~541):** Zero-exponent check widened from exact `"0E-8"` to regex `r"0E-\d+"`:
   ```python
   # Before:
   value != "0E-8"
   
   # After:
   not re.fullmatch(r"0E-\d+", value)
   ```

5. **Validation order in `normalize_open_interest_records` (line ~590):** Swapped date-boundary check before `_require_development_timestamp` as described in Root Cause 4.

6. **`_DEVELOPMENT_END`:** Changed from `date(2023, 12, 31)` to `date(2024, 12, 31)`.

## Verification

After all fixes, the full 2024 build (1950 archives, 12 workers) completed in ~30 seconds producing 575,025 normalized rows. The combined 2021-2024 cache has 1,913,631 rows.

## Build Strategy for 2024

The full builder (`_build_cycle5_feature_cache_locked`) checks for existing artifacts and raises `FileExistsError` if they exist. Since the 2021-2023 cache already exists, the approach is:

1. Build 2024 into a separate feather via `python -B research/build_2024_cache.py` (uses its own lock: `.cycle5_2024_cache.lock`)
2. The script combines `cycle5_features.feather` (2021-2023) with `cycle5_features_2024.feather` into `cycle5_features_combined.feather`
3. Tests OI divergence and multi-signal fade on all symbols with the combined cache

## 2024 OI Divergence + Multi-Signal Test Results

| Symbol | OI divergence active | Multi-signal strong fade | Multi-signal boost |
|--------|---------------------|--------------------------|-------------------|
| ADAUSDT | 180/366 (49.2%) | 0 | 190 |
| BTCUSDT | 184/366 (50.3%) | 0 | 182 |
| ETHUSDT | 169/366 (46.2%) | 0 | 187 |
| SOLUSDT | 175/366 (47.8%) | 0 | 191 |
| XRPUSDT | 176/366 (48.1%) | 0 | 204 |
