#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
CSV Database Builder

Builds gzip-compressed CSV file from raw JSON collector output.
Maximum compatibility format (spreadsheets, legacy tools).

Features:
- Simple CSV format
- gzip compression
- ~50 MB/year compressed
- Universal compatibility

Adheres to SLO:
- Correctness: Schema validation, raise on build errors
- Observability: Progress logging for build operations
"""

import csv
import gzip
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base_builder import BuildError, DatabaseBuilder, DatabaseSchema


class CSVBuilder(DatabaseBuilder):
    """
    Production CSV database builder.

    Usage:
        builder = CSVBuilder()
        csv_file = builder.build(input_file=Path("data/raw/coingecko_rankings_2025-11-21.json"))
        builder.validate(csv_file)
    """

    def build(self, input_file: Path, output_file: Optional[Path] = None) -> Path:
        """
        Build CSV file from raw JSON file.

        Args:
            input_file: Path to raw JSON file from collector
            output_file: Optional output path (auto-generated if None)

        Returns:
            Path to built .csv.gz file

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
                filename = f"crypto_rankings_{collection_date}_{timestamp}.csv.gz"
                output_file = self.output_dir / filename

            # Build CSV file
            print(f"Building CSV file: {output_file}")
            self._build_csv(rows, output_file)

            # Get file size
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✅ CSV file built: {output_file} ({file_size_mb:.1f} MB)")

            return output_file

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Failed to build CSV file: {e}") from e

    def _build_csv(self, rows: list, output_file: Path) -> None:
        """
        Build gzip-compressed CSV file.

        Args:
            rows: List of row dictionaries
            output_file: Path to output .csv.gz file

        Raises:
            BuildError: If CSV creation fails
        """
        try:
            # Column names from schema
            columns = [col[0] for col in DatabaseSchema.COLUMNS]

            # Write CSV with gzip compression
            with gzip.open(output_file, 'wt', encoding='utf-8', compresslevel=6) as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)

        except Exception as e:
            # Clean up on failure
            if output_file.exists():
                output_file.unlink()
            raise BuildError(f"CSV creation failed: {e}") from e

    def validate(self, csv_file: Path) -> bool:
        """
        Validate built CSV file.

        Args:
            csv_file: Path to .csv.gz file

        Returns:
            True if valid

        Raises:
            BuildError: If validation fails
        """
        if not csv_file.exists():
            raise BuildError(f"CSV file not found: {csv_file}")

        try:
            print(f"Validating CSV file: {csv_file}")

            # Read CSV file
            with gzip.open(csv_file, 'rt', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Check header
                expected_columns = [col[0] for col in DatabaseSchema.COLUMNS]
                if reader.fieldnames != expected_columns:
                    raise BuildError(
                        f"CSV header mismatch.\nExpected: {expected_columns}\nActual: {reader.fieldnames}"
                    )

                # Count rows and check for required fields
                row_count = 0
                null_counts = {col: 0 for col in ["date", "rank", "coin_id"]}

                for row in reader:
                    row_count += 1

                    # Check for empty required fields
                    for field in ["date", "rank", "coin_id"]:
                        if not row.get(field) or row[field].strip() == "":
                            null_counts[field] += 1

                    # Validate rank (spot check first 10 rows)
                    if row_count <= 10:
                        try:
                            rank = int(row["rank"])
                            if rank < 1:
                                raise BuildError(f"Invalid rank in row {row_count}: {rank}")
                        except ValueError:
                            raise BuildError(f"Non-integer rank in row {row_count}: {row['rank']}")

            print(f"  Row count: {row_count}")

            if row_count == 0:
                raise BuildError("CSV file is empty")

            # Check for nulls in required fields
            for field, null_count in null_counts.items():
                if null_count > 0:
                    raise BuildError(f"Found {null_count} empty values in required field: {field}")

            print("✅ CSV validation passed")
            return True

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Validation failed: {e}") from e


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: uv run build_csv.py <input_json_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    builder = CSVBuilder()

    try:
        # Build CSV file
        csv_file = builder.build(input_file)

        # Validate
        builder.validate(csv_file)

        print(f"\n{'='*80}")
        print("✅ Build successful!")
        print(f"{'='*80}")
        print(f"  Input: {input_file}")
        print(f"  Output: {csv_file}")
        print(f"  Size: {csv_file.stat().st_size / (1024*1024):.1f} MB")
        print(f"{'='*80}")

    except BuildError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
