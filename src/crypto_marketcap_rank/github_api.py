"""
GitHub Releases API Client

Fetches cryptocurrency rankings databases from GitHub Releases.
Pattern copied from src/collectors/coingecko_collector.py (request patterns).

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/1
"""

import contextlib
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
        """Get the latest daily release info.

        Queries releases with 'daily-' prefix and returns the most recent.
        Does NOT use /releases/latest (which returns semantic version tags).

        Returns:
            ReleaseInfo for the latest daily release.

        Raises:
            DataNotFoundError: If no daily releases available.
            DownloadError: If API request fails.
        """
        # Query all releases and filter for daily-* tags
        # GitHub's /releases/latest returns the latest semantic version, not daily-*
        url = f"{self.API_BASE}/repos/{self.REPO}/releases"
        logger.debug(f"Fetching releases to find latest daily-*: {url}")

        try:
            resp = self._session.get(url, params={"per_page": 100}, timeout=30)
            if resp.status_code == 404:
                raise DataNotFoundError("No releases found in repository")
            resp.raise_for_status()

            releases = resp.json()

            # Filter for daily-* releases with DuckDB assets
            daily_releases = []
            for rel in releases:
                tag = rel.get("tag_name", "")
                if tag.startswith("daily-"):
                    # Check for DuckDB asset
                    has_duckdb = any(a["name"].endswith(".duckdb") for a in rel.get("assets", []))
                    if has_duckdb:
                        daily_releases.append(rel)

            if not daily_releases:
                raise DataNotFoundError("No daily releases with DuckDB assets found")

            # Sort by date (daily-YYYY-MM-DD format) and return most recent
            daily_releases.sort(key=lambda r: r["tag_name"], reverse=True)
            latest = daily_releases[0]

            logger.debug(f"Found latest daily release: {latest['tag_name']}")
            return self._parse_release(latest)

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

    def get_available_releases(self) -> list[ReleaseInfo]:
        """Get all available daily releases.

        Returns:
            List of ReleaseInfo for all daily-* releases, sorted by date descending.

        Raises:
            DownloadError: If API request fails.
        """
        url = f"{self.API_BASE}/repos/{self.REPO}/releases"
        logger.debug(f"Fetching all releases: {url}")

        all_releases = []
        page = 1

        try:
            while True:
                resp = self._session.get(url, params={"per_page": 100, "page": page}, timeout=30)
                resp.raise_for_status()

                releases = resp.json()
                if not releases:
                    break

                for rel in releases:
                    tag = rel.get("tag_name", "")
                    if tag.startswith("daily-"):
                        has_duckdb = any(a["name"].endswith(".duckdb") for a in rel.get("assets", []))
                        if has_duckdb:
                            with contextlib.suppress(DataNotFoundError):
                                all_releases.append(self._parse_release(rel))

                page += 1

            # Sort by date descending
            all_releases.sort(key=lambda r: r.date, reverse=True)
            return all_releases

        except requests.RequestException as e:
            raise DownloadError(f"Failed to fetch releases: {e}") from e

    def get_data_availability(self) -> dict:
        """Get information about available data without downloading.

        Returns:
            Dictionary with availability info:
            - earliest: Earliest available date
            - latest: Most recent available date
            - total_days: Number of days with data
            - source: Data source description

        Example:
            >>> client = GitHubReleasesClient()
            >>> info = client.get_data_availability()
            >>> print(f"Data from {info['earliest']} to {info['latest']}")
        """
        releases = self.get_available_releases()

        if not releases:
            return {
                "earliest": None,
                "latest": None,
                "total_days": 0,
                "source": "CoinGecko API via GitHub Releases",
            }

        return {
            "earliest": releases[-1].date,  # Oldest (list is sorted descending)
            "latest": releases[0].date,  # Newest
            "total_days": len(releases),
            "source": "CoinGecko API via GitHub Releases",
        }

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
