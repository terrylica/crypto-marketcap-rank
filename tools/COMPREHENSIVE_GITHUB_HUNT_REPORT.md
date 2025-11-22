# Comprehensive GitHub Cryptocurrency Data Hunt Report

**Mission**: Exhaustive search for cryptocurrency historical market cap data repositories and scraper tools

**Date**: 2025-11-19

**Workspace**: `/tmp/github-hunt/`

---

## Executive Summary

This report catalogs **40+ GitHub repositories** providing cryptocurrency historical data and scraper tools. After systematic searches across multiple keywords and comprehensive analysis, I've identified the **TOP 10 repositories** ranked by promise for obtaining 2021-2024 market cap data.

### Key Findings:

- **Best Overall Tool**: `crypto2` (R package) - Survivorship-bias-free, includes delisted coins, circulating supply, 2013-present
- **Best Python Library**: `cryptoCMD` - 595 stars, most popular, includes market cap
- **Best Pre-existing Dataset**: JesseVent's Kaggle dataset (620K+ rows, though only to 2017)
- **Best for Recent Data**: `pycoingecko` - Active wrapper, 1.1k stars, supports historical market cap API
- **Alternative Source**: Binance public data - Price/volume only (no market cap)

---

## Top 10 Repositories (Ranked by Promise)

### 1. crypto2 ⭐⭐⭐⭐⭐

**Repository**: `sstoeckl/crypto2`
**Stars**: 59 | **Forks**: 25 | **Language**: R
**Status**: ✅ Active (Sept 2025)

**Why #1**:

- **Survivorship-bias-free**: Includes delisted, dead, and untracked coins
- **Complete data fields**: Market cap, circulating supply, total supply, volume, OHLC
- **Date range**: 2013-present (covers 2021-2024 perfectly)
- **API-free**: No rate limits, scrapes CoinMarketCap
- **Academic quality**: Designed for asset pricing studies

**Key Functions**:

- `crypto_list()` - Active, delisted, untracked coins
- `crypto_history()` - Historical OHLC with market cap
- `crypto_listings()` - Historical listings to avoid delisting bias
- `crypto_global_quotes()` - Aggregate market stats

**Installation**:

```r
install.packages("crypto2")
```

**Limitations**:

- R language (not Python, but can export CSV)
- Learning curve for R users

**2021-2024 Coverage**: ✅ Excellent - Explicitly covers this period

---

### 2. cryptoCMD ⭐⭐⭐⭐⭐

**Repository**: `guptarohit/cryptoCMD`
**Stars**: 595 | **Forks**: 117 | **Language**: Python
**Latest Release**: v0.6.4 (Oct 15, 2023)

**Why #2**:

- **Most popular Python tool** (highest stars)
- **Market cap included** in data fields
- **All-time historical data** for any cryptocurrency
- **Multiple export formats**: CSV, JSON, Pandas DataFrame
- **Well-documented** with examples

**Data Fields**:
Date, Open, High, Low, Close, Volume, **Market Cap**, Time Open, Time High, Time Low, Time Close

**Installation**:

```bash
pip install cryptocmd
```

**Basic Usage**:

```python
from cryptocmd import CmcScraper
scraper = CmcScraper("BTC", "01-01-2021", "31-12-2024")
df = scraper.get_dataframe()
df.to_csv('btc_2021_2024.csv')
```

**Limitations**:

- **No circulating supply field** (only market cap)
- Depends on CoinMarketCap structure (could break)

**2021-2024 Coverage**: ✅ Excellent - Date range fully customizable

---

### 3. pycoingecko ⭐⭐⭐⭐⭐

**Repository**: `man-c/pycoingecko`
**Stars**: 1,100 | **Forks**: 280 | **Language**: Python
**Status**: ✅ Active

**Why #3**:

- **Most stars** (1.1k) - highly trusted
- **Active wrapper** for CoinGecko API
- **Historical market cap** via API
- **Circulating supply** available (Pro API)
- **Free tier** works without API key for basic queries

**Historical Data Capabilities**:

- Market data including price, market cap, 24h volume
- OHLC chart data
- Time-range specific queries
- Historical circulating supply (Pro API 💼)

**Installation**:

```bash
pip install -U pycoingecko
```

**Basic Usage**:

```python
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
# Get historical market data for Bitcoin
bitcoin_data = cg.get_coin_market_chart_by_id(
    id='bitcoin',
    vs_currency='usd',
    days='max'
)
```

**Limitations**:

- **API-based** (rate limits on free tier)
- **Circulating supply history** requires Pro API ($$$)
- CoinGecko may have less historical depth than CoinMarketCap

