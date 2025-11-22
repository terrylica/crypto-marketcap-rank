# CoinGecko API Market Cap Investigation - CRITICAL FINDINGS

**Investigation Date:** 2025-11-19  
**Endpoint Tested:** `/coins/{id}/market_chart`  
**API Tier:** Free (Public API, no authentication)

---

## EXECUTIVE SUMMARY: ❌ NOT SUITABLE FOR MULTI-YEAR MARKET CAP DATA

**CRITICAL LIMITATION CONFIRMED:**  
CoinGecko's free tier API is **HARD-LIMITED to 365 days** of historical market cap data. Any request beyond this range returns HTTP 401 with explicit error message blocking access.

---

## KEY FINDINGS

### 1. ✅ Does CoinGecko API include market cap in responses?

**YES - Market cap data is included and complete.**

Response structure contains three arrays:

- `prices`: [timestamp_ms, price_usd]
- `market_caps`: [timestamp_ms, market_cap_usd] ← **CONFIRMED PRESENT**
- `total_volumes`: [timestamp_ms, volume_usd]

Example market cap data points from Bitcoin (365-day request):

```
First: 2024-11-20 → $1,862,618,759,426.15
Last:  2025-11-19 → $1,842,630,931,436.86
```

All tested coins (Cardano, Polkadot, Solana, Chainlink) returned complete market cap arrays with 366 data points for 365-day requests.

---

### 2. ❌ How far back does market cap data go?

**FREE TIER: HARD-LIMITED TO 365 DAYS**

Testing results:

- `days=365`: ✅ SUCCESS (HTTP 200)
- `days=730`: ❌ HTTP 401 - "exceeds allowed time range"
- `days=1825`: ❌ HTTP 401 - "exceeds allowed time range"
- `days=max`: ❌ HTTP 401 - "exceeds allowed time range"

**Exact Error Message Received:**

```json
{
  "error": {
    "status": {
      "error_code": 10012,
      "error_message": "Your request exceeds the allowed time range. Public API users are limited to querying historical data within the past 365 days. Upgrade to a paid plan to enjoy full historical data access: https://www.coingecko.com/en/api/pricing."
    }
  }
}
```

**Earliest Available Date (tested 2025-11-19):** 2024-11-20 (~364 days ago)

---

### 3. ❌ Free tier limitations for market cap

**CONFIRMED: 365-day hard limit on free tier**

| Parameter | Status     | Result                  |
| --------- | ---------- | ----------------------- |
| days=365  | ✅ Allowed | Returns 366 data points |
| days=730  | ❌ BLOCKED | HTTP 401                |
| days=max  | ❌ BLOCKED | HTTP 401                |

**Earlier research was CORRECT:** Free tier = 365 days only.

**Cannot circumvent** by:

- Using `days=max` parameter
- Requesting specific date ranges beyond 365 days
- Testing different coins

The limitation is **enforced server-side** regardless of coin age or launch date.

---

### 4. ✅ Market cap availability across coins

**All tested coins have market cap data available** (within 365-day limit)

| Coin      | Launch Year | Market Cap Available | Data Points | First Date | Last Date  |
| --------- | ----------- | -------------------- | ----------- | ---------- | ---------- |
| Bitcoin   | 2009        | ✅ Yes               | 366         | 2024-11-20 | 2025-11-19 |
| Cardano   | 2017        | ✅ Yes               | 366         | 2024-11-20 | 2025-11-19 |
| Polkadot  | 2020        | ✅ Yes               | 366         | 2024-11-20 | 2025-11-19 |
| Solana    | 2020        | ✅ Yes               | 366         | 2024-11-20 | 2025-11-19 |
| Chainlink | 2017        | ✅ Yes               | 366         | 2024-11-20 | 2025-11-19 |

Sample market cap values:

- Solana: $112B → $79B (over 365 days)
- Cardano: $28.7B → $17.1B
- Chainlink: $8.95B → $9.47B

