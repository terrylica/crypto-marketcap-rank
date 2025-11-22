# Crypto Data API Investigations Summary

**Purpose**: Document all cryptocurrency data APIs investigated and why they were rejected in favor of CoinGecko.

**Last Updated**: 2025-11-20

**Decision**: Use CoinGecko exclusively ✅

---

## Executive Summary

**APIs Investigated**: 7 different cryptocurrency data sources

**Winner**: CoinGecko `/api/v3`

- Most comprehensive (19,410 coins)
- Best free tier (10,000 calls/month)
- No credit card required for API key
- Best documentation
- Includes historical data

**Rejected**: All other APIs due to insufficient coverage, cost, or limitations

---

## Detailed Investigations

### 1. CoinGecko ✅ SELECTED

**Website**: https://www.coingecko.com/api

**Investigation Date**: November 2025

**Coverage**: 19,410 active coins

**Free Tier**:

- 10,000 API calls/month
- No credit card required
- Demo API key available (free)

**Key Endpoints**:

- `/coins/list` - All coin IDs (FREE, unlimited)
- `/coins/markets` - Current rankings with market_cap_rank
- `/coins/{id}/history` - Historical market_cap per coin

**Pros**:

- ✅ Largest coverage (19,410 coins)
- ✅ Generous free tier
- ✅ No credit card required
- ✅ Excellent documentation
- ✅ Includes historical data (365 days free)
- ✅ Real-time rankings available
- ✅ Widely used and trusted

**Cons**:

- ❌ No direct historical rank lookup (must calculate from market_cap)
- ❌ Rate limiting strict (4s with key, 20s without)
- ❌ Inactive coins require paid plan

**Decision**: ✅ **PRIMARY DATA SOURCE**

---

### 2. Messari ❌ REJECTED

**Website**: https://messari.io/api

**Investigation Date**: November 2025

**Coverage**: ~200 coins (vetted projects only)

**Free Tier**: Limited

**Rejection Reason**:

