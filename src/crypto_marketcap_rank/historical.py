"""
Historical Data Query Functions.

Convenience functions for backtesting and historical analysis.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/3
"""

from datetime import date

import pandas as pd

from .connection import RankingsDatabase


def get_top_n_at_date(db: RankingsDatabase, target_date: date, n: int = 100) -> pd.DataFrame:
    """Get top N coins at specific historical date.

    Args:
        db: RankingsDatabase connection (from load_date_range).
        target_date: Historical date to query.
        n: Number of top coins to return.

    Returns:
        DataFrame with top N coins at the specified date.

    Example:
        >>> db = load_date_range("2025-01-01", "2025-01-31")
        >>> df = get_top_n_at_date(db, date(2025, 1, 15), n=100)
    """
    return db.query(f"""
        SELECT * FROM rankings
        WHERE date = '{target_date}'
        ORDER BY rank
        LIMIT {n}
    """)


def get_universe_over_time(
    db: RankingsDatabase,
    start_date: date,
    end_date: date,
    n: int = 100,
) -> pd.DataFrame:
    """Get dynamic universe (top N at each date in range).

    Returns all coins that were in top N on any date within the range.
    Useful for survivorship-bias-free backtesting.

    Args:
        db: RankingsDatabase connection (from load_date_range).
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        n: Universe size (top N at each date).

    Returns:
        DataFrame with all (date, coin) pairs where coin was in top N.

    Example:
        >>> db = load_date_range("2025-01-01", "2025-01-31")
        >>> df = get_universe_over_time(db, date(2025, 1, 1), date(2025, 1, 31), n=100)
    """
    return db.query(f"""
        SELECT * FROM rankings
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
          AND rank <= {n}
        ORDER BY date, rank
    """)


def get_coin_history(
    db: RankingsDatabase,
    coin_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pd.DataFrame:
    """Get historical data for a specific coin.

    Args:
        db: RankingsDatabase connection.
        coin_id: CoinGecko coin identifier (e.g., 'bitcoin').
        start_date: Optional start date filter.
        end_date: Optional end date filter.

    Returns:
        DataFrame with coin's historical data ordered by date.

    Example:
        >>> db = load_date_range("2025-01-01", "2025-12-31")
        >>> btc = get_coin_history(db, "bitcoin")
    """
    where_clauses = [f"coin_id = '{coin_id}'"]

    if start_date:
        where_clauses.append(f"date >= '{start_date}'")
    if end_date:
        where_clauses.append(f"date <= '{end_date}'")

    where = " AND ".join(where_clauses)

    return db.query(f"""
        SELECT * FROM rankings
        WHERE {where}
        ORDER BY date
    """)


def get_rank_changes(
    db: RankingsDatabase,
    start_date: date,
    end_date: date,
    n: int = 100,
) -> pd.DataFrame:
    """Get coins that entered or exited top N during the period.

    Identifies coins that:
    - Entered top N (wasn't in top N at start, is in top N at end)
    - Exited top N (was in top N at start, isn't in top N at end)

    Args:
        db: RankingsDatabase connection.
        start_date: Start date.
        end_date: End date.
        n: Universe size (top N).

    Returns:
        DataFrame with columns: coin_id, start_rank, end_rank, change_type
        where change_type is 'entered', 'exited', or 'stayed'.
    """
    return db.query(f"""
        WITH start_rankings AS (
            SELECT coin_id, rank as start_rank
            FROM rankings
            WHERE date = '{start_date}' AND rank <= {n}
        ),
        end_rankings AS (
            SELECT coin_id, rank as end_rank
            FROM rankings
            WHERE date = '{end_date}' AND rank <= {n}
        )
        SELECT
            COALESCE(s.coin_id, e.coin_id) as coin_id,
            s.start_rank,
            e.end_rank,
            CASE
                WHEN s.coin_id IS NULL THEN 'entered'
                WHEN e.coin_id IS NULL THEN 'exited'
                ELSE 'stayed'
            END as change_type
        FROM start_rankings s
        FULL OUTER JOIN end_rankings e ON s.coin_id = e.coin_id
        ORDER BY
            CASE change_type
                WHEN 'entered' THEN 1
                WHEN 'exited' THEN 2
                ELSE 3
            END,
            COALESCE(e.end_rank, s.start_rank)
    """)


def get_available_dates(db: RankingsDatabase) -> list[date]:
    """Get list of all available dates in the database.

    Args:
        db: RankingsDatabase connection.

    Returns:
        Sorted list of available dates.
    """
    df = db.query("SELECT DISTINCT date FROM rankings ORDER BY date")
    return df["date"].tolist()
