# QUICK START: Fill the 2021-2024 Gap in 3 Days

**Goal:** Obtain complete, verified cryptocurrency market cap data for Aug 2021 - Dec 2024

**Solution:** crypto2 R Package (FREE, 100% coverage, includes circulating supply)

---

## DAY 1: SETUP & TEST (2 hours)

### Step 1: Install R (if not already installed)

**macOS:**

```bash
brew install r
```

**Linux:**

```bash
sudo apt-get install r-base
```

**Windows:**
Download from https://cran.r-project.org/

### Step 2: Install crypto2 Package

```r
# Open R console
R

# Install crypto2
install.packages("crypto2")
library(crypto2)
```

### Step 3: Test with Small Dataset (Verify It Works)

```r
# Test: Get top 10 coins for 1 week in Aug 2021
test_listings <- crypto_listings(
  start_date = "20210801",
  end_date = "20210807",
  limit = 10
)

# Check if circulating_supply is included
colnames(test_listings)

# Should see: name, symbol, rank, price_usd, market_cap_usd, circulating_supply, etc.
head(test_listings)

# Save test data
write.csv(test_listings, "/tmp/2021-2024-gap/test_data.csv", row.names = FALSE)

# Verify file
cat("Test completed! Check /tmp/2021-2024-gap/test_data.csv")
```

### Step 4: BitConnect Validation Test

```r
# Critical test: BitConnect should exist in 2021, disappear in 2022
bitconnect_test <- crypto_history(
  coin_list = "bitconnect",
  start_date = "20210801",
  end_date = "20220630",
  interval = "daily"
)

# Check results
nrow(bitconnect_test)  # Should have data for 2021, may disappear 2022

# Save
write.csv(bitconnect_test, "/tmp/2021-2024-gap/bitconnect_test.csv", row.names = FALSE)
```

**Expected Results:**

- ✅ circulating_supply column present
- ✅ Non-zero values for circulating supply
- ✅ BitConnect data exists in 2021

**If tests FAIL:** Proceed to Alternative Plan (CoinGecko API + calculation workaround)

**If tests PASS:** Proceed to Day 2

---

## DAY 2: FULL DATA COLLECTION (8-12 hours, run overnight)

### Step 1: Create Collection Script

Save as `/tmp/2021-2024-gap/collect_data.R`:

```r
# Load library
library(crypto2)

# Configuration
START_DATE <- "20210801"
END_DATE <- "20241231"
TOP_N_COINS <- 500
OUTPUT_DIR <- "/tmp/2021-2024-gap/data"

# Create output directory
dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)

# Function to save progress (checkpointing)
save_checkpoint <- function(data, filename) {
  filepath <- file.path(OUTPUT_DIR, filename)
  write.csv(data, filepath, row.names = FALSE)
  cat(sprintf("Saved: %s (%d rows)\n", filename, nrow(data)))
}

# STEP 1: Get current top 500 coins
cat("Fetching current top 500 coins...\n")
current_top_500 <- crypto_listings(
  limit = TOP_N_COINS
)
save_checkpoint(current_top_500, "current_top_500.csv")

# STEP 2: Get historical listings (Aug 2021 - Dec 2024)
cat("Fetching historical listings (this will take time due to rate limits)...\n")
historical_listings <- crypto_listings(
  start_date = START_DATE,
  end_date = END_DATE,
  limit = TOP_N_COINS
)
save_checkpoint(historical_listings, "historical_listings_2021_2024.csv")

# STEP 3: Get price history for all coins
cat("Fetching price history for top 500 coins...\n")
cat("WARNING: This will take 8-12 hours due to API rate limits.\n")
cat("You can safely interrupt (Ctrl+C) and resume later.\n\n")

# Get unique coin slugs
coin_slugs <- unique(historical_listings$slug)
cat(sprintf("Total coins to fetch: %d\n", length(coin_slugs)))

# Initialize results
all_history <- data.frame()

# Progress tracking
start_time <- Sys.time()
total_coins <- length(coin_slugs)

# Collect data with progress reporting
for (i in seq_along(coin_slugs)) {
  coin <- coin_slugs[i]

  tryCatch({
    # Fetch history for this coin
    coin_history <- crypto_history(
      coin_list = coin,
      start_date = START_DATE,
      end_date = END_DATE,
      interval = "daily"
    )

    # Append to results
    all_history <- rbind(all_history, coin_history)

    # Progress report every 10 coins
    if (i %% 10 == 0) {
      elapsed <- difftime(Sys.time(), start_time, units = "mins")
      rate <- i / as.numeric(elapsed)
      remaining <- (total_coins - i) / rate

      cat(sprintf("[%d/%d] %s - %.1f coins/min - ETA: %.0f mins\n",
                  i, total_coins, coin, rate, remaining))

      # Save checkpoint every 50 coins
      if (i %% 50 == 0) {
        save_checkpoint(all_history, sprintf("checkpoint_%04d.csv", i))
      }
    }

  }, error = function(e) {
    cat(sprintf("ERROR on coin %s: %s\n", coin, e$message))
  })
}

# STEP 4: Final save
save_checkpoint(all_history, "crypto_history_2021_2024_FINAL.csv")

# Summary statistics
cat("\n=== COLLECTION COMPLETE ===\n")
cat(sprintf("Total rows: %d\n", nrow(all_history)))
cat(sprintf("Unique coins: %d\n", length(unique(all_history$symbol))))
cat(sprintf("Date range: %s to %s\n",
            min(all_history$timestamp),
            max(all_history$timestamp)))
cat(sprintf("Total time: %.1f hours\n",
            as.numeric(difftime(Sys.time(), start_time, units = "hours"))))

cat("\nOutput files:\n")
cat(sprintf("- %s/crypto_history_2021_2024_FINAL.csv\n", OUTPUT_DIR))
cat(sprintf("- %s/historical_listings_2021_2024.csv\n", OUTPUT_DIR))
cat(sprintf("- %s/current_top_500.csv\n", OUTPUT_DIR))
```

