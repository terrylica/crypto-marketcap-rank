# Data Directory - Cryptocurrency Market Cap Rankings

**Purpose**: Centralized storage for all cryptocurrency data collected from CoinGecko API

**Last Updated**: 2025-11-20

---

## Quick Overview

### What's Here

| Folder        | Content                                   | Size    | Status              |
| ------------- | ----------------------------------------- | ------- | ------------------- |
| `coin_ids/`   | All 19,410 CoinGecko coin IDs             | 2.1 MB  | ✅ Complete         |
| `rankings/`   | Current rankings snapshot (~13,000 coins) | 13.8 MB | ✅ Complete         |
| `raw/kaggle/` | Kaggle historical dataset                 | ~1 GB   | ⏳ Needs validation |

### Total Data Size

- **Current**: ~1.02 GB
- **Coin IDs**: 2.1 MB (19,410 coins)
- **Rankings**: 13.8 MB (13,000 ranked coins, full snapshot)
- **Kaggle**: ~1 GB (historical data, quality TBD)

---

## Data Folders

### 1. `coin_ids/` - Complete Coin ID List ✅

**What it contains**: All 19,410 active CoinGecko coin IDs

**Key files**:

- `coingecko_all_coin_ids.json` (1.5 MB) - Complete JSON with id, symbol, name
- `all_coins.csv` (574 KB) - Easy-to-view CSV format
- `SUMMARY.json` (1.2 KB) - Collection metadata
- `README.md` (3.2 KB) - Detailed documentation

**Collection date**: 2025-11-20

**Source**: CoinGecko `/coins/list` endpoint (FREE, unlimited)

**Includes**: Dead 2013-era coins (Namecoin, Peercoin, etc.) for historical accuracy

**Usage**:

```bash
# View all coin IDs
cat data/coin_ids/all_coins.csv | less

# Search for specific coin
grep -i "ethereum" data/coin_ids/all_coins.csv

# Count total coins
wc -l data/coin_ids/all_coins.csv
```

**Details**: See [`coin_ids/README.md`](coin_ids/README.md)

---

### 2. `rankings/` - Current Market Cap Rankings ✅

**What it contains**: Complete current rankings snapshot

**Date**: 2025-11-20 23:11:08

