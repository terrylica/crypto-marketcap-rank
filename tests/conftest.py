"""
Pytest configuration and fixtures for crypto-marketcap-rank tests.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import duckdb
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_coins():
    """Sample coin data matching CoinGecko API response format."""
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "market_cap_rank": 1,
            "market_cap": 1_000_000_000_000,
            "current_price": 50000.0,
            "total_volume": 10_000_000_000,
            "price_change_percentage_24h": 2.5,
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "market_cap_rank": 2,
            "market_cap": 500_000_000_000,
            "current_price": 3000.0,
            "total_volume": 5_000_000_000,
            "price_change_percentage_24h": -1.2,
        },
        {
            "id": "tether",
            "symbol": "usdt",
            "name": "Tether",
            "market_cap_rank": 3,
            "market_cap": 100_000_000_000,
            "current_price": 1.0,
            "total_volume": 50_000_000_000,
            "price_change_percentage_24h": 0.01,
        },
    ]


@pytest.fixture
def temp_cache_dir():
    """Temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_cache_dir):
    """Path for temporary DuckDB database."""
    return temp_cache_dir / "test_rankings.duckdb"


@pytest.fixture
def sample_db(temp_db_path, sample_coins):
    """Create a sample DuckDB database with test data."""
    con = duckdb.connect(str(temp_db_path))

    # Create rankings table matching Schema V2
    con.execute("""
        CREATE TABLE rankings (
            date DATE,
            rank BIGINT,
            coin_id VARCHAR,
            symbol VARCHAR,
            name VARCHAR,
            market_cap DOUBLE,
            price DOUBLE,
            volume_24h DOUBLE,
            price_change_24h_pct DOUBLE
        )
    """)

    # Insert sample data
    test_date = date(2025, 1, 15)
    for coin in sample_coins:
        con.execute(
            """
            INSERT INTO rankings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                test_date,
                coin["market_cap_rank"],
                coin["id"],
                coin["symbol"],
                coin["name"],
                coin["market_cap"],
                coin["current_price"],
                coin["total_volume"],
                coin["price_change_percentage_24h"],
            ],
        )

    # Create indexes
    con.execute("CREATE INDEX idx_date ON rankings(date)")
    con.execute("CREATE INDEX idx_rank ON rankings(rank)")
    con.close()

    return temp_db_path


@pytest.fixture
def mock_release_info():
    """Mock ReleaseInfo for testing GitHub API client."""
    from crypto_marketcap_rank.github_api import ReleaseInfo

    return ReleaseInfo(
        tag="daily-2025-01-15",
        date=date(2025, 1, 15),
        download_url="https://api.github.com/repos/terrylica/crypto-marketcap-rank/releases/assets/12345",
        asset_name="crypto_rankings_2025-01-15.duckdb",
        size_bytes=150_000_000,
    )


@pytest.fixture
def mock_github_client(mock_release_info):
    """Mock GitHubReleasesClient for testing without network."""
    client = MagicMock()
    client.get_latest_release.return_value = mock_release_info
    client.get_release_by_date.return_value = mock_release_info
    return client
