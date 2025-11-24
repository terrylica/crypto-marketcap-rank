#!/usr/bin/env python3
"""
Cryptocurrency Rankings Schema V2

Single source of truth for database schema across all formats.
Defines native PyArrow types for strict type safety and future-proof interoperability.

Schema Version: 2.0.0
Breaking Changes from V1:
  - date: STRING → pa.date32() (native DATE type)
  - rank: pa.int32() → pa.int64() (consistency with DuckDB INTEGER)

Adheres to SLO:
- Correctness: Strict type enforcement prevents silent data corruption
- Maintainability: Single definition, no drift across formats
- Availability: Apache Arrow ecosystem (10-year future-proof)
"""

import json
from typing import Any, Dict

import pyarrow as pa

# Schema Version
SCHEMA_VERSION = "2.0.0"


# PyArrow Schema - Source of Truth
CRYPTO_RANKINGS_SCHEMA_V2 = pa.schema(
    [
        # Core identification fields (required)
        pa.field(
            "date",
            pa.date32(),
            nullable=False,
            metadata={
                "description": "Collection date (native DATE type, days since epoch)",
                "format": "YYYY-MM-DD",
                "example": "2025-11-23",
            },
        ),
        pa.field(
            "rank",
            pa.int64(),
            nullable=False,
            metadata={"description": "Global market cap rank (1=highest)", "range": "1 to N", "example": "1"},
        ),
        pa.field(
            "coin_id",
            pa.string(),
            nullable=False,
            metadata={
                "description": "CoinGecko coin identifier (unique per coin)",
                "format": "lowercase-slug",
                "example": "bitcoin",
            },
        ),
        # Coin metadata fields (optional)
        pa.field(
            "symbol",
            pa.string(),
            nullable=True,
            metadata={"description": "Ticker symbol", "format": "lowercase", "example": "btc"},
        ),
        pa.field(
            "name",
            pa.string(),
            nullable=True,
            metadata={"description": "Human-readable coin name", "example": "Bitcoin"},
        ),
        # Market data fields (optional, allow NULL for inactive/delisted coins)
        pa.field(
            "market_cap",
            pa.float64(),
            nullable=True,
            metadata={"description": "Total market capitalization in USD", "unit": "USD", "example": "1693396618542.0"},
        ),
        pa.field(
            "price",
            pa.float64(),
            nullable=True,
            metadata={"description": "Current price per coin in USD", "unit": "USD", "example": "84921.0"},
        ),
        pa.field(
            "volume_24h",
            pa.float64(),
            nullable=True,
            metadata={"description": "24-hour trading volume in USD", "unit": "USD", "example": "132655185022.0"},
        ),
        pa.field(
            "price_change_24h_pct",
            pa.float64(),
            nullable=True,
            metadata={"description": "24-hour price change percentage", "unit": "percent", "example": "-2.38937"},
        ),
    ]
)


# Type mapping for documentation
PYARROW_TO_SQL_TYPES = {
    "date32": "DATE",
    "int64": "BIGINT",
    "string": "VARCHAR",
    "float64": "DOUBLE",
}


def export_json_schema() -> Dict[str, Any]:
    """
    Export schema as JSON Schema for documentation purposes.

    Returns:
        JSON Schema dict (JSON Schema Draft 07)
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://github.com/terrylica/crypto-marketcap-rank/schemas/v2",
        "title": "Cryptocurrency Market Cap Rankings",
        "description": "Daily market capitalization rankings for all cryptocurrencies",
        "version": SCHEMA_VERSION,
        "type": "object",
        "required": ["date", "rank", "coin_id"],
        "properties": {
            "date": {
                "type": "string",
                "format": "date",
                "description": "Collection date (YYYY-MM-DD)",
                "example": "2025-11-23",
            },
            "rank": {
                "type": "integer",
                "minimum": 1,
                "description": "Global market cap rank (1=highest)",
                "example": 1,
            },
            "coin_id": {
                "type": "string",
                "pattern": "^[a-z0-9-]+$",
                "description": "CoinGecko coin identifier",
                "example": "bitcoin",
            },
            "symbol": {"type": ["string", "null"], "description": "Ticker symbol (lowercase)", "example": "btc"},
            "name": {"type": ["string", "null"], "description": "Human-readable coin name", "example": "Bitcoin"},
            "market_cap": {
                "type": ["number", "null"],
                "minimum": 0,
                "description": "Total market capitalization in USD",
                "example": 1693396618542.0,
            },
            "price": {
                "type": ["number", "null"],
                "minimum": 0,
                "description": "Current price per coin in USD",
                "example": 84921.0,
            },
            "volume_24h": {
                "type": ["number", "null"],
                "minimum": 0,
                "description": "24-hour trading volume in USD",
                "example": 132655185022.0,
            },
            "price_change_24h_pct": {
                "type": ["number", "null"],
                "description": "24-hour price change percentage",
                "example": -2.38937,
            },
        },
    }


def get_duckdb_ddl() -> str:
    """
    Generate DuckDB CREATE TABLE DDL from PyArrow schema.

    Returns:
        SQL DDL string
    """
    field_definitions = []
    for field in CRYPTO_RANKINGS_SCHEMA_V2:
        # Map PyArrow type to SQL type
        pa_type = str(field.type)
        sql_type = PYARROW_TO_SQL_TYPES.get(pa_type, "VARCHAR")

        # Add NOT NULL constraint
        null_clause = "" if field.nullable else " NOT NULL"

        field_definitions.append(f"    {field.name} {sql_type}{null_clause}")

    return f"""CREATE TABLE rankings (
{chr(10).join(field_definitions)}
)"""


if __name__ == "__main__":
    # Print schema information
    print(f"Cryptocurrency Rankings Schema V{SCHEMA_VERSION}")
    print("=" * 80)
    print()

    print("PyArrow Schema:")
    print("-" * 80)
    print(CRYPTO_RANKINGS_SCHEMA_V2)
    print()

    print("DuckDB DDL:")
    print("-" * 80)
    print(get_duckdb_ddl())
    print()

    print("JSON Schema:")
    print("-" * 80)
    print(json.dumps(export_json_schema(), indent=2))
