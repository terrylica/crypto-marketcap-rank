# ADR-0002: CI/CD Daily Cryptocurrency Rankings Database

**Status**: Accepted
**Date**: 2025-11-21
**Authors**: AI Assistant
**Deciders**: Terry Li

## Context and Problem Statement

Need automated daily collection of comprehensive cryptocurrency market cap rankings (all 19,411 CoinGecko coins) with reliable distribution as queryable database artifacts. Current state has manual collection tools but no automation, no centralized database, and no public distribution mechanism.

**Key Constraints**:

- CoinGecko Free Tier: 10,000 API calls/month, 30 calls/minute
- GitHub Actions Free Tier: Unlimited minutes (public repo), 10 GB cache, 6-hour job timeout
- Need dual-purpose solution: public research dataset + company internal ClickHouse integration
- Empirically validated: 78 API calls required for all 19,411 coins (250 coins per page hard limit)

## Decision Drivers

- **Availability**: Daily automated collection without manual intervention
- **Correctness**: Complete historical coverage, no gaps in data
- **Observability**: Data quality validation, API quota tracking, failure notifications
- **Maintainability**: Simple architecture, OSS tools, conventional commits
- **Cost**: Must operate within free tiers (GitHub + CoinGecko)

## Considered Options

### Option 1: DuckDB Single-File Database (SELECTED)

- **Description**: Distribute single `.duckdb` file via GitHub Releases
- **Pros**: Instant queryability, 150-200 MB compressed, SQL interface, no extraction needed
- **Cons**: Larger than Parquet, not native ClickHouse format
- **Evidence**: Proven pattern (hikeratlas/qrank uses 307 MB SQLite weekly)

### Option 2: Parquet Archive Only

- **Description**: Distribute partitioned Parquet files (50-150 MB/year)
- **Pros**: Smallest size, ClickHouse-native, industry standard
- **Cons**: Requires extraction before querying, less accessible to non-technical users

### Option 3: ClickHouse Embedded (REJECTED)

- **Description**: Use ClickHouse/chDB for database generation
- **Pros**: Company familiarity
- **Cons**: Cannot produce single-file artifacts (execution engine, not file format), 500 MB binary footprint
- **Evidence**: Research confirmed ClickHouse/chDB are query engines, not distributable database formats

## Decision Outcome

**Chosen option**: Hybrid approach providing **all three formats** (DuckDB + Parquet + CSV)

**Rationale**:

- **DuckDB**: Primary public distribution (easy downloads, instant SQL queries)
- **Parquet**: Company internal ClickHouse import (smallest size, native format)
- **CSV**: Maximum compatibility fallback (spreadsheets, legacy tools)

## Implementation Strategy

### Collection Scope

**Decision**: Collect all 19,411 CoinGecko coins daily

- **API Calls**: 78/day (⌈19,411 ÷ 250⌉)
- **Monthly Usage**: 2,340 calls (23% of 10,000 limit)
- **Empirical Evidence**: Multiple GitHub projects + official docs confirm 250 coins/page hard limit
- **Coverage**: 100% of ranked coins
- **Safety Margin**: 77% quota remaining for errors/retries

### Architecture Components

```
Collection → Build → Validate → Release
    ↓          ↓         ↓          ↓
  78 API    3 formats  Quality   GitHub
  calls     built      checks    Releases
```

**Tech Stack**:

- **Collection**: Python + requests + PEP 723 inline deps
- **Databases**: DuckDB (embedded), Parquet (PyArrow), CSV (stdlib)
- **CI/CD**: GitHub Actions (daily cron + manual trigger)
- **Distribution**: GitHub Releases ("latest" tag + monthly archives)
- **Validation**: pytest + custom quality checks
- **Versioning**: semantic-release (conventional commits → auto version/tag/release)

### Data Flow

1. **Daily Trigger** (6:00 AM UTC cron)
2. **Collect**: Fetch /coins/markets endpoint (78 pages × 250 coins)
3. **Build**: Generate DuckDB + Parquet + CSV from raw data
4. **Validate**: Check row counts, rank sequences, duplicates, anomalies
5. **Compress**: DuckDB native, Parquet zstd, CSV gzip
6. **Release**: Atomic update of "latest" GitHub Release assets
7. **Archive**: Monthly snapshot release (v2025-11 format)

### Project Structure

```
crypto-marketcap-rank/
├── .github/workflows/          # CI/CD automation
├── src/                        # Production code (collectors, builders, utils)
├── data/                       # Data storage (gitignored)
├── scripts/                    # Utilities (release, validation)
├── tools/                      # Analysis/research tools
├── docs/
│   ├── architecture/decisions/ # ADRs (this file)
│   └── development/plan/       # Implementation plans
├── logs/                       # Execution logs
└── pyproject.toml             # Dependencies
```

## Consequences

### Positive

- **Availability**: Daily automated updates, no manual intervention
- **Correctness**: Complete coin coverage (19,411), validated before release
- **Observability**: Checkpoint tracking, API quota monitoring, validation reports
- **Maintainability**: Standard Python tooling (uv, pytest), conventional commits
- **Cost**: $0/month (within all free tiers)
- **Accessibility**: Three formats serve all user types (researchers, companies, analysts)

### Negative

- **Complexity**: Managing three output formats adds maintenance overhead
- **Storage**: GitHub repo size will grow (~200 MB artifacts)
  - Mitigation: .gitignore data/, only release assets stored
- **API Dependency**: Reliant on CoinGecko API stability
  - Mitigation: 77% quota buffer, checkpoint resume on failures
- **Build Time**: 15-20 minutes daily (collection + build + compress + release)
  - Acceptable: Well within 6-hour GitHub Actions job limit

### Neutral

- **Kaggle Integration**: Skipped for initial implementation
  - Rationale: Start fresh from today, avoid coin ID mapping complexity
  - Future: Can backfill if historical data needed

## Validation and Compliance

### SLO Targets

- **Availability**: >95% daily collection success rate
- **Correctness**: Zero data quality issues (duplicate rows, null ranks, missing dates)
- **Observability**: All failures logged, Slack notifications on errors
- **Maintainability**: Documentation updates with each release, changelog automated

### Auto-Validation

After each code change:

1. Run `uv run pytest` (unit tests)
2. Run `uv run src/utils/validator.py` (data quality)
3. Build sample databases (validate schemas)
4. Surface errors immediately, auto-fix where possible
5. Do NOT merge/release with known errors

### Error Handling Philosophy

- **Raise + Propagate**: No silent failures, no default fallbacks
- **Fail Fast**: Invalid data stops pipeline immediately
- **Observability**: All errors logged to `logs/{adr-id}-{slug}-YYYYMMDD_HHMMSS.log`
- **Recovery**: Checkpoint-based resume (GitHub Actions cache)

## Related Documents

- **Plan**: `docs/development/plan/0002-cicd-daily-rankings/plan.md`
- **Empirical Research**: Sub-agent reports in session context
- **API Validation**: `tmp/api-call-validation/` (empirical test scripts)

## References

- CoinGecko API Documentation: https://docs.coingecko.com/reference/coins-markets
- Empirical Evidence: 78 API calls formula validated by 6 independent sources
- DuckDB Documentation: https://duckdb.org/docs/
- GitHub Actions Free Tier: Unlimited minutes for public repositories
- Proven Pattern: hikeratlas/qrank (307 MB SQLite, weekly updates)

## Changelog

- **2025-11-21**: ADR-0002 created and accepted
