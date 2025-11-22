# Quick Start Guide

## Installation

```bash
cd /tmp/historical-marketcap-all-coins/
# No installation needed! Uses uv for inline dependencies (PEP 723)
```

## 5-Minute Tutorial

### 1. View Latest Market Data

```bash
uv run advanced_query.py snapshot --date 2025-11-15 --top 10
```

### 2. Find Top Gainers

```bash
uv run advanced_query.py gainers --window 5 --min-growth 15
```

### 3. Get Bitcoin History

```bash
uv run advanced_query.py query-coin --coin bitcoin
```

### 4. Export Data

```bash
uv run export.py export-csv --output data.csv
uv run export.py export-json --coin bitcoin --output btc.json
uv run export.py export-html --top 10
```

### 5. Create Visualizations

```bash
uv run visualize.py price-trend --coins bitcoin,ethereum --output price.png
uv run visualize.py market-cap-trend --output mcap.png
uv run visualize.py top-coins-bar --output top10.png
uv run visualize.py coin-overview --coin bitcoin --output btc.png
```

### 6. Full Analysis Report

```bash
uv run analyze.py
```

## Command Cheat Sheet

| Task             | Command                                                                              |
| ---------------- | ------------------------------------------------------------------------------------ |
| Market snapshot  | `uv run advanced_query.py snapshot --date 2025-11-15`                                |
| Top gainers      | `uv run advanced_query.py gainers --min-growth 15`                                   |
| Coin history     | `uv run advanced_query.py query-coin --coin bitcoin`                                 |
| Price range      | `uv run advanced_query.py price-range --start-date 2025-11-10 --end-date 2025-11-15` |
| Market dominance | `uv run advanced_query.py dominated-by --date 2025-11-15`                            |
| Export CSV       | `uv run export.py export-csv --output data.csv`                                      |
| Export JSON      | `uv run export.py export-json --coin bitcoin`                                        |
| Export summary   | `uv run export.py export-summary`                                                    |
| HTML report      | `uv run export.py export-html --top 10`                                              |
| Price chart      | `uv run visualize.py price-trend --coins bitcoin,ethereum`                           |
| Market cap chart | `uv run visualize.py market-cap-trend --coins bitcoin,ethereum,bnb`                  |
| Top coins bar    | `uv run visualize.py top-coins-bar`                                                  |
| Coin overview    | `uv run visualize.py coin-overview --coin bitcoin`                                   |
| Pie chart        | `uv run visualize.py market-distribution-pie`                                        |
| Full analysis    | `uv run analyze.py`                                                                  |

## Key Results from Sample Data

### Bitcoin Performance (Nov 10-15, 2025)

- **Price**: $85,000 → $94,500 (+11.18%)
- **Market Cap**: $1.70T → $1.88T (+10.68%)
- **Dominance**: 70.49% of total market

### Top Gainers

1. **Polkadot**: +25.00%
2. **Cardano**: +15.15%
3. **Solana**: +14.93%

### Market Snapshot (Nov 15, 2025)

| Rank | Coin     | Symbol | Market Cap |
| ---- | -------- | ------ | ---------- |
| 1    | Bitcoin  | BTC    | $1.88T     |
| 2    | Ethereum | ETH    | $430B      |
| 3    | BNB      | BNB    | $94B       |
| 4    | Cardano  | ADA    | $38B       |
| 5    | Solana   | SOL    | $77B       |

## Available Data

- **Coins**: Bitcoin, Ethereum, BNB, Cardano, Solana, Ripple, Polkadot
- **Period**: 2025-11-10 to 2025-11-15 (6 days)
- **Records**: 42 total (6 per coin)
- **Format**: JSONL (market_cap_history.jsonl)

## Example Workflows

### Workflow 1: Daily Market Analysis

```bash
uv run advanced_query.py snapshot --date 2025-11-15 --top 10
uv run advanced_query.py gainers
uv run advanced_query.py dominated-by --date 2025-11-15
```

### Workflow 2: Coin Deep Dive

```bash
uv run advanced_query.py query-coin --coin ethereum --start-date 2025-11-10 --end-date 2025-11-15
uv run advanced_query.py price-range --start-date 2025-11-10 --end-date 2025-11-15 --coin ethereum
uv run visualize.py coin-overview --coin ethereum
```

### Workflow 3: Generate Report

```bash
uv run export.py export-csv --output report.csv
uv run export.py export-summary
uv run export.py export-html --top 10
uv run visualize.py market-cap-trend --coins bitcoin,ethereum,bnb
```

## Generated Files

After running commands, you'll get:

- **price_chart.png** - Price trends
- **market_cap_chart.png** - Market cap trends
- **top_coins.png** - Ranking chart
- **bitcoin_overview.png** - Detailed analysis
- **report\_\*.html** - HTML report
- **summary\_\*.csv** - Statistics
- **export\_\*.csv** - Raw data

## Troubleshooting

### "No data found for coin"

- Check coin name: bitcoin, ethereum, bnb, cardano, solana, ripple, polkadot
- Use lowercase

### "No data found for date"

- Available dates: 2025-11-10 to 2025-11-15
- Use YYYY-MM-DD format

### "uv not found"

- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Or: `brew install uv`

## Next Steps

1. Read **README.md** for detailed documentation
2. Explore different coin combinations in visualizations
3. Create custom date ranges for analysis
4. Export data for external analysis
5. Modify scripts to add custom metrics

## Support

For detailed information, see:

- README.md - Full documentation
- query_basic.py - Source code comments
- advanced_query.py - CLI help: `uv run advanced_query.py --help`
