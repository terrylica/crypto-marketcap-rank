# START HERE - Historical Market Cap Toolkit Guide

Welcome! This toolkit provides everything you need to query, analyze, and visualize historical cryptocurrency market cap data.

## Quick Navigation

**First time?** Start with these 3 files:

1. Read **QUICK_START.md** (5 minutes) - Command cheat sheet and quick examples
2. Read **README.md** (10 minutes) - Complete feature documentation
3. Read **INDEX.md** (reference) - Detailed API and performance info

**Ready to start?** Run these commands:

```bash
cd /tmp/historical-marketcap-all-coins/

# See latest market snapshot
uv run advanced_query.py snapshot --date 2025-11-15

# Find top gainers
uv run advanced_query.py gainers

# Get Bitcoin historical data
uv run advanced_query.py query-coin --coin bitcoin
```

---

## What's Included

### 5 Powerful Tools

| Tool                  | Purpose                 | Use When                                 |
| --------------------- | ----------------------- | ---------------------------------------- |
| **query_basic.py**    | Read JSONL database     | You want simple queries                  |
| **advanced_query.py** | Advanced CLI queries    | You need complex filtering & date ranges |
| **analyze.py**        | Growth & trend analysis | You want market insights                 |
| **export.py**         | Multi-format export     | You need CSV/JSON/HTML data              |
| **visualize.py**      | Create charts           | You want visualizations                  |

### Sample Database

**market_cap_history.jsonl** contains:

- 42 records
- 7 cryptocurrencies (Bitcoin, Ethereum, BNB, Cardano, Solana, Ripple, Polkadot)
- 6 days of data (November 10-15, 2025)
- Each record: timestamp, coin, symbol, price, market_cap, volume, rank

### 4 Documentation Files

| Document               | Best For                           |
| ---------------------- | ---------------------------------- |
| **QUICK_START.md**     | Quick reference & command examples |
| **README.md**          | Complete feature documentation     |
| **INDEX.md**           | Detailed API reference             |
| **TOOLKIT_SUMMARY.md** | Project overview & architecture    |

---

## 30-Second Quick Start

```bash
# 1. Navigate to toolkit
cd /tmp/historical-marketcap-all-coins/

# 2. View market snapshot (latest data)
uv run advanced_query.py snapshot --date 2025-11-15 --top 10

# 3. Find top gainers
uv run advanced_query.py gainers --min-growth 15

# 4. Export to CSV
uv run export.py export-csv --output my_data.csv

# 5. Create visualization
uv run visualize.py price-trend --coins bitcoin,ethereum
```

Done! Check the generated files (_.csv, _.png).

---

## Command Cheat Sheet

### Queries

```bash
# Market snapshot
uv run advanced_query.py snapshot --date 2025-11-15

# Bitcoin history
uv run advanced_query.py query-coin --coin bitcoin

# Top gainers (15%+ growth)
uv run advanced_query.py gainers --min-growth 15

# Price range analysis
uv run advanced_query.py price-range --start-date 2025-11-10 --end-date 2025-11-15

# Market dominance
uv run advanced_query.py dominated-by --date 2025-11-15
```

### Analysis

```bash
# Full market analysis report
uv run analyze.py
```

### Export

```bash
# Export to CSV
uv run export.py export-csv --output data.csv

# Export to JSON
uv run export.py export-json --coin bitcoin

# Summary stats
uv run export.py export-summary

# HTML report
uv run export.py export-html --top 10
```

### Visualization

```bash
# Price chart
uv run visualize.py price-trend --coins bitcoin,ethereum

# Market cap chart
uv run visualize.py market-cap-trend --coins bitcoin,ethereum,bnb

# Top coins bar
uv run visualize.py top-coins-bar

# Coin overview (4-panel)
uv run visualize.py coin-overview --coin bitcoin

# Market distribution pie
uv run visualize.py market-distribution-pie
```

---

## Key Features