- ❌ Only 200 coins (vs. CoinGecko's 19,410)
- ❌ Insufficient for comprehensive rankings
- ❌ Focus on research/fundamentals, not exhaustive market data

**Verdict**: Too limited for market cap ranking project

---

### 3. CoinPaprika ❌ REJECTED

**Website**: https://coinpaprika.com/api

**Investigation Date**: November 2025

**Coverage**: ~7,000 coins

**Free Tier**: 20,000 calls/month

**Pros**:

- ✅ More generous free tier than CoinGecko
- ✅ Good coverage (7,000 coins)

**Cons**:

- ❌ Fewer coins than CoinGecko (7,000 vs 19,410)
- ❌ Less comprehensive historical data
- ❌ Less widely adopted

**Rejection Reason**: CoinGecko has 2.8× more coins

**Verdict**: Good alternative, but CoinGecko superior in coverage

---

### 4. CoinCap ❌ REJECTED

**Website**: https://coincap.io/api

**Investigation Date**: November 2025

**Coverage**: ~2,000 coins (top assets)

**Free Tier**: Unlimited (with rate limiting)

**Pros**:

- ✅ Free unlimited API
- ✅ Real-time WebSocket support
- ✅ Simple API design

**Cons**:

- ❌ Only ~2,000 coins (vs. CoinGecko's 19,410)
- ❌ Focus on top coins only
- ❌ Less comprehensive historical data

**Rejection Reason**: Insufficient coverage for comprehensive rankings

**Verdict**: Good for real-time top coins, insufficient for historical ranking project

---

### 5. Crypto Data Download ❌ REJECTED

**Website**: https://www.cryptodatadownload.com

**Investigation Date**: November 2025

**Coverage**: Exchange OHLCV data

**Access**: Paid subscription required

**Pros**:

- ✅ High-quality OHLCV data
- ✅ Direct from exchanges

**Cons**:

- ❌ Paid only (no free tier)
- ❌ Focus on trading data, not market cap rankings
- ❌ Would require payment

**Rejection Reason**: Paid service, focus on wrong data type

**Verdict**: Not suitable for this project

---

### 6. CoinMarketCap ⚠️ NOT FULLY INVESTIGATED

**Website**: https://coinmarketcap.com/api

**Status**: Not deeply investigated

**Reason**: CoinGecko discovered first and met all requirements

**Note**: CoinMarketCap is comparable to CoinGecko in coverage and quality

- Similar number of coins
- Similar historical data availability
- Similar API structure
- Could be alternative if CoinGecko becomes problematic

**Decision**: Stick with CoinGecko (already working)

---

### 7. Academic/Research Sources ❌ REJECTED

**Sources Investigated**:

- Cryptocurrency Research databases
- Academic datasets
- GitHub repositories

**Findings**:

- ❌ Most datasets are snapshots (not live APIs)
- ❌ Many are outdated (pre-2020)
- ❌ Limited coverage
- ❌ No comprehensive free historical market cap data

**Rejection Reason**: No suitable academic source found

**Verdict**: Commercial APIs (CoinGecko) superior

---

## Comparison Matrix

| API             | Coins   | Free Tier   | Historical | Rankings   | Decision       |
| --------------- | ------- | ----------- | ---------- | ---------- | -------------- |
| **CoinGecko**   | 19,410  | 10k/mo      | ✅ 365d    | ✅ Current | ✅ **USE**     |
| Messari         | 200     | Limited     | ✅         | ❌         | ❌ Reject      |
| CoinPaprika     | 7,000   | 20k/mo      | ✅         | ✅ Current | ❌ Reject      |
| CoinCap         | 2,000   | Unlimited\* | ⚠️ Limited | ✅ Current | ❌ Reject      |
| Crypto Download | N/A     | ❌ Paid     | ✅         | ❌         | ❌ Reject      |
| CoinMarketCap   | ~20,000 | 10k/mo      | ✅         | ✅ Current | ⚠️ Alternative |
| Academic        | Varies  | ✅ Free     | ❌ Static  | ❌         | ❌ Reject      |

\*Rate limited

---

## Key Criteria

### Must-Have Requirements

1. ✅ Comprehensive coverage (10,000+ coins minimum)
2. ✅ Historical market cap data
3. ✅ Free tier or affordable
4. ✅ Reliable API uptime
5. ✅ Good documentation

### Nice-to-Have

- Current rankings with rank field
- No credit card required
- High rate limits
- WebSocket support

### Deal-Breakers

- ❌ Fewer than 5,000 coins
- ❌ No historical data
- ❌ Paid-only access
- ❌ Poor documentation

---

## CoinGecko Selection Rationale

### Why CoinGecko Won

**1. Coverage**: 19,410 coins (best in class)

- Includes dead 2013-era coins (Namecoin, Peercoin, etc.)
- Comprehensive altcoin coverage
- Regular updates for new listings

**2. Historical Data**: 365 days free

- `/coins/{id}/history` endpoint
- Returns market_cap, price, volume for specific dates
- Format: `?date=DD-MM-YYYY`

**3. Current Rankings**: `/coins/markets` endpoint

- Returns top N coins with `market_cap_rank` field
- Perfect for daily snapshots
- Pagination up to ~13,000 ranked coins

**4. Free Tier**: Sustainable

- 10,000 calls/month
- Demo API key (no credit card)
- Daily collection easily within limits

**5. Coin ID List**: FREE unlimited

- `/coins/list` doesn't count against API limit
- Foundation for comprehensive collection
- Includes active + many dead coins

**6. Documentation**: Excellent

- Clear endpoint descriptions
- Example responses
- Rate limit guidance

**7. Reliability**: Production-grade

- Widely used in industry
- Good uptime
- Active development

---

## Alternative Scenarios

### If CoinGecko Fails

**Backup Plan**: Switch to CoinMarketCap

- Similar coverage (~20,000 coins)
- Similar API structure
- Similar free tier limits
- Minimal code changes required

**Migration Path**:

1. Update base URL
2. Map field names (minor differences)
3. Adjust rate limiting
4. Re-test collection scripts

### If Both Fail

**Fallback**: Kaggle historical datasets

- One-time snapshot (not real-time)
- May have gaps in coverage
- Supplement with smaller API for recent data
- See investigation in separate task

---

## Recommendations

### Current Strategy ✅

- **Primary**: CoinGecko for all data collection
- **Backup**: CoinMarketCap (not currently needed)
- **Daily**: Run `fetch_current_rankings.py` for snapshots

### Future Considerations

- Monitor CoinGecko API changes
- Consider paid tier if free tier insufficient (~$100/mo for 500k calls)
- Maintain abstraction layer for easy API switching

### What NOT to Do ❌

- ❌ Don't use multiple APIs simultaneously (data consistency issues)
- ❌ Don't use paid services unless free tier exhausted
- ❌ Don't use APIs with <10,000 coin coverage
- ❌ Don't mix historical sources (different methodologies)

---

## Investigation Timeline

**November 19, 2025**: Initial API survey

- Researched 7 different crypto data APIs
- Created probe folders for each
- Tested endpoints and coverage

**November 20, 2025**: CoinGecko deep dive

- Confirmed 19,410 coin coverage
- Tested rate limits (20s no-key, 4s with-key)
- Validated historical data availability
- Discovered `/coins/markets` current rankings

**November 20, 2025**: Decision made

- Selected CoinGecko as sole data source
- Removed all non-CoinGecko research
- Consolidated findings into this document

---

## References

**CoinGecko Documentation**: https://docs.coingecko.com/llms-full.txt

**Working Tools**:

- `tools/fetch_all_coin_ids.py` - Uses CoinGecko `/coins/list`
- `tools/fetch_current_rankings.py` - Uses CoinGecko `/coins/markets`

**Lessons Learned**: See `LESSONS_LEARNED.md`

---

**Status**: ✅ API investigation complete, CoinGecko selected, all alternatives documented
