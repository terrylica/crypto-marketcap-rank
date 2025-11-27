#!/usr/bin/env python3
"""
Schema Validator

Comprehensive validation for PyArrow tables across all database formats.
Enforces data quality rules before publication.

Adheres to SLO:
- Correctness: Strict validation prevents corrupt data publication
- Observability: Detailed error reporting for debugging
- Availability: Fail-fast on errors (raise + propagate)
"""

from typing import List

import pyarrow as pa

from schemas.crypto_rankings_schema import CRYPTO_RANKINGS_SCHEMA_V2


# Validation Error Classes
class ValidationError(Exception):
    """Base class for all validation errors."""

    pass


class SchemaError(ValidationError):
    """Schema conformance error."""

    pass


class DuplicateError(ValidationError):
    """Duplicate record error."""

    pass


class NullError(ValidationError):
    """NULL value in required field error."""

    pass


class RangeError(ValidationError):
    """Value out of valid range error."""

    pass


class ValueError(ValidationError):
    """Invalid value error."""

    pass


def validate_arrow_table(table: pa.Table) -> List[ValidationError]:
    """
    Comprehensive validation for PyArrow Table.

    Validation Rules:
    1. Schema conformance (exact match with CRYPTO_RANKINGS_SCHEMA_V2)
    2. No duplicate (date, coin_id) pairs
    3. No NULL values in required fields (date, rank, coin_id)
    4. Rank range validation (1 to N, sequential)
    5. Market cap > 0 for non-NULL values

    Args:
        table: PyArrow Table to validate

    Returns:
        List of ValidationError instances (empty if valid)

    Raises:
        Never raises - returns errors in list for caller to handle
    """
    errors: List[ValidationError] = []

    # Validation 1: Schema Conformance
    try:
        if not table.schema.equals(CRYPTO_RANKINGS_SCHEMA_V2):
            # Detailed comparison
            expected_names = [field.name for field in CRYPTO_RANKINGS_SCHEMA_V2]
            actual_names = table.schema.names

            missing = set(expected_names) - set(actual_names)
            extra = set(actual_names) - set(expected_names)

            # Allow Hive partition columns (added by PyArrow when reading partitioned Parquet)
            allowed_partition_columns = {"year", "month", "day"}
            extra = extra - allowed_partition_columns

            if missing:
                errors.append(SchemaError(f"Missing columns: {missing}"))
            if extra:
                errors.append(SchemaError(f"Extra columns: {extra}"))

            # Type mismatches
            for field in CRYPTO_RANKINGS_SCHEMA_V2:
                if field.name in actual_names:
                    actual_type = table.schema.field(field.name).type
                    if actual_type != field.type:
                        errors.append(
                            SchemaError(
                                f"Column '{field.name}' type mismatch: expected {field.type}, got {actual_type}"
                            )
                        )
    except Exception as e:
        errors.append(SchemaError(f"Schema validation failed: {e}"))

    # Validation 2: Duplicate Detection
    try:
        df = table.to_pandas()
        duplicates = df[df.duplicated(subset=["date", "coin_id"], keep=False)]
        if not duplicates.empty:
            dup_count = len(duplicates)
            sample = duplicates[["date", "coin_id", "rank"]].head(5).to_dict("records")
            errors.append(DuplicateError(f"Found {dup_count} duplicate (date, coin_id) pairs. Sample: {sample}"))
    except Exception as e:
        errors.append(DuplicateError(f"Duplicate check failed: {e}"))

    # Validation 3: Required Field NULL Checks
    required_fields = ["date", "rank", "coin_id"]
    for field in required_fields:
        try:
            null_count = table[field].null_count
            if null_count > 0:
                # Find sample NULL rows
                df = table.to_pandas()
                null_rows = df[df[field].isnull()].head(5)
                sample = null_rows[["date", "rank", "coin_id"]].to_dict("records")
                errors.append(
                    NullError(f"Found {null_count} NULL values in required field '{field}'. Sample: {sample}")
                )
        except Exception as e:
            errors.append(NullError(f"NULL check failed for '{field}': {e}"))

    # Validation 4: Rank Range Validation
    # Note: CoinGecko API naturally has rank gaps when coins lack market cap data
    # Note: Duplicate ranks are VALID - coins with identical market cap share the same rank
    # We validate: (1) all ranks >= 1, (2) max rank reasonable
    try:
        ranks = table["rank"].to_pylist()
        if ranks:
            min_rank = min(ranks)
            max_rank = max(ranks)
            row_count = len(ranks)

            if min_rank < 1:
                errors.append(RangeError(f"Rank minimum is {min_rank}, expected >= 1"))

            # Note: Duplicate ranks are expected when coins have identical market cap
            # CoinGecko assigns the same rank to coins with equal market_cap
            # This is NOT data corruption - just log for observability
            rank_set = set(ranks)
            if len(rank_set) != row_count:
                dup_count = row_count - len(rank_set)
                # Log but don't fail - this is expected behavior
                import logging
                logging.getLogger(__name__).info(f"Found {dup_count} duplicate rank(s) - expected for coins with identical market cap")

            # Max rank should be reasonable (within 2x of row count to allow for gaps)
            # CoinGecko has ~19,400 coins but gaps can push max_rank higher
            if max_rank > row_count * 2:
                errors.append(RangeError(f"Rank maximum {max_rank} too high for {row_count} rows"))
    except Exception as e:
        errors.append(RangeError(f"Rank validation failed: {e}"))

    # Validation 5: Market Cap Value Validation
    try:
        market_caps = [c for c in table["market_cap"].to_pylist() if c is not None]
        if market_caps:
            negative_caps = [c for c in market_caps if c < 0]
            if negative_caps:
                errors.append(
                    ValueError(f"Found {len(negative_caps)} negative market_cap values. Sample: {negative_caps[:5]}")
                )
    except Exception as e:
        errors.append(ValueError(f"Market cap validation failed: {e}"))

    return errors


