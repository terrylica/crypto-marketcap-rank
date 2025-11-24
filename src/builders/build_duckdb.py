#!/usr/bin/env python3
# /// script
# dependencies = [
#   "duckdb>=1.0.0",
#   "pyarrow>=15.0.0",
# ]
# ///
"""
DuckDB Database Builder

Builds single-file DuckDB database from raw JSON collector output.
Uses Schema V2 with zero-copy PyArrow → DuckDB integration.

Features:
- Schema V2: Native DATE type, BIGINT ranks (INT64)
- Zero-copy Arrow integration (instant, memory-efficient)
- Native compression (150-200 MB/year)
- Indexed for fast rank/date queries
- Comprehensive validation
- Single-file distribution

Adheres to SLO:
- Correctness: PyArrow schema enforcement + comprehensive validation
- Observability: Progress logging for build operations
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb
import pyarrow as pa

from validators import validate_arrow_table

from .base_builder import BuildError, DatabaseBuilder


class DuckDBBuilder(DatabaseBuilder):
    """
    Production DuckDB database builder.

    Usage:
        builder = DuckDBBuilder()
        db_file = builder.build(input_file=Path("data/raw/coingecko_rankings_2025-11-21.json"))
        builder.validate(db_file)
    """

    def build(self, input_file: Path, output_file: Optional[Path] = None) -> Path:
        """
        Build DuckDB database from raw JSON file using Schema V2.

        Args:
            input_file: Path to raw JSON file from collector
            output_file: Optional output path (auto-generated if None)

        Returns:
            Path to built .duckdb file

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

            # Generate output filename
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"crypto_rankings_{collection_date}_{timestamp}.duckdb"
                output_file = self.output_dir / filename

            # Build DuckDB database
            print(f"Building DuckDB database: {output_file}")
            self._build_duckdb(table, output_file)

            # Get file size
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✅ DuckDB database built: {output_file} ({file_size_mb:.1f} MB)")

            return output_file

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Failed to build DuckDB database: {e}") from e

    def _build_duckdb(self, table: pa.Table, output_file: Path) -> None:
        """
        Build DuckDB database file using zero-copy Arrow integration.

        Uses DuckDB's native Arrow C Data Interface for instant, memory-efficient
        table creation without serialization overhead.

        Args:
            table: PyArrow Table with Schema V2
            output_file: Path to output .duckdb file

        Raises:
            BuildError: If database creation fails
        """
        try:
            # Create database
            con = duckdb.connect(str(output_file))

            # Zero-copy Arrow → DuckDB via Arrow C Data Interface
            # Register PyArrow table as temp view
            con.register("arrow_temp", table)

            # Create table from Arrow data (zero-copy, instant)
            # DuckDB automatically maps Arrow types to SQL types:
            # - pa.date32() → DATE
            # - pa.int64() → BIGINT
            # - pa.float64() → DOUBLE
            # - pa.string() → VARCHAR
            con.execute("""
                CREATE TABLE rankings AS
                SELECT * FROM arrow_temp
            """)

            # Unregister temp view
            con.unregister("arrow_temp")

            # Create indexes for fast queries
            print("  Creating indexes...")
            con.execute("CREATE INDEX idx_date ON rankings(date)")
            con.execute("CREATE INDEX idx_rank ON rankings(rank)")
            con.execute("CREATE INDEX idx_coin_id ON rankings(coin_id)")

            # Optimize database
            con.execute("CHECKPOINT")

            con.close()

        except Exception as e:
            # Clean up on failure
            if output_file.exists():
                output_file.unlink()
            raise BuildError(f"DuckDB creation failed: {e}") from e

    def validate(self, database_file: Path) -> bool:
        """
        Validate built DuckDB database using comprehensive Schema V2 validation.

        Args:
            database_file: Path to .duckdb file

        Returns:
            True if valid

        Raises:
            BuildError: If validation fails
        """
        if not database_file.exists():
            raise BuildError(f"Database file not found: {database_file}")

        try:
            print(f"Validating DuckDB database: {database_file}")
            con = duckdb.connect(str(database_file), read_only=True)

            # Check table exists
            tables = con.execute("SHOW TABLES").fetchall()
            if not any("rankings" in str(t) for t in tables):
                raise BuildError("Table 'rankings' not found in database")

            # Check row count
            row_count = con.execute("SELECT COUNT(*) FROM rankings").fetchone()[0]
            print(f"  Row count: {row_count}")
            if row_count == 0:
                raise BuildError("Database is empty")

            # Convert DuckDB table to Arrow for comprehensive validation
            print("  Reading table for validation...")
            arrow_table = con.execute("SELECT * FROM rankings").fetch_arrow_table()

            # Comprehensive validation using shared validator
            errors = validate_arrow_table(arrow_table)
            if errors:
                error_messages = "\n".join([f"  - {e}" for e in errors])
                raise BuildError(f"Validation failed with {len(errors)} error(s):\n{error_messages}")

            # Print summary
            min_rank = con.execute("SELECT MIN(rank) FROM rankings").fetchone()[0]
            max_rank = con.execute("SELECT MAX(rank) FROM rankings").fetchone()[0]
            print(f"  Rank range: {min_rank} to {max_rank}")

            con.close()

            print("✅ DuckDB validation passed")
            return True

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Validation failed: {e}") from e


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: uv run build_duckdb.py <input_json_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    builder = DuckDBBuilder()

    try:
        # Build database
        db_file = builder.build(input_file)

        # Validate
        builder.validate(db_file)

        print(f"\n{'=' * 80}")
        print("✅ Build successful!")
        print(f"{'=' * 80}")
        print(f"  Input: {input_file}")
        print(f"  Output: {db_file}")
        print(f"  Size: {db_file.stat().st_size / (1024 * 1024):.1f} MB")
        print(f"{'=' * 80}")

    except BuildError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
