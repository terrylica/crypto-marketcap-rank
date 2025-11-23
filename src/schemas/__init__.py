"""
Cryptocurrency Rankings Schema

Canonical schema definitions for all database formats (DuckDB, Parquet).
Single source of truth to prevent schema drift.
"""

from .crypto_rankings_schema import (
    CRYPTO_RANKINGS_SCHEMA_V2,
    SCHEMA_VERSION,
    export_json_schema,
)

__all__ = [
    "CRYPTO_RANKINGS_SCHEMA_V2",
    "SCHEMA_VERSION",
    "export_json_schema",
]
