#!/usr/bin/env python3
"""
Base Database Builder

Abstract base class for all database builders (DuckDB, Parquet).
Transforms API responses to PyArrow Tables using Schema V2.

Adheres to SLO:
- Correctness: PyArrow schema enforcement, comprehensive validation
- Observability: Progress logging for build operations
"""

from abc import ABC, abstractmethod
from datetime import date as date_type
from pathlib import Path
from typing import Any, Dict, List, Optional

import pyarrow as pa

from schemas.crypto_rankings_schema import CRYPTO_RANKINGS_SCHEMA_V2


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
            with open(input_file, "r") as f:
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

    def _safe_int(self, value, fallback=None):
        """
        Safely convert value to int with fallback.

        Args:
            value: Value to convert (can be int, str, float, or None)
            fallback: Fallback value if conversion fails

        Returns:
            int or fallback value
        """
        if value is None:
            return fallback
        if isinstance(value, int):
            return value
        try:
            # Handle string, float, or other types
            if isinstance(value, str):
                value = value.strip()
                if not value:  # Empty string
                    return fallback
            return int(float(value))  # Convert via float to handle "123.45" -> 123
        except (ValueError, TypeError, AttributeError):
            return fallback

    def _safe_float(self, value):
        """
        Safely convert value to float, return None if invalid.

        Args:
            value: Value to convert (can be int, str, float, or None)

        Returns:
            float or None
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            if isinstance(value, str):
                value = value.strip()
                if not value:  # Empty string
                    return None
            return float(value)
        except (ValueError, TypeError, AttributeError):
            return None

    def _transform_to_rows(self, collection_date: str, coins: List[Dict[str, Any]]) -> pa.Table:
        """
        Transform API response coins to PyArrow Table.

        This method performs defensive type coercion to handle mixed types
        from the CoinGecko API (int/float/string variants).

        Args:
            collection_date: Collection date (YYYY-MM-DD)
            coins: List of coin dictionaries from API

        Returns:
            PyArrow Table conforming to CRYPTO_RANKINGS_SCHEMA_V2

        Raises:
            BuildError: If table construction fails
        """
        # Parse date string to Python date object
        try:
            date_obj = date_type.fromisoformat(collection_date)
        except ValueError as e:
            raise BuildError(f"Invalid collection_date format: {collection_date}") from e

        # Pre-allocate lists for each column (more efficient than row-by-row)
        dates = []
        ranks = []
        coin_ids = []
        symbols = []
        names = []
        market_caps = []
        prices = []
        volumes_24h = []
        price_changes_24h_pct = []

        for idx, coin in enumerate(coins, start=1):
            # Explicit type coercion for all numeric fields
            # API may return strings, especially for lower-ranked coins
            rank = self._safe_int(coin.get("market_cap_rank"), fallback=idx)

            dates.append(date_obj)
            ranks.append(rank)
            coin_ids.append(coin.get("id"))
            symbols.append(coin.get("symbol"))
            names.append(coin.get("name"))
            market_caps.append(self._safe_float(coin.get("market_cap")))
            prices.append(self._safe_float(coin.get("current_price")))
            volumes_24h.append(self._safe_float(coin.get("total_volume")))
            price_changes_24h_pct.append(self._safe_float(coin.get("price_change_percentage_24h")))

        # Construct PyArrow Table with strict schema enforcement
        try:
            table = pa.table(
                {
                    "date": dates,
                    "rank": ranks,
                    "coin_id": coin_ids,
                    "symbol": symbols,
                    "name": names,
                    "market_cap": market_caps,
                    "price": prices,
                    "volume_24h": volumes_24h,
                    "price_change_24h_pct": price_changes_24h_pct,
                },
                schema=CRYPTO_RANKINGS_SCHEMA_V2,
            )
            return table
        except Exception as e:
            raise BuildError(f"Failed to construct PyArrow table: {e}") from e