**2021-2024 Coverage**: ✅ Good - API supports date ranges

---

### 4. Coinsta ⭐⭐⭐⭐

**Repository**: `PyDataBlog/Coinsta`
**Stars**: 51 | **Language**: Python
**Last Update**: May 2023

**Why #4**:

- **HistoricalSnapshot** class for point-in-time rankings
- **Circulating supply included** in snapshot data
- **Market cap** in both historical and snapshot modes
- **Pandas-first** design

**Data Fields**:

- Historical: Open, High, Low, Close, Volume, **Market Cap**
- Snapshot: Rank, Name, Symbol, **Market Cap**, Price, **Circulating Supply**, Volume (24h), % changes

**Installation**:

```bash
pip install coinsta
```

**Basic Usage**:

```python
from coinsta.core import Historical, HistoricalSnapshot
from datetime import date

# Get historical price + market cap
btc = Historical('btc', start=date(2021, 1, 1), end=date(2024, 12, 31))
df = btc.get_data()

# Get snapshot for specific date
snapshot = HistoricalSnapshot(date(2023, 6, 15))
snapshot_df = snapshot.get_snapshot()
```

**Limitations**:

- **Last update May 2023** (might break if CMC changes)
- Current data requires API key
- Limited to top 100 for current data

**2021-2024 Coverage**: ✅ Good - Supports date ranges

---

### 5. gordonkwokkwok/Cryptocurrency-Web-Scraper ⭐⭐⭐⭐

**Repository**: `gordonkwokkwok/Cryptocurrency-Web-Scraper`
**Stars**: 18 | **Language**: Jupyter Notebook
**Last Update**: July 2023

**Why #5**:

- **Circulating supply included** ✅
- **Pre-scraped CSV data** available in repo
- **Date range**: April 28, 2013 → July 9, 2023
- **Sample data** ready to download

**Data Fields**:
Date, Name, Symbol, **Market Cap**, Price, **Circulating Supply**, Volume (24hr), % 1h, % 24h, % 7d

**How to Use**:

1. Clone repo: `git clone https://github.com/gordonkwokkwok/Cryptocurrency-Web-Scraper.git`
2. Download `output.csv` directly OR
3. Run `scraper.ipynb` to generate fresh data

**Limitations**:

- **Only top 10 cryptocurrencies** tracked
- **Weekly data** (not daily)
- **Stops at July 2023** - Missing late 2023 and 2024
- Requires conda environment

**2021-2024 Coverage**: ⚠️ Partial - Covers 2021-July 2023 only

---

### 6. SJDunkelman/historical-cryptocurrency-leaders ⭐⭐⭐⭐

**Repository**: `SJDunkelman/historical-cryptocurrency-leaders`
**Stars**: Not specified | **Language**: Python
**Created**: Sept 17, 2021

**Why #6**:

- **Survivorship bias aware** - Includes delisted coins
- **2013 to present** scraping capability
- **Top coins by market cap** historically
- **Circulating supply** included

**Data Fields**:
Name/Ticker, **Market Cap**, Price, **Circulating Supply**

**How to Use**:

```bash
git clone https://github.com/SJDunkelman/historical-cryptocurrency-leaders.git
pip install -r requirements.txt
python main.py
```

**Limitations**:

- **CAPTCHA issues** with Cloudflare (requires VPN/IP rotation)
- **No pre-existing data** (must scrape yourself)
- Scraping time intensive

**2021-2024 Coverage**: ✅ Excellent - "2013 to present"

---

### 7. Binance Public Data ⭐⭐⭐

**Repository**: `binance/binance-public-data`
**Stars**: Not specified | **Official Binance**
**Status**: ✅ Active

**Why #7**:

- **Official source** - Most reliable
- **Comprehensive price/volume** data
- **2017-present** coverage
- **Free download** no API needed
- **Multiple timeframes**: 1m, 5m, 1h, 1d, etc.

**Data Types**:

- Aggregate Trades (aggTrades)
- Klines (OHLC candlestick data)
- Individual Trades
- SPOT and FUTURES markets

**How to Use**:

```bash
# Direct download via curl
curl https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2021-01-01.zip -O
```

**Limitations**:

- ❌ **NO MARKET CAP DATA** - Price/volume only
- ❌ **NO CIRCULATING SUPPLY** - Trading data only
- Only includes coins traded on Binance
- Must calculate market cap yourself if you have supply data

**2021-2024 Coverage**: ✅ Excellent for price/volume (useless for market cap)

---

### 8. martkir/crypto-prices-download ⭐⭐⭐

