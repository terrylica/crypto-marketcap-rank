"""
Command-line interface for crypto-marketcap-rank.

GitHub Issue: https://github.com/terrylica/crypto-marketcap-rank/issues/2

Usage:
    crypto-marketcap-rank rankings --date latest --top 100
    crypto-marketcap-rank rankings --date 2025-01-15 --format json
    crypto-marketcap-rank export --date latest --format parquet -o data.parquet
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__, load_date, load_latest
from .exceptions import CacheError, DataNotFoundError, DownloadError


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog="crypto-marketcap-rank",
        description="Daily cryptocurrency market cap rankings with auto-download",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Rankings command
    rankings_parser = subparsers.add_parser(
        "rankings",
        help="Query cryptocurrency rankings",
    )
    rankings_parser.add_argument(
        "--date",
        type=str,
        default="latest",
        help="Date to query (YYYY-MM-DD or 'latest')",
    )
    rankings_parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="Number of top coins to show (default: 100)",
    )
    rankings_parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    rankings_parser.add_argument(
        "--symbol",
        type=str,
        help="Find specific coin by symbol (e.g., btc, eth)",
    )

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export rankings to file",
    )
    export_parser.add_argument(
        "--date",
        type=str,
        default="latest",
        help="Date to export (YYYY-MM-DD or 'latest')",
    )
    export_parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Export format (default: parquet)",
    )
    export_parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file path",
    )

    # Cache command
    cache_parser = subparsers.add_parser(
        "cache",
        help="Manage local cache",
    )
    cache_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all cached databases",
    )
    cache_parser.add_argument(
        "--info",
        action="store_true",
        help="Show cache information",
    )

    return parser


def cmd_rankings(args: argparse.Namespace) -> int:
    """Handle rankings command."""
    # Load database
    if args.date == "latest":
        db = load_latest()
    else:
        target_date = date.fromisoformat(args.date)
        db = load_date(target_date)

    # Query data
    if args.symbol:
        df = db.find_coin(args.symbol)
        if df.empty:
            print(f"No coin found with symbol: {args.symbol}", file=sys.stderr)
            return 1
    else:
        df = db.get_top_n(args.top)

    # Format output
    if args.format == "json":
        print(df.to_json(orient="records", indent=2))
    elif args.format == "csv":
        print(df.to_csv(index=False))
    else:
        # Table format - select key columns
        columns = ["rank", "symbol", "name", "price", "market_cap"]
        available = [c for c in columns if c in df.columns]
        print(df[available].to_string(index=False))

    db.close()
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Handle export command."""
    # Load database
    if args.date == "latest":
        db = load_latest()
    else:
        target_date = date.fromisoformat(args.date)
        db = load_date(target_date)

    output_path = Path(args.output)

    # Export
    if args.format == "parquet":
        db.export_parquet(output_path)
    else:
        db.export_csv(output_path)

    print(f"Exported to: {output_path}")
    db.close()
    return 0


def cmd_cache(args: argparse.Namespace) -> int:
    """Handle cache command."""
    from .cache import CacheManager

    cache = CacheManager()

    if args.clear:
        cache.invalidate()
        print("Cache cleared")
    elif args.info:
        cache_dir = cache._dir
        metadata = cache._metadata
        print(f"Cache directory: {cache_dir}")
        print(f"Cached entries: {len(metadata)}")
        for key, info in metadata.items():
            print(f"  - {info.get('filename', key)}: {info.get('downloaded_at', 'unknown')}")
    else:
        print("Use --clear to clear cache or --info to show cache info")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "rankings":
            return cmd_rankings(args)
        elif args.command == "export":
            return cmd_export(args)
        elif args.command == "cache":
            return cmd_cache(args)
        else:
            parser.print_help()
            return 1

    except DataNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except DownloadError as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return 1
    except CacheError as e:
        print(f"Cache error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Invalid input: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