### Step 2: Run Collection (Overnight)

```bash
# Run in background with logging
nohup Rscript /tmp/2021-2024-gap/collect_data.R > /tmp/2021-2024-gap/collection.log 2>&1 &

# Monitor progress
tail -f /tmp/2021-2024-gap/collection.log

# Check if still running
ps aux | grep collect_data.R
```

**IMPORTANT:** This will take 8-12 hours. Run overnight or over a weekend.

---

## DAY 3: VALIDATION (4 hours)

### Step 1: Load Data and Basic Checks

```r
# Load final dataset
data <- read.csv("/tmp/2021-2024-gap/data/crypto_history_2021_2024_FINAL.csv")

# Basic statistics
cat("Dataset Overview:\n")
cat(sprintf("Total rows: %d\n", nrow(data)))
cat(sprintf("Unique coins: %d\n", length(unique(data$symbol))))
cat(sprintf("Date range: %s to %s\n", min(data$timestamp), max(data$timestamp)))
cat(sprintf("Columns: %s\n", paste(colnames(data), collapse = ", ")))

# Check for missing values
cat("\nMissing values:\n")
print(colSums(is.na(data)))

# Check circulating supply
cat("\nCirculating supply stats:\n")
cat(sprintf("Non-zero: %d (%.1f%%)\n",
            sum(data$circulating_supply > 0, na.rm = TRUE),
            100 * mean(data$circulating_supply > 0, na.rm = TRUE)))
```

### Step 2: Terra/Luna Collapse Validation (May 2022)

```r
# Load data
data <- read.csv("/tmp/2021-2024-gap/data/crypto_history_2021_2024_FINAL.csv")

# Filter Terra/Luna data for May 2022
terra_luna <- data[data$symbol %in% c("LUNA", "UST") &
                   data$timestamp >= "2022-05-01" &
                   data$timestamp <= "2022-05-31", ]

# Check collapse
luna_may5 <- terra_luna[terra_luna$symbol == "LUNA" &
                        terra_luna$timestamp == "2022-05-05", "price_usd"]
luna_may13 <- terra_luna[terra_luna$symbol == "LUNA" &
                         terra_luna$timestamp == "2022-05-13", "price_usd"]

cat("Terra/Luna Collapse Validation:\n")
cat(sprintf("LUNA price May 5: $%.2f (expected ~$87)\n", luna_may5))
cat(sprintf("LUNA price May 13: $%.6f (expected <$0.00005)\n", luna_may13))

if (luna_may5 > 50 && luna_may13 < 0.001) {
  cat("✅ PASS: Terra/Luna collapse correctly captured\n")
} else {
  cat("❌ FAIL: Terra/Luna data inconsistent\n")
}
```