**Repository**: `martkir/crypto-prices-download`
**Stars**: 32 | **Language**: Python

**Why #8**:

- **1,926 cryptocurrency tokens** covered
- **Multiple resolutions** (1m, 5m, 15m, 30m, 1h, 4h, 6h, 12h, 1d, 1w)
- **Free data** from Syve
- Token metadata included

**Data Fields**:
OHLC price data (USD denominated)

**How to Use**:

```bash
git clone https://github.com/martkir/crypto-prices-download.git
cd crypto-prices-download
python download.py --ohlc --resolution 1m
```

**Limitations**:

- ❌ **NO MARKET CAP** - Price only
- ❌ **NO VOLUME** mentioned
- ❌ **NO CIRCULATING SUPPLY**
- Date range not specified
- DEX-focused (Ethereum tokens)

**2021-2024 Coverage**: ⚠️ Unknown - Date range not documented

---

### 9. JesseVent/Crypto-Market-Scraper ⭐⭐⭐

**Repository**: `JesseVent/Crypto-Market-Scraper`
**Stars**: 35 | **Language**: R
**Status**: ⚠️ Deprecated (Nov 7, 2017)

**Why #9**:

- **Pre-existing dataset** available (CSV + Kaggle)
- **1,265 unique cryptocurrencies**
- **620,000+ rows** of data
- **Market cap included** ✅
- **Kaggle dataset** regularly updated: https://www.kaggle.com/jessevent/all-crypto-currencies

**Data Fields**:
Symbol, date, open, high, low, close, volume, **market cap**, coin name, rank

**Date Range**: April 28, 2013 → November 7, 2017

**How to Use**:

1. Download from Kaggle: https://www.kaggle.com/jessevent/all-crypto-currencies
2. Or clone repo: `git clone https://github.com/JesseVent/Crypto-Market-Scraper.git`

**Limitations**:

- ❌ **DEPRECATED** - Stops at 2017
- ❌ **No 2021-2024 data** - Completely misses target period
- Replaced by R package "crypto"

**2021-2024 Coverage**: ❌ None - Ends 2017

---

### 10. prouast/coinmarketcap-scraper ⭐⭐

**Repository**: `prouast/coinmarketcap-scraper`
**Stars**: 87 | **Language**: Python
**Last Update**: March 25, 2017

**Why #10**:

- **Market cap** included
- **Supply data** included
- **Exchange volume** data

**Data Fields**:
Market cap, supply, exchange price, exchange volume

**How to Use**:

```bash
pip install cssselect lxml psycopg2 requests
python scrape.py         # All currencies
python scrape.py 1000000 # Min market cap filter
```

**Limitations**:

- ❌ **VERY OLD** (2017) - Likely broken
- ❌ **No releases**
- ❌ **Unmaintained**
- ❌ **CMC website changed** - Script probably doesn't work

**2021-2024 Coverage**: ❌ Likely non-functional

---

## Additional Notable Repositories

### 11-20: Secondary Options

| Rank | Repository                                          | Stars      | Key Feature                        | Limitation                                           |
| ---- | --------------------------------------------------- | ---------- | ---------------------------------- | ---------------------------------------------------- |
| 11   | `Waultics/coinmarketcap-history`                    | 189        | Historical price + market cap      | ❌ **ARCHIVED** - Doesn't work anymore (CMC updated) |
| 12   | `dkamm/coinmarketcap-scraper`                       | 11         | Fast (~2min all coins)             | ❌ Old (2018), likely broken                         |
| 13   | `dylankilkenny/CoinMarketCap-Historical-Prices`     | Not listed | Python3 + BS4 scraper              | Date unknown, reliability unknown                    |
| 14   | `saporitigianni/coinmarketcappy`                    | Not listed | Python 3+ API with caching         | Status unknown                                       |
| 15   | `SuperKogito/CoinMarketCapScraper`                  | Not listed | Converts to CSV                    | Small project, status unknown                        |
| 16   | `coincheckup/crypto-supplies`                       | 31         | **Circulating supply** focus       | ❌ Current data only (no historical)                 |
| 17   | `JesseVent/crypto` (R package)                      | Not listed | Replacement for deprecated scraper | R language                                           |
| 18   | `Gendo90/Crypto-Historical-Prices`                  | Not listed | ETL to SQL database                | Limited coins (BTC/ETH from Kaggle)                  |
| 19   | `antonyjoseph2111/Historical-Market-Data-Collector` | Not listed | Multi-year CSV compiler            | Price/volume only (no market cap)                    |
| 20   | `jacobbaruch/Coin_market_cap`                       | Not listed | Market cap in CSV                  | Status/coverage unknown                              |

