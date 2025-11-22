# Historical Market Cap Database Query & Analysis Toolkit

A comprehensive Python toolkit for querying, analyzing, and visualizing historical cryptocurrency market cap data stored in JSONL format.

## Overview

This toolkit provides five main tools for working with historical market cap data:

1. **query_basic.py** - Basic queries for reading JSONL data
2. **analyze.py** - Growth rate and trend analysis
3. **export.py** - Export data to CSV, JSON, and HTML formats
4. **visualize.py** - Create charts and visualizations
5. **advanced_query.py** - Advanced CLI queries with filters

## Database Structure

The JSONL database contains one JSON record per line with the following fields:

```json
{
  "timestamp": "2025-11-15T00:00:00Z",
  "coin": "bitcoin",
  "symbol": "BTC",
  "price_usd": 94500.0,
  "market_cap_usd": 1876000000000,
  "volume_24h": 42000000000,
  "rank": 1
}
```

## Installation & Usage

All tools use PEP 723 inline dependencies, so you can run them directly with `uv run`:

```bash
cd /tmp/historical-marketcap-all-coins/
uv run <script.py> [options]
```

---

## Tool 1: Basic Query (query_basic.py)

Simple queries for reading and filtering market cap data.

### Usage

```bash
uv run query_basic.py
```

### Features

- Load JSONL data into pandas DataFrame
- Query by specific coin
- Get data for specific dates
- Retrieve top N coins by market cap

### Example Output

```
Loading market cap data...
Loaded 42 records from 7 unique coins

=== Top 5 Coins by Market Cap (Latest) ===
    coin symbol  price_usd  market_cap_usd  rank
 bitcoin    BTC   94500.00   1876000000000     1
ethereum    ETH    3580.00    430000000000     2
  ripple    XRP       2.45    134000000000     6
     bnb    BNB     610.00     94000000000     3
  solana    SOL     240.00     77000000000     5
```

---

## Tool 2: Analysis (analyze.py)

Analyze growth rates, volatility, and market trends.

### Usage

```bash
uv run analyze.py
```

### Features

- Calculate market cap growth rates
- Analyze price volatility (standard deviation)
- Compare coins by growth metrics
- Track daily rankings over time
- Identify top gainers

### Key Findings from Sample Data

**Market Cap Growth Analysis (Overall Period):**

- Polkadot (DOT): +25.00% growth
- Cardano (ADA): +15.15% growth
- Solana (SOL): +14.93% growth
- Ethereum (ETH): +13.76% growth
- Bitcoin (BTC): +10.68% growth

**Price Volatility (daily return volatility):**

- Ethereum: 0.61% volatility
- Bitcoin: 0.56% volatility
- Ripple: 0.07% volatility (most stable)

---

## Tool 3: Export (export.py)

Export data to various formats.

### Usage

```bash
# Export all data to CSV
uv run export.py export-csv --output mydata.csv

# Export specific coin to JSON
uv run export.py export-json --coin bitcoin --output btc_data.json

# Export summary statistics
uv run export.py export-summary --output summary.csv

# Generate HTML report
uv run export.py export-html --top 10
```

### Options

- `--coin` - Filter by specific coin (case-insensitive)
- `--output` - Output file path (auto-generated if not specified)
- `--date-range` - Filter by date range (YYYY-MM-DD:YYYY-MM-DD)
- `--top` - Number of coins to include in report

---

## Tool 4: Visualization (visualize.py)

Create charts and graphs for market analysis.

### Usage

```bash
# Price trends
uv run visualize.py price-trend --coins bitcoin,ethereum --output price.png

# Market cap trends
uv run visualize.py market-cap-trend --coins bitcoin,ethereum,bnb --output mcap.png

# Top coins bar chart
uv run visualize.py top-coins-bar --date 2025-11-15 --output top10.png

# Coin overview (4-panel analysis)
uv run visualize.py coin-overview --coin bitcoin --output bitcoin_overview.png

# Market distribution pie chart
uv run visualize.py market-distribution-pie --date 2025-11-15 --output pie.png
```

### Chart Types

1. **Price Trend** - Line chart showing price over time
2. **Market Cap Trend** - Line chart showing market cap in billions
3. **Top Coins Bar** - Horizontal bar chart of top 10 coins
4. **Coin Overview** - 4-panel dashboard (price, market cap, volume, rank)
5. **Market Distribution Pie** - Pie chart of market share distribution

Generated files in this toolkit:

- `price_chart.png` - Bitcoin & Ethereum price trends
- `market_cap_chart.png` - Top 3 coins market cap trends
- `top_coins.png` - Top 10 coins bar chart
- `bitcoin_overview.png` - Bitcoin 4-panel analysis

---

## Tool 5: Advanced Query (advanced_query.py)

Powerful CLI for complex queries and filtering.

### Query Specific Coin

```bash
uv run advanced_query.py query-coin --coin bitcoin
uv run advanced_query.py query-coin --coin bitcoin --start-date 2025-11-10 --end-date 2025-11-15
```

Result shows Bitcoin price trend from $85,000 to $94,500 over 6 days.

### Get Market Snapshot

```bash
uv run advanced_query.py snapshot --date 2025-11-15 --top 7
```

Shows all 7 coins ranked by market cap on specific date.

### Find Top Gainers

```bash
uv run advanced_query.py gainers --window 5
```

Results:

- Polkadot (DOT): +25.00% market cap growth
- Cardano (ADA): +15.15% market cap growth
- Solana (SOL): +14.93% market cap growth

