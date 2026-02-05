"""
GitHub Releases API Client

Fetches cryptocurrency rankings databases from GitHub Releases.
Pattern copied from src/collectors/coingecko_collector.py (request patterns).

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/1
"""

import logging
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests

from .exceptions import DataNotFoundError, DownloadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ReleaseInfo:
    """GitHub Release metadata."""

    tag: str
    date: date
    download_url: str
    asset_name: str
    size_bytes: int


class GitHubReleasesClient:
    """Client for GitHub Releases API.

    Fetches DuckDB databases from crypto-marketcap-rank releases.

    Release tag format: daily-YYYY-MM-DD
    Asset name format: crypto_rankings_YYYY-MM-DD_*.duckdb
    """

    REPO = "terrylica/crypto-marketcap-rank"
    API_BASE = "https://api.github.com"

    def __init__(self, token: str | None = None):
        """Initialize client.

        Args:
            token: GitHub personal access token (optional, from env GITHUB_TOKEN).
                   Required for higher rate limits (60 -> 5000 req/hr).
        """
        self._token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/vnd.github+json"
        self._session.headers["X-GitHub-Api-Version"] = "2022-11-28"
        if self._token:
            self._session.headers["Authorization"] = f"Bearer {self._token}"
            logger.debug("GitHub token configured")

    def get_latest_release(self) -> ReleaseInfo:
        """Get the latest release info.

        Returns:
            ReleaseInfo for the latest daily release.

        Raises:
            DataNotFoundError: If no releases available.
            DownloadError: If API request fails.
        """
        url = f"{self.API_BASE}/repos/{self.REPO}/releases/latest"
        logger.debug(f"Fetching latest release: {url}")

        try:
            resp = self._session.get(url, timeout=30)
            if resp.status_code == 404:
                raise DataNotFoundError("No releases found in repository")
            resp.raise_for_status()
            return self._parse_release(resp.json())
        except requests.RequestException as e:
            raise DownloadError(f"Failed to fetch latest release: {e}") from e

    def get_release_by_date(self, target_date: date) -> ReleaseInfo:
        """Get release for specific date.

        Args:
            target_date: Date to fetch (datetime.date object).

        Returns:
            ReleaseInfo for the specified date.

        Raises:
            DataNotFoundError: If no release for that date.
            DownloadError: If API request fails.
        """
        tag = f"daily-{target_date.isoformat()}"
        url = f"{self.API_BASE}/repos/{self.REPO}/releases/tags/{tag}"
        logger.debug(f"Fetching release by tag: {tag}")

        try:
            resp = self._session.get(url, timeout=30)
            if resp.status_code == 404:
                raise DataNotFoundError(f"No release found for date: {target_date}")
            resp.raise_for_status()
            return self._parse_release(resp.json())
        except requests.RequestException as e:
            raise DownloadError(f"Failed to fetch release for {target_date}: {e}") from e

    def download_asset(self, release: ReleaseInfo, dest_path: Path) -> Path:
        """Download release asset.

        Args:
            release: ReleaseInfo with download URL.
            dest_path: Destination file path.

        Returns:
            Path to downloaded file.

        Raises:
            DownloadError: If download fails.
        """
        logger.info(f"Downloading {release.asset_name} ({release.size_bytes / 1024 / 1024:.1f} MB)")

        try:
            # GitHub API requires Accept header for asset downloads
            headers = {"Accept": "application/octet-stream"}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"

            resp = self._session.get(
                release.download_url,
                headers=headers,
                stream=True,
                timeout=300,  # 5 min timeout for large files
            )
            resp.raise_for_status()

            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Stream to file
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded to: {dest_path}")
            return dest_path

        except requests.RequestException as e:
            # Clean up partial download
            if dest_path.exists():
                dest_path.unlink()
            raise DownloadError(f"Failed to download {release.asset_name}: {e}") from e

    def _parse_release(self, data: dict) -> ReleaseInfo:
        """Parse release JSON into ReleaseInfo.

        Args:
            data: GitHub API release response.

        Returns:
            ReleaseInfo dataclass.

        Raises:
            DataNotFoundError: If no DuckDB asset in release.
        """
        # Find DuckDB asset
        assets = [a for a in data.get("assets", []) if a["name"].endswith(".duckdb")]
        if not assets:
            raise DataNotFoundError(f"No DuckDB asset in release: {data.get('tag_name')}")

        asset = assets[0]
        tag = data["tag_name"]

        # Parse date from tag (daily-YYYY-MM-DD format)
        try:
            date_str = tag.replace("daily-", "")
            release_date = date.fromisoformat(date_str)
        except ValueError:
            # Fallback to today if tag format is unexpected
            release_date = date.today()

        return ReleaseInfo(
            tag=tag,
            date=release_date,
            download_url=asset["url"],
            asset_name=asset["name"],
            size_bytes=asset["size"],
        )
