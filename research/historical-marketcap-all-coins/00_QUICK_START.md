# Quick Start Guide: Collecting All Coins' Historical Market Cap

**Status**: Ready to implement
**Cost**: $0 (free tier)
**Setup Time**: 30 minutes
**Implementation Time**: 30 days to full monitoring

---

## TL;DR - The Answer

**Question**: How do we collect historical market cap for all 13,532 coins?

**Answer**:

- Use `/v1/tickers` endpoint
- Paginate with limit=250
- Collect once per day (55 API calls/day)
- Store in JSONL format
- Cost: $0 forever
- Risk: Low (with monitoring)

---

## The Problem

- **Total coins**: 13,532
- **Free tier budget**: 20,000 API calls/month
- **Direct approach cost**: 13,532 calls × 30 days = 405,960 calls/month (20x over budget!)
- **Naive endpoint** (`/v1/coins/{id}/ohlcv/today`): Doesn't work

---

## The Solution

**Use `/v1/tickers` with pagination**

Instead of 13,532 separate API calls, make 55 paginated requests:

- Request 1: limit=250, offset=0 (coins 0-249)
- Request 2: limit=250, offset=250 (coins 250-499)
- ...
- Request 55: limit=250, offset=13250 (coins 13250-13531)

**Total**: 55 calls to get all 13,532 coins in one snapshot

---

## Cost Analysis

| Period   | API Calls | Cost | Storage |
| -------- | --------- | ---- | ------- |
| Daily    | 55        | $0   | 2.6 MB  |
| Monthly  | 1,650     | $0   | 77 MB   |
| Yearly   | 20,075    | $0   | 0.92 GB |
| 10 years | 200,750   | $0   | 9.2 GB  |

**Free tier budget**: 20,000 calls/month
**Our usage**: 1,650 calls/month (8%)
**Headroom**: 18,350 calls (92%)

---

## Strategies Ranked

### Strategy 1: Free Daily Snapshots (RECOMMENDED)

- Cost: $0
- Monthly calls: 1,650
- Feasibility: ✓ EXCELLENT
- Implementation: Easy
- Start: Immediately

### Strategy 2: Hybrid - Free + One-time Backfill

- Cost: $40 (Month 1 only)
- Backfill: 30 days of history immediately
- Then: Free tier forever
- Feasibility: ✓ EXCELLENT
- Start: 30 days in

### Strategy 3: Stratified by Rank

- Cost: $0
- Top 100: 4x daily
- Top 500: 2x daily
- Rest: 1x daily
- Feasibility: ✓ EXCELLENT
- Implementation: Medium

### Strategy 4: Per-Coin Collection (NOT RECOMMENDED)

- Cost: $480/month (Starter plan)
- Calls: 13,532/day (20x over free tier)
- Feasibility: ✗ POOR
- Recommendation: DON'T USE

---

## Implementation (30 minutes)

### Step 1: Create Script (10 min)

Create `collect.py`:

```python
#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def collect_market_cap():
    timestamp = datetime.utcnow().isoformat() + 'Z'
    all_coins = []

    # Paginate through all 13,532 coins
    for offset in range(0, 13532, 250):
        response = requests.get(
            "https://api.coinpaprika.com/v1/tickers",
            params={
                "limit": 250,
                "offset": offset,
                "quotes": "USD"
            }
        )

        for coin in response.json():
            record = {
                "timestamp": timestamp,
                "coin_id": coin["id"],
                "symbol": coin["symbol"],
                "rank": coin["rank"],
                "market_cap_usd": coin["quotes"]["USD"]["market_cap"],
                "price_usd": coin["quotes"]["USD"]["price"],
                "volume_24h_usd": coin["quotes"]["USD"]["volume_24h"]
            }
            all_coins.append(record)
            print(json.dumps(record))  # JSONL format

    return len(all_coins)

if __name__ == "__main__":
    count = collect_market_cap()
    print(f"Collected {count} coins")
```

### Step 2: Test (5 min)

```bash
python3 collect.py > market_cap_2025-11-20.jsonl
wc -l market_cap_2025-11-20.jsonl  # Should be 13,532
head -1 market_cap_2025-11-20.jsonl  # Check format
```

### Step 3: Automate (10 min)

Add to crontab (run daily at midnight UTC):

```bash
crontab -e
# Add this line:
0 0 * * * cd /workspace/marketcap && python3 collect.py >> data/$(date +\%Y-\%m-\%d).jsonl 2>&1
```

### Step 4: Monitor (5 min)

```bash
# Check that file was created today
ls -lh data/$(date +%Y-%m-%d).jsonl

# Count coins in file
wc -l data/$(date +%Y-%m-%d).jsonl

# Verify format
head -5 data/$(date +%Y-%m-%d).jsonl | jq '.'
```

---

## What You Get

### After 1 week

- 7 daily snapshots
- 18 MB of storage
- All 13,532 coins tracked

### After 1 month

- 30 daily snapshots
- 77 MB of storage
- 1 month of history

### After 1 year

- 365 daily snapshots
- 920 MB of storage
- 1 year of history

### After 10 years

- 3,650 daily snapshots
- 9.2 GB of storage
- 10 years of history

---

## Common Questions

**Q: Why not use `/v1/coins/{id}/ohlcv/historical`?**
A: Requires one API call per coin (13,532 calls/day) = 20x over budget. The `/v1/tickers` endpoint is 260x more efficient!

**Q: Can I get historical data from before today?**
A: On free tier: No, only current snapshot. Optional: Use $40 Starter plan to backfill 30 days in Month 1.

**Q: How often should I collect?**
A: Once per day is optimal. More frequent = wastes quota. Less frequent = coarser history.

**Q: What if I need hourly data?**
A: Use paid tier (Starter: $40/month for daily, Business: $300+/month for hourly).

**Q: How do I query the data?**
A: Parse JSONL files with Python. One JSON object per line.

**Q: Can the free tier handle this?**
A: Yes! 1,650 calls/month fits easily in 20,000 budget (92% headroom).

**Q: Is there a risk of getting blocked?**
A: No. 55 requests/day is very light usage. Add 50ms delay between requests for safety.

**Q: What's the total cost for 10 years of data?**
A: $0 (free tier) or $40 (one-time backfill if you want 30-day head start).

---

## Files in This Directory

1. **00_QUICK_START.md** ← You are here
2. **01_feasibility_analysis.py** - Detailed calculations
3. **02_endpoint_analysis.py** - Endpoint comparison
4. **03_risk_analysis.md** - Risk mitigation
5. **04_COMPREHENSIVE_STRATEGY_REPORT.md** - Full strategy document
6. **feasibility_calculations.json** - Raw calculations

---

## Next Steps

### Now

1. Read this file (5 min)
2. Review 04_COMPREHENSIVE_STRATEGY_REPORT.md (20 min)

### This Week

3. Write collection script
4. Test manually
5. Set up cron job
6. Start daily collection

### This Month

7. Add monitoring and alerting
8. Validate 30 days of data

### Optional: Month 1

9. Use $40 Starter plan to backfill 30 days
10. Downgrade to free tier
11. Begin long-term storage

---

## Status

✓ Strategy defined
✓ Feasibility confirmed
✓ Rate limits analyzed
✓ Risks mitigated
✓ Timeline created
✓ **Ready to implement**

---

**Start collecting today. Zero cost. Infinite history.**
