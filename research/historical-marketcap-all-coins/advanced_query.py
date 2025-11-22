#!/usr/bin/env python3
"""
Advanced query tool for market cap data with CLI interface
"""
# /// script
# dependencies = [
#     "pandas",
#     "click",
#     "tabulate",
# ]
# ///

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd
import click
from tabulate import tabulate

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

def format_currency(value):
    """Format value as currency"""
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    elif value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    else:
        return f"${value:,.2f}"

@click.group()
def cli():
    """Advanced query tool for market cap data"""
    pass

@cli.command()
@click.option('--coin', required=True, help='Coin name or symbol')
@click.option('--start-date', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD)')
@click.option('--fields', default='timestamp,price_usd,market_cap_usd,volume_24h', help='Comma-separated fields to display')
def query_coin(coin, start_date, end_date, fields):
    """Query specific coin data with date range filtering"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    # Filter by coin
    coin_df = df[df['coin'].str.lower() == coin.lower()]

    if len(coin_df) == 0:
        click.echo(f"No data found for coin: {coin}")
        return

    # Filter by date range
    if start_date:
        coin_df = coin_df[coin_df['timestamp'] >= pd.to_datetime(start_date)]
    if end_date:
        coin_df = coin_df[coin_df['timestamp'] <= pd.to_datetime(end_date)]

    coin_df = coin_df.sort_values('timestamp')

    # Select fields
    field_list = [f.strip() for f in fields.split(',')]
    display_df = coin_df[field_list].copy()

    # Format display
    for col in display_df.columns:
        if 'market_cap' in col or 'volume' in col:
            display_df[col] = display_df[col].apply(format_currency)

    click.echo(tabulate(display_df, headers='keys', tablefmt='grid'))

@cli.command()
@click.option('--date', required=True, help='Target date (YYYY-MM-DD)')
@click.option('--top', default=10, help='Number of top coins to show')
def snapshot(date, top):
    """Get market snapshot for a specific date"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    target_date = pd.to_datetime(date).date()
    snapshot_df = df[df['timestamp'].dt.date == target_date]

    if len(snapshot_df) == 0:
        click.echo(f"No data found for date: {date}")
        return

    snapshot_df = snapshot_df.nlargest(top, 'market_cap_usd')[['rank', 'coin', 'symbol', 'price_usd', 'market_cap_usd', 'volume_24h']]

    display_df = snapshot_df.copy()
    display_df['price_usd'] = display_df['price_usd'].apply(lambda x: f"${x:,.2f}")
    display_df['market_cap_usd'] = display_df['market_cap_usd'].apply(format_currency)
    display_df['volume_24h'] = display_df['volume_24h'].apply(format_currency)

    click.echo(f"\nMarket Snapshot - {date}")
    click.echo(tabulate(display_df, headers='keys', tablefmt='grid'))

@cli.command()
@click.option('--window', default=5, help='Number of days window')
@click.option('--min-growth', default=None, type=float, help='Minimum growth % to filter')
def gainers(window, min_growth):
    """Find top gainers over a period"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    results = []
    for coin in df['coin'].unique():
        coin_df = df[df['coin'] == coin].sort_values('timestamp')

        if len(coin_df) < 2:
            continue

        oldest = coin_df.iloc[0]
        latest = coin_df.iloc[-1]

        market_cap_growth = ((latest['market_cap_usd'] - oldest['market_cap_usd']) / oldest['market_cap_usd']) * 100
        price_growth = ((latest['price_usd'] - oldest['price_usd']) / oldest['price_usd']) * 100

        if min_growth is None or market_cap_growth >= min_growth:
            results.append({
                'coin': coin.upper(),
                'symbol': latest['symbol'],
                'market_cap_growth_%': round(market_cap_growth, 2),
                'price_growth_%': round(price_growth, 2),
                'start_mcap': format_currency(oldest['market_cap_usd']),
                'end_mcap': format_currency(latest['market_cap_usd']),
            })

    result_df = pd.DataFrame(results).sort_values('market_cap_growth_%', ascending=False)
    click.echo(f"\nTop Gainers (Last {window} days)")
    click.echo(tabulate(result_df, headers='keys', tablefmt='grid'))

@cli.command()
@click.option('--start-date', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='End date (YYYY-MM-DD)')
@click.option('--coin', default=None, help='Filter by specific coin')
def price_range(start_date, end_date, coin):
    """Find price range (high/low) for period"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    # Filter by date range
    df = df[(df['timestamp'] >= pd.to_datetime(start_date)) & (df['timestamp'] <= pd.to_datetime(end_date))]

    if coin:
        df = df[df['coin'].str.lower() == coin.lower()]
        coins_list = [coin]
    else:
        coins_list = df['coin'].unique()

    results = []
    for c in coins_list:
        coin_df = df[df['coin'] == c]
        if len(coin_df) > 0:
            results.append({
                'coin': c.upper(),
                'symbol': coin_df.iloc[0]['symbol'],
                'high': f"${coin_df['price_usd'].max():,.2f}",
                'low': f"${coin_df['price_usd'].min():,.2f}",
                'avg': f"${coin_df['price_usd'].mean():,.2f}",
                'volatility_%': round(coin_df['price_usd'].std() / coin_df['price_usd'].mean() * 100, 2),
            })

    result_df = pd.DataFrame(results)
    click.echo(f"\nPrice Range Analysis ({start_date} to {end_date})")
    click.echo(tabulate(result_df, headers='keys', tablefmt='grid'))

@cli.command()
@click.option('--date', default=None, help='Specific date (YYYY-MM-DD) or latest')
@click.option('--threshold', default=1e10, type=float, help='Minimum market cap filter')
def dominated_by(date, threshold):
    """Analyze market dominance (what % top coin controls)"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    if date:
        snapshot_df = df[df['timestamp'].dt.date == pd.to_datetime(date).date()]
    else:
        latest_date = df['timestamp'].max()
        snapshot_df = df[df['timestamp'] == latest_date]

    snapshot_df = snapshot_df.sort_values('market_cap_usd', ascending=False)

    total_mcap = snapshot_df['market_cap_usd'].sum()
    filtered_df = snapshot_df[snapshot_df['market_cap_usd'] >= threshold]

    click.echo(f"\nMarket Dominance Analysis")
    click.echo(f"Total Market Cap: {format_currency(total_mcap)}")
    click.echo(f"Total Coins Analyzed: {len(snapshot_df)}")
    click.echo(f"Coins >= {format_currency(threshold)}: {len(filtered_df)}")

    dominance_data = []
    for idx, row in filtered_df.iterrows():
        pct = (row['market_cap_usd'] / total_mcap) * 100
        dominance_data.append({
            'rank': row['rank'],
            'coin': row['coin'].upper(),
            'symbol': row['symbol'],
            'market_cap': format_currency(row['market_cap_usd']),
            'dominance_%': round(pct, 2),
        })

    dominance_df = pd.DataFrame(dominance_data)
    click.echo(tabulate(dominance_df, headers='keys', tablefmt='grid'))

if __name__ == "__main__":
    cli()
