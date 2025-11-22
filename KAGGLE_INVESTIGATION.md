# Kaggle Dataset Investigation Report

**Investigation Date**: 2025-11-20
**Dataset Location**: `data/raw/kaggle/`
**Status**: ⚠️ USEFUL but STALE - Complement to CoinGecko, not replacement

---

## Executive Summary

**Verdict**: ✅ **USE as historical baseline** + ❌ **NOT for current/future data**

**Key Finding**: Kaggle dataset contains **ACTUAL HISTORICAL RANKINGS** (cmc_rank field) for 8+ years (2013-2021), which CoinGecko API doesn't provide!

**Limitation**: Dataset ends July 31, 2021 (4+ years stale) and only covers 8,928 coins (46% of CoinGecko's 19,410)

**Recommendation**:

1. ✅ Use Kaggle for historical rankings (2013-2021)
2. ✅ Use CoinGecko for current data (2021-present)
3. ✅ Combine both for complete historical database

---

## Dataset Details

### Files Discovered

| File                   | Size   | Records     | Description                        |
| ---------------------- | ------ | ----------- | ---------------------------------- |
| `coinmarketcap.sqlite` | 810 MB | N/A         | SQLite database (not investigated) |
| `coins.csv`            | 9.7 MB | 8,928 coins | Coin metadata                      |
| `historical.csv`       | 866 MB | 4,441,973   | Daily historical data              |

**Total Size**: 1.68 GB (1,685 MB)

---

## Coverage Analysis

### Coin Coverage

**Kaggle**: 8,928 coins
**CoinGecko**: 19,410 coins
**Coverage**: 46% (missing 10,482 coins)

**Implications**:

- ✅ Covers major coins (Bitcoin, Ethereum, etc.)
- ✅ Includes dead 2013-era coins (Namecoin, Terracoin, etc.)
- ❌ Missing 10,482 newer coins (likely post-2021 launches)
- ❌ Missing coins that CoinGecko tracks but CoinMarketCap doesn't

**Overlap**: Unknown (requires coin ID mapping between CMC and CoinGecko)

---

## Date Range

**Start Date**: 2013-04-28
**End Date**: 2021-07-31
**Total Days**: 3,017 days (~8.25 years)

**Freshness**: ❌ 4+ years stale (last update: Aug 9, 2021)

**Gap Analysis**:

- 2013-04-28 to 2021-07-31: ✅ Covered by Kaggle
- 2021-08-01 to 2025-11-20: ❌ Missing (4+ years gap)
- Future: ❌ Not updated (static snapshot)

---

## Data Quality

### Fields Available

**coins.csv** (metadata):

```csv
id, name, slug, symbol, status, category, description, subreddit,
notice, tags, tag_names, website, twitter, message_board, chat,
explorer, reddit, technical_doc, source_code, announcement,
platform_id, date_added, date_launched
```

**historical.csv** (daily data):

```csv
date, coin_id, cmc_rank, market_cap, price, open, high, low, close,
time_high, time_low, volume_24h, percent_change_1h,
percent_change_24h, percent_change_7d, circulating_supply,
total_supply, max_supply, num_market_pairs
```

### Critical Field: cmc_rank ✅

**What it is**: Market cap rank on that specific date

**Example** (Bitcoin on 2021-07-31):

```csv
date,coin_id,cmc_rank,market_cap,price,...
2021-07-31,1,1,781431379811.18,41626.19,...
```

**This is EXACTLY what we need for historical rankings!**

CoinGecko's `/coins/{id}/history` endpoint does NOT provide rank - you must calculate it yourself. Kaggle already has it!

---

## Validation Tests

### Test 1: Bitcoin on Last Date (2021-07-31)

**Kaggle Data**:

- Rank: #1
- Market Cap: $781,431,379,811
- Price: $41,626.20

**Historical Verification** (via web archives):

- Bitcoin was indeed #1 on July 31, 2021
- Price ~$41,000-$42,000 range
- Market cap ~$780B range

**Result**: ✅ Data appears accurate

### Test 2: Total Ranked Coins (2021-07-31)

**Kaggle**: 5,871 coins ranked on last date
**CoinGecko (2025-11-20)**: 13,000 coins ranked currently

**Difference**: CoinGecko has 2.2× more ranked coins now (growth over 4 years)

**Result**: ✅ Consistent with crypto market growth

### Test 3: Historical Depth

**Kaggle Coverage**:

- 2013-04-28: First date (Bitcoin, Litecoin, Namecoin, Terracoin)
- 2021-07-31: Last date (5,871 ranked coins)

**Result**: ✅ Excellent historical depth (8+ years)

---

## Strengths ✅

### 1. Has Historical Rankings

**Critical advantage**: `cmc_rank` field for every coin, every day

Without this, you'd need to:

1. Get market_cap for ALL coins on a date
2. Sort by market_cap
3. Calculate rankings yourself

Kaggle already did this for 3,017 days!

### 2. Comprehensive Time Range

**2013-2021**: 8.25 years of daily data

Covers:

- ✅ Bitcoin-only era (2013)
- ✅ Altcoin emergence (2014-2016)
- ✅ ICO boom (2017)
- ✅ DeFi summer (2020)
- ✅ Bull run (2021)

### 3. Daily Granularity

**One snapshot per day** for each coin

Total records: 4,441,973 rows
Calculation: ~530 coins/day average (growing over time to 5,871 in 2021)

### 4. Includes Dead Coins

**Survivors bias avoided**: Contains coins that existed historically but may be dead now

Examples:

- Namecoin (rank #3 in 2013)
- Terracoin (rank #4 in 2013)
- Many others from 2013-2016 era

### 5. Rich Metadata

**Beyond just rank**: price, volume, supply, market pairs, etc.

Can analyze:

- Rank changes over time
- Market cap trends
- Volume patterns
- Supply inflation

---

## Weaknesses ❌

### 1. Stale Data

**Last Update**: August 9, 2021
**Current Gap**: 4+ years missing

**Impact**:

- ❌ Can't use for current rankings
- ❌ Missing recent bull/bear cycles
- ❌ Missing new coins (2021-2025)
- ❌ Not useful for live tracking

### 2. Limited Coverage

**8,928 coins vs 19,410 on CoinGecko**

**Missing**:

- Newer coins launched after 2021
- Coins tracked by CoinGecko but not CoinMarketCap
- Smaller/newer projects

**Only 46% coverage** of current crypto universe

### 3. Different Source

**CoinMarketCap vs CoinGecko**

**Implications**:

- Different coin IDs (requires mapping)
- Different ranking methodologies (possibly)
- Different coverage sets
- May have slight data discrepancies

### 4. Static Dataset

**No Updates**

This is a one-time snapshot, not a live data source. To continue building historical database, must use CoinGecko API.

### 5. Coin ID Mapping Required

**CMC IDs ≠ CoinGecko IDs**

**Example**:

- CMC: Bitcoin = ID 1
- CoinGecko: Bitcoin = "bitcoin"

Need to create mapping table to combine datasets.

---

## Comparison: Kaggle vs CoinGecko

| Feature                 | Kaggle                    | CoinGecko              | Winner    |
| ----------------------- | ------------------------- | ---------------------- | --------- |
| **Historical Rankings** | ✅ Yes (cmc_rank)         | ❌ No (must calculate) | Kaggle    |
| **Date Range**          | 2013-2021                 | Current + 365d back    | Depends   |
| **Coverage**            | 8,928 coins               | 19,410 coins           | CoinGecko |
| **Freshness**           | July 2021 (stale)         | Real-time              | CoinGecko |
| **Updates**             | ❌ Static                 | ✅ Live API            | CoinGecko |
| **Coin IDs**            | Numeric (CMC)             | String (CoinGecko)     | Tie       |
| **Data Source**         | CoinMarketCap             | CoinGecko              | Tie       |
| **API Calls**           | 0 (local file)            | Counts against limit   | Kaggle    |
| **Total Cost**          | Free (already downloaded) | Free (with limits)     | Tie       |

---

## Use Cases

### ✅ What Kaggle IS Good For

**1. Historical Rankings (2013-2021)**

```python
# Get Bitcoin rank on any date between 2013-2021
df = pd.read_csv('data/raw/kaggle/historical.csv')
btc_2017_12_17 = df[(df['coin_id'] == 1) & (df['date'] == '2017-12-17')]
print(f"Bitcoin rank: #{btc_2017_12_17['cmc_rank'].values[0]}")
```

**2. Historical Analysis**

- Rank changes over time
- Market dominance trends
- Bull/bear cycle analysis
- Dead coin identification

**3. Baseline Historical Database**
Instead of collecting 8 years of data via API:

- ✅ Use Kaggle for 2013-2021
- ✅ Use CoinGecko for 2021-2025
- ✅ Combine for complete database

**4. Avoiding API Costs**
Kaggle provides 4.4M+ records without a single API call!

### ❌ What Kaggle Is NOT Good For

**1. Current Rankings**
Data ends July 2021 - completely stale for current use

**2. Recent Coins**
Missing 4+ years of new coin launches

**3. Live Tracking**
Static snapshot, no updates

**4. Future Data**
Dataset won't update - must use CoinGecko API

---

## Coin ID Mapping Challenge

### Problem

Kaggle uses **CoinMarketCap IDs** (numeric):

```
1 = Bitcoin
2 = Litecoin
3 = Namecoin
```

CoinGecko uses **string IDs**:

```
"bitcoin" = Bitcoin
"litecoin" = Litecoin
"namecoin" = Namecoin
```

### Solution Required

Create mapping table:

```csv
cmc_id,cmc_symbol,coingecko_id,coingecko_symbol
1,BTC,bitcoin,btc
2,LTC,litecoin,ltc
3,NMC,namecoin,nmc
```

**Matching Strategy**:

1. Match by symbol (BTC → bitcoin)
2. Verify by name (Bitcoin → Bitcoin)
3. Manual verification for conflicts

**Tool Needed**: `map_cmc_to_coingecko.py` (not yet created)

---

## Recommendations

### Strategy 1: Hybrid Approach ✅ RECOMMENDED

**Use both Kaggle and CoinGecko for comprehensive coverage**

**Historical (2013-2021)**:

- Source: Kaggle dataset
- Advantage: Already has rankings
- Coverage: 8,928 coins
- API calls: 0

**Current (2021-2025)**:

- Source: CoinGecko API (daily collection)
- Advantage: Live data
- Coverage: 19,410 coins
- API calls: 4/day (sustainable)

**Combined Result**:

- ✅ Complete historical database
- ✅ Maximum coverage
- ✅ Minimal API usage

### Strategy 2: Kaggle-Only (for historical analysis)

**If you only care about 2013-2021**:

- ✅ Use Kaggle exclusively
- ✅ No API calls needed
- ✅ Already has rankings
- ❌ Misses recent 4+ years

### Strategy 3: CoinGecko-Only (for current forward)

**If you only care about 2025 onward**:

- ✅ Use CoinGecko daily collection
- ✅ Build database over time
- ❌ No historical data before today
- ❌ Will take years to match Kaggle's depth

---

## Implementation Plan

### Phase 1: Validate Kaggle Data ✅ (This Investigation)

**Completed**:

- ✅ Checked file structure
- ✅ Validated date range (2013-2021)
- ✅ Confirmed rankings exist (cmc_rank)
- ✅ Verified coverage (8,928 coins)
- ✅ Spot-checked accuracy (Bitcoin on 2021-07-31)

**Verdict**: ✅ Data quality good, suitable for use

### Phase 2: Create Coin ID Mapping (Next)

**Tasks**:

1. Extract unique coins from Kaggle (`coins.csv`)
2. Extract unique coins from CoinGecko (`coin_ids/all_coins.csv`)
3. Match by symbol + name
4. Create mapping table
5. Validate mappings

**Tool**: `tools/map_cmc_to_coingecko.py` (to be created)

**Output**: `data/mappings/cmc_to_coingecko.csv`

### Phase 3: Merge Historical Data (Future)

**Tasks**:

1. Load Kaggle historical data (2013-2021)
2. Load CoinGecko current rankings (2025-11-20)
3. Apply coin ID mapping
4. Combine into unified database
5. Fill gap (2021-2025) with CoinGecko API if needed

**Output**: `data/unified/complete_rankings.csv`

### Phase 4: Daily Collection (Ongoing)

**Tasks**:

1. Set up cron job for daily CoinGecko collection
2. Append new data to unified database
3. Maintain forward from 2025-11-20

**Output**: Growing historical database

---

## Analysis Examples

### Example 1: Find Bitcoin's Rank on Any Historical Date

```python
import pandas as pd

# Load Kaggle historical data
df = pd.read_csv('data/raw/kaggle/historical.csv')

# Get Bitcoin rank on 2017-12-17 (ATH day)
btc_ath = df[(df['coin_id'] == 1) & (df['date'] == '2017-12-17')]
print(f"Rank: #{btc_ath['cmc_rank'].values[0]}")  # Always #1
print(f"Price: ${btc_ath['price'].values[0]:,.2f}")
print(f"Market Cap: ${btc_ath['market_cap'].values[0]:,.2f}")
```

### Example 2: Track Coin Rank Changes Over Time

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data/raw/kaggle/historical.csv')

# Track Litecoin (coin_id=2) rank over time
ltc = df[df['coin_id'] == 2].sort_values('date')

plt.figure(figsize=(12, 6))
plt.plot(pd.to_datetime(ltc['date']), ltc['cmc_rank'])
plt.gca().invert_yaxis()  # Lower rank = better
plt.xlabel('Date')
plt.ylabel('Rank')
plt.title('Litecoin Market Cap Rank Over Time (2013-2021)')
plt.show()
```

### Example 3: Identify Dead Coins

```python
# Coins that had high rank in 2013 but disappeared by 2021
early = df[df['date'] == '2013-04-28']
late = df[df['date'] == '2021-07-31']

early_top_50 = set(early[early['cmc_rank'] <= 50]['coin_id'])
late_all = set(late['coin_id'])

dead_coins = early_top_50 - late_all
print(f"Dead coins from 2013 top 50: {len(dead_coins)}")
```

---

## Storage & Performance

### Current Storage

```
data/raw/kaggle/
├── coinmarketcap.sqlite   810 MB (not analyzed)
├── coins.csv              9.7 MB (8,928 coins)
└── historical.csv         866 MB (4.4M records)

Total: 1,685 MB (~1.68 GB)
```

### Load Performance

**CSV Loading** (historical.csv):

```python
import pandas as pd
import time

start = time.time()
df = pd.read_csv('data/raw/kaggle/historical.csv')
elapsed = time.time() - start

print(f"Loaded {len(df):,} rows in {elapsed:.1f} seconds")
# Expected: ~10-30 seconds depending on hardware
```

**Optimization Options**:

1. Use SQLite database instead of CSV
2. Create date-indexed files (one per year)
3. Use Parquet format (faster than CSV)
4. Load specific date ranges only

---

## Decision Matrix

### Should I Use Kaggle Dataset?

| Your Goal                       | Use Kaggle? | Reason                   |
| ------------------------------- | ----------- | ------------------------ |
| Current rankings (2025)         | ❌ No       | Data ends 2021           |
| Historical rankings (2013-2021) | ✅ YES      | Already has rankings     |
| Building forward from today     | ❌ No       | Use CoinGecko            |
| Complete historical database    | ✅ YES      | Combine with CoinGecko   |
| Analyzing dead coins            | ✅ YES      | Includes historical data |
| Real-time tracking              | ❌ No       | Static snapshot          |
| Avoiding API costs              | ✅ YES      | No API calls needed      |
| Maximum coin coverage           | ❌ No       | Only 46% of CoinGecko    |

---

## Final Verdict

### ✅ USE Kaggle Dataset For:

1. **Historical rankings baseline** (2013-2021)
2. **Avoiding massive API costs** for historical data
3. **Dead coin analysis** (survivorship bias elimination)
4. **Historical trend analysis**
5. **Complement to CoinGecko** (not replacement)

### ❌ DON'T Use Kaggle For:

1. Current rankings (4+ years stale)
2. Future data collection (static)
3. New coins (missing 10,482)
4. Real-time tracking
5. Sole data source (combine with CoinGecko)

### 🎯 Recommended Strategy:

**HYBRID APPROACH**:

1. ✅ Use Kaggle for 2013-2021 historical data
2. ✅ Use CoinGecko for 2021-2025 + future
3. ✅ Create coin ID mapping to unify
4. ✅ Build complete historical database

**Benefits**:

- ✅ 8+ years of historical rankings (FREE!)
- ✅ Current + future data (CoinGecko)
- ✅ Maximum coverage (both sources)
- ✅ Minimal API usage

---

**Status**: ✅ Investigation complete - RECOMMEND using Kaggle + CoinGecko hybrid approach
