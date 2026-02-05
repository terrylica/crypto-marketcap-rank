# Alpha Forge Integration Guide

<!-- GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/6 -->

Integration guide for using `crypto-marketcap-rank` with Alpha Forge backtesting.

## Overview

This SDK provides daily market cap rankings that can be used for:

- **Dynamic universe selection**: Build tradeable universes from top N coins
- **Survivorship-bias-free backtesting**: Use historical rankings, not current ones
- **Market cap weighting**: Weight positions by market cap rank

## Symbol Transformation

CoinGecko uses lowercase symbols (e.g., `btc`), while exchanges typically use uppercase pairs (e.g., `BTCUSDT`).

```python
def to_binance_symbol(symbol: str, quote: str = "USDT") -> str:
    """Convert CoinGecko symbol to Binance trading pair."""
    return f"{symbol.upper()}{quote}"

# Example
symbol = "btc"
binance_pair = to_binance_symbol(symbol)  # "BTCUSDT"
```

## Use Cases

### 1. Dynamic Universe Selection

Build a tradeable universe from the top 100 coins at each date:

```python
from crypto_marketcap_rank import load_date_range, get_universe_over_time
from datetime import date

# Load 6 months of data
db = load_date_range("2024-07-01", "2024-12-31")

# Get dynamic universe (top 100 at each date)
universe = get_universe_over_time(
    db,
    start_date=date(2024, 7, 1),
    end_date=date(2024, 12, 31),
    n=100
)

# Convert to Binance symbols
binance_symbols = (
    universe
    .groupby("date")["symbol"]
    .apply(lambda x: [f"{s.upper()}USDT" for s in x])
    .to_dict()
)

# Use in Alpha Forge backtest
# for date, symbols in binance_symbols.items():
#     universe_at_date = symbols
```

### 2. Survivorship-Bias-Free Backtesting

The key insight: use the historical ranking at each date, not the current ranking.

```python
from crypto_marketcap_rank import load_date_range, get_top_n_at_date
from datetime import date, timedelta

# Load historical data
db = load_date_range("2024-01-01", "2024-12-31")

def get_universe_for_date(target_date: date, n: int = 100) -> list[str]:
    """Get tradeable universe as of a specific historical date."""
    df = get_top_n_at_date(db, target_date, n)
    return [f"{s.upper()}USDT" for s in df["symbol"].tolist()]

# Example: What was the top 100 on 2024-06-15?
june_universe = get_universe_for_date(date(2024, 6, 15))
# This includes coins that may have dropped out of top 100 since then
```

### 3. Market Cap Weighting

Weight positions by inverse market cap rank:

```python
import pandas as pd
from crypto_marketcap_rank import load_date_range, get_top_n_at_date
from datetime import date

db = load_date_range("2024-01-01", "2024-12-31")

def get_weights(target_date: date, n: int = 100) -> dict[str, float]:
    """Get inverse-rank weights for top N coins."""
    df = get_top_n_at_date(db, target_date, n)

    # Inverse rank weighting: rank 1 gets highest weight
    df["weight"] = 1 / df["rank"]
    df["weight"] = df["weight"] / df["weight"].sum()  # Normalize

    return dict(zip(
        [f"{s.upper()}USDT" for s in df["symbol"]],
        df["weight"]
    ))

# Example
weights = get_weights(date(2024, 6, 15), n=50)
# {'BTCUSDT': 0.078, 'ETHUSDT': 0.039, ...}
```

### 4. Tracking Universe Changes

Monitor coins entering/exiting the tradeable universe:

```python
from crypto_marketcap_rank import load_date_range, get_rank_changes
from datetime import date

db = load_date_range("2024-01-01", "2024-12-31")

# Weekly rebalance check
changes = get_rank_changes(
    db,
    start_date=date(2024, 6, 1),
    end_date=date(2024, 6, 7),
    n=100
)

# Coins that entered top 100
entered = changes[changes["change_type"] == "entered"]
print(f"New coins: {entered['coin_id'].tolist()}")

# Coins that exited top 100
exited = changes[changes["change_type"] == "exited"]
print(f"Dropped coins: {exited['coin_id'].tolist()}")
```

## Data Schema

All functions return DataFrames with these columns:

| Column                 | Type    | Description                   |
| ---------------------- | ------- | ----------------------------- |
| `date`                 | DATE    | Collection date               |
| `rank`                 | BIGINT  | Market cap rank (1 = highest) |
| `coin_id`              | VARCHAR | CoinGecko identifier          |
| `symbol`               | VARCHAR | Ticker symbol (lowercase)     |
| `name`                 | VARCHAR | Full coin name                |
| `market_cap`           | DOUBLE  | Market cap in USD             |
| `price`                | DOUBLE  | Price in USD                  |
| `volume_24h`           | DOUBLE  | 24h trading volume            |
| `price_change_24h_pct` | DOUBLE  | 24h price change %            |

## Performance Tips

1. **Load once, query many**: `load_date_range()` downloads and caches data. Load the full backtest period once.

2. **Use SQL for filtering**: The `RankingsDatabase.query()` method accepts raw SQL for complex queries.

3. **Cache locally**: Data is cached in `~/.cache/crypto_marketcap_rank/` for 7 days.

## Limitations

- **Daily granularity**: Rankings are updated once per day
- **No intraday data**: For intraday, use exchange APIs directly
- **Coverage**: ~19,000+ coins from CoinGecko (not all are tradeable)
- **Stablecoin filtering**: May need to manually exclude USDT, USDC from universe

## Example: Full Backtest Setup

```python
from crypto_marketcap_rank import load_date_range, get_universe_over_time
from datetime import date

# 1. Load all historical data needed
db = load_date_range("2024-01-01", "2024-12-31")

# 2. Get dynamic universe
universe = get_universe_over_time(db, date(2024, 1, 1), date(2024, 12, 31), n=50)

# 3. Group by date for backtest loop
daily_universes = universe.groupby("date").apply(
    lambda x: [f"{s.upper()}USDT" for s in x["symbol"]]
).to_dict()

# 4. Run backtest with correct historical universe at each date
# for backtest_date in trading_dates:
#     symbols = daily_universes.get(backtest_date, [])
#     # Execute strategy with these symbols only

db.close()
```

## Related Resources

- [SDK Documentation](../../README.md)
- [Schema Definition](../../src/schemas/crypto_rankings_schema.py)
- [GitHub Releases](https://github.com/terrylica/crypto-marketcap-rank/releases)
