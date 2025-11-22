# Rank Lookup by Coin ID + Date

**Question**: Can I get rank number if I have coin ID and date?

**Answer**: **YES, but only for coins in our current dataset**

---

## Current Capability

### ✅ Available Now (69 Coins)

**Tool**: `tools/lookup_rank_by_id_date.py`

**Usage**:

```bash
uv run tools/lookup_rank_by_id_date.py <coin_id> <date>
```

**Examples**:

```bash
# Bitcoin on 2017 bull run peak
uv run tools/lookup_rank_by_id_date.py bitcoin 2017-12-17
# Output: Rank #1, Market Cap: $320,576,568,850

# Litecoin today
uv run tools/lookup_rank_by_id_date.py litecoin 2024-11-20
# Output: Rank #5, Market Cap: $6,271,205,089

# Namecoin in early crypto era (2013)
uv run tools/lookup_rank_by_id_date.py namecoin 2013-07-26
# Output: Rank #3, Market Cap: $3,611,361
```

### Data Coverage

**Source**: crypto2 R package (CoinMarketCap data)

| Metric            | Value                             |
| ----------------- | --------------------------------- |
| **Total Coins**   | 69                                |
| **Date Range**    | 2013-07-26 to 2024-12-31          |
| **Total Days**    | 4,267 days (~11.7 years)          |
| **Total Records** | 264,388                           |
| **Data Quality**  | VERIFIED (has circulating_supply) |

**Available Coins** (69 total):

- Major: Bitcoin (BTC), Litecoin (LTC), XRP, Dogecoin (DOGE), Monero (XMR), Dash (DASH), Stellar (XLM)
- Historical: Namecoin (NMC), Peercoin (PPC), Novacoin (NVC), Feathercoin (FTC), Primecoin (XPM), Terracoin (TRC)
- Others: BitShares (BTS), Bytecoin (BCN), MonaCoin (MONA), DigiByte (DGB), Syscoin (SYS), and 50+ more

**File**: `data/raw/crypto2/scenario_b_full_20251120_20251120_154741.csv` (61 MB)

---

## Demonstration Results

### Example 1: Bitcoin on 2017 Bull Run Peak

```bash
$ uv run tools/lookup_rank_by_id_date.py bitcoin 2017-12-17
```

```
✅ Found: Bitcoin (BTC)

   Rank on 2017-12-17: #1
   Market Cap: $320,576,568,850
   Circulating Supply: 16,748,337
   Total coins ranked that day: 65
   Data source: crypto2 (CoinMarketCap)

Percentile: Top 1.5% of all coins on 2017-12-17
```

### Example 2: Litecoin Today

```bash
$ uv run tools/lookup_rank_by_id_date.py litecoin 2024-11-20
```

```
✅ Found: Litecoin (LTC)

   Rank on 2024-11-20: #5
   Market Cap: $6,271,205,089
   Circulating Supply: 75,218,687
   Total coins ranked that day: 67
   Data source: crypto2 (CoinMarketCap)

Percentile: Top 7.5% of all coins on 2024-11-20
```

### Example 3: Namecoin in Early Crypto Era (Dead Coin)

```bash
$ uv run tools/lookup_rank_by_id_date.py namecoin 2013-07-26
```

```
✅ Found: Namecoin (NMC)

   Rank on 2013-07-26: #3
   Market Cap: $3,611,361
   Circulating Supply: 6,105,593
   Total coins ranked that day: 13
   Data source: crypto2 (CoinMarketCap)

Percentile: Top 23.1% of all coins on 2013-07-26
```

**Key Insight**: Namecoin was #3 in 2013 but essentially dead today. This demonstrates the value of point-in-time rankings that include historically important coins.

### Example 4: Coin NOT in Dataset

```bash
$ uv run tools/lookup_rank_by_id_date.py ethereum 2024-01-01
```

```
❌ Coin not found in dataset

   Available coins (67):
      1. BTC, 2. LTC, 3. XRP, 4. DOGE, ...
      ... and 47 more
```

**Limitation**: Ethereum is NOT in our crypto2 dataset, so we cannot look up its rank.

---

## What's Missing?

### ❌ NOT Available (Most Coins)

**Problem**: crypto2 dataset only has 69 coins

**Missing Major Coins**:

- Ethereum (ETH) - Would be #2 globally today
- BNB (Binance Coin) - Top 5 coin
- Cardano (ADA) - Top 10 coin
- Solana (SOL) - Top 10 coin
- Polkadot (DOT) - Top 20 coin
- And 19,000+ other coins

**Why Missing**:

- crypto2 R package focuses on historically important coins from 2013 era
- Does not include newer major coins (Ethereum, BNB, Cardano, Solana, etc.)
- Does not include the thousands of altcoins and tokens

---

## Solution: Collect More Historical Data

To get rank for ANY coin ID + date, we need to collect historical data from CoinGecko.

### Option A: Top 500 Coins × 365 Days

**Time**: ~33 minutes (with API key)

