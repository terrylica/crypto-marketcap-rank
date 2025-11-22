# Maximum Ranking Depth - CoinGecko `/coins/markets`

**Your Question**: "How deep can it go? What's the maximum depth that it can rank up to?"

**Answer**: ✅ **CoinGecko ranks approximately 13,000 coins!**

**Maximum Rank**: #12,991 (tested and confirmed)

---

## Discovery Results

### Testing Summary

| Page | Rank Range         | Status          |
| ---- | ------------------ | --------------- |
| 1    | #1 to #250         | ✅ All ranked   |
| 10   | #2,251 to #2,500   | ✅ All ranked   |
| 40   | #9,754 to #10,001  | ✅ All ranked   |
| 50   | #12,251 to #12,500 | ✅ All ranked   |
| 52   | #12,752 to #12,991 | ✅ 241 ranked   |
| 54   | No ranks           | ❌ All unranked |
| 60   | No ranks           | ❌ All unranked |
| 77   | No ranks           | ❌ All unranked |

**Last Ranked Coin**: #12,991 - ladyluck (LUCKY)

---

## What This Means

### Total Breakdown

**CoinGecko Total Coins**: 19,410 coins

**Ranked Coins**: ~13,000 coins (67% of total)

- Have `market_cap_rank` field
- Sorted by market cap
- Accessible via `/coins/markets` endpoint

**Unranked Coins**: ~6,410 coins (33% of total)

- No `market_cap_rank` field
- Too low market cap / insufficient data
- Still in coin list, but not ranked

---

## How Much Can You Get?

### Quick Reference Table

| Scope             | API Calls | Time (API Key) | Time (No Key) | Coverage             |
| ----------------- | --------- | -------------- | ------------- | -------------------- |
| **Top 100**       | 1         | instant        | instant       | 0.5% of all coins    |
| **Top 500**       | 2         | 4 sec          | 20 sec        | 2.6% of all coins    |
| **Top 1,000**     | 4         | 12 sec         | 60 sec        | 5.2% of all coins    |
| **Top 2,500**     | 10        | 36 sec         | 3 min         | 13% of all coins     |
| **Top 5,000**     | 20        | 72 sec         | 6 min         | 26% of all coins     |
| **Top 10,000**    | 40        | 2.4 min        | 12 min        | 52% of all coins     |
| **ALL (~13,000)** | 52        | 3 min          | 16 min        | **67% of all coins** |

### Formula

- **Coins per page**: 250 (maximum allowed by CoinGecko)
- **Pages needed**: `ceil(top_n / 250)`
- **API calls**: Same as pages needed
- **Time with API key**: `pages × 4 seconds`
- **Time without key**: `pages × 20 seconds`

---

## Tool Usage

### Updated `fetch_current_rankings.py`

**Fetch specific number**:

```bash
uv run tools/fetch_current_rankings.py 500      # Top 500
uv run tools/fetch_current_rankings.py 1000     # Top 1,000
uv run tools/fetch_current_rankings.py 5000     # Top 5,000
```

**Fetch ALL ranked coins** (NEW!):

```bash
uv run tools/fetch_current_rankings.py all      # ~13,000 coins
```

**Time estimates**:

- Top 500: 4-20 seconds
- Top 1,000: 12-60 seconds
- ALL (~13,000): 3-16 minutes

---

## Recommended Strategies

### Strategy 1: Quick Snapshot (Top 500)

**Use Case**: Daily collection, track major coins

```bash
# Run daily
uv run tools/fetch_current_rankings.py 500
```

**Benefits**:

- ✅ Very fast (4-20 seconds)
- ✅ Covers all major coins
- ✅ 2 API calls/day × 30 days = 60 calls/month (well within limit)
- ✅ Perfect for building historical database over time

### Strategy 2: Comprehensive Snapshot (Top 1,000-5,000)

**Use Case**: Broader coverage, still efficient

```bash
# Run daily or weekly
uv run tools/fetch_current_rankings.py 1000    # 4 API calls
uv run tools/fetch_current_rankings.py 5000    # 20 API calls
```

**Benefits**:

- ✅ Covers most actively traded coins
- ✅ Still fast (12 seconds to 6 minutes)
- ✅ More comprehensive than top 500
- ✅ 4-20 calls per run