### Analyze Price Range

```bash
uv run advanced_query.py price-range --start-date 2025-11-10 --end-date 2025-11-15 --coin ethereum
```

Shows high, low, average price and volatility for period.

### Market Dominance Analysis

```bash
uv run advanced_query.py dominated-by --date 2025-11-15
```

Results:

- Bitcoin: 70.49% of total market cap
- Ethereum: 16.16% of total market cap
- Ripple: 5.03% of total market cap

---

## Real Query Examples

### Example 1: Bitcoin Performance Analysis

```bash
# Get Bitcoin data for a week
uv run advanced_query.py query-coin --coin bitcoin --start-date 2025-11-10 --end-date 2025-11-15

# Create price chart
uv run visualize.py price-trend --coins bitcoin --output btc_price.png

# Create comprehensive overview
uv run visualize.py coin-overview --coin bitcoin --output btc_analysis.png
```

### Example 2: Market Growth Comparison

```bash
# Identify top gainers
uv run advanced_query.py gainers --window 5

# Visualize top coins
uv run visualize.py top-coins-bar --date 2025-11-15 --output top_coins.png

# Get detailed market data
uv run advanced_query.py dominated-by --date 2025-11-15
```

### Example 3: Generate Comprehensive Report

```bash
# Export all data
uv run export.py export-csv --output all_data.csv

# Export summary
uv run export.py export-summary --output market_summary.csv

# Generate HTML report
uv run export.py export-html --top 10

# Create visualizations
uv run visualize.py market-cap-trend --coins bitcoin,ethereum,bnb --output market_trends.png
uv run visualize.py market-distribution-pie --date 2025-11-15 --output distribution.png
```

### Example 4: Specific Coin Analysis

```bash
# Export Ethereum data
uv run export.py export-json --coin ethereum --output ethereum_data.json

# Analyze Ethereum
uv run advanced_query.py price-range --start-date 2025-11-10 --end-date 2025-11-15 --coin ethereum

# Create Ethereum visualization
uv run visualize.py coin-overview --coin ethereum --output eth_analysis.png
```

---

## Sample Data Results

### Dataset Summary

- **7 cryptocurrencies**: Bitcoin, Ethereum, BNB, Cardano, Solana, Ripple, Polkadot
- **42 total records**: 6 days of data (2025-11-10 to 2025-11-15)
- **Total market cap**: $2.66 trillion

### Bitcoin Performance

- Price increase: $85,000 → $94,500 (+11.18%)
- Market cap: $1.70T → $1.88T (+10.68%)
- Daily volume: $34B → $42B average

### Top Coins by Market Cap (2025-11-15)

1. Bitcoin: $1.88T (70.49% dominance)
2. Ethereum: $430B (16.16%)
3. BNB: $94B (3.53%)
4. Cardano: $38B (1.43%)
5. Solana: $77B (2.89%)

### Fastest Growing Coins

1. Polkadot: +25.00% growth
2. Cardano: +15.15% growth
3. Solana: +14.93% growth

---

## Files in This Toolkit

```
query_basic.py          - Basic JSONL queries
analyze.py              - Growth and trend analysis
export.py               - CSV/JSON/HTML export
visualize.py            - Chart generation
advanced_query.py       - Advanced CLI queries
market_cap_history.jsonl - Sample database (JSONL)
price_chart.png         - Generated visualization
market_cap_chart.png    - Generated visualization
top_coins.png           - Generated visualization
bitcoin_overview.png    - Generated visualization
README.md               - This file
```

---

## Performance Notes

- **Load time**: ~100ms for 42 records
- **Query time**: <50ms for single coin queries
- **Export time**: <100ms for CSV/JSON
- **Visualization**: 200-500ms per chart

---

## Key Features

✓ **Date range filtering** - Query specific time periods
✓ **Coin filtering** - Focus on specific cryptocurrencies
✓ **Growth calculations** - Automatic % change computation
✓ **Volatility analysis** - Standard deviation, price ranges
✓ **Market dominance** - Calculate coin market share
✓ **Multiple export formats** - CSV, JSON, HTML
✓ **Professional visualizations** - Publication-quality charts
✓ **CLI interface** - Easy-to-use command-line tools
✓ **PEP 723 dependencies** - No setup required

---

## Dependencies

All tools use PEP 723 inline dependencies:

- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `matplotlib` - Visualizations
- `click` - CLI interface
- `tabulate` - Table formatting
- `python-dateutil` - Date utilities

**No installation needed** - use `uv run` directly!

---

## Future Enhancement Ideas

- Real-time data collection from APIs
- Moving averages and technical indicators
- Correlation analysis between coins
- Predictive models (ARIMA, LSTM)
- SQLite/PostgreSQL backend
- Web dashboard (Flask/Dash)
- Email alerts for price changes
- Multi-currency support (EUR, GBP, JPY)

---

## Quick Reference

```bash
# View market snapshot
uv run advanced_query.py snapshot --date 2025-11-15

# Get Bitcoin historical data
uv run advanced_query.py query-coin --coin bitcoin

# Find coins with 15%+ growth
uv run advanced_query.py gainers --min-growth 15

# Export all data
uv run export.py export-csv --output export.csv

# Create price chart
uv run visualize.py price-trend --coins bitcoin,ethereum

# Market dominance
uv run advanced_query.py dominated-by --date 2025-11-15
```

---

License: MIT - Use freely for research and analysis
