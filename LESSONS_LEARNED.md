# Lessons Learned - Failed Experiments & Warnings

**Purpose**: Document failed approaches and hard-won discoveries to prevent regression.

**Last Updated**: 2025-11-20

---

## Critical Discoveries

### 1. crypto2 R Package: INSUFFICIENT COVERAGE ❌

**What we tried**: Using crypto2 R package for historical market cap data

**Why it failed**: Only 69 coins total

- Missing major coins: Ethereum, BNB, Cardano, Solana, and thousands of others
- Covers 2013-2024 but only 69 historically important coins
- Insufficient for comprehensive market cap rankings

**Impact**: Cannot build complete historical rankings with only 69 coins

**Decision**: ✅ DELETED - No longer using crypto2 data

**What we learned**: Need ALL coins (19,410 on CoinGecko) for accurate point-in-time rankings

---

### 2. CoinGecko Historical Rank API: DOESN'T EXIST ❌

**What we tried**: Looking for `/coins/{id}/history` endpoint to return `market_cap_rank` field

**API Response**:

```json
{
  "id": "bitcoin",
  "symbol": "btc",
  "name": "Bitcoin",
  "market_data": {
    "current_price": { "usd": 40000 },
    "market_cap": { "usd": 800000000000 }
    // ❌ NO market_cap_rank field!
  }
}
```

**Why it doesn't work**:

- CoinGecko `/coins/{id}/history?date=DD-MM-YYYY` returns market_cap but NOT rank
- To calculate rank for a date, you need ALL coins' market caps for that date
- No single API call can give you "rank on specific historical date"

**Workaround**: Must collect market_cap for ALL coins on a date, then calculate rankings yourself

**What we learned**: Point-in-time rankings require:

1. Get coin IDs first (prerequisite)
2. Collect market_cap for all those coins on target date
3. Sort by market_cap to calculate rankings

---

### 3. Rate Limiting Without API Key: 20 Second Rule ✅

**What we tried**: Finding exact delay for 100% success without registration

**Test Results**:
| Delay | Success Rate | Calls/Min |
|-------|-------------|-----------|
| 2.0s | 13% | ~30 |
| 4.0s | 32% | ~15 |
| 10.0s | 55% | 6 |
| 20.0s | 100% ✅ | 3 |

**Discovery**: CoinGecko free tier (no API key) requires 20s delay between calls

**With Demo API Key** (free, no credit card):

- 4s delay = 100% success
- 15 calls/min
- 5× faster than no-key approach

**What we learned**:

- ✅ Can use CoinGecko WITHOUT registration if willing to wait 20s between calls
- ✅ Free Demo API key is MUCH better (4s vs 20s) and requires NO credit card
- ❌ Documented limits (50 calls/min) are WRONG - actual limit is ~30 calls/min unauthenticated

---

### 4. Maximum Ranking Depth: 13,000 Coins ✅

**What we tested**: How many coins can CoinGecko rank?

**Results**:
| Page | Rank Range | Status |
|------|--------------------|-----------------|
| 1 | #1 to #250 | ✅ All ranked |
| 10 | #2,251 to #2,500 | ✅ All ranked |
| 40 | #9,754 to #10,001 | ✅ All ranked |
| 50 | #12,251 to #12,500 | ✅ All ranked |
| 52 | #12,752 to #12,991 | ✅ 241 ranked |
| 54+ | Beyond #13,000 | ❌ All unranked |

**Discovery**:

- Total CoinGecko coins: 19,410
- Ranked coins: ~13,000 (67%)
- Unranked coins: ~6,410 (33%) - too low market cap or insufficient data

**Last ranked coin**: #12,991 - ladyluck (LUCKY)

**What we learned**:

- ✅ Can get up to 13,000 ranked coins
- ❌ Remaining 6,410 coins have no rank (dead/low-cap/insufficient data)

---

### 5. Survivorship Bias Risk ⚠️

**Problem**: Collecting only TODAY'S top 500 coins historically creates survivorship bias

**Example**:

- 2013-07-26: Top coin was Bitcoin, but also included Namecoin, Peercoin, etc.
- If we collect TODAY'S top 500 coins (2025-11-20), we might miss dead 2013 coins
- Historical rankings would be WRONG because missing dead coins artificially inflates ranks

**Solution**:

1. Get ALL 19,410 coin IDs first (includes dead coins from 2013+)
2. Collect historical data for all those coins
3. Calculate point-in-time rankings from complete data

**What we learned**: Must have complete coin universe BEFORE collecting historical data

---

### 6. Non-CoinGecko APIs: Not Worth Pursuing ❌

**APIs investigated and rejected**:

**Messari** - 200 coins max (insufficient)
**CoinPaprika** - Similar limitations to CoinGecko
**CoinCap** - Fewer features than CoinGecko
**Crypto Data Download** - Paid only
**Academic sources** - No comprehensive free dataset found

**Decision**: Focus exclusively on CoinGecko

- Most comprehensive (19,410 coins)
- Best free tier
- Most reliable data
- Best documentation

