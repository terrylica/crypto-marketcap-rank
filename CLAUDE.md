# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Goal:** Download and rank all cryptocurrencies by daily market cap across 15 years of historical data (2010-2025).

**Approach:** Hybrid strategy combining:

- **Kaggle dataset** (verified market cap, 2013-2021, 4K coins)
- **CryptoCompare API** (estimated market cap, 2010-2025, 18K+ coins)

**Expected Output:** 100-150M row CSV file with daily market cap rankings for all cryptocurrencies.

## Repository Structure

```
crypto-marketcap-rank/
├── research/                    # API investigation & prototypes
│   ├── coinpaprika-probe/       # CoinPaprika API tests (❌ 24hr limit)
│   ├── coingecko-marketcap-probe/ # CoinGecko tests (❌ 365-day limit)
│   ├── coincap-probe/           # CoinCap tests (❌ no market cap field)
│   ├── messari-probe/           # Messari tests (❌ paid only)
│   ├── free-crypto-historical/  # CryptoCompare tests (⚠️ estimated)
│   ├── historical-marketcap-all-coins/ # Production implementations
│   ├── kaggle-datasets-search/  # Kaggle dataset catalog
│   ├── cryptodatadownload-search/
│   └── academic-sources-search/ # 50+ source catalog
├── scripts/                     # (To be created) Production scripts
├── data/                        # (To be created) Downloaded data
├── PROJECT_PLAN.md              # Complete implementation plan
├── RESEARCH_SUMMARY.md          # Research findings summary
└── README.md                    # Quick start guide
```

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
#   "pandas",
# ]
# ///
```

## Research Scripts Organization

### Naming Convention

Scripts follow numbered progression showing iteration:

- `01_*.py` - Initial feasibility/testing
- `02_*.py` - Second iteration/alternative approach
- `03_*.py` - Optimized implementation
- `04_*.py` - Production refinement
- `05_*.py` - Final production version

### Key Research Artifacts

**Production-Ready Collectors:**

- `research/historical-marketcap-all-coins/05_production_implementation.py` - Complete storage system with tiered retention
- `research/free-crypto-historical/get_all_coins_history_final.py` - CryptoCompare batch downloader
- `research/historical-marketcap-all-coins/04_production_collector.py` - Optimized collector with resume capability

**Query/Analysis Tools:**

- `research/historical-marketcap-all-coins/query_basic.py` - Basic JSONL querying
- `research/historical-marketcap-all-coins/advanced_query.py` - Advanced analytics
- `research/historical-marketcap-all-coins/visualize.py` - Data visualization
- `research/historical-marketcap-all-coins/export.py` - CSV export utilities

**Architecture Analysis:**

- `research/historical-marketcap-all-coins/01_storage_analysis.py` - Storage requirements
- `research/historical-marketcap-all-coins/02_storage_engine.py` - Storage engine design
- `research/historical-marketcap-all-coins/04_comprehensive_benchmarks.py` - Performance benchmarks

## Architecture Principles

### Data Storage Strategy

**Tiered Retention System:**

- **HOT** (0-30 days): SQLite with WAL mode, optimized for writes
- **WARM** (30 days - 1 year): Compressed JSONL files
- **COLD** (1-5 years): Gzip-compressed archives
- **ARCHIVE** (5+ years): High compression, infrequent access

### API Rate Limiting

**CryptoCompare (Free Tier):**

- No authentication required
- ~300 requests/hour safe limit
- 100ms delay between requests recommended
- Single-threaded mandatory

**CoinPaprika (Free Tier):**

- 20,000 monthly calls limit
- No authentication required
- Rate limit: ~1 req/sec

### Market Cap Data Quality

| Period    | Source        | Accuracy     | Notes                    |
| --------- | ------------- | ------------ | ------------------------ |
| 2013-2021 | Kaggle        | ✅ HIGH      | Real verified market cap |
| 2010-2013 | CryptoCompare | ⚠️ ESTIMATED | Price × current supply   |
| 2021-2025 | CryptoCompare | ⚠️ ESTIMATED | Price × current supply   |

## Common Development Tasks

### Running Research Scripts

```bash
# Test API connectivity
cd research/free-crypto-historical
uv run test_cryptocompare.py

# Run production collector
cd research/historical-marketcap-all-coins
uv run 05_production_implementation.py

# Query collected data
uv run query_basic.py

# Generate visualizations
uv run visualize.py
```

### Testing Individual APIs

```bash
# CoinGecko (365-day limit test)
cd research/coingecko-marketcap-probe
uv run test_coingecko.py

# CoinCap (price history test)
cd research/coincap-probe
uv run 01_test_history_endpoint.py

# Messari (enterprise restriction verification)
cd research/messari-probe
uv run test_messari_api.py
```

### Data Analysis

```bash
# Basic querying
cd research/historical-marketcap-all-coins
uv run query_basic.py

# Advanced analytics with date ranges
uv run advanced_query.py

# Export to CSV
uv run export.py
```

## Critical Implementation Notes

### Resume Capability Required

All production collectors **must** implement checkpointing:

- Save progress after each coin
- Store last successful timestamp
- Allow restart from checkpoint
- Expected runtime: 50-100 hours for 18K+ coins

### Data Validation

Before accepting any market cap data:

- Check for zero values (invalid)
- Verify timestamps are sequential
- Detect anomalous jumps (>1000% daily change)
- Log missing data points

### File Size Expectations

**Raw Downloads:**

- Kaggle: 820 MB compressed
- CryptoCompare: ~15-20 GB JSONL

**Final Output:**

- Uncompressed CSV: 8-12 GB
- Gzip compressed: 1-2 GB
- Expected rows: 100-150 million

## Project Timeline

| Phase           | Duration     | Type    |
| --------------- | ------------ | ------- |
| Setup scripts   | 2-4 hours    | Active  |
| Download Kaggle | 10 minutes   | Passive |
| Download APIs   | 50-100 hours | Passive |
| Merge & rank    | 1 hour       | Active  |
| **Total**       | **3-5 days** | Mixed   |

## Key Findings from Research

### APIs Tested (5 Total)

❌ **CoinGecko:** 365-day limit on free tier
❌ **CoinCap:** No market cap field in responses
❌ **Messari:** Enterprise plan required ($5K+/year)
⚠️ **CryptoCompare:** 18,637 coins, estimated market cap
✅ **Kaggle:** Real market cap, 4K coins, 2013-2021

### Critical Insight

**No single free source provides historical market cap for all coins.** The hybrid approach (Kaggle + CryptoCompare) is the only viable free solution for complete historical coverage.

## Next Implementation Phase

Three production scripts need to be created in `scripts/`:

1. **download_kaggle.py** - Download and standardize Kaggle dataset
2. **download_cryptocompare.py** - Fetch all 18K+ coins with resume capability
3. **merge_and_rank.py** - Combine datasets, calculate daily rankings, export final CSV

Refer to `PROJECT_PLAN.md` for detailed specifications.
