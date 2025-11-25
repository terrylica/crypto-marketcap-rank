# Cryptocurrency Market Cap Rankings Database

[![Daily Collection](https://github.com/terrylica/crypto-marketcap-rank/actions/workflows/daily-collection.yml/badge.svg)](https://github.com/terrylica/crypto-marketcap-rank/actions/workflows/daily-collection.yml)

Daily automated collection of comprehensive cryptocurrency market cap rankings for all 19,411+ CoinGecko coins. Distributed as queryable database artifacts via GitHub Releases.

## Features

- **Complete Coverage**: All 19,411+ ranked cryptocurrencies
- **Daily Updates**: Automated collection at 6:00 AM UTC
- **Multiple Formats**: DuckDB (SQL queries), Parquet (ClickHouse/analytics)
- **Schema V2**: PyArrow native types with comprehensive validation
- **Zero Cost**: Operates within free tiers (GitHub Actions + CoinGecko API)
- **Public Dataset**: Research-ready, freely downloadable
- **Production Quality**: Validated, versioned, and continuously monitored

## Quick Start

### Download Latest Data

```bash
# Download DuckDB database (recommended)
wget https://github.com/terrylica/crypto-marketcap-rank/releases/download/latest/crypto_rankings_2025-11-21.duckdb

# Query instantly with DuckDB
duckdb crypto_rankings_2025-11-21.duckdb
```

### Query Examples

```sql
-- Top 10 cryptocurrencies by market cap
SELECT rank, symbol, name, market_cap, price
FROM rankings
ORDER BY rank
LIMIT 10;

-- Find specific coin
SELECT * FROM rankings WHERE symbol = 'btc';

-- Filter by market cap range
SELECT COUNT(*) as coin_count
FROM rankings
WHERE market_cap BETWEEN 1e9 AND 10e9;
```

### Python Usage

```python
import duckdb

# Connect to database
con = duckdb.connect('crypto_rankings_2025-11-21.duckdb')

# Query to pandas DataFrame
df = con.execute("""
    SELECT rank, symbol, name, market_cap, price
    FROM rankings
    ORDER BY rank
    LIMIT 100
""").df()

print(df)
```

## Available Formats

### DuckDB (Primary Distribution)

- **File**: `crypto_rankings_YYYY-MM-DD.duckdb`
- **Size**: ~150-200 MB compressed
- **Schema**: Native DATE and BIGINT types (Schema V2)
- **Use Case**: Instant SQL queries, data analysis, no setup required
- **Best For**: Researchers, analysts, quick exploration

### Parquet (Analytics & Data Pipelines)

- **Directory**: `crypto_rankings_YYYY-MM-DD.parquet/`
- **Size**: ~50-150 MB compressed
- **Partitioning**: Hive-style `year=YYYY/month=MM/day=DD/`
- **Schema**: PyArrow native types (pa.date32(), pa.int64(), pa.float64())
- **Compression**: zstd level 3
- **Use Case**: ClickHouse import, data pipelines, columnar analytics
- **Best For**: Companies, data engineers, ETL workflows

## Schema

**Schema V2** (November 2025): All formats share the same PyArrow-native schema:

| Column                 | Type    | PyArrow Type   | Description                  |
| ---------------------- | ------- | -------------- | ---------------------------- |
| `date`                 | DATE    | `pa.date32()`  | Collection date (YYYY-MM-DD) |
| `rank`                 | BIGINT  | `pa.int64()`   | Market cap rank (1-based)    |
| `coin_id`              | VARCHAR | `pa.string()`  | CoinGecko coin identifier    |
| `symbol`               | VARCHAR | `pa.string()`  | Ticker symbol (e.g., BTC)    |
| `name`                 | VARCHAR | `pa.string()`  | Full coin name               |
| `market_cap`           | DOUBLE  | `pa.float64()` | Market capitalization (USD)  |
| `price`                | DOUBLE  | `pa.float64()` | Current price (USD)          |
| `volume_24h`           | DOUBLE  | `pa.float64()` | 24-hour trading volume (USD) |
| `price_change_24h_pct` | DOUBLE  | `pa.float64()` | 24-hour price change (%)     |

> **Breaking Change (v2.0.0)**: Schema V2 uses native DATE type instead of STRING. Historical data (pre-Nov 2025) uses Schema V1. DuckDB automatically handles type conversion in queries.

## Architecture

```
Collection → Build → Validate → Release
    ↓          ↓         ↓          ↓
  78 API    2 formats  5 rules   Daily
  calls     built      enforced   tags
```

### Technical Stack

- **Collection**: Python + CoinGecko API (78 API calls/day)
- **Databases**: DuckDB, Parquet (PyArrow Schema V2)
- **Validation**: Comprehensive schema validation (5 rules: schema conformance, duplicates, nulls, ranges, values)
- **CI/CD**: GitHub Actions (daily cron + manual trigger)
- **Distribution**: GitHub Releases (daily tags: `daily-YYYY-MM-DD`)
- **Versioning**: semantic-release (conventional commits)

## API Quota Usage

- **Daily API Calls**: 78 (⌈19,411 ÷ 250⌉ per page limit)
- **Monthly Usage**: 2,340 calls (23% of 10,000 free tier limit)
- **Safety Margin**: 77% quota remaining for errors/retries

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)

### Setup

```bash
# Clone repository
git clone https://github.com/terrylica/crypto-marketcap-rank.git
cd crypto-marketcap-rank

# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run collection locally
uv run src/main.py
```

### Project Structure

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
└── logs/                   # Execution logs
```

## Releases

### Daily Releases

- **Tag Pattern**: `daily-YYYY-MM-DD` (perpetual storage)
- **Latest Tag**: Points to most recent release (`make_latest: true`)
- **Updated**: Daily at 6:00 AM UTC
- **Contents**: DuckDB + Parquet for each collection date
- **Retention**: Perpetual (all daily releases kept indefinitely)

### Example

```bash
# Download specific date
wget https://github.com/terrylica/crypto-marketcap-rank/releases/download/daily-2025-11-22/crypto_rankings_2025-11-22.duckdb

# Download latest
wget https://github.com/terrylica/crypto-marketcap-rank/releases/latest/download/crypto_rankings_YYYY-MM-DD.duckdb
```

## Quality Assurance

### Automated Validation

- ✅ Row count verification (19,411+ coins)
- ✅ Rank sequence validation (1 to N, no gaps)
- ✅ Duplicate detection (date, rank pairs)
- ✅ NULL check on required fields
- ✅ Schema compliance
- ✅ Anomaly detection (>1000% daily changes)

### SLO Targets

- **Availability**: >95% daily collection success rate
- **Correctness**: Zero data quality issues
- **Observability**: All failures logged, notifications on errors
- **Maintainability**: Documentation updated with each release

## Use Cases

### Research & Analysis

```sql
-- Historical trend analysis
SELECT date, AVG(market_cap) as avg_market_cap
FROM rankings
WHERE rank <= 100
GROUP BY date
ORDER BY date;
```

### ClickHouse Import

```sql
-- Create table
CREATE TABLE crypto_rankings (
    date Date,
    rank UInt32,
    coin_id String,
    symbol String,
    name String,
    market_cap Float64,
    price Float64,
    volume_24h Float64,
    price_change_24h_pct Float64
) ENGINE = MergeTree()
ORDER BY (date, rank);

-- Import Parquet
INSERT INTO crypto_rankings
SELECT * FROM file('crypto_rankings_2025-11-21.parquet/**/*.parquet', Parquet);
```

### Data Science (Python)

```python
import pandas as pd
import duckdb

# Load data
con = duckdb.connect('crypto_rankings_2025-11-21.duckdb')
df = con.execute("SELECT * FROM rankings").df()

# Analyze
top_100 = df[df['rank'] <= 100]
print(f"Top 100 total market cap: ${top_100['market_cap'].sum():,.0f}")
```

## Contributing

Contributions welcome! Please:

1. Follow [conventional commits](https://www.conventionalcommits.org/)
2. Run `uv run pytest` before submitting PR
3. Update documentation for new features
4. Ensure CI passes

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Data source: [CoinGecko API](https://www.coingecko.com/api)
- Inspired by [hikeratlas/qrank](https://github.com/hikeratlas/qrank)
- Built with: DuckDB, PyArrow, GitHub Actions

## Architecture Decisions

See [docs/architecture/decisions/](docs/architecture/decisions/) for detailed ADRs:

- [ADR-0002: CI/CD Daily Rankings Database](docs/architecture/decisions/0002-cicd-daily-rankings-database.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/terrylica/crypto-marketcap-rank/issues)
- **Discussions**: [GitHub Discussions](https://github.com/terrylica/crypto-marketcap-rank/discussions)
- **API Docs**: [CoinGecko API](https://docs.coingecko.com/reference/coins-markets)

---

**Status**: ✅ Production-ready (Daily automated collections active)
