# Crypto Market Cap Rankings - Project Status

**Last Updated**: 2025-11-24
**Status**: ✅ Production-ready (v2.0.0 released 2025-11-23)

---

## Quick Summary

**Goal**: Comprehensive cryptocurrency market cap rankings (historical + current)

**Current State**:

- ✅ Automated daily collection (GitHub Actions, 6:00 AM UTC)
- ✅ Schema V2 migration complete (PyArrow native types)
- ✅ DuckDB + Parquet database formats (CSV deprecated)
- ✅ Daily release tags (`daily-YYYY-MM-DD` pattern)
- ✅ Comprehensive validation (zero duplicate/null data)
- ✅ Production monitoring and error handling

**Data Source**: CoinGecko API (selected after investigating 7 alternatives)

---

## What We Have

### 1. Complete Coin ID List ✅

**File**: `data/coin_ids/coingecko_all_coin_ids.json`
**Count**: 19,410 active coins
**Includes**: Dead 2013-era coins (Namecoin, Peercoin, etc.) for historical accuracy

### 2. Current Rankings Snapshot ✅

**File**: `data/rankings/current_rankings_20251120_231108.csv`
**Count**: 13,000 ranked coins (rank #1 to #12,991)
**Date**: 2025-11-20 23:11:08
**Coverage**: 67% of all CoinGecko coins

### 3. Working Tools ✅

**Location**: `tools/`

- `fetch_all_coin_ids.py` - Get all CoinGecko coin IDs
- `fetch_current_rankings.py` - Get current top N rankings
- `calculate_point_in_time_rankings.py` - Calculate rankings from market_cap data
- `lookup_rank_by_id_date.py` - Lookup specific coin rank on date

### 4. Documentation ✅

**Root Level**:

- `README.md` - Project overview
- `CLAUDE.md` - Working notes
- `LESSONS_LEARNED.md` - Failed experiments & discoveries
- `API_INVESTIGATIONS_SUMMARY.md` - API research results
- `PROJECT_STATUS.md` - This file

**Organized Docs**:

- `docs/canonical/` - Working solutions
- `docs/warnings/` - Failed approaches
- `docs/investigations/` - Research findings
- `docs/archive/` - Historical records

---

## What We Learned

### Critical Discoveries

**1. CoinGecko is the Winner** (after testing 7 APIs)

- Most comprehensive: 19,410 coins
- Best free tier: 10,000 calls/month
- No credit card required
- See: `API_INVESTIGATIONS_SUMMARY.md`

**2. Historical Rankings Don't Exist**

- CoinGecko `/coins/{id}/history` returns market_cap but NOT rank
- Must collect ALL coins' market_caps for a date to calculate rankings
- See: `docs/warnings/COINGECKO_RANK_LIMITATION.md`

**3. crypto2 R Package Insufficient**

- Only 69 coins (missing Ethereum, BNB, Cardano, Solana, etc.)
- Insufficient for comprehensive rankings
- ❌ Deleted - no longer using
- See: `LESSONS_LEARNED.md`

**4. Rate Limiting Without API Key**

- 20s delay = 100% success (3 calls/min)
- 4s delay with free Demo API key = 100% success (15 calls/min)
- Undocumented actual limits stricter than docs claim
- See: `docs/warnings/NO_API_KEY_EXPERIMENT.md`

**5. Maximum Ranking Depth**

- CoinGecko ranks ~13,000 coins (67% of total)
- Remaining 6,410 unranked (too low market cap / dead)
- Last ranked: #12,991
- See: `docs/canonical/MAXIMUM_RANKING_DEPTH.md`

---

## Canonical Workflow

**The ONLY way to get historical point-in-time rankings**:

### Prerequisites

✅ **Step 0**: Get coin IDs first (MANDATORY)

```bash
uv run tools/fetch_all_coin_ids.py
```

**Decision point**: Which coins to rank?

- All 19,410? (comprehensive but slow)
- Top 13,000 ranked? (faster, complete ranked set)
- Top 500/1000? (very fast, major coins only)

### Historical Collection (One-Time Backfill)

⏳ **Step 1**: Collect historical market_cap for all target coins

```bash
# For each coin × each date:
# GET /coins/{coin_id}/history?date=DD-MM-YYYY
```

**Time estimate** (500 coins × 365 days):

- 182,500 API calls
- With API key: ~8.5 days
- Without API key: ~42 days

⏳ **Step 2**: Calculate point-in-time rankings

```bash
uv run tools/calculate_point_in_time_rankings.py
```

### Daily Collection (Recommended Strategy)

✅ **Daily**: Collect current rankings snapshot

```bash
# Automate with cron (once per day)
uv run tools/fetch_current_rankings.py 1000
```

**Benefits**:

- Only 4 API calls/day
- 120 calls/month (1.2% of limit)
- Builds comprehensive database over time
- No survivorship bias
- Sustainable within free tier

---

## Current Capabilities

### What You Can Do RIGHT NOW ✅

**1. Get Current Rankings**

```bash
# Top 500 coins
uv run tools/fetch_current_rankings.py 500

# Top 1,000 coins
uv run tools/fetch_current_rankings.py 1000

# ALL ~13,000 ranked coins
uv run tools/fetch_current_rankings.py all
```

**2. Get All Coin IDs**

```bash
uv run tools/fetch_all_coin_ids.py
```

**3. Explore Data**

```bash
# View current rankings
cat data/rankings/current_rankings_20251120_231108.csv | head -20

# Check coin IDs
cat data/coin_ids/all_coins.csv | grep -i ethereum
```

### What's Pending ⏳

**1. Historical Backfill** (not started)

- Collect market_cap for all target coins on past dates
- Calculate historical rankings
- Very slow (days/weeks depending on scope)

**2. Daily Collection Automation** (not started)

- Set up cron job for daily rankings
- Gradually build historical database

**3. Kaggle Dataset Investigation** (next task)

- Check if existing Kaggle datasets useful
- Verify quality, coverage, freshness

---

## File Organization

### Project Structure

```
crypto-marketcap-rank/
├── README.md                          # Project overview
├── CLAUDE.md                          # Working notes
├── PROJECT_STATUS.md                  # This file
├── LESSONS_LEARNED.md                 # Failed experiments
├── API_INVESTIGATIONS_SUMMARY.md      # API research
│
├── data/
│   ├── README.md                      # Data index (to be created)
│   ├── coin_ids/                      # All 19,410 coin IDs
│   │   ├── README.md                  # Coin ID collection details
│   │   ├── coingecko_all_coin_ids.json
│   │   ├── all_coins.csv
│   │   └── SUMMARY.json
│   └── rankings/                      # Current rankings
│       ├── README.md                  # Rankings collection details
│       ├── current_rankings_*.csv     # Rankings CSV
│       ├── current_rankings_*.json    # Full data
│       ├── summary_*.json             # Metadata
│       └── fetch_current_rankings.py  # Collection script
│
├── tools/                             # Working collection tools
│   ├── fetch_all_coin_ids.py         # Get all coin IDs
│   ├── fetch_current_rankings.py     # Get current rankings
│   ├── calculate_point_in_time_rankings.py
│   └── lookup_rank_by_id_date.py
│
├── docs/
│   ├── canonical/                     # Working solutions
│   │   ├── COIN_IDS_COMPLETE.md
│   │   ├── CURRENT_RANKINGS_SOLUTION.md
│   │   ├── MAXIMUM_RANKING_DEPTH.md
│   │   └── RANK_LOOKUP_GUIDE.md
│   ├── warnings/                      # Failed approaches
│   │   ├── COINGECKO_RANK_LIMITATION.md
│   │   ├── CRYPTO2_QUALITY_ANALYSIS.md
│   │   ├── EXPERIMENT_FILES_GUIDE.md
│   │   └── NO_API_KEY_EXPERIMENT.md
│   ├── investigations/                # Research findings
│   │   ├── COINGECKO_COLLECTION_STATUS.md
│   │   ├── COINGECKO_COVERAGE_ANALYSIS.md
│   │   ├── KAGGLE_VALIDATION_RESULTS.md
│   │   └── RESEARCH_SUMMARY.md
│   └── archive/                       # Historical records
│       └── PROJECT_PLAN.md
│
├── logs/                              # Collection logs (if any)
└── validation/                        # Validation scripts/reports
```

---

## Next Steps

### Immediate (This Session)

- [x] Complete project cleanup
- [x] Create comprehensive documentation
- [ ] Create `data/README.md` as index
- [ ] Create `CANONICAL_WORKFLOW.md` guide
- [ ] Investigate Kaggle dataset

### Short-Term (Next Session)

- [ ] Set up daily collection automation (cron job)
- [ ] Test daily collection workflow
- [ ] Verify data consistency

### Long-Term (Future)

- [ ] Historical backfill strategy
- [ ] Data storage optimization
- [ ] Analysis tools development
- [ ] Visualization/dashboard

---

## Key Files Reference

### Documentation

| File                            | Purpose                                             |
| ------------------------------- | --------------------------------------------------- |
| `README.md`                     | Project overview, quick start                       |
| `PROJECT_STATUS.md`             | Current state, capabilities, next steps (this file) |
| `LESSONS_LEARNED.md`            | Failed experiments, warnings, discoveries           |
| `API_INVESTIGATIONS_SUMMARY.md` | Why CoinGecko, API comparisons                      |

### Data

| Location         | Content                                   |
| ---------------- | ----------------------------------------- |
| `data/coin_ids/` | All 19,410 CoinGecko coin IDs             |
| `data/rankings/` | Current rankings snapshot (~13,000 coins) |

### Tools

| Tool                                  | Function                     |
| ------------------------------------- | ---------------------------- |
| `fetch_all_coin_ids.py`               | Get complete coin ID list    |
| `fetch_current_rankings.py`           | Get current top N rankings   |
| `calculate_point_in_time_rankings.py` | Calculate rankings from data |
| `lookup_rank_by_id_date.py`           | Lookup specific coin rank    |

---

## Decision Log

**2025-11-19**: Project started

- Investigated 7 cryptocurrency data APIs

**2025-11-20**: Major decisions made

- ✅ Selected CoinGecko as sole data source
- ✅ Collected all 19,410 coin IDs
- ✅ Collected complete current rankings snapshot (~13,000 coins)
- ❌ Rejected crypto2 R package (only 69 coins)
- ❌ Rejected non-CoinGecko APIs (insufficient coverage)
- ✅ Discovered rate limiting requirements (20s no-key, 4s with-key)
- ✅ Discovered maximum ranking depth (~13,000 coins)
- ✅ Documented canonical workflow (coin IDs → data collection → ranking calculation)

**2025-11-20**: Project cleanup

- ✅ Deleted crypto2 data (61 MB)
- ✅ Deleted non-CoinGecko research folders
- ✅ Consolidated failed experiments into `LESSONS_LEARNED.md`
- ✅ Organized documentation structure
- ✅ Created comprehensive project status (this file)

---

## Contact & Resources

**Working Directory**: `~/eon/crypto-marketcap-rank/`
**CoinGecko API Docs**: https://docs.coingecko.com/llms-full.txt
**Demo API Key**: Free, no credit card required

---

**Status**: ✅ Foundation complete, ready for historical collection or daily automation
