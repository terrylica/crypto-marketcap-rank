"""
Unit tests for Schema Validators.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import sys
from datetime import date
from pathlib import Path

import pyarrow as pa
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from schemas.crypto_rankings_schema import CRYPTO_RANKINGS_SCHEMA_V2
from validators import validate_arrow_table


def create_valid_table():
    """Create a valid PyArrow table for testing."""
    return pa.table(
        {
            "date": pa.array([date(2025, 1, 15)], type=pa.date32()),
            "rank": pa.array([1], type=pa.int64()),
            "coin_id": pa.array(["bitcoin"]),
            "symbol": pa.array(["btc"]),
            "name": pa.array(["Bitcoin"]),
            "market_cap": pa.array([1e12]),
            "price": pa.array([50000.0]),
            "volume_24h": pa.array([1e10]),
            "price_change_24h_pct": pa.array([2.5]),
        },
        schema=CRYPTO_RANKINGS_SCHEMA_V2,
    )


class TestValidateArrowTable:
    """Test validate_arrow_table function."""

    def test_valid_table_passes(self):
        """Valid table passes validation."""
        table = create_valid_table()
        errors = validate_arrow_table(table)
        assert errors == []

    def test_detects_duplicate_coin_ids(self):
        """Validator detects duplicate (date, coin_id) pairs."""
        # Create table with duplicate coin_id on same date
        table = pa.table(
            {
                "date": pa.array(
                    [date(2025, 1, 15), date(2025, 1, 15)], type=pa.date32()
                ),
                "rank": pa.array([1, 2], type=pa.int64()),
                "coin_id": pa.array(["bitcoin", "bitcoin"]),  # Duplicate!
                "symbol": pa.array(["btc", "btc"]),
                "name": pa.array(["Bitcoin", "Bitcoin"]),
                "market_cap": pa.array([1e12, 5e11]),
                "price": pa.array([50000.0, 3000.0]),
                "volume_24h": pa.array([1e10, 5e9]),
                "price_change_24h_pct": pa.array([2.5, -1.2]),
            },
            schema=CRYPTO_RANKINGS_SCHEMA_V2,
        )

        errors = validate_arrow_table(table)

        # Should detect duplicate
        assert len(errors) > 0
        assert any("duplicate" in str(e).lower() for e in errors)

    def test_detects_null_required_fields(self):
        """Validator detects NULL in required fields."""
        # Create table with NULL coin_id
        table = pa.table(
            {
                "date": pa.array([date(2025, 1, 15)], type=pa.date32()),
                "rank": pa.array([1], type=pa.int64()),
                "coin_id": pa.array([None]),  # NULL!
                "symbol": pa.array(["btc"]),
                "name": pa.array(["Bitcoin"]),
                "market_cap": pa.array([1e12]),
                "price": pa.array([50000.0]),
                "volume_24h": pa.array([1e10]),
                "price_change_24h_pct": pa.array([2.5]),
            },
        )

        errors = validate_arrow_table(table)

        assert len(errors) > 0
        assert any("null" in str(e).lower() for e in errors)

    def test_detects_invalid_rank_values(self):
        """Validator detects invalid rank values (<= 0)."""
        table = pa.table(
            {
                "date": pa.array([date(2025, 1, 15)], type=pa.date32()),
                "rank": pa.array([0], type=pa.int64()),  # Invalid!
                "coin_id": pa.array(["bitcoin"]),
                "symbol": pa.array(["btc"]),
                "name": pa.array(["Bitcoin"]),
                "market_cap": pa.array([1e12]),
                "price": pa.array([50000.0]),
                "volume_24h": pa.array([1e10]),
                "price_change_24h_pct": pa.array([2.5]),
            },
            schema=CRYPTO_RANKINGS_SCHEMA_V2,
        )

        errors = validate_arrow_table(table)

        assert len(errors) > 0
        assert any("rank" in str(e).lower() for e in errors)

    def test_detects_negative_market_values(self):
        """Validator detects negative market_cap/price/volume."""
        table = pa.table(
            {
                "date": pa.array([date(2025, 1, 15)], type=pa.date32()),
                "rank": pa.array([1], type=pa.int64()),
                "coin_id": pa.array(["bitcoin"]),
                "symbol": pa.array(["btc"]),
                "name": pa.array(["Bitcoin"]),
                "market_cap": pa.array([-1e12]),  # Negative!
                "price": pa.array([50000.0]),
                "volume_24h": pa.array([1e10]),
                "price_change_24h_pct": pa.array([2.5]),
            },
            schema=CRYPTO_RANKINGS_SCHEMA_V2,
        )

        errors = validate_arrow_table(table)

        assert len(errors) > 0
        assert any("market_cap" in str(e).lower() or "negative" in str(e).lower() for e in errors)


class TestValidationRules:
    """Test the 5 validation rules from the plan."""

    def test_rule_1_schema_conformance(self):
        """Rule 1: Schema conformance - exact PyArrow Schema V2 match."""
        valid_table = create_valid_table()
        errors = validate_arrow_table(valid_table)
        assert errors == [], "Valid table should pass schema conformance"

    def test_rule_2_duplicate_detection(self):
        """Rule 2: Duplicate detection - no duplicate (date, coin_id) pairs."""
        table = pa.table(
            {
                "date": pa.array(
                    [date(2025, 1, 15), date(2025, 1, 15)], type=pa.date32()
                ),
                "rank": pa.array([1, 2], type=pa.int64()),
                "coin_id": pa.array(["bitcoin", "bitcoin"]),  # Duplicate coin_id!
                "symbol": pa.array(["btc", "btc"]),
                "name": pa.array(["Bitcoin", "Bitcoin"]),
                "market_cap": pa.array([1e12, 5e11]),
                "price": pa.array([50000.0, 3000.0]),
                "volume_24h": pa.array([1e10, 5e9]),
                "price_change_24h_pct": pa.array([2.5, -1.2]),
            },
            schema=CRYPTO_RANKINGS_SCHEMA_V2,
        )
        errors = validate_arrow_table(table)
        assert len(errors) > 0, "Should detect duplicate coin_id"

    def test_rule_3_null_checks(self):
        """Rule 3: NULL checks - required fields non-null."""
        # coin_id is required (nullable=False in schema)
        table = pa.table(
            {
                "date": pa.array([date(2025, 1, 15)], type=pa.date32()),
                "rank": pa.array([1], type=pa.int64()),
                "coin_id": pa.array([None]),
                "symbol": pa.array(["btc"]),
                "name": pa.array(["Bitcoin"]),
                "market_cap": pa.array([1e12]),
                "price": pa.array([50000.0]),
                "volume_24h": pa.array([1e10]),
                "price_change_24h_pct": pa.array([2.5]),
            },
        )
        errors = validate_arrow_table(table)
        assert len(errors) > 0, "Should detect NULL in required field"

    def test_rule_4_range_validation(self):
        """Rule 4: Range validation - ranks >= 1."""
        table = pa.table(
            {
                "date": pa.array([date(2025, 1, 15)], type=pa.date32()),
                "rank": pa.array([-1], type=pa.int64()),
                "coin_id": pa.array(["bitcoin"]),
                "symbol": pa.array(["btc"]),
                "name": pa.array(["Bitcoin"]),
                "market_cap": pa.array([1e12]),
                "price": pa.array([50000.0]),
                "volume_24h": pa.array([1e10]),
                "price_change_24h_pct": pa.array([2.5]),
            },
            schema=CRYPTO_RANKINGS_SCHEMA_V2,
        )
        errors = validate_arrow_table(table)
        assert len(errors) > 0, "Should detect invalid rank"

    def test_rule_5_value_constraints(self):
        """Rule 5: Value constraints - market_cap >= 0."""
        # Note: Actual validator only checks market_cap, not price/volume
        table = pa.table(
            {
                "date": pa.array([date(2025, 1, 15)], type=pa.date32()),
                "rank": pa.array([1], type=pa.int64()),
                "coin_id": pa.array(["bitcoin"]),
                "symbol": pa.array(["btc"]),
                "name": pa.array(["Bitcoin"]),
                "market_cap": pa.array([-1e12]),  # Negative market_cap
                "price": pa.array([50000.0]),
                "volume_24h": pa.array([1e10]),
                "price_change_24h_pct": pa.array([2.5]),
            },
            schema=CRYPTO_RANKINGS_SCHEMA_V2,
        )
        errors = validate_arrow_table(table)
        assert len(errors) > 0, "Should detect negative market_cap"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