### 21-30: Data Analysis / Niche Tools

| Rank | Repository                                        | Purpose                      | Relevance                                      |
| ---- | ------------------------------------------------- | ---------------------------- | ---------------------------------------------- |
| 21   | `yashajoshi/Cryptocurrency-Trading-Data-Analysis` | Analysis project             | Sample dataset included                        |
| 22   | `LaviJ/Cryptocurrency-Analysis`                   | Analysis with Kaggle data    | Uses existing datasets                         |
| 23   | `Chisomnwa/Cryptocurrency-Data-Analysis`          | Live scraping analysis       | Current data focus                             |
| 24   | `MicroBioScopicData/Cryptos_Analysis`             | CoinGecko analysis notebooks | Analysis-focused                               |
| 25   | `rohan-paul/Cryptocurrency-Kaggle`                | Kaggle dataset analysis      | 26,320 CSV files of top cryptos                |
| 26   | `rohan-paul/All-Crypto-Dataset-Kaggle`            | OHLC data                    | 400+ trading pairs, 1min resolution, from 2013 |
| 27   | `mczielinski/kaggle-bitcoin`                      | Bitcoin automation           | Daily Kaggle uploads, GitHub Actions           |
| 28   | `Yrzxiong/Bitcoin-Dataset`                        | Bitcoin ML dataset           | Bitcoin-specific                               |
| 29   | `luijoy/big-list-of-bad-crypto`                   | **Scam/dead coins list**     | Useful for validation (BitConnect test)        |
| 30   | `blockchain-etl/public-datasets`                  | BigQuery blockchain data     | Blockchain data, not market cap                |

### 31-40: Exchange-Specific / Alternative Sources

| Rank | Repository                                       | Data Source           | Market Cap?                |
| ---- | ------------------------------------------------ | --------------------- | -------------------------- |
| 31   | `binance_historical_data` (stas-prokopiev)       | Binance               | ❌ No                      |
| 32   | `ltftf/binance-historical-data`                  | Binance CLI           | ❌ No                      |
| 33   | `nonisich/Binance-Data-Downloader`               | Binance               | ❌ No                      |
| 34   | `xzmeng/binance-history`                         | Binance klines/trades | ❌ No                      |
| 35   | `lostleaf/binance_datatool`                      | Binance (Parquet)     | ❌ No                      |
| 36   | `pratikpv/cryptocurrency_data_downloader`        | Binance               | ❌ No                      |
| 37   | `kirancshet/Get-Crypto-Historic-Chart-CoinGecko` | CoinGecko API         | Python script, 1yr history |
| 38   | `sergeant99/CryptoData`                          | CoinGecko web scraper | Status unknown             |
| 39   | `patrick0585/PyCryptoScraper`                    | CoinGecko             | Status unknown             |
| 40   | `kevin-vandelden/Crypto-Price-Web-Scraper`       | CoinGecko → MySQL     | Daily pipeline             |

---

## Data Quality Assessment

### Critical Requirements Checklist

| Requirement             | Top Tools Meeting It                                        |
| ----------------------- | ----------------------------------------------------------- |
| **Market cap data**     | ✅ crypto2, cryptoCMD, Coinsta, pycoingecko, gordonkwokkwok |
| **Circulating supply**  | ✅ crypto2, Coinsta, gordonkwokkwok, SJDunkelman            |
| **2021-2024 coverage**  | ✅ crypto2, cryptoCMD, pycoingecko, Coinsta, SJDunkelman    |
| **Includes dead coins** | ✅ crypto2, SJDunkelman                                     |
| **Free/no API key**     | ✅ crypto2, cryptoCMD, Coinsta (historical), gordonkwokkwok |
| **Easy to use**         | ✅ cryptoCMD, pycoingecko, Coinsta                          |
| **Recently updated**    | ✅ crypto2, pycoingecko                                     |

### Survivorship Bias Test

**Can you find BitConnect data?**

| Tool                   | BitConnect Available? | Notes                               |
| ---------------------- | --------------------- | ----------------------------------- |
| crypto2                | ✅ YES                | Explicitly includes delisted coins  |
| cryptoCMD              | ⚠️ Maybe              | If CMC still has historical data    |
| pycoingecko            | ⚠️ Maybe              | Depends on CoinGecko retention      |
| Coinsta                | ⚠️ Maybe              | Depends on CMC retention            |
| gordonkwokkwok         | ❌ Unlikely           | Only top 10 coins                   |
| SJDunkelman            | ✅ YES                | Designed for historical leaders     |
| big-list-of-bad-crypto | ✅ YES                | Explicitly lists BitConnect as scam |