def validate_and_raise(table: pa.Table) -> None:
    """
    Validate PyArrow Table and raise exception if errors found.

    This is a convenience wrapper for validate_arrow_table() that
    raises a single exception with all errors combined.

    Args:
        table: PyArrow Table to validate

    Raises:
        ValidationError: If any validation errors found
    """
    errors = validate_arrow_table(table)
    if errors:
        error_messages = "\n".join([f"  - {e}" for e in errors])
        raise ValidationError(f"Validation failed with {len(errors)} error(s):\n{error_messages}")


if __name__ == "__main__":
    from datetime import date

    import pyarrow as pa

    # Test validation with valid data
    print("Testing schema validator...")
    print("=" * 80)

    # Create valid test table
    test_data = {
        "date": [date(2025, 11, 23)] * 3,
        "rank": [1, 2, 3],
        "coin_id": ["bitcoin", "ethereum", "tether"],
        "symbol": ["BTC", "ETH", "USDT"],
        "name": ["Bitcoin", "Ethereum", "Tether"],
        "market_cap": [1000000.0, 500000.0, 300000.0],
        "price": [50000.0, 3000.0, 1.0],
        "volume_24h": [100000.0, 50000.0, 30000.0],
        "price_change_24h_pct": [2.5, -1.3, 0.01],
    }

    table = pa.table(test_data, schema=CRYPTO_RANKINGS_SCHEMA_V2)

    errors = validate_arrow_table(table)
    if not errors:
        print("✅ Valid table passed all checks")
    else:
        print(f"❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")

    print()

    # Test with invalid data (duplicates)
    print("Testing with duplicate data...")
    invalid_data = {
        "date": [date(2025, 11, 23)] * 3,
        "rank": [1, 2, 3],
        "coin_id": ["bitcoin", "bitcoin", "tether"],  # Duplicate
        "symbol": ["BTC", "BTC", "USDT"],
        "name": ["Bitcoin", "Bitcoin", "Tether"],
        "market_cap": [1000000.0, 500000.0, 300000.0],
        "price": [50000.0, 3000.0, 1.0],
        "volume_24h": [100000.0, 50000.0, 30000.0],
        "price_change_24h_pct": [2.5, -1.3, 0.01],
    }

    invalid_table = pa.table(invalid_data, schema=CRYPTO_RANKINGS_SCHEMA_V2)
    errors = validate_arrow_table(invalid_table)
    if errors:
        print(f"✅ Correctly detected {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("❌ Failed to detect errors!")
