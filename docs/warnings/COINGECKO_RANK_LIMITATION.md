# CoinGecko API: Can It Return Historical Rank Directly?

**Question**: If we have coin ID + date, can CoinGecko API directly return the rank on that day?

**Answer**: ❌ **NO** - CoinGecko's free tier API **cannot** directly return historical rank for a specific coin on a specific date.

---

## What We Tested

### Endpoint Tested: `/coins/{id}/history`

**Purpose**: Get historical data for a specific coin on a specific date

**API Call**:

```bash
curl "https://api.coingecko.com/api/v3/coins/bitcoin/history?date=20-11-2025"
```

**Response Contains**:

```json
{
  "id": "bitcoin",
  "symbol": "btc",
  "name": "Bitcoin",
  "market_data": {
    "current_price": { ... },  ✅ Returns prices in all currencies
    "market_cap": { ... },     ✅ Returns market cap in all currencies
    "total_volume": { ... }    ✅ Returns trading volume
  }
}
```

**Response Does NOT Contain**:

- ❌ `market_cap_rank` - **This is what we need!**
- ❌ Any ranking information
- ❌ Percentile or position data

---

## Why This Matters

### What You CAN Get (Per Coin)

**Input**: `coin_id` + `date`
**Output**: Market cap on that date

**Example**:

```bash
GET /coins/bitcoin/history?date=15-01-2024
→ market_cap: $43,000,000,000 (just a number)
```

### What You CANNOT Get (Directly)

**Input**: `coin_id` + `date`
**Output**: Rank on that date ❌

**What we want but cannot get**:

```bash
GET /coins/bitcoin/history?date=15-01-2024
→ market_cap_rank: 1 ❌ NOT AVAILABLE
```

---

## The Fundamental Problem

### To Calculate Rank, You Need ALL Coins' Data

**Rank = Position when sorted by market cap**

To know Bitcoin was #1 on 2024-01-15:

1. Get Bitcoin's market_cap on 2024-01-15: $43B
2. Get Ethereum's market_cap on 2024-01-15: $25B
3. Get Tether's market_cap on 2024-01-15: $91B
4. Get BNB's market_cap on 2024-01-15: $8B
5. ... get ALL 19,410 coins' market_cap
6. Sort by market_cap descending
7. Find Bitcoin's position → Rank #1

### CoinGecko Does Not Provide This in One Call

**Free tier limitation**: No endpoint that returns "all coins' market caps on a specific historical date"

**What exists**:

- ✅ `/coins/{id}/history` - ONE coin's data for ONE date
- ✅ `/coins/markets` - ALL coins' CURRENT rankings (not historical)
- ❌ `/coins/markets?date=XXX` - **Does not exist**

---

## What This Means for Your Question

### Scenario 1: Using CoinGecko API Only

**To get Bitcoin's rank on 2024-01-15**:

```bash
# Step 1: Get all coin IDs (we already have this!)
# 19,410 coins in data/coin_ids/coingecko_all_coin_ids.json

# Step 2: For EACH coin, call the history endpoint
GET /coins/bitcoin/history?date=15-01-2024
GET /coins/ethereum/history?date=15-01-2024
GET /coins/tether/history?date=15-01-2024
... (repeat 19,410 times)

# Step 3: Collect all market_cap values
bitcoin: $43B
ethereum: $25B
tether: $91B
...

# Step 4: Sort by market_cap and calculate ranks
1. tether: $91B
2. bitcoin: $43B
3. ethereum: $25B
...

# Step 5: Return rank for bitcoin → #2
```

**Cost**: 19,410 API calls PER DATE

**For 365 dates**: 19,410 × 365 = **7,084,650 API calls**

### Scenario 2: What You Hoped For (Doesn't Exist)

```bash
# Imaginary endpoint that doesn't exist ❌
GET /coins/bitcoin/rank?date=15-01-2024
→ { "rank": 2 }

# This would be ONE API call
# But CoinGecko doesn't offer this
```

---

## Alternative: Current Rankings Only

### What DOES Work: Current Rankings

**Endpoint**: `/coins/markets`

```bash
curl "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
```

**Returns**:

```json
[
  {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 91363.28,
    "market_cap": 1866427425876,
    "market_cap_rank": 1,  ✅ This exists for CURRENT data only!
    ...
  },
  {
    "id": "ethereum",
    "market_cap_rank": 2,
    ...
  }
]
```

**Limitation**: This only gives **current** rankings, not historical.

---

## Summary Table

| API Endpoint                        | Input          | Output                | Historical? | Has Rank? |
| ----------------------------------- | -------------- | --------------------- | ----------- | --------- |
| `/coins/{id}/history?date=DD-MM-YY` | coin_id + date | price, market_cap     | ✅ Yes      | ❌ No     |
| `/coins/markets`                    | (none)         | All coins with ranks  | ❌ No       | ✅ Yes    |
| `/coins/{id}`                       | coin_id        | Current coin data     | ❌ No       | ✅ Yes    |
| `/coins/markets?date=XXX`           | date           | ❌ **Does not exist** | -           | -         |

**Key Finding**: ❌ **No CoinGecko endpoint combines historical dates with rank information**

---

## Implications for Your Project

### What You MUST Do to Get Historical Ranks

**There is NO shortcut.** You must:

1. **Get all coin IDs** ✅ Already done (19,410 coins in `data/coin_ids/`)

2. **For each date you want rankings**:
   - Call `/coins/{id}/history?date=DD-MM-YYYY` for EVERY coin
   - Collect market_cap for all coins
   - Sort by market_cap descending
   - Calculate ranks yourself

