# Canonical Workflow - Point-in-Time Rankings

**Purpose**: Step-by-step guide for collecting cryptocurrency market cap rankings

**Critical Rule**: You MUST get coin IDs first before collecting any data

**Last Updated**: 2025-11-20

---

## The Golden Rule 🎯

> **For any coin ID we want to rank, we must first decide which coins to include in the ranking universe. Getting coin IDs is the MANDATORY prerequisite - the pre-flight check.**

**Why?**: Rankings are relative. To know that Bitcoin is #1, you need to know what #2, #3, ... #N are. You must define your ranking universe FIRST.

---

## Quick Start

### Option 1: Daily Snapshot (Recommended for Building Database)

```bash
# Run once per day (automate with cron)
uv run tools/fetch_current_rankings.py 1000

# Result: data/rankings/current_rankings_YYYYMMDD_HHMMSS.csv
# Time: 12-60 seconds (4 API calls)
# API usage: 120 calls/month (1.2% of free tier limit)
```

**Perfect for**: Building historical database over time

### Option 2: One-Time Complete Snapshot

```bash
# Get ALL ~13,000 ranked coins RIGHT NOW
uv run tools/fetch_current_rankings.py all

# Result: Complete current market state
# Time: 3-16 minutes (52 API calls)
# API usage: 0.52% of monthly limit
```

**Perfect for**: Baseline snapshot, current market analysis

### Option 3: Historical Point-in-Time (Slow, Pending Implementation)

```bash
# Step 1: Get coin IDs (MANDATORY)
uv run tools/fetch_all_coin_ids.py

# Step 2: Collect market_cap for all coins on target date
# (Not implemented - requires custom script)

# Step 3: Calculate rankings
uv run tools/calculate_point_in_time_rankings.py
```

**Perfect for**: Historical analysis, backtesting

---

## Workflow Details

### Workflow A: Current Rankings (Working ✅)

**Use Case**: "I want to know the top 1,000 coins ranked by market cap RIGHT NOW"

**Steps**:

1. Run collection script
2. Done!

**Example**:

```bash
# Get top 1,000 current rankings
uv run tools/fetch_current_rankings.py 1000

# Check results
ls -lh data/rankings/current_rankings_*.csv
cat data/rankings/current_rankings_*.csv | head -21
```

**Time**: 12-60 seconds (4 API calls)

**Output**:

- `data/rankings/current_rankings_YYYYMMDD_HHMMSS.csv` - Rankings in CSV
- `data/rankings/current_rankings_YYYYMMDD_HHMMSS.json` - Full API data
- `data/rankings/summary_YYYYMMDD_HHMMSS.json` - Metadata + top 10

**What you get**:

```csv
rank,id,symbol,name,market_cap,price,volume_24h
1,bitcoin,btc,Bitcoin,1706984400280,85579,100685354993
2,ethereum,eth,Ethereum,337143314959,2794.74,43768058390
3,tether,usdt,Tether,184561429699,0.998907,143762223948
...
```

---

### Workflow B: Daily Collection (Recommended Strategy ✅)

**Use Case**: "I want to build a comprehensive historical database over time"

**Strategy**: Collect current rankings snapshot ONCE PER DAY

**Why this works**:

- Captures market state as it happens
- No survivorship bias (includes coins before they die)
- Sustainable within free tier (1.2% of monthly limit)
- After 365 days: Complete year of daily rankings!

**Setup**:

**1. Create collection script** (one-time)

```bash
# Create daily_collection.sh
cat > daily_collection.sh << 'EOF'
#!/bin/bash
# Daily rankings collection
uv run tools/fetch_current_rankings.py 1000
EOF

chmod +x daily_collection.sh
```

**2. Set up cron job** (one-time)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2:00 AM)
0 2 * * * cd ~/eon/crypto-marketcap-rank && ./daily_collection.sh
```

**3. Let it run!**

**Result after 30 days**:

```
data/rankings/
├── current_rankings_20251120_020000.csv
├── current_rankings_20251121_020000.csv
├── current_rankings_20251122_020000.csv
...
├── current_rankings_20251220_020000.csv
```

**Analysis**:

```python
import pandas as pd
import glob

# Load all daily snapshots
files = glob.glob('data/rankings/current_rankings_*.csv')
dfs = [pd.read_csv(f) for f in files]

# Combine into time series
all_data = pd.concat(dfs, keys=[f.split('_')[2] for f in files])

