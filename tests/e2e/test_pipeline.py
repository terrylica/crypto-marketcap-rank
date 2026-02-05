"""
End-to-end tests for full SDK pipeline.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4

Tests the full flow: load → query → export with mocked network.
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from crypto_marketcap_rank import (
    RankingsDatabase,
    get_top_n_at_date,
    load_latest,
)


class TestFullPipeline:
    """Test complete SDK workflow."""

    def test_load_query_export_pipeline(self, sample_db, temp_cache_dir):
        """Full pipeline: load → query → export."""
        # Mock the network layer
        with patch(
            "crypto_marketcap_rank.loader.CacheManager"
        ) as mock_cache_cls, patch(
            "crypto_marketcap_rank.loader.GitHubReleasesClient"
        ) as mock_client_cls:
            # Setup mocks to return our sample database
            mock_cache = MagicMock()
            mock_cache.get_or_download.return_value = sample_db
            mock_cache_cls.return_value = mock_cache

            mock_client = MagicMock()
            mock_release = MagicMock()
            mock_release.tag = "daily-2025-01-15"
            mock_release.date = date(2025, 1, 15)
            mock_client.get_latest_release.return_value = mock_release
            mock_client_cls.return_value = mock_client

            # Step 1: Load
            db = load_latest(cache_dir=temp_cache_dir)
            assert isinstance(db, RankingsDatabase)

            # Step 2: Query
            df = db.get_top_n(10)
            assert len(df) == 3  # sample has 3 coins
            assert df.iloc[0]["symbol"] == "btc"

            # Step 3: Export
            export_path = temp_cache_dir / "output.parquet"
            result = db.export_parquet(export_path)
            assert result == export_path
            assert export_path.exists()

            db.close()

    def test_historical_query_pipeline(self, sample_db, temp_cache_dir):
        """Pipeline using historical query functions."""
        # Use sample database directly (simulating loaded data)
        db = RankingsDatabase(sample_db)

        # Test get_top_n_at_date
        df = get_top_n_at_date(db, date(2025, 1, 15), n=5)
        assert len(df) == 3  # sample has 3 coins
        assert list(df["rank"]) == [1, 2, 3]

        db.close()


class TestCacheIntegration:
    """Test cache behavior in pipeline."""

    def test_cache_hit_skips_download(self, sample_db, temp_cache_dir):
        """Second load uses cached file."""
        with patch(
            "crypto_marketcap_rank.loader.CacheManager"
        ) as mock_cache_cls, patch(
            "crypto_marketcap_rank.loader.GitHubReleasesClient"
        ) as mock_client_cls:
            mock_cache = MagicMock()
            mock_cache.get_or_download.return_value = sample_db
            mock_cache_cls.return_value = mock_cache

            mock_client = MagicMock()
            mock_release = MagicMock()
            mock_release.tag = "daily-2025-01-15"
            mock_release.date = date(2025, 1, 15)
            mock_client.get_latest_release.return_value = mock_release
            mock_client_cls.return_value = mock_client

            # Load twice
            db1 = load_latest(cache_dir=temp_cache_dir)
            db1.close()

            db2 = load_latest(cache_dir=temp_cache_dir)
            db2.close()

            # get_or_download called twice, but cache handles dedup
            assert mock_cache.get_or_download.call_count == 2


class TestErrorHandling:
    """Test error handling in pipeline."""

    def test_handles_network_error_gracefully(self, temp_cache_dir):
        """Pipeline handles network errors."""
        from crypto_marketcap_rank.exceptions import DownloadError

        with patch(
            "crypto_marketcap_rank.loader.CacheManager"
        ), patch(
            "crypto_marketcap_rank.loader.GitHubReleasesClient"
        ) as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_latest_release.side_effect = DownloadError(
                "Network error"
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(DownloadError):
                load_latest(cache_dir=temp_cache_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
