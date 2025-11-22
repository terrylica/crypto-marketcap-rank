#!/usr/bin/env python3
"""
Visualization tool for market cap data using matplotlib
"""
# /// script
# dependencies = [
#     "pandas",
#     "matplotlib",
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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
    """Create visualizations for market cap data"""
    pass

@cli.command()
@click.option('--coins', default='bitcoin,ethereum', help='Comma-separated list of coins to plot')
@click.option('--output', default=None, help='Output file path')
def price_trend(coins, output):
    """Plot price trends for specified coins"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    coin_list = [c.strip() for c in coins.split(',')]

    fig, ax = plt.subplots(figsize=(12, 6))

    for coin in coin_list:
        coin_df = df[df['coin'].str.lower() == coin.lower()].sort_values('timestamp')
        if len(coin_df) > 0:
            ax.plot(coin_df['timestamp'], coin_df['price_usd'], marker='o', label=coin.upper())

    ax.set_xlabel('Date')
    ax.set_ylabel('Price (USD)')
    ax.set_title('Cryptocurrency Price Trends')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    if not output:
        output = f"price_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    plt.savefig(output, dpi=300)
    click.echo(f"Saved price trend chart to {output}")
    plt.close()

@cli.command()
@click.option('--coins', default='bitcoin,ethereum,bnb', help='Comma-separated list of coins to plot')
@click.option('--output', default=None, help='Output file path')
def market_cap_trend(coins, output):
    """Plot market cap trends for specified coins"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    coin_list = [c.strip() for c in coins.split(',')]

    fig, ax = plt.subplots(figsize=(12, 6))

    for coin in coin_list:
        coin_df = df[df['coin'].str.lower() == coin.lower()].sort_values('timestamp')
        if len(coin_df) > 0:
            ax.plot(coin_df['timestamp'], coin_df['market_cap_usd'] / 1e9, marker='o', label=coin.upper())

    ax.set_xlabel('Date')
    ax.set_ylabel('Market Cap (Billions USD)')
    ax.set_title('Cryptocurrency Market Cap Trends')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    if not output:
        output = f"market_cap_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    plt.savefig(output, dpi=300)
    click.echo(f"Saved market cap trend chart to {output}")
    plt.close()

@cli.command()
@click.option('--date', default=None, help='Specific date (YYYY-MM-DD) or latest')
@click.option('--output', default=None, help='Output file path')
def top_coins_bar(date, output):
    """Create bar chart of top 10 coins by market cap"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    if date:
        df_filtered = df[df['timestamp'].dt.date == pd.to_datetime(date).date()]
    else:
        latest_date = df['timestamp'].max()
        df_filtered = df[df['timestamp'] == latest_date]

    top_coins = df_filtered.nlargest(10, 'market_cap_usd')

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(top_coins['coin'].str.upper(), top_coins['market_cap_usd'] / 1e9)

    # Color bars with gradient
    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(bars)))
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    ax.set_xlabel('Market Cap (Billions USD)')
    ax.set_title('Top 10 Cryptocurrencies by Market Cap')
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()

    if not output:
        date_str = date or "latest"
        output = f"top_coins_bar_{date_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    plt.savefig(output, dpi=300)
    click.echo(f"Saved top coins bar chart to {output}")
    plt.close()

@cli.command()
@click.option('--coin', required=True, help='Coin to analyze')
@click.option('--output', default=None, help='Output file path')
def coin_overview(coin, output):
    """Create a comprehensive overview chart for a specific coin"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    coin_df = df[df['coin'].str.lower() == coin.lower()].sort_values('timestamp')

    if len(coin_df) == 0:
        click.echo(f"No data found for coin: {coin}")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'{coin.upper()} Analysis', fontsize=16, fontweight='bold')

    # Price trend
    axes[0, 0].plot(coin_df['timestamp'], coin_df['price_usd'], marker='o', color='#1f77b4')
    axes[0, 0].set_title('Price Trend')
    axes[0, 0].set_ylabel('Price (USD)')
    axes[0, 0].grid(True, alpha=0.3)

    # Market cap trend
    axes[0, 1].plot(coin_df['timestamp'], coin_df['market_cap_usd'] / 1e9, marker='o', color='#ff7f0e')
    axes[0, 1].set_title('Market Cap Trend')
    axes[0, 1].set_ylabel('Market Cap (Billions USD)')
    axes[0, 1].grid(True, alpha=0.3)

    # Volume trend
    axes[1, 0].bar(coin_df['timestamp'], coin_df['volume_24h'] / 1e9, color='#2ca02c')
    axes[1, 0].set_title('24h Trading Volume')
    axes[1, 0].set_ylabel('Volume (Billions USD)')
    axes[1, 0].grid(True, alpha=0.3, axis='y')

    # Rank over time
    axes[1, 1].plot(coin_df['timestamp'], coin_df['rank'], marker='o', color='#d62728')
    axes[1, 1].set_title('Market Rank Over Time')
    axes[1, 1].set_ylabel('Rank')
    axes[1, 1].invert_yaxis()
    axes[1, 1].grid(True, alpha=0.3)

    # Format x-axis for all plots
    for ax in axes.flat:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    if not output:
        output = f"overview_{coin}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    plt.savefig(output, dpi=300)
    click.echo(f"Saved overview chart to {output}")
    plt.close()

@cli.command()
@click.option('--date', default=None, help='Specific date (YYYY-MM-DD) or latest')
@click.option('--output', default=None, help='Output file path')
def market_distribution_pie(date, output):
    """Create pie chart showing market cap distribution"""
    db_path = Path(__file__).parent / "market_cap_history.jsonl"
    df = load_jsonl(str(db_path))

    if date:
        df_filtered = df[df['timestamp'].dt.date == pd.to_datetime(date).date()]
    else:
        latest_date = df['timestamp'].max()
        df_filtered = df[df['timestamp'] == latest_date]

    top_coins = df_filtered.nlargest(7, 'market_cap_usd')

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.pie(top_coins['market_cap_usd'], labels=top_coins['coin'].str.upper(), autopct='%1.1f%%',
           startangle=90)
    ax.set_title('Market Cap Distribution by Cryptocurrency')

    if not output:
        date_str = date or "latest"
        output = f"market_distribution_pie_{date_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    plt.savefig(output, dpi=300)
    click.echo(f"Saved pie chart to {output}")
    plt.close()

if __name__ == "__main__":
    import numpy as np
    cli()