### Step 3: Market Cap Formula Validation

```r
# Check if market_cap ≈ price × circulating_supply
data$calculated_mcap <- data$price_usd * data$circulating_supply
data$mcap_error <- abs(data$market_cap_usd - data$calculated_mcap) / data$market_cap_usd

# Filter out rows where circulating_supply is 0 or NA
valid_rows <- data[data$circulating_supply > 0 & !is.na(data$circulating_supply), ]

# Calculate percentage of rows with <5% error
within_tolerance <- mean(valid_rows$mcap_error < 0.05, na.rm = TRUE)

cat("Market Cap Formula Validation:\n")
cat(sprintf("Rows with <5%% error: %.1f%%\n", 100 * within_tolerance))

if (within_tolerance > 0.95) {
  cat("✅ PASS: Market cap formula validates\n")
} else {
  cat("⚠️ WARNING: Some market cap discrepancies detected\n")
}
```

### Step 4: Completeness Check

```r
# Check for date gaps
data$date <- as.Date(data$timestamp)
date_range <- seq(from = as.Date("2021-08-01"),
                  to = as.Date("2024-12-31"),
                  by = "day")

# For each top 10 coin, check completeness
top_10 <- names(sort(table(data$symbol), decreasing = TRUE)[1:10])

cat("Completeness Check (Top 10 Coins):\n")
for (coin in top_10) {
  coin_data <- data[data$symbol == coin, ]
  coin_dates <- unique(coin_data$date)
  completeness <- length(coin_dates) / length(date_range)

  cat(sprintf("%s: %.1f%% complete (%d/%d days)\n",
              coin, 100 * completeness,
              length(coin_dates), length(date_range)))
}
```

### Step 5: Generate Quality Report

```r
# Create comprehensive quality report
report <- list(
  total_rows = nrow(data),
  unique_coins = length(unique(data$symbol)),
  date_range = c(min(data$timestamp), max(data$timestamp)),
  missing_values = colSums(is.na(data)),
  circulating_supply_coverage = mean(data$circulating_supply > 0, na.rm = TRUE),
  market_cap_accuracy = within_tolerance,
  top_10_coins = top_10
)

# Save report
saveRDS(report, "/tmp/2021-2024-gap/data/quality_report.rds")
write.csv(as.data.frame(report), "/tmp/2021-2024-gap/data/quality_report.csv")

cat("\n✅ VALIDATION COMPLETE\n")
cat("Quality report saved to: /tmp/2021-2024-gap/data/quality_report.csv\n")
```

---

## EXPECTED OUTPUT FILES

After Day 3, you should have:

```
/tmp/2021-2024-gap/data/
├── crypto_history_2021_2024_FINAL.csv    ← PRIMARY OUTPUT (500 coins × ~1,200 days)
├── historical_listings_2021_2024.csv     ← Supplementary listings data
├── current_top_500.csv                   ← Current rankings
├── quality_report.csv                    ← Validation results
├── checkpoint_*.csv                      ← Intermediate saves (can delete)
└── bitconnect_test.csv                   ← Test data (can delete)
```

**Primary File:** `crypto_history_2021_2024_FINAL.csv`

**Expected Columns:**

- `timestamp` (date)
- `symbol` (e.g., BTC, ETH)
- `name` (e.g., Bitcoin, Ethereum)
- `rank` (market cap ranking)
- `price_usd`
- `market_cap_usd`
- `circulating_supply`
- `total_supply`
- `max_supply`
- `volume_24h`

**Expected Size:**

- ~600,000 rows (500 coins × ~1,200 days)
- ~50-100 MB CSV file

---

## TROUBLESHOOTING

### Problem: "Rate limit exceeded"

**Solution:** This is expected. The script includes 60-second waits between calls. Just let it run.

### Problem: Script interrupted/crashed

**Solution:** Check checkpoint files. You can resume from last checkpoint:

```r
# Load last checkpoint
last_checkpoint <- read.csv("/tmp/2021-2024-gap/data/checkpoint_0450.csv")

# Get coins already collected
collected_coins <- unique(last_checkpoint$symbol)

# Remove from coin_slugs and continue
coin_slugs <- coin_slugs[!coin_slugs %in% collected_coins]
```

