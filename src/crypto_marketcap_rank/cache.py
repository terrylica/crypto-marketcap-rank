"""
Cache Manager for SDK Downloads

Local caching of downloaded DuckDB databases.
Pattern copied from src/utils/checkpoint_manager.py (JSON caching patterns).

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/1
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from .exceptions import CacheError
from .github_api import GitHubReleasesClient, ReleaseInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CacheManager:
    """Local cache for downloaded databases.

    Features:
    - Atomic metadata writes (tmp + rename)
    - JSON serialization for metadata
    - Auto-invalidation after 7 days
    - Manual invalidation support

    Usage:
        cache = CacheManager()
        db_path = cache.get_or_download(release)
    """

    DEFAULT_DIR = Path.home() / ".cache" / "crypto_marketcap_rank"
    METADATA_FILE = "cache_metadata.json"
    MAX_AGE_DAYS = 7  # Auto-invalidate after 7 days

    def __init__(self, cache_dir: Path | None = None):
        """Initialize cache manager.

        Args:
            cache_dir: Custom cache directory. Defaults to ~/.cache/crypto_marketcap_rank/
        """
        self._dir = cache_dir or self.DEFAULT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self._dir / self.METADATA_FILE
        self._metadata = self._load_metadata()

        logger.debug(f"Cache directory: {self._dir}")
        logger.debug(f"Cached entries: {len(self._metadata)}")

    def get_or_download(
        self,
        release: ReleaseInfo,
        force_refresh: bool = False,
    ) -> Path:
        """Get cached file or download if missing/stale.

        Args:
            release: ReleaseInfo with download details.
            force_refresh: If True, re-download even if cached.

        Returns:
            Path to cached DuckDB file.

        Raises:
            CacheError: If cache operations fail.
        """
        cache_key = self._make_key(release)
        cached = self._metadata.get(cache_key)

        # Check if cached and valid
        if not force_refresh and cached and self._is_valid(cached):
            cached_path = self._dir / cached["filename"]
            if cached_path.exists():
                logger.info(f"Cache hit: {cached_path.name}")
                return cached_path

        # Download needed
        logger.info(f"Cache miss: downloading {release.asset_name}")

        try:
            client = GitHubReleasesClient()
            dest = self._dir / release.asset_name
            client.download_asset(release, dest)

            # Update metadata atomically
            self._metadata[cache_key] = {
                "filename": release.asset_name,
                "downloaded_at": datetime.now().isoformat(),
                "size_bytes": release.size_bytes,
                "tag": release.tag,
            }
            self._save_metadata()

            return dest

        except Exception as e:
            raise CacheError(f"Failed to download and cache {release.asset_name}: {e}") from e

    def invalidate(self, release: ReleaseInfo | None = None) -> None:
        """Invalidate cache (specific release or all).

        Args:
            release: Specific release to invalidate, or None for all.

        Raises:
            CacheError: If invalidation fails.
        """
        try:
            if release:
                # Invalidate specific release
                key = self._make_key(release)
                if key in self._metadata:
                    cached_file = self._dir / self._metadata[key]["filename"]
                    cached_file.unlink(missing_ok=True)
                    del self._metadata[key]
                    logger.info(f"Invalidated: {release.tag}")
            else:
                # Invalidate all
                for entry in self._metadata.values():
                    cached_file = self._dir / entry["filename"]
                    cached_file.unlink(missing_ok=True)
                self._metadata = {}
                logger.info("Invalidated all cache entries")

            self._save_metadata()

        except Exception as e:
            raise CacheError(f"Failed to invalidate cache: {e}") from e

    def _make_key(self, release: ReleaseInfo) -> str:
        """Create unique cache key from release info."""
        return f"{release.tag}:{release.asset_name}"

    def _is_valid(self, entry: dict) -> bool:
        """Check if cache entry is still valid (not expired)."""
        try:
            downloaded = datetime.fromisoformat(entry["downloaded_at"])
            return datetime.now() - downloaded < timedelta(days=self.MAX_AGE_DAYS)
        except (KeyError, ValueError):
            return False

    def _load_metadata(self) -> dict:
        """Load cache metadata from JSON file."""
        if self._metadata_path.exists():
            try:
                with open(self._metadata_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save cache metadata atomically (tmp + rename)."""
        try:
            tmp_path = self._metadata_path.with_suffix(".json.tmp")

            with open(tmp_path, "w") as f:
                json.dump(self._metadata, f, indent=2)

            # Atomic rename
            tmp_path.replace(self._metadata_path)

        except OSError as e:
            raise CacheError(f"Failed to save cache metadata: {e}") from e