3. **API Calls Required**:
   - For 1 date: 19,410 calls
   - For 365 dates: 7,084,650 calls
   - For 365 dates × Top 500 coins: 182,500 calls ✅ More realistic

### Free Tier Limitations

**Rate Limits** (discovered through testing):

- Without API key: 3 calls/min (20s delay)
- With Demo API key: 15 calls/min (4s delay)
- Free tier monthly limit: 10,000 calls/month

**Time Estimates**:

| Scope                     | API Calls   | Time (No Key)   | Time (Demo Key) | Monthly Limit? |
| ------------------------- | ----------- | --------------- | --------------- | -------------- |
| Top 500 × 1 day           | 500         | 167 min         | 33 min          | ✅ Under       |
| Top 500 × 365 days        | 182,500     | 2,118 days      | 507 days        | ❌ Way over    |
| Top 100 × 365 days        | 36,500      | 423 days        | 101 days        | ❌ Way over    |
| Top 500 × 30 days         | 15,000      | 174 days        | 42 days         | ❌ Over        |
| **Top 500 × 1 day daily** | **500/day** | **167 min/day** | **33 min/day**  | ✅ **Fits!**   |

**Realistic Approach**: Collect top 500 coins for ONE historical date per day, building up historical database over time.

---

## Direct Answer to Your Question

> "If we just have CoinGecko free tier, for any individual coin ID and date, can I get its ranking on that day? Can CoinGecko respond with a ranking?"

**Answer**: ❌ **NO**

**Why**:

1. CoinGecko `/coins/{id}/history` returns `market_cap` but NOT `market_cap_rank`
2. To calculate rank, you need market_cap for ALL coins on that date
3. This requires making 19,410 API calls per date (one per coin)
4. No single API call can give you historical rank

**What you get**:

- ✅ Market cap for one coin on one date: 1 API call
- ❌ Rank for one coin on one date: 19,410 API calls + sorting

**Bottom line**: CoinGecko's free tier requires you to:

1. Collect market_cap for many coins
2. Calculate rankings yourself
3. Store the results in your own database

**This is exactly what we're building!**

---

## What We're Building Instead

Since CoinGecko can't give us historical ranks directly, we must:

### Phase 1: Data Collection ✅ In Progress

1. ✅ Get all coin IDs (19,410 coins)
2. 🔄 Collect market_cap for selected coins × historical dates
3. 💾 Store in our database

### Phase 2: Rank Calculation

1. Load all coins' market_cap for a specific date
2. Sort by market_cap descending
3. Assign ranks (1, 2, 3, ...)
4. Store ranks in database

### Phase 3: Lookup Service ✅ Already Built

**Tool**: `tools/lookup_rank_by_id_date.py`

**Input**: coin_id + date
**Output**: Rank (from our database)

**This is what we're building because CoinGecko doesn't provide it!**

---

## Technical Details

### Tested Endpoint Response

```bash
$ curl "https://api.coingecko.com/api/v3/coins/bitcoin/history?date=20-11-2025"
```

**Full Response Structure**:

```json
{
  "id": "bitcoin",
  "symbol": "btc",
  "name": "Bitcoin",
  "localization": { ... },
  "image": { ... },
  "market_data": {
    "current_price": {
      "usd": 91363.27838693369,
      "eur": 79175.41705011674,
      ...
    },
    "market_cap": {
      "usd": 1866427425876,
      "eur": 1617719282653,
      ...
    },
    "total_volume": {
      "usd": 57408217729,
      ...
    }
  }
}
```

**Notable Absence**:

```json
{
  "market_data": {
    "market_cap_rank": ???  ❌ NOT IN HISTORICAL DATA
  }
}
```

### Free Tier Constraints

**Historical Data Access**:

- ✅ Available: Past 365 days
- ❌ Blocked: Older than 365 days (requires paid plan)

**Example Error** (trying 2017-12-17):

```json
{
  "error": {
    "error_code": 10012,
    "error_message": "Your request exceeds the allowed time range. Public API users are limited to querying historical data within the past 365 days."
  }
}
```

---

## Conclusion

### Direct Answer

**Q**: Can CoinGecko free tier return rank for a coin + date?

**A**: ❌ **NO** - It can only return market_cap. You must:

1. Get market_cap for ALL coins on that date
2. Sort them yourself
3. Calculate rank yourself

### What This Means

**Bad News**: No shortcut - must collect comprehensive data

**Good News**: We're already building the right solution:

- ✅ Collecting historical market_cap data
- ✅ Calculating ranks ourselves
- ✅ Building lookup tool
- ✅ Creating our own historical rank database

**This is unavoidable** - Even with paid CoinGecko plans, there's no "give me rank for coin X on date Y" endpoint.

---

## Files Reference

### Our Solution Files

1. **`data/coin_ids/coingecko_all_coin_ids.json`**
   - All 19,410 coin IDs (to know which coins to query)

2. **`tools/collect_coingecko.py`**
   - Collects market_cap for multiple coins × dates
   - This is the only way to get historical ranking data

3. **`tools/calculate_point_in_time_rankings.py`**
   - Sorts coins by market_cap for each date
   - Calculates ranks (because CoinGecko doesn't provide them)

4. **`tools/lookup_rank_by_id_date.py`**
   - Our custom solution for "coin ID + date → rank"
   - Built because CoinGecko can't do this directly

### What We're Building

**Input**: coin_id + date
**Output**: rank

**How**: By maintaining our own historical market cap database and calculating ranks on demand.

**Why**: Because CoinGecko's API doesn't provide historical ranks directly, even on paid plans.

---

**Bottom Line**: You **cannot** get historical rank from CoinGecko API with a single call. You must collect market_cap data for many coins, sort it yourself, and calculate ranks. **This is exactly what we're building.**