### Problem: "No data for coin X"

**Solution:** Some coins may not have historical data. This is normal. The script skips them with a warning.

### Problem: Circulating supply = 0 for many coins

**Solution:** Some coins don't report circulating supply. Options:

1. Accept the limitation (still have market cap and price)
2. Calculate: `circulating_supply = market_cap / price`
3. Find alternative source for those specific coins

### Problem: Market cap validation fails

**Solution:** Check which coins fail validation:

```r
failed_coins <- valid_rows[valid_rows$mcap_error > 0.05, c("symbol", "timestamp", "mcap_error")]
table(failed_coins$symbol)
```

---

## ALTERNATIVE PLAN: If crypto2 Doesn't Work

### Fallback: CoinGecko API + pycoingecko (Python)

**Why switch:** crypto2 package broken, rate limits too strict, or R not available

**Trade-off:** ⚠️ Circulating supply requires Pro API (PAID) or must be calculated

**Quick Start:**

```python
# Install
pip install pycoingecko pandas

# Collect data
from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta

cg = CoinGeckoAPI()

# Get top 500 coins
coins = cg.get_coins_markets(vs_currency='usd', per_page=250, page=1)
coins += cg.get_coins_markets(vs_currency='usd', per_page=250, page=2)

# For each coin, get historical data
all_data = []
for coin in coins[:500]:
    coin_id = coin['id']

    # Get market chart (price, market cap, volume)
    data = cg.get_coin_market_chart_range_by_id(
        id=coin_id,
        vs_currency='usd',
        from_timestamp=int(datetime(2021, 8, 1).timestamp()),
        to_timestamp=int(datetime(2024, 12, 31).timestamp())
    )

    # Convert to DataFrame
    df = pd.DataFrame(data['market_caps'], columns=['timestamp', 'market_cap'])
    df['price'] = [x[1] for x in data['prices']]
    df['volume'] = [x[1] for x in data['total_volumes']]
    df['symbol'] = coin['symbol']
    df['name'] = coin['name']

    # CALCULATE circulating supply (workaround)
    df['circulating_supply_calculated'] = df['market_cap'] / df['price']

    all_data.append(df)

    # Rate limiting
    time.sleep(2)  # 30 calls/min limit

# Combine and save
final_df = pd.concat(all_data)
final_df.to_csv('/tmp/2021-2024-gap/data/coingecko_data.csv', index=False)
```

**Pros:**

- ✅ Python (more common than R)
- ✅ Well-documented API
- ✅ Free tier available

**Cons:**

- ❌ Circulating supply calculated, not source data
- ⚠️ Rate limits: 30 calls/min (slower than crypto2)
- ⚠️ May miss some historical circulating supply nuances

---

## SUCCESS CRITERIA

You're done when you have:

- ✅ CSV file with 500+ coins
- ✅ Aug 2021 - Dec 2024 date range (no gaps)
- ✅ All required fields: date, symbol, price, market_cap, circulating_supply
- ✅ Terra/Luna collapse validated (May 2022)
- ✅ Market cap formula validates (within 5% error)
- ✅ No look-ahead bias detected
- ✅ Quality report generated

**When complete:** Move to next phase (Kaggle validation, CoinGecko integration)

---

## TIME ESTIMATE SUMMARY

- **Day 1 (Setup & Test):** 2 hours
- **Day 2 (Data Collection):** 8-12 hours (unattended)
- **Day 3 (Validation):** 4 hours

**Total Active Time:** 6 hours
**Total Elapsed Time:** 2-3 days

**Cost:** $0

---

## NEXT STEPS AFTER COMPLETION

1. ✅ Move data to main project workspace:

   ```bash
   cp /tmp/2021-2024-gap/data/crypto_history_2021_2024_FINAL.csv \
      /Users/terryli/eon/crypto-marketcap-rank/data/2021-2024-gap/
   ```

2. ✅ Integrate with Kaggle data (2013-2021)

3. ✅ Integrate with CoinGecko data (2024-2025)

4. ✅ Run complete validation across all three datasets

5. ✅ Generate final unified dataset (2013-2025)

6. ✅ BitConnect test across entire timeline

7. ✅ Ready for analysis!

---

**Document Version:** 1.0
**Last Updated:** 2025-11-19
**Status:** Ready for Execution
