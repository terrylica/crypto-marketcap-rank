# CoinGecko API Market Cap Investigation

**Investigation Date:** November 19, 2025  
**Objective:** Determine if CoinGecko's free API can be used to download historical market cap data for all cryptocurrencies  
**Result:** ❌ **NOT SUITABLE** - Free tier limited to 365 days only

---

## Quick Answer

**Can we use CoinGecko free API for multi-year historical market cap data?**

# NO

The free tier has a **hard 365-day limit** on historical data access. Any request beyond this returns HTTP 401 error.

---

## What We Tested

1. ✅ **Market cap data availability** - Confirmed present in API responses
2. ❌ **Historical data range** - LIMITED to 365 days on free tier
3. ❌ **Free tier limitations** - Cannot access data beyond 1 year
4. ✅ **Market cap across coins** - All tested coins have market cap data
5. 🚨 **Rate limits** - Very restrictive (~10-30 calls/minute)

---

## Key Findings

### 1. Market Cap Data is Available

- Response includes: `prices`, `market_caps`, `total_volumes`
- Market cap format: `[timestamp_ms, market_cap_usd]`
- Data is complete and accurate (within 365-day window)

### 2. 365-Day Hard Limit (Free Tier)

```
days=365  → ✅ HTTP 200 (Success)
days=730  → ❌ HTTP 401 (Blocked)
days=max  → ❌ HTTP 401 (Blocked)
```

**Error received:**

> "Public API users are limited to querying historical data within the past 365 days. Upgrade to a paid plan..."

### 3. Aggressive Rate Limiting

- Limit: ~10-30 requests/minute
- HTTP 429 errors encountered frequently
- Would take **11-32 hours** to download all 19,416 coins

### 4. Sample Data (Bitcoin, 365 days)

```
Data Points:  366
Date Range:   2024-11-20 to 2025-11-19
First MC:     $1,862,618,759,426.15
Last MC:      $1,842,630,931,436.86
```

---

## Files in This Directory

| File                             | Description                             |
| -------------------------------- | --------------------------------------- |
| `README.md`                      | This file - investigation summary       |
| `FINDINGS.md`                    | Detailed findings and critical analysis |
| `API_DOCUMENTATION.md`           | Technical API reference and examples    |
| `coin_comparison_table.md`       | Tested coins comparison data            |
| `test_coingecko.py`              | Comprehensive test suite                |
| `test_slower.py`                 | Rate-limit aware testing script         |
| `test_results.json`              | Raw test results data                   |
| `coin_comparison.json`           | Cross-coin comparison data              |
| `sample_response_structure.json` | API response format example             |

---

## Critical Limitations

1. **365-Day Maximum** - Cannot access historical data beyond 1 year
2. **No Workarounds** - Tested multiple approaches, all blocked
3. **Rate Limited** - Too slow for bulk downloads (11-32 hours for all coins)
4. **Paid Plan Required** - Must pay $129-499/month for full historical data

---

## Recommendations

### If you need multi-year historical data:

#### Option 1: Pay for CoinGecko

- Analyst Plan: $129/month (full historical data)
- Pro Plan: $499/month (full historical + higher limits)
- URL: https://www.coingecko.com/en/api/pricing

#### Option 2: Use Alternative APIs

- **CoinCap API** - Free, has historical data
- **Messari API** - Limited free tier with multi-year data
- **CryptoCompare** - Free tier with historical access
- **CoinMarketCap** - Free tier with limited historical data

#### Option 3: Public Datasets

- Kaggle cryptocurrency datasets
- Historical data dumps from exchanges
- Academic research datasets (often multi-year coverage)

### If 365 days is sufficient:

- CoinGecko free API works fine
- Be mindful of rate limits
- Implement delays between requests (5-7 seconds)

---

## Example Usage (Python)

```python
import requests
import time

def get_market_cap(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {'vs_currency': 'usd', 'days': '365'}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()['market_caps']
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Get Bitcoin market cap history
bitcoin_mc = get_market_cap('bitcoin')
time.sleep(5)  # Avoid rate limits

# Get Ethereum market cap history
ethereum_mc = get_market_cap('ethereum')
```

---

## Testing Evidence

### Successful Tests (HTTP 200)

- Bitcoin (365 days) - 366 data points
- Cardano (365 days) - 366 data points
- Polkadot (365 days) - 366 data points
- Solana (365 days) - 366 data points
- Chainlink (365 days) - 366 data points

### Failed Tests (HTTP 401 - Beyond 365 days)

- Bitcoin (730 days) - BLOCKED
- Bitcoin (1825 days) - BLOCKED
- Bitcoin (max) - BLOCKED

### Rate Limited Tests (HTTP 429)

- Ethereum (after ~5 rapid requests)
- Multiple coins when testing too quickly

---

## Conclusion

CoinGecko's free API:

- ✅ **Does** provide market cap data
- ✅ **Is** reliable and accurate (within limits)
- ❌ **Cannot** provide multi-year historical data
- ❌ **Is not** suitable for comprehensive historical analysis

**For the stated goal of downloading historical market cap data for all cryptocurrencies, you MUST use a paid plan or alternative data source.**

---

## Contact & Resources

- CoinGecko API Docs: https://www.coingecko.com/en/api/documentation
- CoinGecko Pricing: https://www.coingecko.com/en/api/pricing
- Total Coins Available: 19,416 (as of 2025-11-19)

**Investigation conducted by:** Automated testing with real API calls  
**Data collection method:** Python scripts with requests library  
**Verification:** Multiple coins tested across different time ranges