# Track Bitcoin rank over time (should always be #1)
btc = all_data[all_data['symbol'] == 'btc']
print(btc[['rank', 'market_cap']])

# Track a coin's rank changes
ada = all_data[all_data['symbol'] == 'ada']
print(ada[['rank', 'market_cap']].sort_index())
```

**API Usage**:

- 4 calls/day × 30 days = 120 calls/month
- 1.2% of 10,000 monthly limit
- ✅ Perfectly sustainable!

---

### Workflow C: Historical Point-in-Time (Pending Implementation ⏳)

**Use Case**: "I want to know what the top 500 coins were on 2024-01-15"

**Why it's complex**: Historical rankings don't exist in CoinGecko API. You must collect ALL coins' market_caps for that date and calculate rankings yourself.

**Prerequisites (MANDATORY)**:

**Step 0: Define Your Ranking Universe**

**Critical Decision**: Which coins do you want to include in your rankings?

**Option A**: All 19,410 coins (comprehensive)

```bash
uv run tools/fetch_all_coin_ids.py
# Result: data/coin_ids/coingecko_all_coin_ids.json (19,410 coins)
```

**Option B**: Top 13,000 ranked coins (from current snapshot)

```bash
uv run tools/fetch_current_rankings.py all
# Extract coin IDs from current rankings
jq -r '.[].id' data/rankings/current_rankings_*.json > ranking_universe.txt
```

**Option C**: Specific subset (e.g., top 666, top 888)

```bash
uv run tools/fetch_current_rankings.py 666
# Or manually create list of coin IDs you care about
```

**Why this matters**:

- Rankings are RELATIVE to your universe
- If you only include top 500, ranks will be 1-500
- If you include all 19,410, ranks could be 1-19,410
- Different universes = different rankings!

**Example**:

```
Universe A (Top 1000 only): Cardano rank #10
Universe B (All 19,410): Cardano rank #10

Bitcoin rank: Same in both
Obscure coin rank: Not in A, #15,432 in B
```

**Step 1: Collect Historical Market Caps**

For each coin in your universe, for each target date:

```bash
# Pseudo-code (not implemented yet)
for coin_id in $(cat coin_ids.txt); do
  for date in $(cat target_dates.txt); do
    # Format: DD-MM-YYYY
    curl "https://api.coingecko.com/api/v3/coins/${coin_id}/history?date=${date}"
    sleep 4  # Rate limit (with API key)
  done
done
```

**Time estimate**:

- 500 coins × 365 days = 182,500 API calls
- With API key (4s delay): ~8.5 days continuous runtime
- Without API key (20s delay): ~42 days continuous runtime

**API usage**:

- 182,500 calls ÷ 10,000 monthly limit = 18.25 months worth of quota
- ❌ Not feasible with free tier for full year!

**Alternative**: Collect 1 day at a time

```bash
# Just get rankings for 2024-01-15
# 500 coins × 1 date = 500 API calls (5% of monthly limit)
```

**Step 2: Calculate Point-in-Time Rankings**

Once you have market_cap for all coins on a specific date:

```python
import pandas as pd

# Load data for specific date
df = pd.read_csv('market_caps_2024-01-15.csv')

# Calculate rankings
df = df.sort_values('market_cap', ascending=False)
df['rank'] = range(1, len(df) + 1)

# Save ranked results
df.to_csv('rankings_2024-01-15.csv', index=False)
```

**Tool** (partially implemented):

```bash
uv run tools/calculate_point_in_time_rankings.py \
  --input market_caps_2024-01-15.csv \
  --output rankings_2024-01-15.csv
```

**Step 3: Analyze Historical Rankings**

```python
import pandas as pd

# Load historical rankings
df = pd.read_csv('rankings_2024-01-15.csv')

# Find specific coin's rank on that date
cardano_rank = df[df['symbol'] == 'ada']['rank'].values[0]
print(f"Cardano rank on 2024-01-15: #{cardano_rank}")

