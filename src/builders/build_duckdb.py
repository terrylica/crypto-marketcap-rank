#!/usr/bin/env python3
# /// script
# dependencies = [
#   "duckdb>=1.0.0",
# ]
# ///
"""
DuckDB Database Builder

Builds single-file DuckDB database from raw JSON collector output.
Primary format for public distribution (instant queryability).

Features:
- Native compression (150-200 MB/year)
- Indexed for fast rank/date queries
- SQL interface
- Single-file distribution

Adheres to SLO:
- Correctness: Schema validation, raise on build errors
- Observability: Progress logging for build operations
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb

from .base_builder import BuildError, DatabaseBuilder, DatabaseSchema


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
        Build DuckDB database from raw JSON file.

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

            # Transform to rows
            print("Transforming to database rows...")
            rows = self._transform_to_rows(collection_date, coins)
            print(f"  Rows: {len(rows)}")

            # Generate output filename
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"crypto_rankings_{collection_date}_{timestamp}.duckdb"
                output_file = self.output_dir / filename

            # Build DuckDB database
            print(f"Building DuckDB database: {output_file}")
            self._build_duckdb(rows, output_file)

            # Get file size
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✅ DuckDB database built: {output_file} ({file_size_mb:.1f} MB)")

            return output_file

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Failed to build DuckDB database: {e}") from e

    def _build_duckdb(self, rows: list, output_file: Path) -> None:
        """
        Build DuckDB database file with schema and indexes.

        Args:
            rows: List of row dictionaries
            output_file: Path to output .duckdb file

        Raises:
            BuildError: If database creation fails
        """
        try:
            # Create database
            con = duckdb.connect(str(output_file))

            # Create table with schema
            con.execute("""
                CREATE TABLE rankings (
                    date DATE NOT NULL,
                    rank INTEGER NOT NULL,
                    coin_id VARCHAR NOT NULL,
                    symbol VARCHAR,
                    name VARCHAR,
                    market_cap DOUBLE,
                    price DOUBLE,
                    volume_24h DOUBLE,
                    price_change_24h_pct DOUBLE
                )
            """)

            # Insert data
            con.executemany("""
                INSERT INTO rankings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    row["date"],
                    row["rank"],
                    row["coin_id"],
                    row["symbol"],
                    row["name"],
                    row["market_cap"],
                    row["price"],
                    row["volume_24h"],
                    row["price_change_24h_pct"],
                )
                for row in rows
            ])

            # Create indexes for fast queries
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
        Validate built DuckDB database.

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

            # Check schema
            schema = con.execute("DESCRIBE rankings").fetchall()
            expected_columns = [col[0] for col in DatabaseSchema.COLUMNS]
            actual_columns = [row[0] for row in schema]

            missing = set(expected_columns) - set(actual_columns)
            if missing:
                raise BuildError(f"Missing columns in database: {missing}")

            # Check for nulls in required fields
            null_checks = [
                ("date", con.execute("SELECT COUNT(*) FROM rankings WHERE date IS NULL").fetchone()[0]),
                ("rank", con.execute("SELECT COUNT(*) FROM rankings WHERE rank IS NULL").fetchone()[0]),
                ("coin_id", con.execute("SELECT COUNT(*) FROM rankings WHERE coin_id IS NULL").fetchone()[0]),
            ]

            for field, null_count in null_checks:
                if null_count > 0:
                    raise BuildError(f"Found {null_count} NULL values in required field: {field}")

            # Check rank sequence
            min_rank = con.execute("SELECT MIN(rank) FROM rankings").fetchone()[0]
            max_rank = con.execute("SELECT MAX(rank) FROM rankings").fetchone()[0]
            print(f"  Rank range: {min_rank} to {max_rank}")

            if min_rank != 1:
                raise BuildError(f"Invalid minimum rank: {min_rank} (expected 1)")

            # Check for duplicates
            dup_count = con.execute("""
                SELECT COUNT(*) FROM (
                    SELECT date, rank, COUNT(*) as cnt
                    FROM rankings
                    GROUP BY date, rank
                    HAVING cnt > 1
                )
            """).fetchone()[0]

            if dup_count > 0:
                raise BuildError(f"Found {dup_count} duplicate (date, rank) pairs")

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

        print(f"\n{'='*80}")
        print("✅ Build successful!")
        print(f"{'='*80}")
        print(f"  Input: {input_file}")
        print(f"  Output: {db_file}")
        print(f"  Size: {db_file.stat().st_size / (1024*1024):.1f} MB")
        print(f"{'='*80}")

    except BuildError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
