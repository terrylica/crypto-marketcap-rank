# [2.0.0](https://github.com/terrylica/crypto-marketcap-rank/compare/v1.0.0...v2.0.0) (2025-11-23)

- feat!: deprecate CSV format and migrate to daily release tags ([99e2937](https://github.com/terrylica/crypto-marketcap-rank/commit/99e29379332e5c14dd69ca06a67b2792b33c7110))

### Bug Fixes

- **release:** use SSH URL for repositoryUrl to enable authentication ([19c2d9c](https://github.com/terrylica/crypto-marketcap-rank/commit/19c2d9c78bce9cf1fdcc3b2b741115dea2d86091))

### Code Refactoring

- migrate to PyArrow Schema V2 with zero-copy DuckDB integration ([a5597cd](https://github.com/terrylica/crypto-marketcap-rank/commit/a5597cd8c5f3547ebb394b1c5f794ae5cbfbd7d3))

### Documentation

- update README and plan to reflect Schema V2 migration ([3058915](https://github.com/terrylica/crypto-marketcap-rank/commit/30589155192891ffaeef27dca17293718a2e9d6c))

### BREAKING CHANGES

- Notice\*\*:
  Schema V2 (v2.0.0) uses native DATE type instead of STRING. Historical data (pre-Nov 2025) uses Schema V1. DuckDB automatically handles type conversion in queries.
- CSV format no longer generated

**Changes**:

- **CSV Builder Removal**:
  - Deleted `src/builders/build_csv.py`
  - Removed CSV references from `scripts/test_builders.py`
  - Updated test script to only build DuckDB + Parquet

- **Workflow Updates**:
  - Removed CSV artifact upload from daily-collection.yml
  - Changed release tag pattern: latest → daily-YYYY-MM-DD
  - Updated release body to remove CSV references
  - Deleted .github/workflows/monthly-archive.yml (perpetual daily releases)
  - Deleted .github/workflows/monitor-collection.yml.bak (cleanup)

- **GitHub Releases**:
  - Daily tags (daily-YYYY-MM-DD) for perpetual storage
  - make_latest: true ensures latest release is always current
  - No monthly archives (replaced by daily releases)

**Rationale**:

- Parquet is 5x smaller than CSV (DuckDB benchmark 2024)
- Parquet provides self-describing schema (embedded metadata)
- CSV provides minimal value for analytical data (slow, large, untyped)
- Daily tags enable long-term data retention without monthly aggregation

* Schema V2 introduces PyArrow native types (pa.date32(), pa.int64())

**Changes**:

- **Schema Foundation**:
  - Created `src/schemas/crypto_rankings_schema.py` as single source of truth
  - Defined CRYPTO_RANKINGS_SCHEMA_V2 with PyArrow native types
  - Date field: STRING → pa.date32() (native DATE type)
  - Rank field: pa.int32() → pa.int64() (consistency with DuckDB BIGINT)
  - Added JSON Schema export for documentation

- **Comprehensive Validation**:
  - Created `src/validators/schema_validator.py` with 5 validation rules
  - Schema conformance (exact type matching)
  - Duplicate detection ((date, coin_id) pairs)
  - NULL checks (required fields: date, rank, coin_id)
  - Range validation (rank 1 to N, sequential)
  - Value validation (market_cap > 0)

- **Base Builder Refactoring**:
  - Removed DatabaseSchema class (replaced by PyArrow schema)
  - Updated \_transform_to_rows() to return pa.Table instead of List[Dict]
  - Kept defensive type coercion (\_safe_int, \_safe_float)
  - Parse date string to Python date object for pa.date32()

- **Parquet Builder (Schema V2)**:
  - Uses CRYPTO_RANKINGS_SCHEMA_V2 directly
  - Hive-style partitioning (year=/month=/day=/)
  - Validation before write (fail-fast)
  - Simplified \_build_parquet() (table already constructed)

- **DuckDB Builder (Zero-Copy Arrow)**:
  - Implements zero-copy PyArrow → DuckDB via con.register()
  - No serialization overhead (instant, memory-efficient)
  - DuckDB auto-maps Arrow types: pa.date32() → DATE, pa.int64() → BIGINT
  - Validation using shared validate_arrow_table()

- **CI/CD Fix**:
  - Reverted .github/workflows/release.yml: npm install → npm ci
  - Restores deterministic CI builds

**Migration Strategy**:

- No backward compatibility (fresh start approach)
- Historical data (v1) and future data (v2) coexist
- DuckDB handles mixed schemas via automatic type conversion

# 1.0.0 (2025-11-23)

### Bug Fixes

- Add explicit type coercion for rank field to handle string values from API ([5ccd06f](https://github.com/terrylica/crypto-marketcap-rank/commit/5ccd06f8c48adf1921fca5ead2edc0293899e324))
- add repositoryUrl to semantic-release config ([6796506](https://github.com/terrylica/crypto-marketcap-rank/commit/6796506c465558c1f494c24434bbccab84cf7557))
- allow duplicate ranks in validation (valid API behavior) ([97e3ba1](https://github.com/terrylica/crypto-marketcap-rank/commit/97e3ba1acab092fd3f2980ec64d531934566f172))
- Apply comprehensive type coercion to all numeric fields in data transformation ([53e4e30](https://github.com/terrylica/crypto-marketcap-rank/commit/53e4e30c3313dfaee2703863cf6333398123e161))
- **ci:** use npm install instead of npm ci to resolve lockfile mismatch ([8eb15bd](https://github.com/terrylica/crypto-marketcap-rank/commit/8eb15bd2db60238217464fdbc7ee62254d392df0))
- deduplicate coins during collection ([ff50326](https://github.com/terrylica/crypto-marketcap-rank/commit/ff5032691e6fce12cef2a590de9aaa7edcdd8e13))
- resolve ruff linting errors in CI workflow ([50241c6](https://github.com/terrylica/crypto-marketcap-rank/commit/50241c6d912d798d8a9e118bb6081aff52cea6dc))
- update repository URLs to correct GitHub username ([6b16f72](https://github.com/terrylica/crypto-marketcap-rank/commit/6b16f726b5bf8f36b6c960ef4ac2a9927ace3a38))
- use curl for Pushover notifications ([0f6450f](https://github.com/terrylica/crypto-marketcap-rank/commit/0f6450fadfc9bda77e08c725f026b03ab08ef4e4))

### Features

- Add Pushover notification test workflow ([e247000](https://github.com/terrylica/crypto-marketcap-rank/commit/e2470000eaf68b5d6ed8afbac2a3d30c0f1c46f4))
- add workflow monitoring with Pushover notifications ([6d5203a](https://github.com/terrylica/crypto-marketcap-rank/commit/6d5203a132fe16d0211276445f01985a2554ddb4))
- implement CI/CD daily cryptocurrency rankings database ([b2a3132](https://github.com/terrylica/crypto-marketcap-rank/commit/b2a31326afc75e45d4672702ba284c1542c06a71))
- Use Doppler for Pushover credentials in monitoring workflow ([3ff128c](https://github.com/terrylica/crypto-marketcap-rank/commit/3ff128c93d8484895a1c5be90d42dd8d6796ff0c))
