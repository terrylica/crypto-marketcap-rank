#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyarrow>=15.0.0",
# ]
# ///
"""
Parquet Database Builder

Builds partitioned Parquet files from raw JSON collector output.
Optimized for ClickHouse import (smallest size, native format).

Features:
- Date partitioning: year=YYYY/month=MM/day=DD/
- zstd compression level 3
- 50-150 MB/year compressed
- ClickHouse-native format

Adheres to SLO:
- Correctness: Schema validation, raise on build errors
- Observability: Progress logging for build operations
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pyarrow as pa
import pyarrow.parquet as pq

from .base_builder import BuildError, DatabaseBuilder, DatabaseSchema


class ParquetBuilder(DatabaseBuilder):
    """
    Production Parquet database builder.

    Usage:
        builder = ParquetBuilder()
        parquet_dir = builder.build(input_file=Path("data/raw/coingecko_rankings_2025-11-21.json"))
        builder.validate(parquet_dir)
    """

    def build(self, input_file: Path, output_file: Optional[Path] = None) -> Path:
        """
        Build Parquet files from raw JSON file.

        Args:
            input_file: Path to raw JSON file from collector
            output_file: Optional output directory path (auto-generated if None)

        Returns:
            Path to built Parquet directory

        Raises:
            BuildError: If build fails
        """
        if not input_file.exists():
            raise BuildError(f"Input file not found: {input_file}")

        try:
            # Parse raw JSON
            print(f"Parsing raw JSON: {input_file}")
            collection_date, coins = self._parse_raw_json(input_file)
            print(f"  Date: {collection_date}, Coins: {len(coins)}")

            # Transform to rows
            print("Transforming to database rows...")
            rows = self._transform_to_rows(collection_date, coins)
            print(f"  Rows: {len(rows)}")

            # Generate output directory
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dirname = f"crypto_rankings_{collection_date}_{timestamp}.parquet"
                output_file = self.output_dir / dirname

            output_file.mkdir(parents=True, exist_ok=True)

            # Build Parquet files
            print(f"Building Parquet files: {output_file}")
            self._build_parquet(rows, output_file, collection_date)

            # Get total size
            total_size = sum(f.stat().st_size for f in output_file.rglob("*.parquet"))
            size_mb = total_size / (1024 * 1024)
            print(f"✅ Parquet files built: {output_file} ({size_mb:.1f} MB)")

            return output_file

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Failed to build Parquet files: {e}") from e

    def _build_parquet(self, rows: list, output_dir: Path, collection_date: str) -> None:
        """
        Build Parquet files with partitioning.

        Args:
            rows: List of row dictionaries
            output_dir: Path to output directory
            collection_date: Collection date (YYYY-MM-DD)

        Raises:
            BuildError: If Parquet creation fails
        """
        try:
            # Define PyArrow schema (date as string for simplicity)
            schema = pa.schema([
                ("date", pa.string()),
                ("rank", pa.int32()),
                ("coin_id", pa.string()),
                ("symbol", pa.string()),
                ("name", pa.string()),
                ("market_cap", pa.float64()),
                ("price", pa.float64()),
                ("volume_24h", pa.float64()),
                ("price_change_24h_pct", pa.float64()),
            ])

            # Convert rows to PyArrow table
            table = pa.table({
                "date": [row["date"] for row in rows],
                "rank": [row["rank"] for row in rows],
                "coin_id": [row["coin_id"] for row in rows],
                "symbol": [row["symbol"] for row in rows],
                "name": [row["name"] for row in rows],
                "market_cap": [row["market_cap"] for row in rows],
                "price": [row["price"] for row in rows],
                "volume_24h": [row["volume_24h"] for row in rows],
                "price_change_24h_pct": [row["price_change_24h_pct"] for row in rows],
            }, schema=schema)

            # Parse date for partitioning
            date_obj = datetime.strptime(collection_date, "%Y-%m-%d")
            year = date_obj.year
            month = date_obj.month
            day = date_obj.day

            # Create partition directory
            partition_dir = output_dir / f"year={year}" / f"month={month:02d}" / f"day={day:02d}"
            partition_dir.mkdir(parents=True, exist_ok=True)

            # Write Parquet file with zstd compression
            parquet_file = partition_dir / "data.parquet"
            pq.write_table(
                table,
                parquet_file,
                compression='zstd',
                compression_level=3,
                use_dictionary=True,
            )

        except Exception as e:
            raise BuildError(f"Parquet creation failed: {e}") from e

    def validate(self, database_dir: Path) -> bool:
        """
        Validate built Parquet directory.

        Args:
            database_dir: Path to Parquet directory

        Returns:
            True if valid

        Raises:
            BuildError: If validation fails
        """
        if not database_dir.exists() or not database_dir.is_dir():
            raise BuildError(f"Parquet directory not found: {database_dir}")

        try:
            print(f"Validating Parquet directory: {database_dir}")

            # Find all Parquet files
            parquet_files = list(database_dir.rglob("*.parquet"))
            if not parquet_files:
                raise BuildError("No Parquet files found in directory")

            print(f"  Parquet files: {len(parquet_files)}")

            total_rows = 0
            for pf in parquet_files:
                # Read Parquet file
                table = pq.read_table(pf)
                total_rows += len(table)

                # Check schema
                expected_columns = [col[0] for col in DatabaseSchema.COLUMNS]
                actual_columns = table.schema.names

                missing = set(expected_columns) - set(actual_columns)
                if missing:
                    raise BuildError(f"Missing columns in {pf.name}: {missing}")

                # Check for nulls in required fields
                for field in ["date", "rank", "coin_id"]:
                    null_count = table.column(field).null_count
                    if null_count > 0:
                        raise BuildError(f"Found {null_count} NULL values in required field: {field}")

                # Check rank range
                rank_column = table.column("rank")
                min_rank = rank_column.to_pylist()
                if min_rank:
                    min_val = min(min_rank)
                    max_val = max(min_rank)
                    print(f"  {pf.name}: {len(table)} rows, rank range {min_val}-{max_val}")

            print(f"  Total rows: {total_rows}")

            if total_rows == 0:
                raise BuildError("Parquet directory is empty")

            print("✅ Parquet validation passed")
            return True

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Validation failed: {e}") from e


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: uv run build_parquet.py <input_json_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    builder = ParquetBuilder()

    try:
        # Build Parquet files
        parquet_dir = builder.build(input_file)

        # Validate
        builder.validate(parquet_dir)

        # Calculate total size
        total_size = sum(f.stat().st_size for f in parquet_dir.rglob("*.parquet"))
        size_mb = total_size / (1024 * 1024)

        print(f"\n{'='*80}")
        print("✅ Build successful!")
        print(f"{'='*80}")
        print(f"  Input: {input_file}")
        print(f"  Output: {parquet_dir}")
        print(f"  Size: {size_mb:.1f} MB")
        print(f"{'='*80}")

    except BuildError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