**Coverage**: 13,000 ranked coins (rank #1 to #12,991)

**Key files**:

- `current_rankings_20251120_231108.csv` (748 KB) - Rankings CSV
- `current_rankings_20251120_231108.json` (13 MB) - Full API data
- `summary_20251120_231108.json` (1.4 KB) - Metadata + top 10
- `fetch_current_rankings.py` - Collection script (for reproducibility)
- `README.md` (16 KB, 584 lines) - Comprehensive guide

**Source**: CoinGecko `/coins/markets` endpoint

**Fields**:

- `rank` - Market cap rank (1 to 12,991)
- `id` - CoinGecko coin ID
- `symbol` - Coin ticker (BTC, ETH, etc.)
- `name` - Full coin name
- `market_cap` - Market capitalization in USD
- `price` - Current price in USD
- `volume_24h` - 24-hour trading volume in USD

**Top 10** (as of 2025-11-20):

```
1. Bitcoin (BTC)         - $1,706,984,400,280
2. Ethereum (ETH)        - $337,143,314,959
3. Tether (USDT)         - $184,561,429,699
4. XRP (XRP)             - $118,267,904,315
5. BNB (BNB)             - $117,487,000,279
6. USDC (USDC)           - $73,794,548,331
7. Solana (SOL)          - $73,232,193,414
8. TRON (TRX)            - $26,587,338,044
9. Lido Staked Ether     - $24,118,479,828
10. Dogecoin (DOGE)      - $22,153,880,643
```

**Usage**:

```bash
# View top 20 coins
head -21 data/rankings/current_rankings_20251120_231108.csv

# Search for specific coin
grep -i "cardano" data/rankings/current_rankings_20251120_231108.csv

# Get coin rank
grep "^123," data/rankings/current_rankings_20251120_231108.csv
```

**How to reproduce**:

```bash
# Get top 500 current rankings
uv run tools/fetch_current_rankings.py 500

# Get ALL ~13,000 ranked coins
uv run tools/fetch_current_rankings.py all
```

**Details**: See [`rankings/README.md`](rankings/README.md)

---

### 3. `raw/kaggle/` - Historical Dataset (Needs Validation) ⏳

**What it contains**: Historical cryptocurrency data from Kaggle

**Status**: ⏳ Not yet validated

**Size**: ~1 GB

**Source**: Kaggle datasets (source TBD - needs investigation)

**Next steps**:

1. Verify data quality (accuracy, completeness)
2. Check coverage (how many coins, date range)
3. Validate against CoinGecko current data
4. Determine if useful for historical rankings

**Investigation task**: See todo list (Kaggle dataset validation)

---

## Data Collection Status

### Completed ✅

**1. Coin IDs** (2025-11-20)

- Source: CoinGecko `/coins/list`
- Count: 19,410 active coins
- Format: JSON + CSV
- API calls: 1 (FREE, doesn't count against limit)
- Time: < 5 seconds

**2. Current Rankings** (2025-11-20 23:11:08)

- Source: CoinGecko `/coins/markets`
- Count: 13,000 ranked coins
- Format: CSV + JSON
- API calls: 52 (all pages)
- Time: ~17 minutes (20s delay, no API key)

### Pending ⏳

**1. Kaggle Dataset Validation**

- Verify quality, coverage, freshness
- Compare with CoinGecko data
- Determine usefulness for project

**2. Historical Backfill**

- Collect market_cap for all coins on past dates
- Calculate point-in-time rankings
- Very slow (days/weeks depending on scope)

**3. Daily Collection**

- Set up automated daily rankings collection
- Gradually build historical database
- Sustainable within free tier

---

## Data Freshness

| Dataset          | Date             | Age     | Update Frequency         |
| ---------------- | ---------------- | ------- | ------------------------ |
| Coin IDs         | 2025-11-20       | Current | On demand                |
| Current Rankings | 2025-11-20 23:11 | Current | Manual (should be daily) |
| Kaggle           | Unknown          | Unknown | Static snapshot          |

**Recommendation**: Set up daily collection automation

---

## Storage & Management

### Current Storage

```
data/
├── coin_ids/                    2.1 MB
│   ├── coingecko_all_coin_ids.json  1.5 MB
│   ├── all_coins.csv                574 KB
│   ├── SUMMARY.json                 1.2 KB
│   └── README.md                    3.2 KB
│
├── rankings/                    13.8 MB
│   ├── current_rankings_*.csv       748 KB
│   ├── current_rankings_*.json      13 MB
│   ├── summary_*.json               1.4 KB
│   ├── fetch_current_rankings.py    6.5 KB
│   └── README.md                    16 KB
│
└── raw/
    └── kaggle/                  ~1 GB
        └── (various files)

Total: ~1.02 GB
```

### Future Growth Estimates

**Daily Collection** (top 1,000 coins):

- CSV size: ~180 KB/day
- JSON size: ~2.5 MB/day
- Monthly: ~73 MB
- Yearly: ~876 MB

**Historical Backfill** (500 coins × 365 days):

- Raw JSON: ~1.8 GB
- Processed CSV: ~66 MB
- Calculated rankings: ~180 MB
- Total: ~2 GB

---

## Data Quality

### Verified ✅

**Coin IDs**:

- ✅ Contains 19,410 active coins
- ✅ Includes dead 2013-era coins (Namecoin, Peercoin, Primecoin, etc.)
- ✅ Matches CoinGecko official count
- ✅ Format validated (id, symbol, name)

**Current Rankings**:

- ✅ Contains 13,000 ranked coins
- ✅ Ranks sequential: #1 to #12,991
- ✅ Market caps monotonically decreasing
- ✅ Top 10 matches CoinGecko website (Nov 20, 2025)
- ✅ All required fields present

### Pending Validation ⏳

**Kaggle Dataset**:

- ⏳ Quality unknown
- ⏳ Coverage unknown
- ⏳ Freshness unknown
- ⏳ Comparison with CoinGecko needed

---

## Usage Examples

### Get All Coin IDs

```bash
# CSV format
cat data/coin_ids/all_coins.csv

# JSON format
jq '.' data/coin_ids/coingecko_all_coin_ids.json | less

# Search for Ethereum-related coins
grep -i "ethereum" data/coin_ids/all_coins.csv
```

### Get Current Rankings

```bash
# View top 20
head -21 data/rankings/current_rankings_20251120_231108.csv

# Find specific coin rank
grep -i "cardano" data/rankings/current_rankings_20251120_231108.csv

# Count ranked coins
tail -n +2 data/rankings/current_rankings_20251120_231108.csv | wc -l
```

### Python Analysis

```python
import pandas as pd

# Load rankings
df = pd.read_csv('data/rankings/current_rankings_20251120_231108.csv')

# Top 10 by market cap
top10 = df.head(10)
print(top10[['rank', 'symbol', 'name', 'market_cap']])

# Find specific coin
cardano = df[df['symbol'] == 'ada']
print(f"Cardano rank: #{cardano['rank'].values[0]}")

# Market cap distribution
import matplotlib.pyplot as plt
df['market_cap'].hist(bins=50)
plt.yscale('log')
plt.xlabel('Market Cap (USD)')
plt.ylabel('Count')
plt.title('Market Cap Distribution')
plt.show()
```

---

## Data Sources

### CoinGecko API

**Base URL**: `https://api.coingecko.com/api/v3`

**Endpoints Used**:

1. `/coins/list` - All coin IDs (FREE, unlimited)
2. `/coins/markets` - Current rankings with pagination

**Authentication**:

- Optional: Demo API key (free, no credit card)
- Without key: 20s delay required between calls
- With key: 4s delay required between calls

**Rate Limits**:

- Free tier: 10,000 calls/month
- Current usage: 53 calls total (0.53% of monthly limit)

**Documentation**: https://docs.coingecko.com/llms-full.txt

### Kaggle (Pending Validation)

**Status**: Dataset present but not yet validated

**Next Steps**: Investigation task pending

---

## Data Governance

### What We Keep

- ✅ All coin IDs (foundation for rankings)
- ✅ Current rankings snapshots (timestamped)
- ✅ Collection scripts (reproducibility)
- ✅ Metadata (SUMMARY.json, README.md)

### What We Don't Keep

- ❌ Duplicate snapshots (unless different dates)
- ❌ Intermediate processing files
- ❌ Unvalidated external data (must validate first)

### Backup Strategy

**Current**: None (local only)

**Recommended**:

- Daily: git commit + push to remote
- Weekly: cloud backup (Google Drive, AWS S3, etc.)
- Monthly: archive old snapshots

---

## Related Documentation

**Project Level**:

- [`../README.md`](../README.md) - Project overview
- [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md) - Current status, next steps
- [`../LESSONS_LEARNED.md`](../LESSONS_LEARNED.md) - Failed experiments, discoveries

**Data Specific**:

- [`coin_ids/README.md`](coin_ids/README.md) - Coin ID collection details
- [`rankings/README.md`](rankings/README.md) - Rankings collection details

**Canonical Workflows**:

- [`../docs/canonical/COIN_IDS_COMPLETE.md`](../docs/canonical/COIN_IDS_COMPLETE.md)
- [`../docs/canonical/CURRENT_RANKINGS_SOLUTION.md`](../docs/canonical/CURRENT_RANKINGS_SOLUTION.md)
- [`../docs/canonical/MAXIMUM_RANKING_DEPTH.md`](../docs/canonical/MAXIMUM_RANKING_DEPTH.md)

---

## FAQs

**Q: How often is data updated?**
A: Currently manual. Recommended: daily collection automation (pending).

**Q: How far back does historical data go?**
A: Current snapshot only (2025-11-20). Historical backfill pending.

**Q: Can I get rankings for a specific past date?**
A: Not yet. Need to collect market_cap for all coins on that date first, then calculate rankings.

**Q: What's the difference between coin_ids and rankings?**
A: `coin_ids` = ALL 19,410 coins. `rankings` = Top 13,000 ranked coins with market_cap data.

**Q: Why only 13,000 ranked instead of 19,410?**
A: CoinGecko only ranks coins with sufficient market_cap. Remaining 6,410 coins too low/dead/insufficient data.

**Q: Should I use Kaggle data?**
A: Unknown - needs validation first (pending task).

---

**Status**: ✅ Core data complete (coin IDs + current rankings), validation & historical collection pending
