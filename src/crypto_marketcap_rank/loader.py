"""
SDK Loader Functions

Main API functions for loading cryptocurrency rankings data.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/1
"""

import logging
import tempfile
from datetime import date
from pathlib import Path

import duckdb

from .cache import CacheManager
from .connection import RankingsDatabase
from .exceptions import DataNotFoundError
from .github_api import GitHubReleasesClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_latest(
    cache_dir: Path | None = None,
    force_refresh: bool = False,
) -> RankingsDatabase:
    """Load the most recent rankings database.

    Downloads from GitHub Releases if not cached locally.

    Args:
        cache_dir: Custom cache directory. Defaults to ~/.cache/crypto_marketcap_rank/
        force_refresh: If True, re-download even if cached.

    Returns:
        RankingsDatabase connection for querying.

    Raises:
        DataNotFoundError: If no releases available.
        DownloadError: If download fails.

    Example:
        >>> db = load_latest()
        >>> df = db.get_top_n(10)
        >>> print(df[['rank', 'symbol', 'name', 'market_cap']])
    """
    logger.info("Loading latest rankings database...")

    cache = CacheManager(cache_dir)
    client = GitHubReleasesClient()

    # Get latest release info
    release = client.get_latest_release()
    logger.info(f"Latest release: {release.tag} ({release.date})")

    # Get or download cached database
    db_path = cache.get_or_download(release, force_refresh=force_refresh)

    return RankingsDatabase(db_path)


def load_date(
    target_date: date | str,
    cache_dir: Path | None = None,
    force_refresh: bool = False,
) -> RankingsDatabase:
    """Load rankings for a specific date.

    Args:
        target_date: Date as datetime.date or 'YYYY-MM-DD' string.
        cache_dir: Custom cache directory.
        force_refresh: If True, re-download even if cached.

    Returns:
        RankingsDatabase connection.

    Raises:
        DataNotFoundError: If no release for that date.
        DownloadError: If download fails.

    Example:
        >>> db = load_date("2025-01-15")
        >>> df = db.find_coin("btc")
        >>> print(df[['rank', 'price', 'market_cap']])
    """
    # Parse string date if needed
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    logger.info(f"Loading rankings for {target_date}...")

    cache = CacheManager(cache_dir)
    client = GitHubReleasesClient()

    # Get release for specific date
    release = client.get_release_by_date(target_date)

    # Get or download cached database
    db_path = cache.get_or_download(release, force_refresh=force_refresh)

    return RankingsDatabase(db_path)


def load_date_range(
    start_date: date | str,
    end_date: date | str,
    cache_dir: Path | None = None,
) -> RankingsDatabase:
    """Load rankings for a date range (merged into single database).

    Downloads all releases in range and merges into a unified view.
    Useful for historical analysis and backtesting.

    Args:
        start_date: Start date (inclusive) as date or 'YYYY-MM-DD'.
        end_date: End date (inclusive) as date or 'YYYY-MM-DD'.
        cache_dir: Custom cache directory.

    Returns:
        RankingsDatabase with merged data from all dates.

    Raises:
        DataNotFoundError: If no releases found in range.
        DownloadError: If download fails.

    Example:
        >>> db = load_date_range("2025-01-01", "2025-01-31")
        >>> df = db.query("SELECT DISTINCT date FROM rankings ORDER BY date")
        >>> print(f"Dates loaded: {len(df)}")
    """
    # Parse string dates if needed
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    logger.info(f"Loading rankings from {start_date} to {end_date}...")

    cache = CacheManager(cache_dir)
    client = GitHubReleasesClient()

    # Collect all dates in range
    dates_to_load = []
    current = start_date
    while current <= end_date:
        dates_to_load.append(current)
        current = date(current.year, current.month, current.day + 1) if current.day < 28 else _next_day(current)

    if not dates_to_load:
        raise DataNotFoundError(f"No dates in range {start_date} to {end_date}")

    # Download all available releases
    db_paths = []
    skipped_dates = []

    for target_date in dates_to_load:
        try:
            release = client.get_release_by_date(target_date)
            db_path = cache.get_or_download(release)
            db_paths.append(db_path)
        except DataNotFoundError:
            skipped_dates.append(target_date)
            logger.debug(f"No release for {target_date}, skipping")

    if not db_paths:
        raise DataNotFoundError(f"No releases found between {start_date} and {end_date}")

    if skipped_dates:
        logger.warning(f"Skipped {len(skipped_dates)} dates with no releases")

    # Merge into single database
    merged_path = _merge_databases(db_paths, cache_dir)

    logger.info(f"Loaded {len(db_paths)} dates, merged into {merged_path}")
    return RankingsDatabase(merged_path)


def get_data_availability() -> dict:
    """Get information about available data without downloading.

    Queries GitHub API to determine the date range of available data.

    Returns:
        Dictionary with availability info:
        - earliest: Earliest available date (datetime.date)
        - latest: Most recent available date (datetime.date)
        - total_days: Number of days with data
        - source: Data source description

    Example:
        >>> from crypto_marketcap_rank import get_data_availability
        >>> info = get_data_availability()
        >>> print(f"Data available from {info['earliest']} to {info['latest']}")
        >>> print(f"Total days: {info['total_days']}")
    """
    client = GitHubReleasesClient()
    return client.get_data_availability()


def _next_day(d: date) -> date:
    """Get next day, handling month/year boundaries."""
    from datetime import timedelta
    return d + timedelta(days=1)


def _merge_databases(db_paths: list[Path], cache_dir: Path | None) -> Path:
    """Merge multiple DuckDB databases into one.

    Uses DuckDB ATTACH to read from source databases and merge data.

    Args:
        db_paths: List of database file paths.
        cache_dir: Cache directory for merged database.

    Returns:
        Path to merged database.
    """
    if len(db_paths) == 1:
        return db_paths[0]

    # Create merged database in cache or temp
    if cache_dir:
        merged_path = cache_dir / "merged_rankings.duckdb"
    else:
        merged_path = Path(tempfile.gettempdir()) / "crypto_marketcap_rank_merged.duckdb"

    # Remove existing merged database
    merged_path.unlink(missing_ok=True)

    # Create and populate merged database using ATTACH
    con = duckdb.connect(str(merged_path))

    for i, db_path in enumerate(db_paths):
        alias = f"db_{i}"
        con.execute(f"ATTACH '{db_path}' AS {alias} (READ_ONLY)")

        if i == 0:
            # Create table from first database
            con.execute(f"CREATE TABLE rankings AS SELECT * FROM {alias}.rankings")
        else:
            # Insert from subsequent databases
            con.execute(f"INSERT INTO rankings SELECT * FROM {alias}.rankings")

        con.execute(f"DETACH {alias}")

    # Create indexes for query performance
    con.execute("CREATE INDEX IF NOT EXISTS idx_date ON rankings(date)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_rank ON rankings(rank)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_coin_id ON rankings(coin_id)")
    con.execute("CHECKPOINT")
    con.close()

    logger.info(f"Merged {len(db_paths)} databases into {merged_path}")
    return merged_path
