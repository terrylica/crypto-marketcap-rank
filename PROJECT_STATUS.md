# Crypto Market Cap Rankings - Project Status

**Last Updated**: 2025-11-24
**Status**: ✅ Production-ready (v2.0.0 released 2025-11-23)
**Version**: v2.0.0

---

## Quick Summary

**Goal**: Daily automated collection of comprehensive cryptocurrency market cap rankings.

**Production State**:

- ✅ Automated daily collection (GitHub Actions, 6:00 AM UTC)
- ✅ Schema V2 migration complete (PyArrow native types)
- ✅ DuckDB + Parquet database formats (CSV deprecated)
- ✅ Daily release tags (`daily-YYYY-MM-DD` pattern)
- ✅ Comprehensive validation (5 rules, zero duplicate/null data)
- ✅ Production monitoring and error handling

**Data Source**: CoinGecko API (19,400+ ranked coins, 78 API calls/day)

---

## Architecture

```
Collection → Build → Validate → Release
    ↓          ↓         ↓          ↓
  78 API    2 formats  5 rules   Daily
  calls     built      enforced   tags
```

### Technical Stack

| Component    | Technology                                   |
| ------------ | -------------------------------------------- |
| Collection   | Python + CoinGecko API                       |
| Databases    | DuckDB (primary), Parquet (analytics)        |
| Schema       | PyArrow Schema V2 (native DATE, BIGINT)      |
| Validation   | 5-rule validation layer                      |
| CI/CD        | GitHub Actions (daily cron + manual trigger) |
| Distribution | GitHub Releases (daily tags)                 |
| Versioning   | semantic-release (conventional commits)      |

---

## Current Capabilities

### Daily Automated Collection ✅

**Workflow**: `.github/workflows/daily-collection.yml`
**Schedule**: Daily at 6:00 AM UTC
**Output**: DuckDB + Parquet databases via GitHub Releases

```bash
# Download latest data
gh release download daily-2025-11-24 -p "*.duckdb" -D ./data/
```

### Schema V2 (PyArrow Native Types) ✅

| Column               | Type    | Description                  |
| -------------------- | ------- | ---------------------------- |
| date                 | DATE    | Collection date (YYYY-MM-DD) |
| rank                 | BIGINT  | Market cap rank (1-based)    |
| coin_id              | VARCHAR | CoinGecko coin identifier    |
| symbol               | VARCHAR | Ticker symbol (lowercase)    |
| name                 | VARCHAR | Full coin name               |
| market_cap           | DOUBLE  | Market capitalization (USD)  |
| price                | DOUBLE  | Current price (USD)          |
| volume_24h           | DOUBLE  | 24-hour trading volume (USD) |
| price_change_24h_pct | DOUBLE  | 24-hour price change (%)     |

### Validation (5 Rules) ✅

1. **Schema Conformance**: Exact PyArrow Schema V2 match
2. **Duplicate Detection**: No duplicate (date, rank) pairs
3. **NULL Checks**: Required fields (date, rank, coin_id) non-null
4. **Range Validation**: Ranks sequential (1 to N, no gaps)
5. **Value Constraints**: market_cap, price, volume_24h ≥ 0

---

## API Usage

| Metric          | Value                                  |
| --------------- | -------------------------------------- |
| Daily API Calls | 78 (⌈19,411 ÷ 250⌉ per page limit)     |
| Monthly Usage   | ~2,340 calls (23% of 10,000 free tier) |
| Rate Limiting   | 4s delay with API key                  |
| Safety Margin   | 77% quota remaining for errors/retries |

---

## Release Strategy

### Daily Releases

- **Tag Pattern**: `daily-YYYY-MM-DD` (perpetual storage)
- **Latest Tag**: Points to most recent release
- **Contents**: DuckDB + Parquet for each collection date
- **Retention**: Perpetual (all daily releases kept)

### Semantic Versioning

- **Current**: v2.0.0 (Schema V2 migration)
- **Tool**: semantic-release (conventional commits)
- **Major**: Breaking schema changes
- **Minor**: New features
- **Patch**: Bug fixes

---

## Repository Structure

```
crypto-marketcap-rank/
├── .github/workflows/      # CI/CD automation
│   ├── daily-collection.yml  # Daily collection + release
│   └── release.yml           # Semantic release
├── src/                    # Production code
│   ├── collectors/         # CoinGecko API collector
│   ├── builders/           # Database builders
│   ├── schemas/            # PyArrow Schema V2
│   ├── validators/         # Validation layer
│   └── main.py             # Entry point
├── tests/                  # Unit tests
├── docs/                   # Architecture decisions & plans
│   ├── architecture/decisions/  # ADRs (MADR format)
│   └── development/plan/        # Implementation plans
├── data/                   # Data storage (gitignored)
└── logs/                   # Execution logs
```

---

## Development Commands

### Run Full Collection Pipeline

```bash
uv run src/main.py
```

### Run Tests

```bash
uv run pytest tests/ -v
```

### Code Quality

```bash
uv run ruff check src/ tests/
```

---

## Architecture Decisions

| ADR      | Title                                            | Status   |
| -------- | ------------------------------------------------ | -------- |
| ADR-0002 | CI/CD Daily Rankings Database                    | Accepted |
| ADR-0003 | Schema V2 Migration - PyArrow Native Types       | Accepted |
| ADR-0008 | Repository Housekeeping and Standards Compliance | Accepted |

---

## Decision Log

**2025-11-19**: Project started

- Investigated 7 cryptocurrency data APIs
- Selected CoinGecko as sole data source

**2025-11-20**: Research phase complete

- Collected all 19,410 coin IDs
- Discovered maximum ranking depth (~13,000 coins)
- Documented canonical workflow

**2025-11-22**: Production implementation

- Implemented automated daily collection
- Created DuckDB + Parquet builders
- Set up GitHub Actions workflows

**2025-11-23**: v2.0.0 released

- Schema V2 migration (PyArrow native types)
- Comprehensive validation layer
- First daily release: daily-2025-11-23

**2025-11-24**: Repository housekeeping (ADR-0008)

- Security: CVE-2025-64756 mitigated
- Policy: CI workflow aligned with local-first development
- Documentation: Cleaned up redundant files

---

## Contact & Resources

- **Repository**: https://github.com/terrylica/crypto-marketcap-rank
- **Releases**: https://github.com/terrylica/crypto-marketcap-rank/releases
- **CoinGecko API**: https://docs.coingecko.com/reference/coins-markets

---

**Status**: ✅ Production-ready with daily automated collection
