"""
Integration tests for DuckDB Builder.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import json
import sys
import tempfile
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from builders.base_builder import BuildError
from builders.build_duckdb import DuckDBBuilder


@pytest.fixture
def raw_json_file(sample_coins):
    """Create a raw JSON file matching collector output format."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        data = {
            "coins": sample_coins,
            "metadata": {
                "collection_date": "2025-01-15",
                "api_calls_used": 1,
                "collection_time": "2025-01-15T06:00:00Z",
            },
        }
        json.dump(data, f)
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def builder(temp_cache_dir):
    """Create DuckDBBuilder with temp output directory."""
    return DuckDBBuilder(output_dir=temp_cache_dir)


class TestDuckDBBuilderBuild:
    """Test DuckDB build functionality."""

    def test_build_creates_database(self, builder, raw_json_file):
        """Build creates a valid DuckDB database."""
        db_path = builder.build(raw_json_file)

        assert db_path.exists()
        assert db_path.suffix == ".duckdb"

    def test_build_database_has_rankings_table(self, builder, raw_json_file):
        """Built database contains rankings table."""
        db_path = builder.build(raw_json_file)

        con = duckdb.connect(str(db_path), read_only=True)
        tables = con.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        con.close()

        assert "rankings" in table_names

    def test_build_database_has_correct_schema(self, builder, raw_json_file):
        """Built database has correct column types."""
        db_path = builder.build(raw_json_file)

        con = duckdb.connect(str(db_path), read_only=True)
        schema = con.execute("DESCRIBE rankings").fetchall()
        con.close()

        # Build dict of column -> type
        col_types = {row[0]: row[1] for row in schema}

        assert col_types["date"] == "DATE"
        assert col_types["rank"] == "BIGINT"
        assert col_types["coin_id"] == "VARCHAR"
        assert col_types["market_cap"] == "DOUBLE"
        assert col_types["price"] == "DOUBLE"

    def test_build_database_has_indexes(self, builder, raw_json_file):
        """Built database has required indexes."""
        db_path = builder.build(raw_json_file)

        con = duckdb.connect(str(db_path), read_only=True)
        # DuckDB stores indexes in system tables
        indexes = con.execute("""
            SELECT index_name FROM duckdb_indexes()
        """).fetchall()
        con.close()

        index_names = [idx[0] for idx in indexes]
        assert "idx_date" in index_names
        assert "idx_rank" in index_names
        assert "idx_coin_id" in index_names

    def test_build_database_has_correct_data(
        self, builder, raw_json_file, sample_coins
    ):
        """Built database contains correct data."""
        db_path = builder.build(raw_json_file)

        con = duckdb.connect(str(db_path), read_only=True)
        rows = con.execute(
            "SELECT coin_id, symbol, rank FROM rankings ORDER BY rank"
        ).fetchall()
        con.close()

        assert len(rows) == len(sample_coins)
        assert rows[0] == ("bitcoin", "btc", 1)
        assert rows[1] == ("ethereum", "eth", 2)
        assert rows[2] == ("tether", "usdt", 3)

    def test_build_fails_on_missing_input(self, builder):
        """Build raises error for missing input file."""
        with pytest.raises(BuildError, match="Input file not found"):
            builder.build(Path("/nonexistent/file.json"))


class TestDuckDBBuilderExportParquet:
    """Test Parquet export functionality."""

    def test_export_parquet_flat(self, builder, raw_json_file, temp_cache_dir):
        """Export to flat Parquet file."""
        db_path = builder.build(raw_json_file)
        output_dir = temp_cache_dir / "parquet_output"

        result = builder.export_parquet(db_path, output_dir, partition=False)

        assert result == output_dir
        parquet_file = output_dir / "rankings.parquet"
        assert parquet_file.exists()

    def test_export_parquet_partitioned(
        self, builder, raw_json_file, temp_cache_dir
    ):
        """Export to partitioned Parquet files."""
        db_path = builder.build(raw_json_file)
        output_dir = temp_cache_dir / "parquet_partitioned"

        result = builder.export_parquet(db_path, output_dir, partition=True)

        assert result == output_dir
        # Check Hive-style partition exists (year=2025/month=1/day=15)
        parquet_files = list(output_dir.rglob("*.parquet"))
        assert len(parquet_files) > 0

    def test_export_parquet_fails_on_missing_db(self, builder, temp_cache_dir):
        """Export raises error for missing database."""
        with pytest.raises(BuildError, match="Database file not found"):
            builder.export_parquet(
                Path("/nonexistent/db.duckdb"),
                temp_cache_dir / "output",
            )


class TestDuckDBBuilderValidate:
    """Test database validation."""

    def test_validate_passes_for_valid_db(self, builder, raw_json_file):
        """Validate passes for correctly built database."""
        db_path = builder.build(raw_json_file)

        result = builder.validate(db_path)

        assert result is True

    def test_validate_fails_for_missing_db(self, builder):
        """Validate raises error for missing database."""
        with pytest.raises(BuildError, match="Database file not found"):
            builder.validate(Path("/nonexistent/db.duckdb"))

    def test_validate_fails_for_empty_db(self, builder, temp_cache_dir):
        """Validate fails for empty database."""
        empty_db = temp_cache_dir / "empty.duckdb"
        con = duckdb.connect(str(empty_db))
        con.execute("CREATE TABLE rankings (date DATE, rank BIGINT, coin_id VARCHAR)")
        con.close()

        with pytest.raises(BuildError, match="Database is empty"):
            builder.validate(empty_db)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
