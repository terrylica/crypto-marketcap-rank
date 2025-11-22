# CoinGecko Coverage Analysis - Does It Cover crypto2's Gap?

**Date**: 2025-11-20
**Question**: Does CoinGecko have enough historical data to cover the gap left by crypto2?

---

## Executive Summary

**Answer**: ✅ **YES** - CoinGecko's 365-day historical data **PERFECTLY** covers the gap left by crypto2

**Gap to Fill**: 325 days (2025-01-01 to 2025-11-20)

**CoinGecko Coverage**: 365 days (free tier)

**Result**: ✅ Complete overlap with 40 days extra buffer

**Registration Required**: ❌ **NO** (optional but recommended)

---

## Coverage Match Analysis

### Gap Left by crypto2

**crypto2 Coverage**: 2013-04-28 to **2024-12-31**

**Missing Period**: 2025-01-01 to 2025-11-20 (today)

**Gap Size**: **325 days**

### CoinGecko Free Tier Coverage

**Historical Data Limit**: **365 days** (from present)

**Calculation**:

```
Today: 2025-11-20
365 days ago: 2024-11-21

CoinGecko coverage: 2024-11-21 to 2025-11-20
crypto2 ends at:    2024-12-31
Gap starts at:      2025-01-01

Overlap: 2024-11-21 to 2024-12-31 (10 days)
Gap coverage: 2025-01-01 to 2025-11-20 (325 days)
```

**Result**: ✅ **PERFECT FIT** - CoinGecko covers entire 2025 gap PLUS 10-day overlap for validation

---

## Historical Documentation We Already Have

### 1. validate_coingecko.py Script

**Location**: `validation/scripts/validate_coingecko.py`

**Purpose**: Validate CoinGecko 365-day historical data quality

**Tests Implemented**:

1. ✅ Date range coverage (expects ~365 days)
2. ✅ Field schema validation (date, price, market_cap, rank)
3. ✅ Data completeness (no critical nulls/zeros)
4. ✅ Market cap consistency checks
5. ✅ Major coin coverage (BTC, ETH, USDT)
6. ✅ Quality tier assessment (flags as 'unverified')

**Expected Schema**:

```python
Required fields:
- date (or timestamp)
- symbol or id
- name
- price or current_price
- market_cap or market_cap_usd
- rank or market_cap_rank
```

**Quality Tier**: UNVERIFIED (no circulating_supply field)

### 2. ADR-0001 Documentation

**Location**: `docs/architecture/decisions/0001-hybrid-free-data-acquisition.md`

**CoinGecko Role Documented**:

- Source #3 in hybrid strategy
- Coverage: 2024-2025 recent period
- Quality tier: Unverified (pre-calculated market cap)
- Limitation: No circulating supply to verify calculation

**Planned Use**:

```
crypto2 (2013-2024)      +      CoinGecko (2024-2025)
    VERIFIED                      UNVERIFIED
        ↓                               ↓
    Primary source              Supplementary source
```

### 3. Merge Strategy Already Designed

**Script**: `tools/merge_datasets.py` (ready to use)

**Merge Logic**:

```python
priority_order = ['crypto2', 'coingecko']
# crypto2 data wins in overlaps
# CoinGecko fills gaps only
```

**Quality Flags**:

- crypto2 records: `quality_tier='verified'`
- CoinGecko records: `quality_tier='unverified'`

---

## CoinGecko Free API - 2025 Research Findings

### Free Tier Options (No Payment Required)

**Option 1: No Registration** (Truly Free)

- **API Key**: NOT required
- **Rate Limit**: 30 calls/minute
- **Monthly Limit**: Not specified
- **Coverage**: 365 days historical
- **Cost**: $0
- **Attribution**: Required (must credit CoinGecko)

**Option 2: Demo Plan** (Free with Registration)

- **API Key**: Required (free to generate)
- **Rate Limit**: 30 calls/minute (same as no-key)
- **Monthly Limit**: 10,000 calls/month
- **Coverage**: 365 days historical
- **Cost**: $0
- **Benefits**: Better tracking, monthly cap visibility

### Recommendation: Register for Demo API

**Why Register** (even though optional):

1. ✅ Get monthly usage tracking (10,000 call cap)
2. ✅ More reliable rate limiting
3. ✅ Better error messages
4. ✅ Still 100% free
5. ✅ Easy registration (email only, 2 minutes)

**Registration Process**:

1. Go to: https://www.coingecko.com/en/api
2. Click "Get Your Free API Key"
3. Sign up with email
4. Generate Demo API key
5. Use key in API calls: `?x_cg_demo_api_key=YOUR_KEY`

### API Endpoint for Historical Data

**Endpoint**: `/coins/{id}/market_chart`

**Example**:

```bash
# Bitcoin, last 365 days
https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365

# With API key (recommended)
https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365&x_cg_demo_api_key=YOUR_KEY
```

**Parameters**:

- `id`: Coin ID (e.g., "bitcoin", "ethereum")
- `vs_currency`: "usd" (default)
- `days`: "365" (or "max" for 365 days on free tier)

**Response Format**:

```json
{
  "prices": [[timestamp, price], ...],
  "market_caps": [[timestamp, market_cap], ...],
  "total_volumes": [[timestamp, volume], ...]
}
```

### Recent API Changes (January 2025)

**NEW Restriction**: Each API request limited to **6-month date range**

**Workaround**: Use `before_timestamp` parameter to fetch older data within 365-day window

**Example** (for full 365 days):

```bash
# Last 6 months (most recent)
/coins/bitcoin/market_chart?days=180

# Previous 6 months (within 365 days)
/coins/bitcoin/market_chart?days=180&before_timestamp=<6_months_ago>
```