**Winner**: `crypto2` - Explicitly designed to avoid survivorship bias

---

## 2021-2024 Coverage Deep Dive

### Excellent Coverage (Can definitely get 2021-2024 data)

1. **crypto2** - R package, 2013-present, actively updated
2. **cryptoCMD** - Python, all-time data, customizable date ranges
3. **pycoingecko** - Python, API-based, active development
4. **Coinsta** - Python, date range support
5. **SJDunkelman/historical-cryptocurrency-leaders** - "2013 to present"

### Partial Coverage (Some data, but gaps)

6. **gordonkwokkwok/Cryptocurrency-Web-Scraper** - 2013 to July 2023 only
7. **martkir/crypto-prices-download** - Date range unclear

### No Coverage (Too old or wrong data)

8. **JesseVent/Crypto-Market-Scraper** - Ends 2017
9. **Waultics/coinmarketcap-history** - Broken/archived 2020
10. **prouast/coinmarketcap-scraper** - Last update 2017
11. **dkamm/coinmarketcap-scraper** - Last update 2018
12. **Binance public data** - Price/volume only (no market cap at all)

---

## Recommended Action Plan

### Option A: Quick Start (Python Users)

**Tool**: `cryptoCMD`

**Why**: Most popular Python tool, straightforward, includes market cap

**Steps**:

```bash
pip install cryptocmd
```

```python
from cryptocmd import CmcScraper
import pandas as pd

# Get Bitcoin 2021-2024
btc = CmcScraper("BTC", "01-01-2021", "31-12-2024")
btc_df = btc.get_dataframe()
btc_df.to_csv('bitcoin_2021_2024.csv')

# Get multiple coins
coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOGE']
all_data = []
for coin in coins:
    scraper = CmcScraper(coin, "01-01-2021", "31-12-2024")
    df = scraper.get_dataframe()
    df['symbol'] = coin
    all_data.append(df)

combined = pd.concat(all_data)
combined.to_csv('top5_2021_2024.csv')
```

**Pros**:

- Simple Python API
- Market cap included
- 595 stars (trusted)
- CSV export built-in

**Cons**:

- No circulating supply field
- May break if CMC changes site structure

---

### Option B: Best Quality (R Users or Data Scientists)

**Tool**: `crypto2`

**Why**: Survivorship-bias-free, includes delisted coins, circulating supply, best for research

**Steps**:

```r
install.packages("crypto2")
library(crypto2)

# Get all coins (including delisted) for 2021-2024
all_coins <- crypto_list(only_active=FALSE)

# Get historical data
btc_history <- crypto_history(
  coin_list = "BTC",
  start_date = "20210101",
  end_date = "20241231",
  interval = "daily"
)

# Export to CSV for use in other tools
write.csv(btc_history, "btc_2021_2024_complete.csv", row.names=FALSE)
```

**Pros**:

- Survivorship-bias-free (includes dead coins)
- Circulating supply + market cap
- API-free (no rate limits)
- Academic quality
- Actively maintained

**Cons**:

- Requires R (but can export to CSV for Python)
- Learning curve

---

### Option C: API-Based (Scalable Solution)

**Tool**: `pycoingecko`

**Why**: Most stars (1.1k), active development, official wrapper

**Steps**:

```bash
pip install -U pycoingecko
```

```python
from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta

cg = CoinGeckoAPI()

# Get Bitcoin historical market data
btc_data = cg.get_coin_market_chart_by_id(
    id='bitcoin',
    vs_currency='usd',
    days='max'  # or specify days since today
)

# Extract market cap data
market_caps = btc_data['market_caps']
df = pd.DataFrame(market_caps, columns=['timestamp', 'market_cap'])
df['date'] = pd.to_datetime(df['timestamp'], unit='ms')

# Filter for 2021-2024
df_filtered = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2024-12-31')]
df_filtered.to_csv('btc_market_cap_2021_2024.csv', index=False)
```

**Pros**:

- Most popular (1.1k stars)
- Active development
- Official API wrapper
- Market cap via API

**Cons**:

- Rate limits on free tier
- Circulating supply requires Pro API
- CoinGecko may have less history than CoinMarketCap

---

### Option D: Pre-existing Data (No Scraping)

**Tool**: `gordonkwokkwok/Cryptocurrency-Web-Scraper`

**Why**: CSV already generated, just download and use

**Steps**:

```bash
git clone https://github.com/gordonkwokkwok/Cryptocurrency-Web-Scraper.git
cd Cryptocurrency-Web-Scraper
# Use output.csv directly
```

