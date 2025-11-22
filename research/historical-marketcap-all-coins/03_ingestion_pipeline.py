#!/usr/bin/env python3
"""
Data Ingestion Pipeline & Retention Policy
Handles continuous collection and intelligent data retention
"""
# /// script
# dependencies = [
#   "pyarrow==17.0.0",
# ]
# ///

import sqlite3
import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import os

class RetentionPolicy(Enum):
    """Data retention strategies"""
    HOT = "hot"           # Last 30 days: raw SQLite, hourly sampling
    WARM = "warm"         # 30 days to 1 year: compressed JSONL, daily sampling
    COLD = "cold"         # 1+ years: columnar Parquet, weekly sampling
    ARCHIVE = "archive"   # 5+ years: quarterly sampling only

class DataRetentionManager:
    """Manages multi-tier data retention with automatic archival"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.setup_directories()
    
    def setup_directories(self):
        """Create tier-specific directories"""
        self.hot_dir = self.base_path / "hot"      # SQLite (30 days)
        self.warm_dir = self.base_path / "warm"    # Compressed JSONL (1 year)
        self.cold_dir = self.base_path / "cold"    # Parquet (5 years)
        self.archive_dir = self.base_path / "archive"  # Long-term storage
        
        for dir_path in [self.hot_dir, self.warm_dir, self.cold_dir, self.archive_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_policy_for_timestamp(self, timestamp: datetime) -> RetentionPolicy:
        """Determine retention tier for a given timestamp"""
        now = datetime.now()
        age = now - timestamp
        
        if age.days <= 30:
            return RetentionPolicy.HOT
        elif age.days <= 365:
            return RetentionPolicy.WARM
        elif age.days <= 1825:  # 5 years
            return RetentionPolicy.COLD
        else:
            return RetentionPolicy.ARCHIVE
    
    def should_sample_for_tier(self, timestamp: datetime, policy: RetentionPolicy) -> bool:
        """Determine if record should be kept based on sampling policy"""
        if policy == RetentionPolicy.HOT:
            return True  # Keep all hourly data
        elif policy == RetentionPolicy.WARM:
            # Keep daily samples (day boundary)
            return timestamp.hour == 0
        elif policy == RetentionPolicy.COLD:
            # Keep weekly samples (Mondays at midnight)
            return timestamp.weekday() == 0 and timestamp.hour == 0
        elif policy == RetentionPolicy.ARCHIVE:
            # Keep quarterly samples (1st of Q months at midnight)
            return timestamp.month in [1, 4, 7, 10] and timestamp.day == 1 and timestamp.hour == 0
        return False
    
    def estimate_retention_storage(self, num_coins: int = 13532) -> Dict[str, float]:
        """Estimate storage for multi-tier retention"""
        
        # 350 bytes per record (compressed varies by tier)
        record_size = 350
        
        # Hot tier: 30 days * 24 hours = 720 records per coin
        hot_records = num_coins * 30 * 24
        hot_size = hot_records * record_size / (1024**3)
        
        # Warm tier: 335 days * 1 record/day = 335 records per coin
        warm_records = num_coins * 335
        warm_size = warm_records * record_size * 0.25 / (1024**3)  # 75% compression
        
        # Cold tier: 4 years * 52 weeks = 208 records per coin
        cold_records = num_coins * 4 * 52
        cold_size = cold_records * record_size * 0.20 / (1024**3)  # 80% compression
        
        # Archive: minimal, negligible
        archive_records = num_coins * 20  # ~20 quarterly samples
        archive_size = archive_records * record_size * 0.15 / (1024**3)
        
        total_size = hot_size + warm_size + cold_size + archive_size
        
        return {
            "hot_gb": hot_size,
            "warm_gb": warm_size,
            "cold_gb": cold_size,
            "archive_gb": archive_size,
            "total_gb": total_size,
            "hot_records": hot_records,
            "warm_records": warm_records,
            "cold_records": cold_records,
            "archive_records": archive_records,
        }


class IngestionPipeline:
    """Handles continuous data ingestion and archival"""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.retention_mgr = DataRetentionManager(str(self.storage_path))
        self.hot_db_path = self.retention_mgr.hot_dir / "current.db"
        self.setup_hot_database()
    
    def setup_hot_database(self):
        """Initialize hot tier (current) database"""
        conn = sqlite3.connect(str(self.hot_db_path))
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS market_cap_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            price REAL NOT NULL,
            market_cap INTEGER NOT NULL,
            volume_24h REAL NOT NULL,
            market_cap_change_24h REAL,
            percent_change_24h REAL,
            percent_change_7d REAL,
            percent_change_30d REAL,
            rank INTEGER,
            collection_source TEXT,
            UNIQUE(coin_id, timestamp)
        )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_coin_time ON market_cap_history(coin_id, timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON market_cap_history(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_market_cap ON market_cap_history(market_cap)")
        
        conn.commit()
        conn.close()
    
    def ingest_batch(self, records: List[Dict[str, Any]]):
        """Ingest a batch of market cap records"""
        conn = sqlite3.connect(str(self.hot_db_path))
        
        insertions = [
            (r.get('id'), r.get('timestamp'), r.get('price'), 
             r.get('market_cap'), r.get('volume_24h'),
             r.get('market_cap_change_24h'), r.get('percent_change_24h'),
             r.get('percent_change_7d'), r.get('percent_change_30d'),
             r.get('rank'), r.get('source', 'coinpaprika'))
            for r in records
        ]
        
        try:
            conn.executemany("""
            INSERT INTO market_cap_history
            (coin_id, timestamp, price, market_cap, volume_24h,
             market_cap_change_24h, percent_change_24h, percent_change_7d,
             percent_change_30d, rank, collection_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, insertions)
            conn.commit()
        finally:
            conn.close()
    
    def archive_old_data(self, days_threshold: int = 30):
        """Move records older than threshold to warm tier"""
        conn = sqlite3.connect(str(self.hot_db_path))
        
        cutoff = datetime.now() - timedelta(days=days_threshold)
        
        # Get records to archive
        cursor = conn.execute("""
        SELECT coin_id, timestamp, price, market_cap, volume_24h,
               market_cap_change_24h, percent_change_24h, percent_change_7d,
               percent_change_30d, rank, collection_source
        FROM market_cap_history
        WHERE timestamp < ?
        """, (cutoff.isoformat(),))
        
        records = cursor.fetchall()
        
        # Write to compressed JSONL
        if records:
            archive_date = cutoff.strftime("%Y-%m-%d")
            archive_file = self.retention_mgr.warm_dir / f"archive-{archive_date}.jsonl.gz"
            
            with gzip.open(str(archive_file), 'wt', encoding='utf-8') as f:
                for record in records:
                    obj = {
                        'coin_id': record[0],
                        'timestamp': record[1],
                        'price': record[2],
                        'market_cap': record[3],
                        'volume_24h': record[4],
                        'market_cap_change_24h': record[5],
                        'percent_change_24h': record[6],
                        'percent_change_7d': record[7],
                        'percent_change_30d': record[8],
                        'rank': record[9],
                    }
                    f.write(json.dumps(obj) + '\n')
            
            # Delete archived records
            conn.execute("DELETE FROM market_cap_history WHERE timestamp < ?", (cutoff.isoformat(),))
            conn.commit()
        
        conn.close()
        return len(records)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        conn = sqlite3.connect(str(self.hot_db_path))
        
        cursor = conn.execute("SELECT COUNT(*) FROM market_cap_history")
        hot_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM market_cap_history")
        min_ts, max_ts = cursor.fetchone()
        
        cursor = conn.execute("SELECT COUNT(DISTINCT coin_id) FROM market_cap_history")
        num_coins = cursor.fetchone()[0]
        
        conn.close()
        
        # Count warm tier files
        warm_files = list(self.retention_mgr.warm_dir.glob("*.jsonl.gz"))
        
        return {
            "hot_tier_records": hot_count,
            "hot_tier_coins": num_coins,
            "hot_tier_timespan": f"{min_ts} to {max_ts}" if min_ts else "empty",
            "warm_tier_files": len(warm_files),
            "hot_db_size_mb": os.path.getsize(str(self.hot_db_path)) / (1024**2),
        }


