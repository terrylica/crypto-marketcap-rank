#!/usr/bin/env python3
"""
Production-Ready Market Cap Storage System
Complete implementation with all components integrated
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
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import os

class RetentionTier(Enum):
    """Storage tiers for different data ages"""
    HOT = "hot"          # 0-30 days
    WARM = "warm"        # 30 days - 1 year
    COLD = "cold"        # 1-5 years
    ARCHIVE = "archive"  # 5+ years

@dataclass
class MarketCapRecord:
    """Market cap record data class"""
    coin_id: str
    timestamp: datetime
    price: float
    market_cap: int
    volume_24h: float
    market_cap_change_24h: float
    percent_change_24h: float
    percent_change_7d: float
    percent_change_30d: float
    rank: int
    source: str = "coinpaprika"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketCapRecord':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ProductionMarketCapStorage:
    """Production-grade market cap storage system"""
    
    def __init__(self, base_path: str = "/tmp/historical-marketcap-all-coins"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize tier directories
        self.tiers = {
            RetentionTier.HOT: self.base_path / "data" / "hot",
            RetentionTier.WARM: self.base_path / "data" / "warm",
            RetentionTier.COLD: self.base_path / "data" / "cold",
            RetentionTier.ARCHIVE: self.base_path / "data" / "archive",
        }
        
        for tier_path in self.tiers.values():
            tier_path.mkdir(parents=True, exist_ok=True)
        
        self.hot_db = self.tiers[RetentionTier.HOT] / "current.db"
        self._setup_hot_database()
    
    def _setup_hot_database(self):
        """Initialize hot tier database with optimal settings"""
        conn = sqlite3.connect(str(self.hot_db))
        
        # Performance optimizations
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")
        conn.execute("PRAGMA page_size = 4096")
        
        # Create main table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS market_cap_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            price REAL NOT NULL,
            market_cap INTEGER NOT NULL,
            volume_24h REAL NOT NULL,
            market_cap_change_24h REAL NOT NULL,
            percent_change_24h REAL NOT NULL,
            percent_change_7d REAL NOT NULL,
            percent_change_30d REAL NOT NULL,
            rank INTEGER NOT NULL,
            source TEXT NOT NULL,
            UNIQUE(coin_id, timestamp)
        )
        """)
        
        # Create optimized indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_coin_id ON market_cap_history(coin_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON market_cap_history(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_market_cap ON market_cap_history(market_cap)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_coin_time ON market_cap_history(coin_id, timestamp)")
        
        # Create metadata table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
    
    def ingest(self, records: List[MarketCapRecord]) -> Dict[str, Any]:
        """Ingest market cap records with transaction support"""
        conn = sqlite3.connect(str(self.hot_db))
        
        inserted = 0
        skipped = 0
        
        try:
            for record in records:
                try:
                    conn.execute("""
                    INSERT INTO market_cap_history
                    (coin_id, timestamp, price, market_cap, volume_24h,
                     market_cap_change_24h, percent_change_24h, percent_change_7d,
                     percent_change_30d, rank, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.coin_id,
                        record.timestamp.isoformat(),
                        record.price,
                        record.market_cap,
                        record.volume_24h,
                        record.market_cap_change_24h,
                        record.percent_change_24h,
                        record.percent_change_7d,
                        record.percent_change_30d,
                        record.rank,
                        record.source
                    ))
                    inserted += 1
                except sqlite3.IntegrityError:
                    skipped += 1
            
            conn.commit()
        finally:
            conn.close()
        
        return {
            "inserted": inserted,
            "skipped": skipped,
            "total": len(records)
        }
    
    def query_latest(self, coin_id: Optional[str] = None, limit: int = 1000) -> List[MarketCapRecord]:
        """Query latest records"""
        conn = sqlite3.connect(str(self.hot_db))
        
        if coin_id:
            cursor = conn.execute("""
            SELECT coin_id, timestamp, price, market_cap, volume_24h,
                   market_cap_change_24h, percent_change_24h, percent_change_7d,
                   percent_change_30d, rank, source
            FROM market_cap_history
            WHERE coin_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """, (coin_id, limit))
        else:
            cursor = conn.execute("""
            SELECT coin_id, timestamp, price, market_cap, volume_24h,
                   market_cap_change_24h, percent_change_24h, percent_change_7d,
                   percent_change_30d, rank, source
            FROM market_cap_history
            ORDER BY timestamp DESC
            LIMIT ?
            """, (limit,))
        
        records = []
        for row in cursor:
            record = MarketCapRecord(
                coin_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                price=row[2],
                market_cap=row[3],
                volume_24h=row[4],
                market_cap_change_24h=row[5],
                percent_change_24h=row[6],
                percent_change_7d=row[7],
                percent_change_30d=row[8],
                rank=row[9],
                source=row[10]
            )
            records.append(record)
        
        conn.close()
        return records
    
    def archive_old_data(self, cutoff_days: int = 30) -> Dict[str, Any]:
        """Archive records older than cutoff to warm tier"""
        conn = sqlite3.connect(str(self.hot_db))
        
        cutoff = datetime.now() - timedelta(days=cutoff_days)
        
        # Fetch records to archive
        cursor = conn.execute("""
        SELECT coin_id, timestamp, price, market_cap, volume_24h,
               market_cap_change_24h, percent_change_24h, percent_change_7d,
               percent_change_30d, rank, source
        FROM market_cap_history
        WHERE timestamp < ?
        ORDER BY timestamp
        """, (cutoff.isoformat(),))
        
        records = cursor.fetchall()
        
        archived = 0
        if records:
            # Write to compressed JSONL
            archive_date = cutoff.strftime("%Y-%m-%d")
            archive_file = self.tiers[RetentionTier.WARM] / f"archive-{archive_date}.jsonl.gz"
            
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
                        'source': record[10],
                    }
                    f.write(json.dumps(obj) + '\n')
            
            # Delete from hot tier
            conn.execute("DELETE FROM market_cap_history WHERE timestamp < ?", (cutoff.isoformat(),))
            conn.commit()
            archived = len(records)
        
        conn.close()
        
        return {
            "archived_records": archived,
            "archive_file": str(archive_file) if archived > 0 else None
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        conn = sqlite3.connect(str(self.hot_db))
        
        cursor = conn.execute("SELECT COUNT(*) FROM market_cap_history")
        total_records = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT coin_id) FROM market_cap_history")
        num_coins = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM market_cap_history")
        min_ts, max_ts = cursor.fetchone()
        
        cursor = conn.execute("SELECT COUNT(*) FROM market_cap_history WHERE rank <= 100")
        top_100_records = cursor.fetchone()[0]
        
        conn.close()
        
        # Get storage sizes
        hot_size = self.hot_db.stat().st_size / (1024**2) if self.hot_db.exists() else 0
        
        warm_size = 0
        for f in self.tiers[RetentionTier.WARM].glob("*.jsonl.gz"):
            warm_size += f.stat().st_size / (1024**2)
        
        return {
            "hot_records": total_records,
            "unique_coins": num_coins,
            "top_100_records": top_100_records,
            "date_range": {
                "earliest": min_ts,
                "latest": max_ts
            },
            "storage": {
                "hot_mb": hot_size,
                "warm_mb": warm_size,
                "total_mb": hot_size + warm_size
            }
        }


def test_production_system():
    """Test the production implementation"""
    print("=" * 70)
    print("PRODUCTION SYSTEM TEST")
    print("=" * 70)
    
    storage = ProductionMarketCapStorage("/tmp/historical-marketcap-all-coins/production")
    
    # Create test records
    print("\n1. Ingesting 10,000 sample records...")
    records = []
    for i in range(10000):
        ts = datetime.now() - timedelta(hours=i)
        coin_idx = i % 500
        records.append(MarketCapRecord(
            coin_id=f"coin-{coin_idx}",
            timestamp=ts,
            price=100.0 + i * 0.1,
            market_cap=1000000000 + i * 10000,
            volume_24h=500000000.0,
            market_cap_change_24h=-0.5,
            percent_change_24h=-0.5,
            percent_change_7d=-5.0,
            percent_change_30d=-10.0,
            rank=(i % 100) + 1,
        ))
    
    result = storage.ingest(records)
    print(f"   Inserted: {result['inserted']:,}")
    print(f"   Skipped: {result['skipped']:,}")
    
    # Query test
    print("\n2. Querying latest records...")
    latest = storage.query_latest("coin-0", limit=5)
    print(f"   Found {len(latest)} records for coin-0")
    if latest:
        print(f"   Latest: {latest[0].timestamp} @ ${latest[0].price}")
    
    # Stats test
    print("\n3. Getting system statistics...")
    stats = storage.get_statistics()
    print(f"   Total records: {stats['hot_records']:,}")
    print(f"   Unique coins: {stats['unique_coins']}")
    print(f"   Top 100 records: {stats['top_100_records']:,}")
    print(f"   Storage: {stats['storage']['total_mb']:.2f} MB")
    
    # Archive test
    print("\n4. Testing archival (move 4-day+ old records to warm)...")
    archive_result = storage.archive_old_data(cutoff_days=4)
    print(f"   Archived: {archive_result['archived_records']:,} records")
    
    # Final stats
    print("\n5. Final statistics...")
    stats = storage.get_statistics()
    print(f"   Hot tier records: {stats['hot_records']:,}")
    print(f"   Hot tier size: {stats['storage']['hot_mb']:.2f} MB")
    print(f"   Warm tier size: {stats['storage']['warm_mb']:.2f} MB")
    print(f"   Date range: {stats['date_range']['latest']} to {stats['date_range']['earliest']}")


if __name__ == "__main__":
    test_production_system()