# Top 10 on that date
top10 = df.head(10)
print(top10[['rank', 'symbol', 'name', 'market_cap']])
```

---

## Decision Tree

### "I want current rankings..."

**→ Use Workflow A**: `uv run tools/fetch_current_rankings.py <N>`

**Questions**:

- Top 100? → `N = 100` (instant, 1 API call)
- Top 500? → `N = 500` (4-20 sec, 2 API calls)
- Top 1,000? → `N = 1000` (12-60 sec, 4 API calls)
- ALL ranked? → `N = all` (3-16 min, 52 API calls)

---

### "I want to build historical database..."

**→ Use Workflow B**: Daily collection automation

**Steps**:

1. Set up cron job (one-time)
2. Let it run daily
3. After N days: N snapshots of rankings

**Benefits**:

- Sustainable (1.2% monthly limit)
- No survivorship bias
- Real-time accuracy
- After 1 year: 365 daily snapshots!

---

### "I want rankings for specific past date..."

**→ Use Workflow C**: Historical point-in-time (complex!)

**Prerequisite**: Define ranking universe first!

**Steps**:

1. Get coin IDs for your universe
2. Collect market_cap for all coins on target date
3. Calculate rankings from collected data

**Limitations**:

- Very slow (days for full year)
- High API usage (may need paid tier)
- Complex to implement

**Alternative**: Wait for daily collection to build up database

---

## Prerequisite Workflow Explained

### Why "Coin IDs First" is Mandatory

**The Problem**:

You can't rank coins without knowing what coins exist.

**Example**:

Bad workflow:

```
❌ User: "What was Bitcoin's rank on 2024-01-15?"
❌ System: Gets Bitcoin data, but doesn't know what to compare it to
❌ Result: Can't calculate rank!
```

Correct workflow:

```
✅ Step 1: Get coin universe (all 19,410 coins or subset)
✅ Step 2: Get market_cap for ALL coins on 2024-01-15
✅ Step 3: Sort by market_cap → Bitcoin is #1
✅ Result: Bitcoin rank #1 on 2024-01-15
```

**The Insight**:

Ranking is a **relative** operation. You need the ENTIRE set to calculate rankings.

### Workflow Diagram

```
Start
  ↓
[Decision: What ranking universe?]
  ├─ All 19,410 coins → fetch_all_coin_ids.py
  ├─ Top 13,000 ranked → fetch_current_rankings.py all
  └─ Top N current → fetch_current_rankings.py N
  ↓
[Save coin IDs to file: universe.txt]
  ↓
[Decision: What data do you want?]
  ├─ Current rankings → DONE (already collected)
  ├─ Daily snapshots → Set up cron job
  └─ Historical date → Continue below
  ↓
[For each coin in universe.txt]
  ↓
[For each target date]
  ↓
[GET /coins/{id}/history?date=DD-MM-YYYY]
  ↓
[Extract market_cap]
  ↓
[Save to file: market_caps_DATE.csv]
  ↓
[All coins collected for date?]
  ↓
[Sort by market_cap descending]
  ↓
[Assign ranks: 1, 2, 3, ...]
  ↓
[Save: rankings_DATE.csv]
  ↓
End
```

---

## Examples

### Example 1: Get Current Top 100

**Command**:

```bash
uv run tools/fetch_current_rankings.py 100
```

**Time**: Instant (1 API call)

**Output**: `data/rankings/current_rankings_20251120_*.csv`

**Top 5**:

```csv
rank,id,symbol,name,market_cap
1,bitcoin,btc,Bitcoin,1706984400280
2,ethereum,eth,Ethereum,337143314959
3,tether,usdt,Tether,184561429699
4,ripple,xrp,XRP,118267904315
5,binancecoin,bnb,BNB,117487000279
```

---

### Example 2: Daily Collection for 30 Days

**Setup** (one-time):

```bash
crontab -e
# Add: 0 2 * * * cd ~/eon/crypto-marketcap-rank && uv run tools/fetch_current_rankings.py 1000
```

**After 30 days**:

```bash
ls data/rankings/ | grep current_rankings | wc -l
# Result: 30 files
```

**Analysis**:

```python
import pandas as pd
import glob

files = sorted(glob.glob('data/rankings/current_rankings_*.csv'))

# Load all daily snapshots
dfs = {f.split('_')[2]: pd.read_csv(f) for f in files}

# Track Cardano rank over 30 days
for date, df in dfs.items():
    ada = df[df['symbol'] == 'ada']
    if len(ada) > 0:
        print(f"{date}: Cardano rank #{ada['rank'].values[0]}")
```

---

### Example 3: Historical Ranking for Single Date

**Goal**: Get top 500 coins ranked by market cap on 2024-01-15

**Step 1**: Define universe

```bash
uv run tools/fetch_current_rankings.py 500
jq -r '.[].id' data/rankings/current_rankings_*.json > top500_ids.txt
```

**Step 2**: Collect market_cap for all 500 coins on 2024-01-15

```bash
# Pseudo-code (script needed)
for coin_id in $(cat top500_ids.txt); do
  curl "https://api.coingecko.com/api/v3/coins/${coin_id}/history?date=15-01-2024" \
    -o "data/historical/${coin_id}_2024-01-15.json"
  sleep 4  # Rate limit
