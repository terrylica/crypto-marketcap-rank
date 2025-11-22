# ADR-0001: Hybrid Free Data Acquisition Strategy for Historical Cryptocurrency Market Cap

## Status

Accepted

## Context

We need historical daily market cap rankings for all cryptocurrencies covering 2010-2025 (15+ years) with the following constraints:

- **Budget**: $0 (no paid APIs or services)
- **Quality**: Verified market cap (price × historical circulating supply), not estimated
- **Bias Prevention**: Point-in-time rankings without look-ahead bias (survivorship bias)
- **Coverage**: Top 500 coins per day with daily granularity
- **Critical Gap**: August 2021 - December 2024 (3.3 years between free sources)

### Research Findings

After exhaustive investigation of 50+ sources:

**Verified Free Sources**:

- Kaggle "CoinMarketCap Historical Data" (2013-2021, claims verified, **unvalidated**)
- crypto2 R package (2013-present, includes circulating supply, **validated**)
- CoinGecko Free API (365 days, pre-calculated market cap, **no circulating supply**)
- Archive.org Wayback Machine (sporadic snapshots, **currently offline**)

**Rejected Sources**:

- CryptoCompare: Price only, no market cap or circulating supply
- CoinCap: Price only, no market cap
- Messari: Enterprise plan required ($5,000+/year)
- CoinGecko Premium: Circulating supply requires paid tier ($129-499/month)
- CoinMarketCap API: Historical data requires paid tier ($79+/month)

### Critical Discovery

The **crypto2 R package** emerged as the only free tool providing historical circulating supply data, solving the 2021-2024 gap.

## Decision

Implement a **hybrid free data acquisition strategy** combining three complementary sources:

1. **Kaggle dataset** (2013-2021) - IF BitConnect validation test passes
2. **crypto2 R package** (2021-2024 gap, or full 2013-2024 if Kaggle fails)
3. **CoinGecko free tier** (2024-2025) - Accept pre-calculated market cap with quality warnings

### Quality Tiers

- **Verified**: Data with historical circulating supply (Kaggle if validated, crypto2)
- **Unverified**: Pre-calculated market cap without supply transparency (CoinGecko)
- **Estimated**: Price × current supply approximation (rejected, not used)

## Consequences

### Positive

- **Zero cost**: Complete solution using only free tools
- **Verified coverage**: 2013-2024 (11 years) with circulating supply
- **No look-ahead bias**: BitConnect test validates point-in-time data
- **Reproducible**: All sources are publicly accessible
- **Fallback options**: Multiple alternatives if primary sources fail

### Negative

- **Manual validation required**: Kaggle dataset quality unknown until tested
- **R dependency**: crypto2 requires R installation (not Python)
- **Unverified recent data**: 2024-2025 cannot verify market cap calculation
- **Maintenance**: Need to continue collecting daily snapshots going forward
- **Processing time**: crypto2 collection estimated 8-12 hours for 500 coins

### Risks and Mitigations

| Risk                        | Probability | Mitigation                                                |
| --------------------------- | ----------- | --------------------------------------------------------- |
| Kaggle has look-ahead bias  | 20%         | BitConnect test detects this; use crypto2 for full period |
| crypto2 R package breaks    | 5%          | Have cryptoCMD Python alternative ready                   |
| CoinGecko data is estimated | 60%         | Document limitation; acceptable for recent data           |
| Archive.org never restores  | 10%         | Not critical; have complete coverage without it           |

## Validation Criteria

Before accepting data sources:

1. **BitConnect Presence Test**: Must include coins that died (BitConnect Jan 2016 - Jan 2018)
2. **Circulating Supply Variation**: Bitcoin supply must increase 14.5M (2015) → 19.8M (2025)
3. **Rank Consistency**: Calculated rank from market cap must match provided rank
4. **Dead Coin Coverage**: Include delisted coins (Paycoin, Bytecoin, etc.)
5. **Historical Event Validation**: Terra/Luna collapse, FTX bankruptcy correctly reflected

## Implementation Notes

- All data flagged with source and quality tier in metadata
- Validation scripts created for reproducibility
- Documentation emphasizes limitations and quality tiers
- Future: Continue daily snapshot collection to build verified recent history

## Alternatives Considered

### Alternative 1: Pay for CoinGecko Pro ($129/month)

- **Pros**: Complete verified data with circulating supply, 2013-present
- **Cons**: Violates $0 budget constraint
- **Decision**: Rejected due to cost

### Alternative 2: Use only CryptoCompare (estimated market cap)

- **Pros**: Free, 15+ years, easy access
- **Cons**: No circulating supply = estimated market cap with ±5-15% variance
- **Decision**: Rejected due to unacceptable accuracy loss

### Alternative 3: Archive.org exclusive scraping

- **Pros**: Free, potential point-in-time snapshots
- **Cons**: Currently offline, uncertain coverage, high extraction complexity
- **Decision**: Rejected as primary strategy; considered supplementary when online

### Alternative 4: Build blockchain extractors

- **Pros**: Perfect accuracy for major coins
- **Cons**: Complex, chain-specific, limited to ~50 coins, high engineering effort
- **Decision**: Rejected due to complexity vs. benefit trade-off

## References

- Research workspace: `/Users/terryli/eon/crypto-marketcap-rank/research/`
- Agent reports: `/tmp/{kaggle-validation,academic-datasets,github-hunt,2021-2024-gap}/`
- Kaggle dataset: https://www.kaggle.com/datasets/bizzyvinci/coinmarketcap-historical-data
- crypto2 package: https://github.com/sstoeckl/crypto2
- CoinGecko API: https://www.coingecko.com/en/api/documentation