**Would Add**:

- Ethereum, BNB, Cardano, Solana, Polkadot
- All current top 500 coins
- Historical data for past 365 days

**Limitation**: Still has survivorship bias (only today's top coins)

### Option B: Top 1000 Coins × 365 Days

**Time**: ~66 minutes (with API key)

**Would Add**: More comprehensive coverage including many mid-cap coins

### Option C: All 19,410 Coins × 365 Days

**Time**: ~22 days (with API key)

**Would Add**: Complete historical data for all CoinGecko coins

**Benefit**: TRUE point-in-time rankings for any coin on any date (within 365 days)

---

## Comparison: Current vs After Collection

| Scenario                     | Current (69 coins) | After Top 500 | After Top 1000 | After All 19,410 |
| ---------------------------- | ------------------ | ------------- | -------------- | ---------------- |
| **Can lookup Bitcoin?**      | ✅ YES             | ✅ YES        | ✅ YES         | ✅ YES           |
| **Can lookup Ethereum?**     | ❌ NO              | ✅ YES        | ✅ YES         | ✅ YES           |
| **Can lookup obscure coin?** | ❌ NO              | ❌ Unlikely   | ❌ Unlikely    | ✅ YES           |
| **Date range**               | 2013-2024          | 2023-2024     | 2023-2024      | 2023-2024        |
| **Total lookups possible**   | ~294,000           | ~183,000      | ~365,000       | ~7,084,650       |
| **Collection time**          | ✅ Already done    | 33 min        | 66 min         | 22 days          |

**Note**: crypto2 has longer date range (2013-2024) but fewer coins. CoinGecko has more coins but limited to ~365 days historical data (free tier).

---

## How Rank is Calculated

### Algorithm

For a specific date:

1. Get all coins' market_cap on that date
2. Sort by market_cap descending
3. Assign rank: 1 = highest market cap, 2 = second, etc.

### Example: 2024-11-20

```
Rank 1: Bitcoin    - $1,866,427,425,876
Rank 2: XRP        - $62,755,593,015
Rank 3: Dogecoin   - $55,445,049,324
Rank 4: Stellar    - $7,418,916,004
Rank 5: Litecoin   - $6,271,205,089
...
```

**Point-in-Time**: Rankings are calculated using THAT day's market cap, not retroactive.

---

## Technical Details

### Lookup Tool Source

**File**: `tools/lookup_rank_by_id_date.py`

**Key Function**:

```python
def get_rank_for_coin_on_date(coin_id: str, date: str) -> dict:
    # 1. Load historical data
    # 2. Filter to specific date
    # 3. Calculate rankings by market_cap
    # 4. Find the specific coin
    # 5. Return rank + metadata
```

**Return Format**:

```python
{
    "coin_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "date": "2024-11-20",
    "rank": 1,
    "market_cap": 1866427425875.83,
    "market_cap_formatted": "$1,866,427,425,876",
    "circulating_supply": 19785175.0,
    "total_coins_that_day": 67,
    "data_source": "crypto2 (CoinMarketCap)"
}
```

### Data Format

**CSV Schema**:

```csv
id,slug,name,symbol,timestamp,market_cap,circulating_supply,...
1,bitcoin,Bitcoin,BTC,2024-11-20 23:59:59,1866427425875.83,19785175.0,...
```

**Rank Calculation**:

1. Parse timestamp → extract date
2. Group by date
3. Sort by market_cap descending
4. Assign sequential rank

---

## Usage Examples

### Basic Lookup

```bash
uv run tools/lookup_rank_by_id_date.py bitcoin 2024-01-01
```

### Check Available Coins

```bash
# Try a non-existent coin to see all available coins
uv run tools/lookup_rank_by_id_date.py test 2024-01-01
```

### Programmatic Usage

```python
from tools.lookup_rank_by_id_date import get_rank_for_coin_on_date

result = get_rank_for_coin_on_date("bitcoin", "2024-11-20")

if "error" not in result:
    print(f"Rank: #{result['rank']}")
    print(f"Market Cap: {result['market_cap_formatted']}")
else:
    print(f"Error: {result['error']}")
```

---

## Summary

### ✅ Current Status

**YES, you can get rank by coin ID + date for:**

- 69 historically important coins
- Dates from 2013-07-26 to 2024-12-31
- Total: ~294,000 possible lookups

**Tool**: `tools/lookup_rank_by_id_date.py`

### 🔄 To Enable More Coins

**Need to collect historical data from CoinGecko**:

- Top 500 coins: 33 min → +183,000 lookups
- Top 1000 coins: 66 min → +365,000 lookups
- All 19,410 coins: 22 days → +7,084,650 lookups

**Trade-off**: More coins vs. collection time

---

**Bottom Line**:

- ✅ **Works NOW** for 69 coins (2013-2024)
- 🔄 **Need more data** for other coins (requires CoinGecko collection)
- 📋 **All tools ready** to collect comprehensive historical data when decided