✓ **Query any time period** - Date range filtering (2025-11-10 to 2025-11-15)
✓ **Filter by coin** - Bitcoin, Ethereum, BNB, Cardano, Solana, Ripple, Polkadot
✓ **Calculate growth** - Automatic % change, growth comparisons
✓ **Analyze trends** - Volatility, rankings, top gainers
✓ **Export formats** - CSV, JSON, HTML, Summary statistics
✓ **Create charts** - Price trends, market cap, rankings, pie charts
✓ **CLI interface** - Easy command-line usage
✓ **Zero setup** - PEP 723 dependencies, just `uv run`

---

## Real Example Results

### Bitcoin Performance (Nov 10-15, 2025)

```
Price:      $85,000 → $94,500 (+11.18%)
Market Cap: $1.70T → $1.88T (+10.68%)
Dominance:  70.49% of total market
```

### Top Gainers

```
1. Polkadot: +25.00% growth
2. Cardano: +15.15% growth
3. Solana: +14.93% growth
```

### Market Snapshot (Nov 15, 2025)

```
Bitcoin:  $1.88T (70.49%)
Ethereum: $430B (16.16%)
BNB:      $94B (3.53%)
Ripple:   $134B (5.03%)
```

---

## Common Workflows

### Workflow 1: Daily Report (2 minutes)

```bash
uv run advanced_query.py snapshot --date 2025-11-15
uv run advanced_query.py gainers
uv run advanced_query.py dominated-by --date 2025-11-15
```

### Workflow 2: Coin Analysis (3 minutes)

```bash
uv run advanced_query.py query-coin --coin ethereum
uv run advanced_query.py price-range --start-date 2025-11-10 --coin ethereum
uv run visualize.py coin-overview --coin ethereum
```

### Workflow 3: Generate Report (5 minutes)

```bash
uv run analyze.py
uv run export.py export-csv --output report.csv
uv run export.py export-html --top 10
uv run visualize.py market-cap-trend --coins bitcoin,ethereum,bnb
```

---

## File Organization

```
/tmp/historical-marketcap-all-coins/
├── 00_START_HERE.md          <- You are here
├── QUICK_START.md            <- Quick reference (5 min read)
├── README.md                 <- Full documentation
├── INDEX.md                  <- API reference
├── TOOLKIT_SUMMARY.md        <- Project overview
├── VERIFICATION.txt          <- Test results
│
├── query_basic.py            <- Basic queries
├── advanced_query.py         <- Advanced CLI
├── analyze.py                <- Analysis
├── export.py                 <- Export tools
├── visualize.py              <- Charts
│
└── market_cap_history.jsonl  <- Sample database
```

---

## Troubleshooting

### "uv not found"

Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### "No data found for coin"

Available coins: bitcoin, ethereum, bnb, cardano, solana, ripple, polkadot

### "No data found for date"

Available dates: 2025-11-10 to 2025-11-15 (use YYYY-MM-DD format)

### "File not found"

Make sure you're in: `/tmp/historical-marketcap-all-coins/`

---

## Next Steps

1. **Read QUICK_START.md** - 5-minute quick reference
2. **Try a query** - `uv run advanced_query.py snapshot --date 2025-11-15`
3. **Read README.md** - Full documentation
4. **Explore visualizations** - Create your first chart
5. **Export data** - Try CSV or JSON export

---

## Support

- **Quick questions?** See QUICK_START.md
- **How to use X?** Check README.md
- **Function details?** Look in INDEX.md
- **How it works?** Read TOOLKIT_SUMMARY.md
- **Did it work?** Check VERIFICATION.txt

---

## Key Stats

- **Data**: 42 records, 7 coins, 6 days
- **Tools**: 5 Python scripts
- **Docs**: 4 comprehensive guides
- **Performance**: <100ms for queries
- **Setup**: Zero - works immediately
- **Status**: Production ready

---

**Ready? Start with:**

```bash
uv run advanced_query.py snapshot --date 2025-11-15
```

Enjoy exploring the toolkit!
