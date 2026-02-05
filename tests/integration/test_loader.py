"""
Integration tests for SDK Loader.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from crypto_marketcap_rank import load_date, load_latest
from crypto_marketcap_rank.exceptions import DataNotFoundError


class TestLoadLatest:
    """Test load_latest() function."""

    def test_load_latest_returns_database(self, sample_db, temp_cache_dir):
        """load_latest returns RankingsDatabase on success."""
        with patch(
            "crypto_marketcap_rank.loader.CacheManager"
        ) as mock_cache_cls, patch(
            "crypto_marketcap_rank.loader.GitHubReleasesClient"
        ) as mock_client_cls:
            # Setup mocks
            mock_cache = MagicMock()
            mock_cache.get_or_download.return_value = sample_db
            mock_cache_cls.return_value = mock_cache

            mock_client = MagicMock()
            mock_release = MagicMock()
            mock_release.tag = "daily-2025-01-15"
            mock_release.date = date(2025, 1, 15)
            mock_client.get_latest_release.return_value = mock_release
            mock_client_cls.return_value = mock_client

            db = load_latest(cache_dir=temp_cache_dir)

            assert db is not None
            assert db.path == sample_db
            db.close()

    def test_load_latest_force_refresh(self, sample_db, temp_cache_dir):
        """force_refresh=True passes through to cache."""
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

            db = load_latest(cache_dir=temp_cache_dir, force_refresh=True)

            mock_cache.get_or_download.assert_called_once()
            call_kwargs = mock_cache.get_or_download.call_args[1]
            assert call_kwargs["force_refresh"] is True
            db.close()


class TestLoadDate:
    """Test load_date() function."""

    def test_load_date_with_date_object(self, sample_db, temp_cache_dir):
        """load_date accepts datetime.date object."""
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
            mock_client.get_release_by_date.return_value = mock_release
            mock_client_cls.return_value = mock_client

            target = date(2025, 1, 15)
            db = load_date(target, cache_dir=temp_cache_dir)

            mock_client.get_release_by_date.assert_called_once_with(target)
            db.close()

    def test_load_date_with_string(self, sample_db, temp_cache_dir):
        """load_date accepts ISO date string."""
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
            mock_client.get_release_by_date.return_value = mock_release
            mock_client_cls.return_value = mock_client

            db = load_date("2025-01-15", cache_dir=temp_cache_dir)

            # Should convert string to date
            mock_client.get_release_by_date.assert_called_once_with(
                date(2025, 1, 15)
            )
            db.close()

    def test_load_date_not_found(self, temp_cache_dir):
        """load_date raises DataNotFoundError for missing date."""
        with patch(
            "crypto_marketcap_rank.loader.CacheManager"
        ), patch(
            "crypto_marketcap_rank.loader.GitHubReleasesClient"
        ) as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_release_by_date.side_effect = DataNotFoundError(
                "No release for 2020-01-01"
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(DataNotFoundError):
                load_date("2020-01-01", cache_dir=temp_cache_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