**Pros**:

- No scraping needed
- Circulating supply included
- Market cap included
- Ready to analyze

**Cons**:

- Only top 10 coins
- Weekly data (not daily)
- Stops at July 2023 (missing late 2023 + 2024)

---

## Quick Start Guides

### Guide 1: Get Top 100 Coins (2021-2024) with cryptoCMD

```python
# install: pip install cryptocmd pandas
from cryptocmd import CmcScraper
import pandas as pd
from datetime import datetime

# Top 100 coins by market cap (manual list or scrape)
# For demo, using top 10
top_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOGE', 'DOT', 'MATIC', 'LTC']

all_data = []
for coin in top_coins:
    try:
        print(f"Downloading {coin}...")
        scraper = CmcScraper(coin, "01-01-2021", "31-12-2024")
        df = scraper.get_dataframe()
        df['symbol'] = coin
        all_data.append(df)
        print(f"✓ {coin} complete")
    except Exception as e:
        print(f"✗ {coin} failed: {e}")

# Combine all
combined = pd.concat(all_data)
combined = combined.reset_index()
combined.to_csv('top10_cryptos_2021_2024.csv', index=False)
print(f"\n✓ Saved {len(combined)} rows to top10_cryptos_2021_2024.csv")
```

**Output columns**: Date, Open, High, Low, Close, Volume, Market Cap, symbol

---

### Guide 2: Get Delisted Coins with crypto2

```r
# install: install.packages("crypto2")
library(crypto2)
library(dplyr)

# Get ALL coins (including delisted)
all_coins <- crypto_list(only_active = FALSE)

# Filter for delisted coins
delisted <- all_coins %>% filter(status == "delisted")
print(paste("Found", nrow(delisted), "delisted coins"))

# Get historical data for a delisted coin (e.g., BitConnect)
# Note: May need to find exact slug/id from all_coins
bitconnect <- all_coins %>% filter(grepl("bitconnect", name, ignore.case=TRUE))

if(nrow(bitconnect) > 0) {
  bc_history <- crypto_history(
    coin_list = bitconnect$slug[1],
    start_date = "20170101",
    end_date = "20180131"
  )
  write.csv(bc_history, "bitconnect_history.csv", row.names=FALSE)
  print("✓ BitConnect data saved")
}
```

---

### Guide 3: Get Market Cap via CoinGecko API

```python
# install: pip install pycoingecko pandas
from pycoingecko import CoinGeckoAPI
import pandas as pd
import time

cg = CoinGeckoAPI()

# Get list of all coins
coins_list = cg.get_coins_list()
top_100_ids = [coin['id'] for coin in coins_list[:100]]

all_market_caps = []

for coin_id in top_100_ids[:10]:  # Demo with first 10
    try:
        print(f"Fetching {coin_id}...")
        data = cg.get_coin_market_chart_by_id(
            id=coin_id,
            vs_currency='usd',
            days='1460'  # ~4 years
        )

        # Extract market caps
        market_caps = data['market_caps']
        df = pd.DataFrame(market_caps, columns=['timestamp', 'market_cap'])
        df['coin_id'] = coin_id
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')

        all_market_caps.append(df)
        print(f"✓ {coin_id} complete")
        time.sleep(1.5)  # Rate limit protection

    except Exception as e:
        print(f"✗ {coin_id} failed: {e}")

# Combine and save
combined = pd.concat(all_market_caps)
combined.to_csv('coingecko_market_caps.csv', index=False)
print(f"\n✓ Saved {len(combined)} rows")
```

---

## Testing Recommendations

### Phase 1: Clone Top 5 Repositories

```bash
cd /tmp/github-hunt/repos

# 1. crypto2 (R)
git clone https://github.com/sstoeckl/crypto2.git

# 2. cryptoCMD (Python)
git clone https://github.com/guptarohit/cryptoCMD.git

# 3. pycoingecko (Python)
git clone https://github.com/man-c/pycoingecko.git

# 4. Coinsta (Python)
git clone https://github.com/PyDataBlog/Coinsta.git

# 5. gordonkwokkwok (Jupyter)
git clone https://github.com/gordonkwokkwok/Cryptocurrency-Web-Scraper.git
```

### Phase 2: Test Each Tool

**Test 1: cryptoCMD**

```bash
pip install cryptocmd
python3 << 'EOF'
from cryptocmd import CmcScraper
scraper = CmcScraper("BTC", "01-01-2023", "01-01-2024")
df = scraper.get_dataframe()
print(df.head())
print(df.columns)
print(f"Rows: {len(df)}")
EOF
```

