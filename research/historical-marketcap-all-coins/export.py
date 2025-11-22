#!/usr/bin/env python3
"""
Export tools for market cap data (CSV, JSON, TSV formats)
"""
# /// script
# dependencies = [
#     "pandas",
#     "click",
# ]
# ///

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd
import click

def load_jsonl(file_path: str) -> pd.DataFrame:
    """Load JSONL file into DataFrame"""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

@click.group()
def cli():
    """Export market cap data to various formats"""
    pass

@cli.command()
@click.option('--coin', default=None, help='Filter by specific coin')
@click.option('--output', default=None, help='Output file path')
@click.option('--date-range', default=None, help='Date range (YYYY-MM-DD:YYYY-MM-DD)')
def export_csv(coin, output, date_range):
    """Export data to CSV format"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    # Filter by coin
    if coin:
        df = df[df['coin'].str.lower() == coin.lower()]

    # Filter by date range
    if date_range:
        start, end = date_range.split(':')
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]

    # Determine output file
    if not output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        coin_str = f"_{coin}" if coin else ""
        output = f"export_csv{coin_str}_{timestamp}.csv"

    # Export
    df = df.sort_values('timestamp')
    df.to_csv(output, index=False)
    click.echo(f"Exported {len(df)} records to {output}")

@cli.command()
@click.option('--coin', default=None, help='Filter by specific coin')
@click.option('--output', default=None, help='Output file path')
@click.option('--date-range', default=None, help='Date range (YYYY-MM-DD:YYYY-MM-DD)')
def export_json(coin, output, date_range):
    """Export data to JSON format (records)"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    # Filter by coin
    if coin:
        df = df[df['coin'].str.lower() == coin.lower()]

    # Filter by date range
    if date_range:
        start, end = date_range.split(':')
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]

    # Determine output file
    if not output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        coin_str = f"_{coin}" if coin else ""
        output = f"export_json{coin_str}_{timestamp}.json"

    # Convert timestamp to string for JSON serialization
    df['timestamp'] = df['timestamp'].astype(str)
    df = df.sort_values('timestamp')

    # Export as JSON records
    with open(output, 'w') as f:
        json.dump(df.to_dict('records'), f, indent=2)

    click.echo(f"Exported {len(df)} records to {output}")

@cli.command()
@click.option('--output', default=None, help='Output file path')
def export_summary(output):
    """Export summary statistics by coin"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    # Calculate summary stats
    summary_data = []
    for coin in df['coin'].unique():
        coin_df = df[df['coin'] == coin]
        summary_data.append({
            'coin': coin,
            'symbol': coin_df.iloc[0]['symbol'],
            'record_count': len(coin_df),
            'latest_price': coin_df.iloc[-1]['price_usd'],
            'latest_market_cap': coin_df.iloc[-1]['market_cap_usd'],
            'latest_rank': coin_df.iloc[-1]['rank'],
            'avg_price': coin_df['price_usd'].mean(),
            'min_price': coin_df['price_usd'].min(),
            'max_price': coin_df['price_usd'].max(),
            'avg_market_cap': coin_df['market_cap_usd'].mean(),
            'first_recorded': coin_df['timestamp'].min().strftime('%Y-%m-%d'),
            'last_recorded': coin_df['timestamp'].max().strftime('%Y-%m-%d'),
        })

    summary_df = pd.DataFrame(summary_data).sort_values('latest_market_cap', ascending=False)

    if not output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = f"summary_{timestamp}.csv"

    summary_df.to_csv(output, index=False)
    click.echo(f"Exported summary for {len(summary_df)} coins to {output}")

@cli.command()
@click.option('--top', default=5, help='Number of top coins to show')
def export_html(top):
    """Generate HTML report"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    # Get latest snapshot
    latest_date = df['timestamp'].max()
    latest_df = df[df['timestamp'] == latest_date].nlargest(top, 'market_cap_usd')

    # Create HTML
    html_content = f"""
    <html>
    <head>
        <title>Market Cap Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Cryptocurrency Market Cap Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Data as of: {latest_date.strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Top {top} Cryptocurrencies by Market Cap</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>Coin</th>
                <th>Symbol</th>
                <th>Price (USD)</th>
                <th>Market Cap (USD)</th>
                <th>24h Volume (USD)</th>
            </tr>
    """

    for idx, row in latest_df.iterrows():
        html_content += f"""
            <tr>
                <td>{row['rank']}</td>
                <td>{row['coin'].upper()}</td>
                <td>{row['symbol']}</td>
                <td>${row['price_usd']:,.2f}</td>
                <td>${row['market_cap_usd']:,.0f}</td>
                <td>${row['volume_24h']:,.0f}</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    output = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output, 'w') as f:
        f.write(html_content)

    click.echo(f"Generated HTML report: {output}")

if __name__ == "__main__":
    cli()
