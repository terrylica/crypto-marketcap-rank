#!/usr/bin/env python3
"""
Base Database Builder

Abstract base class for all database builders (DuckDB, Parquet, CSV).
Defines shared schema and validation logic.

Adheres to SLO:
- Correctness: Schema validation, raise on invalid data
- Observability: Progress logging for build operations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class DatabaseSchema:
    """
    Standard schema for all database formats.

    Fields:
    - date: Collection date (YYYY-MM-DD)
    - rank: Market cap rank (1-based)
    - coin_id: CoinGecko coin ID
    - symbol: Ticker symbol
    - name: Coin name
    - market_cap: Market capitalization in USD
    - price: Current price in USD
    - volume_24h: 24-hour trading volume in USD
    - price_change_24h_pct: 24-hour price change percentage
    """

    COLUMNS = [
        ("date", "DATE"),
        ("rank", "INTEGER"),
        ("coin_id", "VARCHAR"),
        ("symbol", "VARCHAR"),
        ("name", "VARCHAR"),
        ("market_cap", "DOUBLE"),
        ("price", "DOUBLE"),
        ("volume_24h", "DOUBLE"),
        ("price_change_24h_pct", "DOUBLE"),
    ]

    @classmethod
    def validate_row(cls, row: Dict[str, Any]) -> None:
        """
        Validate single row against schema.

        Args:
            row: Dictionary with column values

        Raises:
            ValueError: If row is invalid
        """
        required_fields = [col[0] for col in cls.COLUMNS]
        missing = [f for f in required_fields if f not in row]
        if missing:
            raise ValueError(f"Row missing required fields: {missing}")

        # Validate types
        if row["rank"] is not None and (not isinstance(row["rank"], int) or row["rank"] < 1):
            raise ValueError(f"Invalid rank: {row['rank']}")

        if row["market_cap"] is not None and row["market_cap"] < 0:
            raise ValueError(f"Invalid market_cap: {row['market_cap']}")


class BuildError(Exception):
    """Raised when database build fails."""
    pass


class DatabaseBuilder(ABC):
    """
    Abstract base class for database builders.

    All builders must implement:
    - build(): Build database from raw JSON files
    - validate(): Validate built database
    """

    def __init__(self, output_dir: str = "data/processed"):
        """
        Initialize builder.

        Args:
            output_dir: Directory to save built databases
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def build(self, input_file: Path, output_file: Optional[Path] = None) -> Path:
        """
        Build database from raw JSON file.

        Args:
            input_file: Path to raw JSON file from collector
            output_file: Optional output path (auto-generated if None)

        Returns:
            Path to built database file

        Raises:
            BuildError: If build fails
        """
        pass

    @abstractmethod
    def validate(self, database_file: Path) -> bool:
        """
        Validate built database.

        Args:
            database_file: Path to database file

        Returns:
            True if valid

        Raises:
            BuildError: If validation fails
        """
        pass

    def _parse_raw_json(self, input_file: Path) -> tuple[str, List[Dict[str, Any]]]:
        """
        Parse raw JSON file from collector.

        Args:
            input_file: Path to raw JSON file

        Returns:
            Tuple of (collection_date, list of coin records)

        Raises:
            BuildError: If JSON is invalid
        """
        import json

        try:
            with open(input_file, 'r') as f:
                data = json.load(f)

            if "metadata" not in data or "coins" not in data:
                raise BuildError("Invalid JSON structure: missing metadata or coins")

            collection_date = data["metadata"]["collection_date"]
            coins = data["coins"]

            return collection_date, coins

        except json.JSONDecodeError as e:
            raise BuildError(f"Invalid JSON file: {e}") from e
        except Exception as e:
            raise BuildError(f"Failed to parse raw JSON: {e}") from e

    def _transform_to_rows(self, collection_date: str, coins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform API response coins to database rows.

        Args:
            collection_date: Collection date (YYYY-MM-DD)
            coins: List of coin dictionaries from API

        Returns:
            List of row dictionaries matching DatabaseSchema
        """
        rows = []

        for idx, coin in enumerate(coins, start=1):
            row = {
                "date": collection_date,
                "rank": coin.get("market_cap_rank") or idx,
                "coin_id": coin.get("id"),
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "market_cap": coin.get("market_cap"),
                "price": coin.get("current_price"),
                "volume_24h": coin.get("total_volume"),
                "price_change_24h_pct": coin.get("price_change_percentage_24h"),
            }

            # Validate row
            DatabaseSchema.validate_row(row)
            rows.append(row)

        return rows