### Strategy 3: Maximum Coverage (ALL ~13,000)

**Use Case**: One-time comprehensive snapshot

```bash
# Run once to get complete current state
uv run tools/fetch_current_rankings.py all
```

**Benefits**:

- ✅ Maximum coverage (67% of all coins)
- ✅ Every single ranked coin on CoinGecko
- ✅ Complete current market state
- ✅ Only 52 API calls

**Then**:

```bash
# Daily: Track changes with top 500-1000
uv run tools/fetch_current_rankings.py 1000
```

---

## Coverage Analysis

### What Percentage of Coins Do You Get?

**Out of 19,410 total CoinGecko coins**:

| Scope          | Coins       | % of Total | % of Ranked |
| -------------- | ----------- | ---------- | ----------- |
| Top 100        | 100         | 0.5%       | 0.8%        |
| Top 500        | 500         | 2.6%       | 3.8%        |
| Top 1,000      | 1,000       | 5.2%       | 7.7%        |
| Top 2,500      | 2,500       | 13%        | 19%         |
| Top 5,000      | 5,000       | 26%        | 38%         |
| Top 10,000     | 10,000      | 52%        | 77%         |
| **All Ranked** | **~13,000** | **67%**    | **100%**    |

**Key Insight**: Top 5,000 covers 26% of all coins but represents 38% of all RANKED coins. This is a good balance between coverage and API efficiency.

---

## Why Some Coins Are Unranked

### Reasons for Missing `market_cap_rank`

**Out of 19,410 total coins, ~6,410 are unranked because**:

1. **Too low market cap**
   - Market cap below CoinGecko's threshold
   - Insufficient liquidity

2. **Insufficient data**
   - New coins without enough history
   - Missing price/volume data
   - Not enough exchanges listing

3. **Dead/inactive coins**
   - No longer actively traded
   - Delisted from exchanges
   - Project abandoned

4. **Data quality issues**
   - Unreliable price data
   - Manipulation concerns
   - Circulating supply unknown

**These coins still appear in `/coins/list` (our 19,410 coin IDs) but not in ranked `/coins/markets` results.**

---

## Comparison: Different Data Sources

### Current Rankings (CoinGecko `/coins/markets`)

**What you get**:

- ✅ Current rankings with market_cap_rank
- ✅ Up to ~13,000 ranked coins
- ✅ Real-time snapshot
- ✅ Fast (2-52 API calls)

**What you don't get**:

- ❌ Historical rankings
- ❌ Unranked coins (~6,410 coins)

### Historical Data (CoinGecko `/coins/{id}/history`)

**What you get**:

- ✅ Market cap for specific dates
- ✅ Any coin (all 19,410 coins)
- ✅ Past 365 days

**What you don't get**:

- ❌ No market_cap_rank field
- ❌ Requires many API calls (1 per coin per date)

### Existing Data (crypto2 R package)

**What you get**:

- ✅ 69 historically important coins
- ✅ 2013-2024 date range
- ✅ Verified data with circulating_supply

**What you don't get**:

- ❌ Only 69 coins (missing Ethereum, BNB, Cardano, Solana, etc.)
- ❌ No recent additions

---

## Free Tier Sustainability

### Monthly Limit: 10,000 API Calls

**Daily Collection Options**:

| Scope           | Calls/Day | Days/Month | Total Calls/Month | Status           |
| --------------- | --------- | ---------- | ----------------- | ---------------- |
| Top 500 daily   | 2         | 30         | 60                | ✅ 0.6% of limit |
| Top 1,000 daily | 4         | 30         | 120               | ✅ 1.2% of limit |
| Top 5,000 daily | 20        | 30         | 600               | ✅ 6% of limit   |
| ALL daily       | 52        | 30         | 1,560             | ✅ 16% of limit  |

**One-Time Collection + Daily Tracking**:

```bash
# Month 1, Day 1: Get ALL ranked coins (one-time)
uv run tools/fetch_current_rankings.py all
# 52 API calls

# Month 1, Days 2-30: Track changes with top 1,000 daily
uv run tools/fetch_current_rankings.py 1000
# 4 calls/day × 29 days = 116 calls

# Total Month 1: 52 + 116 = 168 calls (1.7% of monthly limit) ✅
```

