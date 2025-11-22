# CoinGecko API Technical Documentation

## Endpoint: Market Chart

### Base URL

```
https://api.coingecko.com/api/v3
```

### Endpoint Path

```
GET /coins/{id}/market_chart
```

### Parameters

| Parameter     | Type       | Required | Description                           | Free Tier Limit |
| ------------- | ---------- | -------- | ------------------------------------- | --------------- |
| `id`          | string     | Yes      | Coin ID (e.g., "bitcoin", "ethereum") | -               |
| `vs_currency` | string     | Yes      | Target currency (e.g., "usd", "eur")  | -               |
| `days`        | string/int | Yes      | Data up to number of days ago         | **Max: 365**    |

### Free Tier Limitations

1. **Historical Data Range**
   - Maximum: 365 days
   - Attempts to request more result in HTTP 401
2. **Rate Limits**
   - Estimated: 10-30 calls per minute
   - Exceeded limit returns HTTP 429
   - No API key available for free tier

3. **Data Granularity** (based on days parameter)
   - 1-90 days: Hourly data
   - 91-365 days: Daily data
   - > 365 days: BLOCKED on free tier

### Response Format

```json
{
  "prices": [
    [timestamp_milliseconds, price_usd],
    ...
  ],
  "market_caps": [
    [timestamp_milliseconds, market_cap_usd],
    ...
  ],
  "total_volumes": [
    [timestamp_milliseconds, volume_usd],
    ...
  ]
}
```

### Example Request

```bash
curl "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365"
```

### Example Response (Abbreviated)

```json
{
  "prices": [
    [1700524800000, 94321.45],
    [1700611200000, 94856.23]
  ],
  "market_caps": [
    [1700524800000, 1862618759426.15],
    [1700611200000, 1948284556982.05]
  ],
  "total_volumes": [
    [1700524800000, 42563789123.45],
    [1700611200000, 45234567890.12]
  ]
}
```

### Error Responses

#### HTTP 401 - Time Range Exceeded

```json
{
  "error": {
    "status": {
      "timestamp": "2025-11-20T02:49:16.124+00:00",
      "error_code": 10012,
      "error_message": "Your request exceeds the allowed time range. Public API users are limited to querying historical data within the past 365 days. Upgrade to a paid plan to enjoy full historical data access: https://www.coingecko.com/en/api/pricing."
    }
  }
}
```

**Triggered by:**

- `days=730`
- `days=max`
- Any value > 365

#### HTTP 429 - Rate Limit Exceeded

```json
{
  "status": {
    "error_code": 429,
    "error_message": "You've exceeded the Rate Limit. Please visit https://www.coingecko.com/en/api/pricing to subscribe to our API plans for higher rate limits."
  }
}
```

**Triggered by:**

- Making too many requests in short time period
- Estimated threshold: ~10-30 requests/minute

### Coin List Endpoint

To get available coin IDs:

```
GET /coins/list
```

Response:

```json
[
  {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin"
  },
  ...
]
```

**Total coins available:** 19,416 (as of 2025-11-19)

### Best Practices

1. **Rate Limiting**
   - Add 3-5 second delays between requests
   - Implement exponential backoff on 429 errors
   - Monitor response headers for rate limit info

2. **Error Handling**
   - Check for HTTP 401: data range too large
   - Check for HTTP 429: slow down requests
   - Implement retry logic with delays

3. **Data Processing**
   - Timestamps are in milliseconds (not seconds)
   - Convert to datetime: `datetime.fromtimestamp(ms/1000)`
   - Market caps are in USD (full precision float)

### Python Example

```python
import requests
import time
from datetime import datetime

def get_market_cap(coin_id, days=365):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data['market_caps']
    elif response.status_code == 401:
        print("Error: Time range exceeds 365 days")
    elif response.status_code == 429:
        print("Error: Rate limited - wait before retrying")

    return None

# Usage with rate limiting
market_caps = get_market_cap('bitcoin', days=365)
time.sleep(5)  # Avoid rate limits
```

### Pricing Information

**Free Tier:**

- 365 days historical data only
- 10-30 calls/minute (estimated)
- No API key
- No support

**Paid Plans:**

- Analyst: $129/month - Full historical data
- Pro: $499/month - Full historical + higher rate limits
- More info: https://www.coingecko.com/en/api/pricing

---

## Data Quality Notes

**Confirmed Working:**

- Market cap data present in all responses (within 365-day limit)
- Data completeness: No gaps observed
- Data granularity: Daily snapshots for 365-day requests
- Data accuracy: Values appear consistent with market data

**Limitations:**

- Cannot verify historical accuracy beyond 365 days (blocked on free tier)
- No data validation possible for older coins (e.g., Bitcoin pre-2024)
- Rate limits make bulk downloads impractical on free tier
