#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyarrow>=15.0.0",
# ]
# ///
"""
Parquet Database Builder

Builds partitioned Parquet files from raw JSON collector output.
Uses Schema V2 with native PyArrow types (pa.date32(), pa.int64()).

Features:
- Schema V2: Native DATE type, INT64 ranks
- Hive-style partitioning: year=/month=/day=/
- zstd compression level 3
- Comprehensive validation before write
- ClickHouse-native format

Adheres to SLO:
- Correctness: PyArrow schema enforcement + comprehensive validation
- Observability: Progress logging for build operations
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pyarrow as pa
import pyarrow.parquet as pq

from validators import validate_arrow_table

from .base_builder import BuildError, DatabaseBuilder


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
        Build Parquet files from raw JSON file using Schema V2.

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

            # Transform to PyArrow Table
            print("Transforming to PyArrow Table...")
            table = self._transform_to_rows(collection_date, coins)
            print(f"  Rows: {len(table)}")

            # Validate table before writing
            print("Validating table...")
            errors = validate_arrow_table(table)
            if errors:
                error_messages = "\n".join([f"  - {e}" for e in errors])
                raise BuildError(f"Validation failed with {len(errors)} error(s):\n{error_messages}")
            print("  ✅ Validation passed")

            # Generate output directory
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dirname = f"crypto_rankings_{collection_date}_{timestamp}.parquet"
                output_file = self.output_dir / dirname

            output_file.mkdir(parents=True, exist_ok=True)

            # Build Parquet files
            print(f"Building Parquet files: {output_file}")
            self._build_parquet(table, output_file, collection_date)

            # Get total size
            total_size = sum(f.stat().st_size for f in output_file.rglob("*.parquet"))
            size_mb = total_size / (1024 * 1024)
            print(f"✅ Parquet files built: {output_file} ({size_mb:.1f} MB)")

            return output_file

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Failed to build Parquet files: {e}") from e

    def _build_parquet(self, table: pa.Table, output_dir: Path, collection_date: str) -> None:
        """
        Build Parquet files with Hive-style partitioning.

        Args:
            table: PyArrow Table with Schema V2
            output_dir: Path to output directory
            collection_date: Collection date (YYYY-MM-DD)

        Raises:
            BuildError: If Parquet creation fails
        """
        try:
            # Parse date for partitioning
            date_obj = datetime.strptime(collection_date, "%Y-%m-%d")
            year = date_obj.year
            month = date_obj.month
            day = date_obj.day

            # Create Hive-style partition directory (year=/month=/day=/)
            partition_dir = output_dir / f"year={year}" / f"month={month:02d}" / f"day={day:02d}"
            partition_dir.mkdir(parents=True, exist_ok=True)

            # Write Parquet file with zstd compression
            parquet_file = partition_dir / "data.parquet"
            pq.write_table(
                table,
                parquet_file,
                compression="zstd",
                compression_level=3,
                use_dictionary=True,
            )

            print(f"  Wrote: {parquet_file.relative_to(output_dir)}")

        except Exception as e:
            raise BuildError(f"Parquet creation failed: {e}") from e

    def validate(self, database_dir: Path) -> bool:
        """
        Validate built Parquet directory using comprehensive Schema V2 validation.

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
            all_errors = []

            for pf in parquet_files:
                # Read Parquet file
                table = pq.read_table(pf)
                total_rows += len(table)

                # Comprehensive validation
                errors = validate_arrow_table(table)
                if errors:
                    all_errors.extend([f"{pf.name}: {e}" for e in errors])

                # Print summary
                if not errors:
                    rank_column = table.column("rank")
                    ranks = rank_column.to_pylist()
                    if ranks:
                        min_val = min(ranks)
                        max_val = max(ranks)
                        print(f"  {pf.name}: {len(table)} rows, rank range {min_val}-{max_val}")

            # Check if any errors found
            if all_errors:
                error_messages = "\n".join([f"  - {e}" for e in all_errors])
                raise BuildError(f"Validation failed with {len(all_errors)} error(s):\n{error_messages}")

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

        print(f"\n{'=' * 80}")
        print("✅ Build successful!")
        print(f"{'=' * 80}")
        print(f"  Input: {input_file}")
        print(f"  Output: {parquet_dir}")
        print(f"  Size: {size_mb:.1f} MB")
        print(f"{'=' * 80}")

    except BuildError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
