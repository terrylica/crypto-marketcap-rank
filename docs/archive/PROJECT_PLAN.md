# Cryptocurrency Historical Market Cap Download Project

**Project Goal:** Download daily historical market cap data for all cryptocurrencies, generate rankings, export to CSV

**Created:** 2025-11-19
**Workspace:** ~/eon/crypto-marketcap-rank/

---

## User Requirements (Final Clarified)

1. **Scope:** All 18,637+ cryptocurrencies available
2. **Time Range:** Maximum historical data available (varies by coin, up to 15 years)
3. **Output Format:** Single CSV file with all coins combined
4. **Data Fields Required:**
   - Date
   - Symbol (coin ticker)
   - Price (USD)
   - Market Cap (USD) - **PRIMARY FOCUS**
   - Volume (24h trading volume)
   - **Daily Rank by market cap** (calculated)

5. **Collection Strategy:**
   - Get ALL coins first (discovery phase)
   - Download historical data for each
   - Filter to top 500 per day during analysis
   - Single-threaded (avoid rate limits)
   - Resume-able (50-100 hour download acceptable)

6. **Focus:** Market cap is the ONLY metric that matters - price/volume are supplementary

---

## Research Findings Summary

### APIs Investigated (5 total)

#### ❌ **CoinGecko**

- **Verdict:** NOT SUITABLE
- **Reason:** Free tier hard-limited to 365 days
- **Paid Option:** $129-499/month for historical data
- **Research:** `/research/coingecko-marketcap-probe/`

#### ❌ **CoinCap**

- **Verdict:** NOT SUITABLE
- **Reason:** No market cap field in API responses (price only)
- **Historical Depth:** Excellent (13+ years) but missing market cap
- **Research:** `/research/coincap-probe/`

#### ❌ **Messari**

- **Verdict:** NOT SUITABLE
- **Reason:** All historical endpoints require Enterprise plan ($5000+/year)
- **Free Tier:** Only current data, no historical market cap
- **Research:** `/research/messari-probe/`

#### ⚠️ **CryptoCompare**

- **Verdict:** USABLE (with caveats)
- **Has:** 15 years of price data, free, 18,637 coins
- **Missing:** Direct market cap field
- **Workaround:** Can estimate market cap (price × approximate supply)
- **Research:** `/research/free-crypto-historical/` & `/research/coinpaprika-probe/`

#### ✅ **Kaggle Datasets**

- **Verdict:** BEST for verified market cap (2013-2021)
- **Coverage:** 4,000+ coins with REAL market cap values
- **Date Range:** April 2013 - August 2021 (8 years)
- **File Size:** 820 MB
- **Research:** `/research/kaggle-datasets-search/`

### Other Sources Investigated

- **CryptoDataDownload:** Bitcoin-only market cap (other coins via OHLCV + manual calc)
- **Academic Sources:** 50+ datasets catalogued in `/research/academic-sources-search/`
- **GitHub/Public:** Various partial datasets available

---

## Recommended Hybrid Approach

### Phase 1: Download Kaggle Dataset (FAST)

**Time:** 5-10 minutes
**Source:** "Coinmarketcap Historical Data" by bizzyvinci
**Output:** 4,000 coins with verified market cap (2013-2021)
**Accuracy:** ✅ HIGH - Real historical market cap values

### Phase 2: Download CryptoCompare Data (SLOW)

**Time:** 50-100 hours (single-threaded)
**Source:** CryptoCompare API
**Output:** 18,637 coins with price/volume (2010-2025)
**Accuracy:** ⚠️ ESTIMATED market cap (price × current supply approximation)

### Phase 3: Merge & Calculate Rankings

**Time:** 30-60 minutes
**Process:** Combine datasets, calculate daily rankings
**Output:** Final CSV with complete historical market cap rankings

---

## Technical Implementation Plan

### Script 1: `download_kaggle.py`

