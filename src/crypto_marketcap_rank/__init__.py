"""
Crypto Marketcap Rank SDK

Python SDK for loading cryptocurrency market cap rankings from GitHub Releases.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/1

Example:
    >>> from crypto_marketcap_rank import load_latest
    >>> db = load_latest()
    >>> df = db.get_top_n(10)
    >>> print(df[['rank', 'symbol', 'name', 'market_cap']])
"""

from .connection import RankingsDatabase
from .exceptions import CacheError, DataNotFoundError, DownloadError
from .historical import (
    get_available_dates,
    get_coin_history,
    get_rank_changes,
    get_top_n_at_date,
    get_universe_over_time,
)
from .loader import load_date, load_date_range, load_latest

__all__ = [
    # Exceptions
    "CacheError",
    "DataNotFoundError",
    "DownloadError",
    # Database wrapper
    "RankingsDatabase",
    # Historical query functions
    "get_available_dates",
    "get_coin_history",
    "get_rank_changes",
    "get_top_n_at_date",
    "get_universe_over_time",
    # Loader functions
    "load_date",
    "load_date_range",
    "load_latest",
]

__version__ = "0.1.0"