**For Our Use Case**: Only need 325 days, so can fetch in two calls if needed:

- Call 1: Last 180 days (2025-05-24 to 2025-11-20)
- Call 2: Previous 145 days (2025-01-01 to 2025-05-23)

---

## Collection Strategy

### Estimated API Calls

**Top 500 coins** × **2 calls per coin** (to cover 365 days) = **1,000 API calls**

**Within Free Limits**:

- No-key option: 30 calls/min = ~34 minutes total
- Demo plan: 10,000 calls/month = well within limit

**Rate Limiting**:

```python
import time
for coin in top_500_coins:
    # Call 1: Recent 180 days
    fetch_market_chart(coin, days=180)
    time.sleep(2)  # 30 calls/min = 2 sec delay

    # Call 2: Older 180 days (within 365)
    fetch_market_chart(coin, days=180, before=six_months_ago)
    time.sleep(2)
```

**Total Time**: ~34 minutes (with 2-second delay between calls)

---

## Validation Coverage

### What We Can Validate

✅ **Schema**: Date, symbol, price, market_cap, rank
✅ **Date Coverage**: 365 days (covers our 325-day gap)
✅ **Completeness**: No nulls/zeros in critical fields
✅ **Market Cap Consistency**: Rank ordering matches values
✅ **Major Coins**: BTC, ETH, USDT presence

### What We CANNOT Validate

❌ **Circulating Supply**: Not provided by free tier
❌ **Market Cap Calculation**: Cannot verify `price × supply`
❌ **Exact Accuracy**: Must trust CoinGecko's pre-calculated values

**Result**: CoinGecko data flagged as **'unverified'** quality tier

---

## Does CoinGecko Cover the Gap? - FINAL ANSWER

### Question 1: Does CoinGecko have enough historical data?

**Answer**: ✅ **YES - PERFECT COVERAGE**

- Gap to fill: 325 days (2025-01-01 to 2025-11-20)
- CoinGecko provides: 365 days
- Result: Full coverage + 40 days buffer

### Question 2: Do we have historical documentation?

**Answer**: ✅ **YES - FULLY DOCUMENTED**

**Existing Documentation**:

1. ✅ `validate_coingecko.py` - Complete validation script
2. ✅ `ADR-0001` - CoinGecko role in hybrid strategy
3. ✅ `merge_datasets.py` - Merge logic ready
4. ✅ Expected schema documented
5. ✅ Quality tier strategy defined

### Question 3: Do you need to register for API account?

**Answer**: ❌ **NO - But RECOMMENDED**

**Two Options**:

1. **No Registration**: Works, but no usage tracking
2. **Demo Registration** (Recommended): Free, better rate limits, usage visibility

**Registration Process**: 2 minutes, free forever

### Question 4: Will registration help?

**Answer**: ✅ **YES - Recommended for Better Experience**

**Benefits of Demo API Registration**:

1. Monthly usage cap visibility (10,000 calls/month)
2. Better rate limit management
3. More reliable API access
4. Clear error messages
5. Still 100% FREE

**Drawbacks**: None (registration takes 2 minutes)

---

## Next Steps - CoinGecko Collection

### Step 1: Register for Demo API (Optional but Recommended)

**Time**: 2 minutes

**Steps**:

1. Visit: https://www.coingecko.com/en/api
2. Click "Get Your Free API Key"
3. Sign up with email
4. Generate API key
5. Save key to `.env` file

**Alternative**: Skip registration, use no-key option (still works)

### Step 2: Create CoinGecko Collection Script

**Script**: `tools/collect_coingecko.py` (to be created)

**Features**:

- Fetch 365-day market_chart data for top 500 coins
- Rate limiting: 2-second delay (30 calls/min)
- Handle 6-month API restriction (split into 2 calls if needed)
- Save to: `data/raw/coingecko/market_cap_YYYYMMDD_HHMMSS.csv`
- Comprehensive logging

**Estimated Runtime**: ~34 minutes for 500 coins

### Step 3: Validate CoinGecko Data

**Script**: `validation/scripts/validate_coingecko.py` (already exists)

**Run**:

```bash
uv run validation/scripts/validate_coingecko.py data/raw/coingecko/market_cap_*.csv
```

**Expected Result**: ✅ PASS with warnings about 'unverified' quality tier

### Step 4: Merge with crypto2 Data

**Script**: `tools/merge_datasets.py` (already exists)

**Run**:

```bash
uv run tools/merge_datasets.py \
  --crypto2 data/raw/crypto2/scenario_b_full_*.csv \
  --coingecko data/raw/coingecko/market_cap_*.csv \
  --output data/final/merged_market_cap_2013_2025.csv
```

**Output**:

- Merged CSV with quality tier flags
- Metadata JSON with source attribution
- Coverage report

---

## Summary

**Does CoinGecko cover the gap?** ✅ **YES**

**Coverage Match**:

```
crypto2:      [===============================] 2013-2024
                                              ↓
                                         2024-12-31
                                              ↓
CoinGecko:                          [=============] 2024-2025
                                         ↑
                                    2024-11-21 (365 days ago)

Overlap: 10 days (2024-11-21 to 2024-12-31)
Gap Fill: 325 days (2025-01-01 to 2025-11-20) ✅
```

**Registration Required?** ❌ NO (but recommended)

**Documentation Complete?** ✅ YES (validation + merge scripts ready)

**Ready to Collect?** ✅ YES (as soon as crypto2 collection completes)

---

**Status**: Analysis complete - CoinGecko is perfect fit for covering crypto2's gap