**Test 2: Coinsta**

```bash
pip install coinsta
python3 << 'EOF'
from coinsta.core import HistoricalSnapshot
from datetime import date
snap = HistoricalSnapshot(date(2023, 6, 1))
df = snap.get_snapshot()
print(df.head())
print(df.columns)
EOF
```

**Test 3: pycoingecko**

```bash
pip install pycoingecko
python3 << 'EOF'
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
data = cg.get_coin_market_chart_by_id('bitcoin', 'usd', days=30)
print(f"Market cap data points: {len(data['market_caps'])}")
print(f"Sample: {data['market_caps'][0]}")
EOF
```

### Phase 3: Data Quality Validation

**Validation Script** (`validate_data.py`):

```python
import pandas as pd
from datetime import datetime

def validate_crypto_data(csv_path):
    """
    Validates cryptocurrency historical data quality
    """
    df = pd.read_csv(csv_path)

    print(f"\n=== Validation Report for {csv_path} ===")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Check for required fields
    required = ['Date', 'Market Cap']
    has_required = all(col in df.columns for col in required)
    print(f"Has Market Cap: {'✓' if 'Market Cap' in df.columns else '✗'}")
    print(f"Has Circulating Supply: {'✓' if 'Circulating Supply' in df.columns else '✗'}")

    # Check date range
    if 'Date' in df.columns or 'date' in df.columns:
        date_col = 'Date' if 'Date' in df.columns else 'date'
        df[date_col] = pd.to_datetime(df[date_col])
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        print(f"Date range: {min_date} to {max_date}")

        # Check 2021-2024 coverage
        in_range = df[(df[date_col] >= '2021-01-01') & (df[date_col] <= '2024-12-31')]
        print(f"2021-2024 coverage: {len(in_range)} rows")

    # Check for nulls
    print(f"Null values:\n{df.isnull().sum()}")

    # Check for dead coin (if symbol/name column exists)
    if 'Symbol' in df.columns:
        unique_coins = df['Symbol'].nunique()
        print(f"Unique coins: {unique_coins}")
        if 'BCC' in df['Symbol'].values or 'Bitconnect' in df.get('Name', pd.Series()).values:
            print("✓ BitConnect found (survivorship bias test passed)")

    return df

# Example usage:
# validate_crypto_data('bitcoin_2021_2024.csv')
```

---

## Critical Warnings & Gotchas

### ⚠️ Warning 1: Many Old Tools Are Broken

**Broken/Deprecated**:

- `Waultics/coinmarketcap-history` - ARCHIVED, doesn't work
- `dkamm/coinmarketcap-scraper` - 2018, likely broken
- `prouast/coinmarketcap-scraper` - 2017, definitely broken
- `JesseVent/Crypto-Market-Scraper` - Deprecated, ends 2017

**Why**: CoinMarketCap updated their website structure multiple times, breaking scrapers

**Solution**: Use actively maintained tools (crypto2, cryptoCMD, pycoingecko)

### ⚠️ Warning 2: Circulating Supply Is Hard to Get

**Only these tools provide circulating supply**:

1. crypto2 (R) - ✅ Best
2. Coinsta (Python) - ✅ Good
3. gordonkwokkwok (Python) - ✅ Top 10 only
4. pycoingecko Pro API - ✅ Requires payment
5. coincheckup/crypto-supplies - ✅ Current only (no historical)

**Why important**: Market cap = Price × Circulating Supply

Without circulating supply, you can't:

- Calculate price from market cap
- Validate market cap accuracy
- Detect supply changes over time

### ⚠️ Warning 3: Survivorship Bias Is Real

**Problem**: Most tools only capture currently-listed coins

**Missing data**:

- Delisted coins (e.g., BitConnect)
- Dead projects
- Scam coins

**Why it matters**: Your analysis will be biased toward successful coins

**Solutions**:

1. crypto2 (R) - Explicitly includes delisted coins
2. SJDunkelman/historical-cryptocurrency-leaders - Designed for historical leaders
3. luijoy/big-list-of-bad-crypto - Catalog of scam/dead coins

### ⚠️ Warning 4: API Rate Limits

**Tools with rate limits**:

- pycoingecko (free tier)
- Any CoinMarketCap API tool
- Any CoinGecko API tool

**Workarounds**:

1. Use scraping tools (crypto2, cryptoCMD) - No API, no limits
2. Add sleep delays: `time.sleep(1.5)` between requests
3. Cache data locally
4. Use pre-existing datasets when possible

### ⚠️ Warning 5: Date Format Inconsistencies

