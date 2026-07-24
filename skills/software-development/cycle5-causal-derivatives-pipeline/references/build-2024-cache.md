# Incremental 2024 Cache Build

## When to Use

The 2021-2023 cache already exists at `research/generated/cycle5_features.feather` and the full builder (`_build_cycle5_feature_cache_locked`) refuses to overwrite existing artifacts. Use this incremental approach to append 2024 data without re-downloading 2021-2023.

## One-Shot Build

```bash
cd /c/Users/kevin/Desktop/freqtrade
python -B research/build_2024_cache.py
```

Downloads 1950 archives (1830 OI + 60 funding + 60 premium) across 5 symbols for 2024-01-01 to 2024-12-31, then:

1. Normalizes via existing `cycle5_feature_cache.py` parsers
2. Validates rows via `validate_feature_rows`
3. Writes `research/generated/cycle5_features_2024.feather`
4. Combines with existing `cycle5_features.feather` into `cycle5_features_combined.feather`
5. Tests OI divergence and multi-signal fade on each symbol

## Output Files

| File | Contents |
|------|----------|
| `research/generated/cycle5_features_2024.feather` | 2024-only (5 symbols, all 3 families) |
| `research/generated/cycle5_features_combined.feather` | 2021-2023 + 2024 concatenated |
| `research/generated/cycle5_2024_quality.csv` | Per-pair quality metrics for 2024 |
| `research/generated/cycle5_2024_manifest.json` | Build manifest with source archive lineage |

## Architecture

The script reuses every validation and normalization function from `cycle5_feature_cache.py`:

- `_expected_cycle5_source_tasks()` — generates full task list, then filters to 2024-only via year regex
- `_retrieve_archive_tasks()` — parallel download + normalize with 12 workers
- `validate_feature_rows()` — timestamp chronology, monotonicity, source lineage
- `_write_feature_feather()` — atomic zstd-compressed output with schema metadata
- `_build_quality_csv()` — per-pair row counts, conflicts, outside-window counts

Uses its own lock file (`.cycle5_2024_cache.lock`) to prevent concurrent builds.

## Adding a New Year

To extend to 2025 in the future:

1. Update `_DEVELOPMENT_END` in `cycle5_feature_cache.py`
2. Update URL patterns from `202[1-4]` to `202[1-5]`
3. Update year sets in `_require_development_timestamp` and `normalize_open_interest_records`
4. Copy `build_2024_cache.py` → `build_2025_cache.py`, update the year filter regex
5. Run the new script

Or better: refactor `build_NNNN_cache.py` to accept a year parameter.