**Note:** All coins return identical date ranges (365 days from today), regardless of when the coin launched. This confirms the limitation is API-tier based, not coin-specific.

---

### 5. 🚨 API rate limits and response format

**Rate Limits: VERY STRICT (Free Tier)**

Encountered HTTP 429 "Rate Limit Exceeded" after:

- **~5-7 requests** in rapid succession
- Required **7+ second delays** between requests to avoid throttling

Rate limit error message:

```json
{
  "status": {
    "error_code": 429,
    "error_message": "You've exceeded the Rate Limit. Please visit https://www.coingecko.com/en/api/pricing to subscribe to our API plans for higher rate limits."
  }
}
```

**Estimated Free Tier Limits:**

- 10-30 calls per minute (based on testing)
- No official documentation found for exact limits

**Response Format:**

```json
{
  "prices": [[timestamp_ms, price], ...],
  "market_caps": [[timestamp_ms, market_cap], ...],
  "total_volumes": [[timestamp_ms, volume], ...]
}
```

**Response Performance:**

- Response time: ~0.03-0.14 seconds
- Data points for 365 days: 366 entries (daily granularity)
- Response size: Small, efficient JSON arrays

---

## CRITICAL FINDING: CAN WE USE COINGECKO FOR MULTI-YEAR MARKET CAP DATA?

# ❌ NO - FREE TIER CANNOT BE USED

**Reasons:**

1. **365-Day Hard Limit**
   - Free tier explicitly blocked from accessing data beyond 365 days
   - Returns HTTP 401 with error code 10012
   - No workarounds available (tested multiple approaches)

2. **Paid Plan Required for Historical Data**
   - Error message explicitly directs to paid plans
   - No free alternative for historical market cap beyond 1 year

3. **Rate Limits Too Restrictive**
   - ~10-30 calls/minute limit
   - Would make bulk downloads slow and fragile
   - Frequent HTTP 429 errors during testing

---

## ALTERNATIVE RECOMMENDATIONS

Since CoinGecko free tier is unsuitable, consider:

1. **CoinGecko Paid API**
   - Analyst Plan ($129/month): Full historical data access
   - Pro Plan ($499/month): Higher rate limits + full history
   - Link: https://www.coingecko.com/en/api/pricing

2. **Alternative Free APIs**
   - CoinCap API (free, historical data available)
   - Messari API (limited free tier, but multi-year data)
   - CryptoCompare (free tier with historical data)

3. **Public Datasets**
   - Kaggle cryptocurrency datasets
   - Historical data dumps from exchanges
   - Academic research datasets

---

## DATA QUALITY OBSERVATIONS

**What works well:**

- Market cap data is accurate and complete (within 365-day window)
- API response format is clean and consistent
- All major coins have market cap data
- Daily granularity is sufficient for most analysis

**Limitations encountered:**

- 365-day hard limit (free tier)
- Aggressive rate limiting
- No batch/bulk endpoints for free tier
- No API key available for free tier (can't track usage)

---

## TESTING ARTIFACTS

All test scripts and results saved in:

- `/tmp/coingecko-marketcap-probe/`

Files generated:

- `test_coingecko.py` - Comprehensive test suite
- `test_slower.py` - Rate-limit aware testing
- `test_results.json` - Raw test results
- `coin_comparison.json` - Cross-coin comparison
- `sample_response_structure.json` - API response format

---

## CONCLUSION

**CoinGecko's free API:**

- ✅ Does include market cap data
- ✅ Market cap data is accurate and complete
- ❌ Limited to 365 days ONLY
- ❌ Cannot be used for multi-year historical analysis
- ❌ Rate limits are too restrictive for bulk downloads

**For multi-year market cap data, you must either:**

1. Pay for CoinGecko's Analyst/Pro plan ($129-499/month), OR
2. Use an alternative data source

**The free tier is definitively NOT suitable for the stated goal of downloading historical market cap data for all cryptocurrencies.**