**What we learned**: CoinGecko is the clear winner for free comprehensive crypto data

---

## Working Solutions ✅

### Current Rankings Snapshot

**Endpoint**: `/coins/markets`

**What it does**: Returns current top N coins with `market_cap_rank` field

**Usage**:

```bash
# Get top 500 current rankings
uv run tools/fetch_current_rankings.py 500

# Get ALL ~13,000 ranked coins
uv run tools/fetch_current_rankings.py all
```

**Benefits**:

- ✅ Real-time rankings
- ✅ Fast (2 API calls for top 500)
- ✅ Includes rank, id, symbol, name, market_cap
- ✅ Works without API key (just slower)

**Limitations**:

- ❌ Current rankings only (not historical dates)
- ❌ Max 13,000 ranked coins

---

### Complete Coin ID List

**Endpoint**: `/coins/list`

**What it does**: Returns all 19,410 active coin IDs

**Usage**:

```bash
uv run tools/fetch_all_coin_ids.py
```

**Benefits**:

- ✅ FREE (no API calls against limit)
- ✅ Includes dead 2013-era coins (Namecoin, Peercoin, etc.)
- ✅ Foundation for comprehensive data collection

**Note**: "Active" includes many dead coins, but excludes some truly delisted coins (requires paid plan for full inactive list)

---

## Canonical Workflow 🎯

**The ONLY way to get historical point-in-time rankings**:

### Step 1: Get Coin IDs (PREREQUISITE)

```bash
uv run tools/fetch_all_coin_ids.py
```

**Output**: 19,410 coin IDs saved to `data/coin_ids/`

**Decision point**:

- All 19,410 coins? (comprehensive but slow)
- Top 13,000 ranked? (faster, covers most activity)
- Top 500/1000? (very fast, covers major coins)

### Step 2: Collect Historical Market Caps

For each coin ID × each target date:

```bash
# Example: Get Bitcoin market cap on 2024-01-15
curl "https://api.coingecko.com/api/v3/coins/bitcoin/history?date=15-01-2024"
```

**Time estimate** (for 365 days):

- 500 coins × 365 days = 182,500 API calls
- With API key (4s delay): ~8.5 days
- Without API key (20s delay): ~42 days

### Step 3: Calculate Point-in-Time Rankings

```bash
uv run tools/calculate_point_in_time_rankings.py
```

**Process**:

1. Load all market_cap data for target date
2. Sort by market_cap descending
3. Assign rank numbers (1, 2, 3, ...)
4. Save ranked results

---

## Key Takeaways

### What Works ✅

1. **CoinGecko `/coins/markets`** - Current rankings (up to 13,000 coins)
2. **CoinGecko `/coins/list`** - All coin IDs (19,410 active)
3. **CoinGecko `/coins/{id}/history`** - Historical market_cap per coin (NOT rank)
4. **20s delay** - 100% success without API key
5. **4s delay** - 100% success with free Demo API key

### What Doesn't Work ❌

1. ❌ crypto2 R package (only 69 coins)
2. ❌ Direct historical rank lookup (no such API)
3. ❌ Non-CoinGecko APIs (insufficient coverage)
4. ❌ Collecting today's top N historically (survivorship bias)

### Critical Requirements 🎯

1. **MUST get coin IDs first** (prerequisite for ranking)
2. **MUST collect ALL coins for a date** (to calculate complete rankings)
3. **MUST avoid survivorship bias** (include dead coins)
4. **MUST respect rate limits** (20s no-key, 4s with-key)

---

## Future Strategy

### Daily Collection (Recommended)

```bash
# Run once per day (automate with cron)
uv run tools/fetch_current_rankings.py 1000

# Each day: 4 API calls
# Month: 120 calls (1.2% of 10,000 monthly limit)
# Year: Complete historical database built gradually!
```

**Benefits**:

- ✅ Sustainable (well within free tier)
- ✅ No survivorship bias (captures coins as they exist)
- ✅ Real-time accuracy
- ✅ Builds comprehensive database over time

### Historical Backfill (One-Time)

For historical dates before daily collection started:

1. Get coin IDs snapshot for that era
2. Collect market_cap for all coins on target dates
3. Calculate rankings from collected data
4. Very slow (days/weeks for full backfill)

---

## References

**Working Tools**:

- `tools/fetch_all_coin_ids.py` - Get all 19,410 coin IDs
- `tools/fetch_current_rankings.py` - Get current top N rankings
- `tools/calculate_point_in_time_rankings.py` - Calculate rankings from market_cap data
- `tools/lookup_rank_by_id_date.py` - Lookup specific coin rank on specific date

**Data Locations**:

- `data/coin_ids/` - All 19,410 CoinGecko coin IDs
- `data/rankings/` - Current rankings snapshots

**Documentation**:

- `data/coin_ids/README.md` - Coin ID collection details
- `data/rankings/README.md` - Rankings collection details

---

**Status**: ✅ All major discoveries documented, failed approaches archived
