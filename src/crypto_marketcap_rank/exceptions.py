"""
SDK Exceptions

Custom exceptions for the crypto_marketcap_rank SDK.
Pattern copied from src/builders/base_builder.py:BuildError.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/1
"""


class DataNotFoundError(Exception):
    """Raised when no release data is found for the requested date.

    Examples:
        - No GitHub release exists for the specified date
        - Release exists but contains no DuckDB asset
    """

    pass


class DownloadError(Exception):
    """Raised when download from GitHub Releases fails.

    Examples:
        - Network connectivity issues
        - GitHub API rate limiting
        - Asset download timeout
    """

    pass


class CacheError(Exception):
    """Raised when cache operations fail.

    Examples:
        - Cache directory not writable
        - Corrupted cache metadata
        - Cache invalidation failure
    """

    pass