**Perfectly sustainable!**

---

## Real-World Use Cases

### Use Case 1: Daily Market Snapshot

**Goal**: Track top 500 coins daily to build historical database

**Command**:

```bash
# Run this daily (automate with cron)
uv run tools/fetch_current_rankings.py 500
```

**Result**:

- Daily CSV files in `data/rankings/`
- After 365 days: Complete year of top 500 rankings
- Only 730 API calls total (7.3% of monthly limit)

### Use Case 2: One-Time Comprehensive Snapshot

**Goal**: Get complete current state of crypto market

**Command**:

```bash
# Run once
uv run tools/fetch_current_rankings.py all
```

**Result**:

- ~13,000 ranked coins in single CSV
- Complete current market state
- 52 API calls (0.5% of monthly limit)

### Use Case 3: Weekly Deep Dive

**Goal**: Track top 5,000 coins weekly

**Command**:

```bash
# Run weekly (Sundays)
uv run tools/fetch_current_rankings.py 5000
```

**Result**:

- Weekly snapshots of top 5,000 coins
- 20 calls/week × 4 weeks = 80 calls/month
- 0.8% of monthly limit

---

## Technical Details

### Pagination Mechanics

**Endpoint**: `https://api.coingecko.com/api/v3/coins/markets`

**Parameters**:

- `vs_currency=usd` - Price/market cap in USD
- `order=market_cap_desc` - Sort by market cap (highest first)
- `per_page=250` - Coins per page (max 250)
- `page=N` - Page number

**Examples**:

```bash
# Page 1: Ranks #1 to #250
page=1

# Page 2: Ranks #251 to #500
page=2

# Page 52: Ranks #12,751 to #13,000
page=52
```

### Response Structure

**Each coin includes**:

```json
{
  "id": "bitcoin",
  "symbol": "btc",
  "name": "Bitcoin",
  "market_cap_rank": 1,
  "current_price": 86043,
  "market_cap": 1715444849724,
  "total_volume": 101410616764,
  "circulating_supply": 19950600.0,
  ...
}
```

**Unranked coins** (beyond #12,991):

```json
{
  "id": "some-coin",
  "symbol": "XYZ",
  "name": "Some Coin",
  "market_cap_rank": null,  // ← No rank!
  ...
}
```

---

## Summary

### Direct Answer

**Q**: "How deep can CoinGecko rankings go?"

**A**: **~13,000 coins maximum** (rank #1 to #12,991)

### Key Numbers

- **Total CoinGecko Coins**: 19,410
- **Ranked Coins**: ~13,000 (67%)
- **Unranked Coins**: ~6,410 (33%)
- **API Calls for ALL ranked**: 52 calls
- **Time for ALL ranked**: 3-16 minutes

### What You Can Do

✅ **Get top 500**: 2 API calls, 4-20 seconds
✅ **Get top 1,000**: 4 API calls, 12-60 seconds
✅ **Get top 5,000**: 20 API calls, 72 seconds - 6 minutes
✅ **Get ALL ~13,000 ranked**: 52 API calls, 3-16 minutes

### Recommendation

**For daily collection**: Top 1,000 coins

- 4 API calls/day
- 120 calls/month
- 1.2% of monthly limit
- Excellent coverage

**For one-time snapshot**: ALL ~13,000 ranked coins

- 52 API calls
- 3-16 minutes
- Complete current market state
- Then switch to daily top 500-1000

---

## Tools Available

### `fetch_current_rankings.py`

**Location**: `tools/fetch_current_rankings.py`

**Usage**:

```bash
# Specific number
uv run tools/fetch_current_rankings.py 500
uv run tools/fetch_current_rankings.py 1000
uv run tools/fetch_current_rankings.py 5000

# ALL ranked coins
uv run tools/fetch_current_rankings.py all
```

**Output**:

- `data/rankings/current_rankings_YYYYMMDD_HHMMSS.csv`
- `data/rankings/current_rankings_YYYYMMDD_HHMMSS.json`
- `data/rankings/summary_YYYYMMDD_HHMMSS.json`

---

**Status**: ✅ **Maximum ranking depth discovered: ~13,000 coins!**
**Coverage**: 67% of all CoinGecko coins
**Accessibility**: Free tier, no registration required (but slower without API key)
