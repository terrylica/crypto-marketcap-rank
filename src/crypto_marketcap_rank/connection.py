"""
RankingsDatabase Connection Wrapper

DuckDB connection wrapper with convenience methods.
Pattern copied from src/builders/build_duckdb.py (DuckDB patterns).

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/1
"""

import logging
from pathlib import Path
from types import TracebackType

import duckdb
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RankingsDatabase:
    """DuckDB connection wrapper with convenience methods.

    Provides high-level API for querying cryptocurrency rankings data.

    Usage:
        # Context manager (recommended)
        with RankingsDatabase(db_path) as db:
            df = db.get_top_n(100)

        # Manual management
        db = RankingsDatabase(db_path)
        df = db.query("SELECT * FROM rankings WHERE rank <= 10")
        db.close()
    """

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to DuckDB database file.
        """
        self._path = db_path
        self._con = duckdb.connect(str(db_path), read_only=True)
        logger.debug(f"Connected to database: {db_path}")

    def query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame.

        Args:
            sql: SQL query string.

        Returns:
            pandas DataFrame with query results.
        """
        return self._con.execute(sql).df()

    def get_top_n(self, n: int = 100) -> pd.DataFrame:
        """Get top N coins by market cap rank.

        Args:
            n: Number of coins to return (default: 100).

        Returns:
            DataFrame with top N coins ordered by rank.
        """
        return self.query(f"SELECT * FROM rankings ORDER BY rank LIMIT {n}")

    def find_coin(self, symbol: str) -> pd.DataFrame:
        """Find coin by symbol (case-insensitive).

        Args:
            symbol: Coin symbol to search for (e.g., 'btc', 'eth').

        Returns:
            DataFrame with matching coin(s).
        """
        return self.query(f"SELECT * FROM rankings WHERE LOWER(symbol) = LOWER('{symbol}')")

    def get_by_rank_range(self, min_rank: int, max_rank: int) -> pd.DataFrame:
        """Get coins within a rank range.

        Args:
            min_rank: Minimum rank (inclusive).
            max_rank: Maximum rank (inclusive).

        Returns:
            DataFrame with coins in the specified rank range.
        """
        return self.query(
            f"SELECT * FROM rankings WHERE rank BETWEEN {min_rank} AND {max_rank} ORDER BY rank"
        )

    def export_parquet(
        self,
        output_path: Path,
        compression: str = "zstd",
    ) -> Path:
        """Export to Parquet format.

        Args:
            output_path: Output file path.
            compression: Compression codec (zstd, snappy, gzip).

        Returns:
            Path to exported file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._con.execute(f"""
            COPY rankings TO '{output_path}' (
                FORMAT PARQUET,
                COMPRESSION {compression}
            )
        """)

        logger.info(f"Exported to Parquet: {output_path}")
        return output_path

    def export_csv(self, output_path: Path) -> Path:
        """Export to CSV format.

        Args:
            output_path: Output file path.

        Returns:
            Path to exported file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._con.execute(f"COPY rankings TO '{output_path}' (FORMAT CSV, HEADER)")

        logger.info(f"Exported to CSV: {output_path}")
        return output_path

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Raw DuckDB connection for advanced queries.

        Returns:
            DuckDB connection object.
        """
        return self._con

    @property
    def path(self) -> Path:
        """Path to the database file.

        Returns:
            Database file path.
        """
        return self._path

    def close(self) -> None:
        """Close database connection."""
        if self._con:
            self._con.close()
            logger.debug(f"Closed connection to: {self._path}")

    def __enter__(self) -> "RankingsDatabase":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"RankingsDatabase('{self._path}')"
