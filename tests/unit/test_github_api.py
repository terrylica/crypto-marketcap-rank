"""
Unit tests for SDK GitHubReleasesClient.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/4
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from crypto_marketcap_rank.exceptions import DataNotFoundError, DownloadError
from crypto_marketcap_rank.github_api import GitHubReleasesClient, ReleaseInfo


@pytest.fixture
def mock_response():
    """Mock GitHub API release response."""
    return {
        "tag_name": "daily-2025-01-15",
        "assets": [
            {
                "name": "crypto_rankings_2025-01-15.duckdb",
                "url": "https://api.github.com/repos/terrylica/crypto-marketcap-rank/releases/assets/12345",
                "size": 150_000_000,
            }
        ],
    }


@pytest.fixture
def client():
    """Create GitHubReleasesClient."""
    return GitHubReleasesClient()


class TestReleaseInfo:
    """Test ReleaseInfo dataclass."""

    def test_release_info_creation(self):
        """ReleaseInfo can be created with all fields."""
        info = ReleaseInfo(
            tag="daily-2025-01-15",
            date=date(2025, 1, 15),
            download_url="https://example.com/asset",
            asset_name="test.duckdb",
            size_bytes=100,
        )

        assert info.tag == "daily-2025-01-15"
        assert info.date == date(2025, 1, 15)
        assert info.asset_name == "test.duckdb"


class TestGitHubReleasesClientLatest:
    """Test get_latest_release functionality."""

    def test_get_latest_release_success(self, client, mock_response):
        """Successfully fetches latest release."""
        with patch.object(client._session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_get.return_value = mock_resp

            result = client.get_latest_release()

            assert isinstance(result, ReleaseInfo)
            assert result.tag == "daily-2025-01-15"
            assert result.date == date(2025, 1, 15)

    def test_get_latest_release_404(self, client):
        """Raises DataNotFoundError when no releases exist."""
        with patch.object(client._session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp

            with pytest.raises(DataNotFoundError, match="No releases found"):
                client.get_latest_release()

    def test_get_latest_release_no_duckdb_asset(self, client):
        """Raises DataNotFoundError when no DuckDB asset in release."""
        with patch.object(client._session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "tag_name": "daily-2025-01-15",
                "assets": [{"name": "README.md", "url": "...", "size": 100}],
            }
            mock_get.return_value = mock_resp

            with pytest.raises(DataNotFoundError, match="No DuckDB asset"):
                client.get_latest_release()


class TestGitHubReleasesClientByDate:
    """Test get_release_by_date functionality."""

    def test_get_release_by_date_success(self, client, mock_response):
        """Successfully fetches release for specific date."""
        with patch.object(client._session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_get.return_value = mock_resp

            result = client.get_release_by_date(date(2025, 1, 15))

            assert result.tag == "daily-2025-01-15"
            mock_get.assert_called_once()
            # Verify URL includes correct tag
            call_url = mock_get.call_args[0][0]
            assert "daily-2025-01-15" in call_url

    def test_get_release_by_date_404(self, client):
        """Raises DataNotFoundError for missing date."""
        with patch.object(client._session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp

            with pytest.raises(DataNotFoundError, match="No release found for date"):
                client.get_release_by_date(date(2025, 1, 15))


class TestGitHubReleasesClientDownload:
    """Test download_asset functionality."""

    def test_download_asset_success(self, client, temp_cache_dir):
        """Successfully downloads asset to file."""
        release = ReleaseInfo(
            tag="daily-2025-01-15",
            date=date(2025, 1, 15),
            download_url="https://api.github.com/repos/test/releases/assets/123",
            asset_name="test.duckdb",
            size_bytes=1000,
        )
        dest_path = temp_cache_dir / "test.duckdb"

        with patch.object(client._session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.iter_content.return_value = [b"test content"]
            mock_get.return_value = mock_resp

            result = client.download_asset(release, dest_path)

            assert result == dest_path
            assert dest_path.exists()
            assert dest_path.read_text() == "test content"

    def test_download_asset_cleans_up_on_failure(self, client, temp_cache_dir):
        """Removes partial file on download failure."""
        import requests

        release = ReleaseInfo(
            tag="daily-2025-01-15",
            date=date(2025, 1, 15),
            download_url="https://api.github.com/repos/test/releases/assets/123",
            asset_name="test.duckdb",
            size_bytes=1000,
        )
        dest_path = temp_cache_dir / "test.duckdb"

        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")

            with pytest.raises(DownloadError):
                client.download_asset(release, dest_path)

            assert not dest_path.exists()


class TestGitHubReleasesClientAuth:
    """Test authentication behavior."""

    def test_client_uses_github_token_env(self):
        """Client uses GITHUB_TOKEN from environment."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            client = GitHubReleasesClient()
            assert "Authorization" in client._session.headers

    def test_client_uses_gh_token_env(self):
        """Client uses GH_TOKEN from environment."""
        with patch.dict("os.environ", {"GH_TOKEN": "test-token"}, clear=True):
            client = GitHubReleasesClient()
            assert "Authorization" in client._session.headers

    def test_client_explicit_token(self):
        """Client uses explicitly provided token."""
        client = GitHubReleasesClient(token="explicit-token")
        assert client._session.headers["Authorization"] == "Bearer explicit-token"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
