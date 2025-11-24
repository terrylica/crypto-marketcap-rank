# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Goal:** Daily automated collection of comprehensive cryptocurrency market cap rankings for all 19,411+ CoinGecko coins.

**Current Status:** Production-ready system with daily GitHub Actions automation.

**Distribution:** DuckDB and Parquet databases via GitHub Releases (daily tags).

## Architecture

```
Collection → Build → Validate → Release
    ↓          ↓         ↓          ↓
  78 API    2 formats  5 rules   Daily
  calls     built      enforced   tags
```

### Technical Stack

- **Collection**: Python + CoinGecko API (78 API calls/day)
- **Databases**: DuckDB (primary), Parquet (analytics)
- **Schema**: PyArrow Schema V2 (native DATE and BIGINT types)
- **Validation**: Comprehensive validation layer (5 rules)
- **CI/CD**: GitHub Actions (daily cron + manual trigger)
- **Distribution**: GitHub Releases (daily tags: `daily-YYYY-MM-DD`)
- **Versioning**: semantic-release (conventional commits)

## Repository Structure

```
crypto-marketcap-rank/
├── .github/workflows/      # CI/CD automation
│   ├── daily-collection.yml  # Daily data collection + release
│   └── ci.yml                # Continuous integration
├── src/                    # Production code
│   ├── collectors/         # CoinGecko API collector
│   ├── builders/           # Database builders (DuckDB/Parquet)
│   ├── schemas/            # PyArrow Schema V2 definition
│   ├── validators/         # Comprehensive validation layer
│   ├── utils/              # RateLimiter, CheckpointManager
│   └── main.py             # Entry point
├── tests/                  # Unit tests
├── docs/                   # Architecture decisions & plans
├── data/                   # Data storage (gitignored)
│   ├── raw/               # Raw JSON from API
│   ├── processed/         # Built databases
│   └── .checkpoints/      # Resume checkpoints
├── logs/                   # Execution logs
└── research/              # Historical research (archived)
```

## Schema V2

All formats share the same PyArrow-native schema (single source of truth):

| Column                 | Type    | PyArrow Type   | Description                  |
| ---------------------- | ------- | -------------- | ---------------------------- |
| `date`                 | DATE    | `pa.date32()`  | Collection date (YYYY-MM-DD) |
| `rank`                 | BIGINT  | `pa.int64()`   | Market cap rank (1-based)    |
| `coin_id`              | VARCHAR | `pa.string()`  | CoinGecko coin identifier    |
| `symbol`               | VARCHAR | `pa.string()`  | Ticker symbol (lowercase)    |
| `name`                 | VARCHAR | `pa.string()`  | Full coin name               |
| `market_cap`           | DOUBLE  | `pa.float64()` | Market capitalization (USD)  |
| `price`                | DOUBLE  | `pa.float64()` | Current price (USD)          |
| `volume_24h`           | DOUBLE  | `pa.float64()` | 24-hour trading volume (USD) |
| `price_change_24h_pct` | DOUBLE  | `pa.float64()` | 24-hour price change (%)     |

**Source of Truth:** `/Users/terryli/eon/crypto-marketcap-rank/src/schemas/crypto_rankings_schema.py`

**Breaking Change (v2.0.0):** Schema V2 uses native DATE type instead of STRING.

## Python Execution Standard

**CRITICAL:** All Python scripts use PEP 723 inline dependencies. Execute with:

```bash
uv run scriptname.py
```

**Never use:** `pip install`, `python scriptname.py`, `conda`, `poetry`, or `setuptools`.

### Dependency Declaration Pattern

All scripts include PEP 723 metadata at the top:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "pyarrow>=15.0.0",
# ]
# ///
```

## Common Development Tasks

### Run Full Collection Pipeline

```bash
# Run from repository root
uv run src/main.py
```

This executes:
1. CoinGecko API collection (78 paginated requests)
2. DuckDB database build
3. Parquet dataset build
4. Comprehensive validation (5 rules)

### Run Individual Components

```bash
# Collector only (saves raw JSON)
uv run src/collectors/coingecko_collector.py

# Build DuckDB from raw JSON
uv run src/builders/build_duckdb.py data/raw/coingecko_rankings_2025-11-24.json

# Build Parquet from raw JSON
uv run src/builders/build_parquet.py data/raw/coingecko_rankings_2025-11-24.json

# Validate existing database
uv run src/validators/validator.py data/processed/crypto_rankings_2025-11-24.duckdb
```

### Run Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_schema.py -v
```

## Data Flow

### Collection Phase

**CoinGecko API:**
- Endpoint: `/coins/markets`
- Pagination: 250 coins per page (API hard limit)
- Total API calls: ⌈19,411 ÷ 250⌉ = 78
- Rate limiting: 4s delay with API key, 20s without
- Output: `data/raw/coingecko_rankings_YYYY-MM-DD.json`

### Build Phase

**DuckDB Builder:**
- Input: Raw JSON from collector
- Transformation: PyArrow Table with Schema V2
- Output: `data/processed/crypto_rankings_YYYY-MM-DD.duckdb`
- Size: ~150-200 MB compressed
- Features: Indexed (date, rank, coin_id), zero-copy Arrow integration

