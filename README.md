# Cryptocurrency Market Cap Rankings Database

[![Daily Collection](https://github.com/tainora/crypto-marketcap-rank/actions/workflows/daily-collection.yml/badge.svg)](https://github.com/tainora/crypto-marketcap-rank/actions/workflows/daily-collection.yml)
[![CI Status](https://github.com/tainora/crypto-marketcap-rank/actions/workflows/ci.yml/badge.svg)](https://github.com/tainora/crypto-marketcap-rank/actions/workflows/ci.yml)

Daily automated collection of comprehensive cryptocurrency market cap rankings for all 19,411+ CoinGecko coins. Distributed as queryable database artifacts via GitHub Releases.

## Features

- **Complete Coverage**: All 19,411+ ranked cryptocurrencies
- **Daily Updates**: Automated collection at 6:00 AM UTC
- **Multiple Formats**: DuckDB (SQL queries), Parquet (ClickHouse), CSV (universal)
- **Zero Cost**: Operates within free tiers (GitHub Actions + CoinGecko API)
- **Public Dataset**: Research-ready, freely downloadable
- **Production Quality**: Validated, versioned, and continuously monitored

## Quick Start

### Download Latest Data

```bash
# Download DuckDB database (recommended)
wget https://github.com/tainora/crypto-marketcap-rank/releases/download/latest/crypto_rankings_2025-11-21.duckdb

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
SELECT * FROM rankings WHERE symbol = 'BTC';

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
- **Use Case**: Instant SQL queries, data analysis, no setup required
- **Best For**: Researchers, analysts, quick exploration

### Parquet (ClickHouse Import)

- **Directory**: `crypto_rankings_YYYY-MM-DD.parquet/`
- **Size**: ~50-150 MB compressed
- **Partitioning**: `year=YYYY/month=MM/day=DD/`
- **Use Case**: ClickHouse import, data pipelines, production systems
- **Best For**: Companies, data engineers, ETL workflows

### CSV (Universal Compatibility)

- **File**: `crypto_rankings_YYYY-MM-DD.csv.gz`
- **Size**: ~50 MB compressed
- **Use Case**: Spreadsheets, legacy tools, maximum compatibility
- **Best For**: Excel users, non-technical users, quick viewing

## Schema

All formats share the same schema:

| Column                 | Type    | Description                  |
| ---------------------- | ------- | ---------------------------- |
| `date`                 | DATE    | Collection date (YYYY-MM-DD) |
| `rank`                 | INTEGER | Market cap rank (1-based)    |
| `coin_id`              | VARCHAR | CoinGecko coin identifier    |
| `symbol`               | VARCHAR | Ticker symbol (e.g., BTC)    |
| `name`                 | VARCHAR | Full coin name               |
| `market_cap`           | DOUBLE  | Market capitalization (USD)  |
| `price`                | DOUBLE  | Current price (USD)          |
| `volume_24h`           | DOUBLE  | 24-hour trading volume (USD) |
| `price_change_24h_pct` | DOUBLE  | 24-hour price change (%)     |

## Architecture

```
Collection → Build → Validate → Release
    ↓          ↓         ↓          ↓
  78 API    3 formats  Quality   GitHub
  calls     built      checks    Releases
```

### Technical Stack

- **Collection**: Python + CoinGecko API (78 API calls/day)
- **Databases**: DuckDB, Parquet (PyArrow), CSV
- **CI/CD**: GitHub Actions (daily cron + manual trigger)
- **Distribution**: GitHub Releases ("latest" tag + monthly archives)
- **Validation**: pytest + data quality checks
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
git clone https://github.com/tainora/crypto-marketcap-rank.git
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
│   ├── daily-collection.yml
│   ├── monthly-archive.yml
│   └── ci.yml
├── src/                    # Production code
│   ├── collectors/         # CoinGecko API collector
│   ├── builders/           # Database builders (DuckDB/Parquet/CSV)
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

### Latest Release

- **Tag**: `latest`
- **Updated**: Daily at 6:00 AM UTC
- **Contents**: DuckDB, Parquet, CSV for most recent collection date

### Monthly Archives

- **Tags**: `v2025-11`, `v2025-12`, etc.
- **Created**: 1st of every month
- **Contents**: Compressed archive of previous month's daily collections

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

- **Issues**: [GitHub Issues](https://github.com/tainora/crypto-marketcap-rank/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tainora/crypto-marketcap-rank/discussions)
- **API Docs**: [CoinGecko API](https://docs.coingecko.com/reference/coins-markets)

---

**Status**: ✅ Production-ready (Daily automated collections active)
