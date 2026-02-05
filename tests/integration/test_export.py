"""
Integration tests for Parquet Export.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import sys
from pathlib import Path

import pyarrow.parquet as pq
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from crypto_marketcap_rank.connection import RankingsDatabase


class TestRankingsDatabaseExportParquet:
    """Test RankingsDatabase.export_parquet()."""

    def test_export_parquet_creates_file(self, sample_db, temp_cache_dir):
        """export_parquet creates a Parquet file."""
        db = RankingsDatabase(sample_db)
        output_path = temp_cache_dir / "export.parquet"

        result = db.export_parquet(output_path)

        assert result == output_path
        assert output_path.exists()
        db.close()

    def test_export_parquet_readable(self, sample_db, temp_cache_dir):
        """Exported Parquet file is readable with PyArrow."""
        db = RankingsDatabase(sample_db)
        output_path = temp_cache_dir / "export.parquet"

        db.export_parquet(output_path)

        # Read back with PyArrow
        table = pq.read_table(output_path)
        assert len(table) == 3  # sample_coins has 3 coins
        assert "rank" in table.column_names
        assert "symbol" in table.column_names
        db.close()

    def test_export_parquet_schema_matches(self, sample_db, temp_cache_dir):
        """Exported Parquet has expected columns."""
        db = RankingsDatabase(sample_db)
        output_path = temp_cache_dir / "export.parquet"

        db.export_parquet(output_path)

        table = pq.read_table(output_path)
        expected_columns = {
            "date",
            "rank",
            "coin_id",
            "symbol",
            "name",
            "market_cap",
            "price",
            "volume_24h",
            "price_change_24h_pct",
        }
        assert set(table.column_names) == expected_columns
        db.close()


class TestRankingsDatabaseExportCSV:
    """Test RankingsDatabase.export_csv()."""

    def test_export_csv_creates_file(self, sample_db, temp_cache_dir):
        """export_csv creates a CSV file."""
        db = RankingsDatabase(sample_db)
        output_path = temp_cache_dir / "export.csv"

        result = db.export_csv(output_path)

        assert result == output_path
        assert output_path.exists()
        db.close()

    def test_export_csv_readable(self, sample_db, temp_cache_dir):
        """Exported CSV is readable as text."""
        db = RankingsDatabase(sample_db)
        output_path = temp_cache_dir / "export.csv"

        db.export_csv(output_path)

        content = output_path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 4  # 1 header + 3 data rows
        assert "rank" in lines[0]
        assert "symbol" in lines[0]
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