**Parquet Builder:**
- Input: Same raw JSON
- Partitioning: Hive-style `year=YYYY/month=MM/day=DD/`
- Output: `data/processed/crypto_rankings_YYYY-MM-DD.parquet/`
- Compression: zstd level 3
- Size: ~50-150 MB

### Validation Phase

Comprehensive validation enforces 5 rules:

1. **Schema Conformance**: Exact PyArrow Schema V2 match
2. **Duplicate Detection**: No duplicate (date, rank) pairs
3. **NULL Checks**: Required fields (date, rank, coin_id) non-null
4. **Range Validation**: Ranks sequential (1 to N, no gaps)
5. **Value Constraints**: market_cap, price, volume_24h ≥ 0

## API Quota Usage

- **Daily API Calls**: 78 (⌈19,411 ÷ 250⌉ per page limit)
- **Monthly Usage**: 2,340 calls (23% of 10,000 free tier limit)
- **Safety Margin**: 77% quota remaining for errors/retries

## CI/CD Automation

### Daily Collection Workflow

**File:** `.github/workflows/daily-collection.yml`

**Schedule:** Daily at 6:00 AM UTC (cron: `0 6 * * *`)

**Steps:**
1. Run collection pipeline (`uv run src/main.py`)
2. Validate databases (5-rule validation)
3. Create GitHub Release (tag: `daily-YYYY-MM-DD`)
4. Upload DuckDB and Parquet as release assets

**Manual Trigger:** Supports `workflow_dispatch` for on-demand collection

### Continuous Integration

**File:** `.github/workflows/ci.yml`

**Triggers:** Pull requests to main branch

**Checks:**
- Lint code with ruff
- Run unit tests with pytest

**Note:** NO testing or linting in GitHub Actions per workspace policy (local-first development)

## Release Strategy

### Daily Releases

- **Tag Pattern**: `daily-YYYY-MM-DD` (perpetual storage)
- **Latest Tag**: Points to most recent release (`make_latest: true`)
- **Contents**: DuckDB + Parquet for each collection date
- **Retention**: Perpetual (all daily releases kept indefinitely)

### Semantic Versioning

- **Tool**: semantic-release (conventional commits)
- **Major version bumps**: Breaking schema changes (e.g., v2.0.0 for Schema V2)
- **Minor version bumps**: New features
- **Patch version bumps**: Bug fixes

## Critical Implementation Notes

### Schema V2 Migration (Completed)

**Commit:** `a5597cd` (Nov 2025)

**Changes:**
- `date`: STRING → pa.date32() (native DATE type)
- `rank`: pa.int32() → pa.int64() (BIGINT)
- DuckDB zero-copy Arrow integration
- Removed CSV format (deprecated)

**Migration Plan:** `docs/development/plan/0003-schema-v2-migration/plan.md`

### Resume Capability

All production collectors implement checkpointing:
- Save progress after each page
- Store last successful timestamp
- Allow restart from checkpoint
- Checkpoint location: `data/.checkpoints/`

### Data Validation Rules

Before accepting any data:
- ✅ Row count verification (19,411+ coins)
- ✅ Rank sequence validation (1 to N, no gaps)
- ✅ Duplicate detection (date, rank pairs)
- ✅ NULL check on required fields
- ✅ Schema compliance (exact PyArrow match)

## Project Evolution

### Research Phase (Archived)

The `research/` directory contains historical API investigations:
- CoinPaprika, CoinGecko, CoinCap, Messari, CryptoCompare tests
- Historical market cap data exploration
- Kaggle dataset analysis

**Note:** This research informed the current production implementation but is no longer actively used.

### Production Phase (Current)

**Pivot:** From historical data collection → daily automated rankings

**Key Decision:** Focus on CoinGecko API for current market cap rankings instead of 15-year historical data.

**Rationale:**
- CoinGecko provides comprehensive coverage (19,411+ coins)
- Free tier supports daily automation (78 API calls/day)
- Real-time market cap data (not estimated)
- Established reliability and data quality

## Troubleshooting

### Collection Failures

**Symptom:** API rate limiting (429 errors)

**Solution:** Collector auto-retries with exponential backoff (60s wait)

### Validation Failures

**Symptom:** Schema mismatch errors

**Solution:** Check `CRYPTO_RANKINGS_SCHEMA_V2` definition matches actual data

### Build Failures

**Symptom:** Type conversion errors

**Solution:** Verify raw JSON contains expected field types

## Documentation

### Architecture Decisions

See `docs/architecture/decisions/` for detailed ADRs:
- ADR-0002: CI/CD Daily Rankings Database
- ADR-0007: GitHub Actions Prohibition of Testing and Linting

### Development Plans

See `docs/development/plan/` for implementation plans:
- 0003-schema-v2-migration: Schema V2 migration plan (completed)

## Support

- **Issues**: [GitHub Issues](https://github.com/terrylica/crypto-marketcap-rank/issues)
- **Discussions**: [GitHub Discussions](https://github.com/terrylica/crypto-marketcap-rank/discussions)
- **API Docs**: [CoinGecko API](https://docs.coingecko.com/reference/coins-markets)

---

**Status**: ✅ Production-ready (Daily automated collections active)
