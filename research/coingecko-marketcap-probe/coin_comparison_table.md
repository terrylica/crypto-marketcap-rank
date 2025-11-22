# Coin Comparison Table - CoinGecko Market Cap Data

## Successfully Tested Coins (365-day data)

| Coin ID   | Name      | Launch Year | Data Points | Days Span | First Date | Last Date  | First Market Cap | Last Market Cap |
| --------- | --------- | ----------- | ----------- | --------- | ---------- | ---------- | ---------------- | --------------- |
| bitcoin   | Bitcoin   | 2009        | 366         | 364       | 2024-11-20 | 2025-11-19 | $1,862.6B        | $1,842.6B       |
| cardano   | Cardano   | 2017        | 366         | 364       | 2024-11-20 | 2025-11-19 | $28.8B           | $17.1B          |
| polkadot  | Polkadot  | 2020        | 366         | 364       | 2024-11-20 | 2025-11-19 | $8.3B            | $4.4B           |
| solana    | Solana    | 2020        | 366         | 364       | 2024-11-20 | 2025-11-19 | $112.0B          | $79.2B          |
| chainlink | Chainlink | 2017        | 366         | 364       | 2024-11-20 | 2025-11-19 | $9.0B            | $9.5B           |

## Key Observations

1. **All coins return identical date ranges** (2024-11-20 to 2025-11-19)
   - This is independent of when the coin was launched
   - Confirms the 365-day limit is API-tier based, not coin-specific

2. **Consistent data granularity**
   - 366 data points for 365 days (one point per day + current)
   - Daily snapshots at approximately the same time each day

3. **Market cap volatility visible**
   - Polkadot: -46.5% (from $8.3B to $4.4B)
   - Cardano: -40.5% (from $28.8B to $17.1B)
   - Solana: -29.3% (from $112B to $79.2B)
   - Bitcoin: -1.1% (from $1,862B to $1,842B)
   - Chainlink: +5.8% (from $9.0B to $9.5B)

4. **Data completeness**
   - No missing data points observed
   - All tested coins (old and new) have complete market cap history
   - Data quality appears consistent across all coins

## Coins That Could Not Be Fully Tested (Rate Limited)

- Ethereum (2015)
- Litecoin (2011)
- XRP/Ripple (2012)
- Stellar (2014)
- Dogecoin (2013)

**Note:** These coins were rate-limited during testing, but based on successful tests of other coins, they should also have market cap data available (within the 365-day free tier limit).

## Total Coins Available

CoinGecko API reported **19,416 total coins** available in their database as of 2025-11-19.

**Implication for bulk downloads:**

- At ~10-30 calls/minute (free tier rate limit)
- Downloading all 19,416 coins would take: **11-32 hours**
- This assumes no API failures or additional throttling