```python
# Download Kaggle dataset via API
# Extract CSV files
# Standardize format
# Output: data/kaggle_marketcap_2013_2021.csv
```

### Script 2: `download_cryptocompare.py`

```python
# Get all 18,637 coin symbols
# For each coin:
#   - Download complete price history
#   - Estimate market cap (price × supply)
#   - Save to incremental CSV
#   - Log progress
# Resume-able from checkpoint
# Output: data/cryptocompare_all_coins.csv
```

### Script 3: `merge_and_rank.py`

```python
# Load Kaggle data (verified market cap)
# Load CryptoCompare data (estimated market cap)
# For overlapping dates: prefer Kaggle
# Calculate daily rankings
# Output: data/crypto_historical_marketcap_ranked.csv
```

---

## Expected Output

### Final CSV Structure

```csv
date,symbol,name,price_usd,volume_24h_usd,market_cap_usd,rank
2013-04-28,BTC,Bitcoin,135.30,0,1500000000,1
2013-04-28,LTC,Litecoin,3.83,0,92000000,2
...
2025-11-19,BTC,Bitcoin,92549.40,341587851,1847245181083,1
2025-11-19,ETH,Ethereum,3038.57,285849271,366997912297,2
```

### File Specifications

- **Estimated rows:** 100-150 million (18,637 coins × ~5,606 days avg)
- **File size uncompressed:** 8-12 GB
- **File size compressed (gzip):** 1-2 GB
- **Coins covered:** All 18,637 available
- **Date range:** 2010-2025 (varies by coin launch)

### Market Cap Accuracy by Period

| Period    | Source        | Accuracy     | Notes                    |
| --------- | ------------- | ------------ | ------------------------ |
| 2013-2021 | Kaggle        | ✅ HIGH      | Real verified market cap |
| 2010-2013 | CryptoCompare | ⚠️ ESTIMATED | Price × current supply   |
| 2021-2025 | CryptoCompare | ⚠️ ESTIMATED | Price × current supply   |

---

## Timeline Estimate

| Phase     | Task                      | Duration      | Effort  |
| --------- | ------------------------- | ------------- | ------- |
| Setup     | Create scripts, test APIs | 2-4 hours     | Active  |
| Phase 1   | Download Kaggle           | 10 min        | Passive |
| Phase 2   | Download 18,637 coins     | 50-100 hours  | Passive |
| Phase 3   | Merge & rank              | 1 hour        | Active  |
| **Total** | **End-to-end**            | **~3-5 days** | Mixed   |

---

## Storage Requirements

- **Working directory:** 20 GB (intermediate files)
- **Final output:** 12 GB (uncompressed CSV)
- **Compressed output:** 2 GB (gzip)
- **Checkpoints:** +3 GB (safety)
- **Research files:** 500 MB (documentation)

---

## Rate Limits & API Constraints

**CryptoCompare:**

- No authentication required
- ~300 requests/hour safe limit
- 100ms delay between requests recommended
- Single-threaded mandatory

**Kaggle:**

- API key required
- No rate limits for datasets
- One-time download

---

## Risk Mitigation

✅ **Resume-able:** Save after each coin, can restart anytime
✅ **Error handling:** Log failures, skip problematic coins, continue
✅ **Progress tracking:** Real-time stats, ETA calculation
✅ **Data validation:** Check for zeros, missing dates, anomalies
✅ **Incremental saves:** Checkpoint every 100 coins

---

## Next Steps

1. ✅ Research complete (5 APIs + 50+ datasets investigated)
2. ⏸️ Awaiting approval to proceed
3. 📝 Implement 3 Python scripts
4. 🚀 Start download process
5. 📊 Generate final ranked CSV

---

## Research Documentation

All findings archived in `/research/` subdirectory:

- API test results
- Sample responses
- Comparison tables
- Source code examples
- Alternative datasets catalog

**Total research artifacts:** ~500 MB, 200+ files