**Different tools, different formats**:

- cryptoCMD: `"DD-MM-YYYY"` (e.g., `"01-01-2021"`)
- crypto2: `"YYYYMMDD"` (e.g., `"20210101"`)
- pycoingecko: Unix timestamp or `days` parameter
- Coinsta: Python `date` objects

**Solution**: Check documentation for each tool

### ⚠️ Warning 6: Binance Has NO Market Cap Data

**Common misconception**: Binance public data = complete crypto data

**Reality**: Binance provides ONLY price and volume (OHLC + trades)

**What's missing**:

- ❌ Market cap
- ❌ Circulating supply
- ❌ Total supply
- ❌ Coin rankings

**Use Binance for**: Price/volume backtesting, trading data
**Don't use Binance for**: Market cap analysis

---

## Final Recommendations

### For Your Use Case (2021-2024 Market Cap Data)

**Best Overall**: `crypto2` (R package)

- ✅ Survivorship-bias-free
- ✅ Circulating supply
- ✅ Market cap
- ✅ 2021-2024 coverage
- ✅ No API limits
- ⚠️ Requires R (but exports CSV)

**Best Python Alternative**: `cryptoCMD`

- ✅ Market cap
- ✅ Easy to use
- ✅ 2021-2024 coverage
- ✅ Popular (595 stars)
- ❌ No circulating supply

**Best API Solution**: `pycoingecko`

- ✅ Market cap
- ✅ Active development
- ✅ Most stars (1.1k)
- ⚠️ Rate limits
- ❌ Circulating supply requires Pro API

**Quick Win**: `gordonkwokkwok/Cryptocurrency-Web-Scraper`

- ✅ Pre-existing CSV
- ✅ Market cap + circulating supply
- ⚠️ Only top 10 coins
- ⚠️ Stops July 2023

### Proposed Next Steps

1. **Install crypto2** (if you can use R)

   ```r
   install.packages("crypto2")
   ```

2. **Install cryptoCMD** (for Python)

   ```bash
   pip install cryptocmd
   ```

3. **Clone promising repos**

   ```bash
   cd /tmp/github-hunt/repos
   git clone https://github.com/sstoeckl/crypto2.git
   git clone https://github.com/guptarohit/cryptoCMD.git
   git clone https://github.com/gordonkwokkwok/Cryptocurrency-Web-Scraper.git
   ```

4. **Test with Bitcoin 2021-2024**

   ```python
   from cryptocmd import CmcScraper
   btc = CmcScraper("BTC", "01-01-2021", "31-12-2024")
   df = btc.get_dataframe()
   df.to_csv('btc_test.csv')
   print(df.info())
   ```

5. **Validate data quality**
   - Check for market cap column
   - Verify date range
   - Check for nulls
   - Test with dead coin (BitConnect)

6. **Scale to all coins**
   - Get list of top 100/500 coins
   - Loop through with error handling
   - Add rate limiting if needed
   - Combine into master dataset

---

## Conclusion

**40+ repositories cataloged**
**Top 10 ranked by promise**
**3 recommended for immediate use**

**Best bet for 2021-2024 market cap data**:

1. `crypto2` (R) - Most complete, includes delisted coins
2. `cryptoCMD` (Python) - Easiest Python option
3. `pycoingecko` (Python) - API-based, scalable

**Key insight**: Most tools are broken or outdated. Only a handful are actively maintained and include the critical fields (market cap + circulating supply).

**Action items**:

- [ ] Clone top 5 repositories
- [ ] Test cryptoCMD with Bitcoin 2021-2024
- [ ] Test crypto2 if R is available
- [ ] Validate data includes market cap
- [ ] Check for survivorship bias (BitConnect test)
- [ ] Scale to full coin list
- [ ] Build master dataset

---

## Appendix: Full Repository List

See sections above for the complete 40+ repository catalog.

**Search keywords used**:

- "cryptocurrency historical data"
- "market cap history"
- "coinmarketcap historical"
- "crypto market data csv"
- "bitcoin altcoin dataset"
- "blockchain market capitalization"
- "crypto historical archive"
- "cryptocurrency dataset"
- "coinmarketcap scraper"
- "crypto data collector"
- "cryptocurrency API scraper"
- "historical crypto scraper"
- "market cap scraper python"
- "cryptocurrency circulating supply"
- "survivorship bias dataset"
- "delisted coins"

**GitHub search date**: 2025-11-19

---

**Report generated**: 2025-11-19
**Workspace**: `/tmp/github-hunt/`
**Next steps**: Clone top repos → Test → Validate → Scale