def test_ingestion_pipeline():
    """Test the ingestion pipeline"""
    print("=" * 70)
    print("INGESTION PIPELINE & RETENTION POLICY TESTING")
    print("=" * 70)
    
    # Test retention policy
    retention_mgr = DataRetentionManager("/tmp/historical-marketcap-all-coins/retention-test")
    
    print("\nData Retention Tiers:")
    print("-" * 70)
    timestamps = [
        ("Now (hot)", datetime.now()),
        ("30 days ago (warm)", datetime.now() - timedelta(days=30)),
        ("1 year ago (cold)", datetime.now() - timedelta(days=365)),
        ("5 years ago (cold/archive)", datetime.now() - timedelta(days=1825)),
    ]
    
    for label, ts in timestamps:
        policy = retention_mgr.get_policy_for_timestamp(ts)
        print(f"  {label:<30} -> {policy.value.upper()}")
    
    # Test storage estimation
    print("\n" + "=" * 70)
    print("MULTI-TIER RETENTION STORAGE ESTIMATES")
    print("=" * 70)
    
    estimates = retention_mgr.estimate_retention_storage()
    print(f"\nFor all 13,532 coins with optimal retention policies:")
    print(f"  Hot tier (30 days, all records): {estimates['hot_gb']:.2f} GB")
    print(f"  Warm tier (30d-1y, daily samples): {estimates['warm_gb']:.2f} GB")
    print(f"  Cold tier (1-5 years, weekly samples): {estimates['cold_gb']:.2f} GB")
    print(f"  Archive (5+ years, quarterly): {estimates['archive_gb']:.4f} GB")
    print(f"  ─────────────────────────────────")
    print(f"  Total: {estimates['total_gb']:.2f} GB")
    
    print(f"\nRecord Distribution:")
    print(f"  Hot tier: {estimates['hot_records']:,} records")
    print(f"  Warm tier: {estimates['warm_records']:,} records")
    print(f"  Cold tier: {estimates['cold_records']:,} records")
    print(f"  Archive tier: {estimates['archive_records']:,} records")
    
    # Test ingestion pipeline
    print("\n" + "=" * 70)
    print("INGESTION PIPELINE TESTING")
    print("=" * 70)
    
    pipeline = IngestionPipeline("/tmp/historical-marketcap-all-coins/pipeline-test")
    
    # Ingest sample data
    print("\nIngesting 5,000 sample records...")
    sample_records = []
    for i in range(5000):
        sample_records.append({
            'id': f'coin-{i % 500}',
            'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
            'price': 100.0 + i * 0.1,
            'market_cap': 1000000000 + i * 10000,
            'volume_24h': 500000000.0,
            'market_cap_change_24h': -0.5,
            'percent_change_24h': -0.5,
            'percent_change_7d': -5.0,
            'percent_change_30d': -10.0,
            'rank': (i % 100) + 1,
        })
    
    pipeline.ingest_batch(sample_records)
    
    # Show stats
    stats = pipeline.get_stats()
    print(f"\nPipeline Statistics:")
    print(f"  Hot tier records: {stats['hot_tier_records']:,}")
    print(f"  Hot tier coins: {stats['hot_tier_coins']:,}")
    print(f"  Database size: {stats['hot_db_size_mb']:.2f} MB")
    
    # Test archival
    print(f"\nArchiving records older than 30 days...")
    archived_count = pipeline.archive_old_data(30)
    print(f"  Archived: {archived_count:,} records")
    
    stats = pipeline.get_stats()
    print(f"  Hot tier records after archival: {stats['hot_tier_records']:,}")


if __name__ == "__main__":
    test_ingestion_pipeline()
