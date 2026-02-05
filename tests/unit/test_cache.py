"""
Unit tests for SDK CacheManager.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from crypto_marketcap_rank.cache import CacheManager
from crypto_marketcap_rank.github_api import ReleaseInfo


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create CacheManager with temp directory."""
    return CacheManager(temp_cache_dir)


@pytest.fixture
def release_info():
    """Sample ReleaseInfo for testing."""
    return ReleaseInfo(
        tag="daily-2025-01-15",
        date=date(2025, 1, 15),
        download_url="https://api.github.com/repos/test/test/releases/assets/123",
        asset_name="crypto_rankings_2025-01-15.duckdb",
        size_bytes=150_000_000,
    )


class TestCacheManagerInit:
    """Test CacheManager initialization."""

    def test_creates_cache_directory(self, temp_cache_dir):
        """Cache manager creates directory if missing."""
        cache_dir = temp_cache_dir / "new_cache"
        assert not cache_dir.exists()

        CacheManager(cache_dir)

        assert cache_dir.exists()

    def test_loads_existing_metadata(self, temp_cache_dir):
        """Cache manager loads existing metadata."""
        # Create metadata file
        metadata = {"test-key": {"filename": "test.duckdb", "downloaded_at": datetime.now().isoformat()}}
        metadata_file = temp_cache_dir / "cache_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        cache = CacheManager(temp_cache_dir)

        assert "test-key" in cache._metadata

    def test_handles_corrupted_metadata(self, temp_cache_dir):
        """Cache manager handles corrupted metadata gracefully."""
        metadata_file = temp_cache_dir / "cache_metadata.json"
        metadata_file.write_text("invalid json{")

        cache = CacheManager(temp_cache_dir)

        assert cache._metadata == {}


class TestCacheManagerGetOrDownload:
    """Test get_or_download functionality."""

    def test_cache_hit_returns_cached_file(
        self, cache_manager, release_info, temp_cache_dir
    ):
        """Cache hit returns cached file path."""
        # Create cached file
        cached_file = temp_cache_dir / release_info.asset_name
        cached_file.write_text("dummy db content")

        # Add to metadata
        cache_key = f"{release_info.tag}:{release_info.asset_name}"
        cache_manager._metadata[cache_key] = {
            "filename": release_info.asset_name,
            "downloaded_at": datetime.now().isoformat(),
            "size_bytes": release_info.size_bytes,
            "tag": release_info.tag,
        }

        result = cache_manager.get_or_download(release_info)

        assert result == cached_file

    def test_cache_miss_downloads_file(
        self, cache_manager, release_info, temp_cache_dir
    ):
        """Cache miss triggers download."""
        with patch(
            "crypto_marketcap_rank.cache.GitHubReleasesClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock download to create file
            def create_file(rel, dest):
                dest.write_text("downloaded content")
                return dest

            mock_client.download_asset.side_effect = create_file

            result = cache_manager.get_or_download(release_info)

            assert result.exists()
            mock_client.download_asset.assert_called_once()

    def test_force_refresh_redownloads(
        self, cache_manager, release_info, temp_cache_dir
    ):
        """force_refresh=True redownloads even if cached."""
        # Create cached file
        cached_file = temp_cache_dir / release_info.asset_name
        cached_file.write_text("old content")

        # Add to metadata
        cache_key = f"{release_info.tag}:{release_info.asset_name}"
        cache_manager._metadata[cache_key] = {
            "filename": release_info.asset_name,
            "downloaded_at": datetime.now().isoformat(),
            "size_bytes": release_info.size_bytes,
            "tag": release_info.tag,
        }

        with patch(
            "crypto_marketcap_rank.cache.GitHubReleasesClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            def create_file(rel, dest):
                dest.write_text("new content")
                return dest

            mock_client.download_asset.side_effect = create_file

            cache_manager.get_or_download(release_info, force_refresh=True)

            mock_client.download_asset.assert_called_once()

    def test_expired_cache_redownloads(
        self, cache_manager, release_info, temp_cache_dir
    ):
        """Expired cache (>7 days) triggers redownload."""
        # Create cached file
        cached_file = temp_cache_dir / release_info.asset_name
        cached_file.write_text("old content")

        # Add expired metadata (8 days ago)
        cache_key = f"{release_info.tag}:{release_info.asset_name}"
        old_date = datetime.now() - timedelta(days=8)
        cache_manager._metadata[cache_key] = {
            "filename": release_info.asset_name,
            "downloaded_at": old_date.isoformat(),
            "size_bytes": release_info.size_bytes,
            "tag": release_info.tag,
        }

        with patch(
            "crypto_marketcap_rank.cache.GitHubReleasesClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            def create_file(rel, dest):
                dest.write_text("new content")
                return dest

            mock_client.download_asset.side_effect = create_file

            cache_manager.get_or_download(release_info)

            mock_client.download_asset.assert_called_once()


class TestCacheManagerInvalidate:
    """Test cache invalidation."""

    def test_invalidate_specific_release(
        self, cache_manager, release_info, temp_cache_dir
    ):
        """Invalidate removes specific release from cache."""
        # Create cached file
        cached_file = temp_cache_dir / release_info.asset_name
        cached_file.write_text("content")

        # Add to metadata
        cache_key = f"{release_info.tag}:{release_info.asset_name}"
        cache_manager._metadata[cache_key] = {
            "filename": release_info.asset_name,
            "downloaded_at": datetime.now().isoformat(),
        }
        cache_manager._save_metadata()

        cache_manager.invalidate(release_info)

        assert not cached_file.exists()
        assert cache_key not in cache_manager._metadata

    def test_invalidate_all(self, cache_manager, temp_cache_dir):
        """Invalidate without args clears all cache."""
        # Create multiple cached files
        for i in range(3):
            f = temp_cache_dir / f"file_{i}.duckdb"
            f.write_text("content")
            cache_manager._metadata[f"key_{i}"] = {
                "filename": f.name,
                "downloaded_at": datetime.now().isoformat(),
            }
        cache_manager._save_metadata()

        cache_manager.invalidate()

        assert cache_manager._metadata == {}
        # Files should be deleted
        duckdb_files = list(temp_cache_dir.glob("*.duckdb"))
        assert len(duckdb_files) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