done
```

**Time**: 500 coins × 4s = 33 minutes

**Step 3**: Extract market_cap and calculate rankings

```python
import json
import pandas as pd
import glob

# Load all collected data
data = []
for file in glob.glob('data/historical/*_2024-01-15.json'):
    with open(file) as f:
        coin_data = json.load(f)
        data.append({
            'id': coin_data['id'],
            'symbol': coin_data['symbol'],
            'name': coin_data['name'],
            'market_cap': coin_data['market_data']['market_cap']['usd']
        })

# Create DataFrame and rank
df = pd.DataFrame(data)
df = df.sort_values('market_cap', ascending=False)
df['rank'] = range(1, len(df) + 1)

# Save rankings
df.to_csv('rankings_2024-01-15.csv', index=False)
print(df.head(10))
```

**Result**: `rankings_2024-01-15.csv` with top 500 coins ranked for that date

---

## Tools Reference

| Tool                                  | Purpose                                 | Input                  | Output               |
| ------------------------------------- | --------------------------------------- | ---------------------- | -------------------- |
| `fetch_all_coin_ids.py`               | Get all CoinGecko coin IDs              | None                   | 19,410 coin IDs      |
| `fetch_current_rankings.py`           | Get current top N rankings              | N (100-13000 or "all") | Current rankings CSV |
| `calculate_point_in_time_rankings.py` | Calculate rankings from market_cap data | market_caps CSV        | Rankings CSV         |
| `lookup_rank_by_id_date.py`           | Lookup specific coin rank on date       | coin_id, date          | Rank                 |

---

## Best Practices

### 1. Always Define Universe First ✅

```bash
# Good
uv run tools/fetch_all_coin_ids.py  # Define universe
# Then collect data for those coins

# Bad
# Start collecting random coins without universe definition
```

### 2. Use Daily Collection for Historical Database ✅

```bash
# Good: Build over time
# Day 1: 4 API calls
# Day 2: 4 API calls
# ...
# After 1 year: 1,460 calls total (14.6% of annual limit)

# Bad: Try to collect 1 year all at once
# 500 coins × 365 days = 182,500 calls (18× annual limit) ❌
```

### 3. Respect Rate Limits ✅

```bash
# With API key: 4s delay
# Without: 20s delay
# Don't try to rush - will hit 429 errors
```

### 4. Save Raw Data + Calculated Rankings ✅

```bash
# Good
data/raw/market_caps_2024-01-15.csv  # Raw data
data/processed/rankings_2024-01-15.csv  # Calculated rankings

# Can recalculate if needed
# Can verify calculations
```

---

## Troubleshooting

### "I collected data but can't calculate rankings"

**Problem**: Missing coins in universe

**Solution**: Verify you collected ALL coins in your defined universe

```bash
# Check how many coins collected
ls data/historical/*_2024-01-15.json | wc -l

# Check how many should be collected
wc -l top500_ids.txt

# If numbers don't match, find missing coins
comm -23 <(sort top500_ids.txt) <(ls data/historical | cut -d_ -f1 | sort)
```

### "Rankings don't match CoinGecko website"

**Possible causes**:

1. Different ranking universe (website uses all ranked coins, you used subset)
2. Different timestamps (market_cap changes continuously)
3. API data lag (CoinGecko caches data)

**Solution**: Use larger universe or collect at same time as website

### "Rate limit errors"

**Problem**: Requests too fast

**Solution**:

```bash
# Increase delay
sleep 20  # Without API key
sleep 4   # With Demo API key

# Or get API key (free, no credit card)
export COINGECKO_API_KEY=your_key_here
```

---

## Next Steps

**Immediate**:

- ✅ Collect current rankings snapshot (done)
- ✅ Set up daily collection automation (ready to implement)

**Short-term**:

- ⏳ Implement historical collection script
- ⏳ Validate Kaggle dataset (alternative source)

**Long-term**:

- ⏳ Historical backfill for specific dates
- ⏳ Analysis tools for rank changes over time
- ⏳ Visualization dashboard

---

**Status**: ✅ Current rankings workflow complete, historical workflow documented (pending implementation)
