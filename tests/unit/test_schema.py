"""
Unit tests for Cryptocurrency Rankings Schema V2.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import sys
from pathlib import Path

import pyarrow as pa
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from schemas.crypto_rankings_schema import (
    CRYPTO_RANKINGS_SCHEMA_V2,
    SCHEMA_VERSION,
    export_json_schema,
    get_duckdb_ddl,
)


class TestSchemaV2Structure:
    """Test Schema V2 structure and field definitions."""

    def test_schema_version(self):
        """Schema version is 2.0.0."""
        assert SCHEMA_VERSION == "2.0.0"

    def test_schema_has_9_fields(self):
        """Schema has exactly 9 fields."""
        assert len(CRYPTO_RANKINGS_SCHEMA_V2) == 9

    def test_required_fields_exist(self):
        """Required fields (date, rank, coin_id) exist."""
        field_names = [f.name for f in CRYPTO_RANKINGS_SCHEMA_V2]
        assert "date" in field_names
        assert "rank" in field_names
        assert "coin_id" in field_names

    def test_all_expected_fields_present(self):
        """All expected fields are present."""
        expected = [
            "date",
            "rank",
            "coin_id",
            "symbol",
            "name",
            "market_cap",
            "price",
            "volume_24h",
            "price_change_24h_pct",
        ]
        actual = [f.name for f in CRYPTO_RANKINGS_SCHEMA_V2]
        assert actual == expected


class TestSchemaV2Types:
    """Test Schema V2 field types match specification."""

    def test_date_is_date32(self):
        """date field is pa.date32() for native DATE support."""
        field = CRYPTO_RANKINGS_SCHEMA_V2.field("date")
        assert field.type == pa.date32()

    def test_rank_is_int64(self):
        """rank field is pa.int64() (BIGINT in DuckDB)."""
        field = CRYPTO_RANKINGS_SCHEMA_V2.field("rank")
        assert field.type == pa.int64()

    def test_coin_id_is_string(self):
        """coin_id field is pa.string()."""
        field = CRYPTO_RANKINGS_SCHEMA_V2.field("coin_id")
        assert field.type == pa.string()

    def test_market_data_fields_are_float64(self):
        """Market data fields (market_cap, price, volume_24h, price_change_24h_pct) are float64."""
        float_fields = ["market_cap", "price", "volume_24h", "price_change_24h_pct"]
        for name in float_fields:
            field = CRYPTO_RANKINGS_SCHEMA_V2.field(name)
            assert field.type == pa.float64(), f"{name} should be float64"


class TestSchemaV2Nullability:
    """Test Schema V2 nullability constraints."""

    def test_required_fields_not_nullable(self):
        """Required fields (date, rank, coin_id) are NOT nullable."""
        required = ["date", "rank", "coin_id"]
        for name in required:
            field = CRYPTO_RANKINGS_SCHEMA_V2.field(name)
            assert not field.nullable, f"{name} should not be nullable"

    def test_optional_fields_nullable(self):
        """Optional fields (symbol, name, market data) are nullable."""
        optional = ["symbol", "name", "market_cap", "price", "volume_24h", "price_change_24h_pct"]
        for name in optional:
            field = CRYPTO_RANKINGS_SCHEMA_V2.field(name)
            assert field.nullable, f"{name} should be nullable"


class TestSchemaExports:
    """Test schema export functions."""

    def test_json_schema_export(self):
        """JSON schema export produces valid structure."""
        json_schema = export_json_schema()

        assert json_schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert json_schema["version"] == SCHEMA_VERSION
        assert json_schema["type"] == "object"
        assert set(json_schema["required"]) == {"date", "rank", "coin_id"}

    def test_json_schema_has_all_properties(self):
        """JSON schema has all field properties."""
        json_schema = export_json_schema()
        properties = json_schema["properties"]

        expected = [
            "date",
            "rank",
            "coin_id",
            "symbol",
            "name",
            "market_cap",
            "price",
            "volume_24h",
            "price_change_24h_pct",
        ]
        assert set(properties.keys()) == set(expected)

    def test_duckdb_ddl_export(self):
        """DuckDB DDL export produces valid SQL."""
        ddl = get_duckdb_ddl()

        assert "CREATE TABLE rankings" in ddl
        # Note: The DDL export uses VARCHAR as fallback for unmapped types
        # The actual schema types are tested in TestSchemaV2Types
        assert "rank BIGINT NOT NULL" in ddl
        assert "coin_id VARCHAR NOT NULL" in ddl


class TestSchemaMetadata:
    """Test schema field metadata."""

    def test_date_field_has_metadata(self):
        """date field has description metadata."""
        field = CRYPTO_RANKINGS_SCHEMA_V2.field("date")
        assert field.metadata is not None
        assert b"description" in field.metadata

    def test_rank_field_has_range_metadata(self):
        """rank field has range metadata."""
        field = CRYPTO_RANKINGS_SCHEMA_V2.field("rank")
        assert field.metadata is not None
        assert b"range" in field.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
