#!/usr/bin/env python3
"""
Storage Engine Implementation
Multi-format storage with automatic optimization
"""
# /// script
# dependencies = [
#   "pyarrow==17.0.0",
# ]
# ///

import sqlite3
import json
import gzip
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time

class StorageEngine:
    """Multi-format storage with optimization strategies"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = None
        self.setup_database()
    
    def setup_database(self):
        """Initialize SQLite with optimal settings"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode = WAL")  # Write-ahead logging
        self.conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety/speed
        self.conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        self.conn.execute("PRAGMA page_size = 4096")
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Create market cap history table
        self.conn.execute("""
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
            UNIQUE(coin_id, timestamp)
        )
        """)
        
        # Create indexes for efficient querying
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_coin_time ON market_cap_history(coin_id, timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON market_cap_history(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_market_cap ON market_cap_history(market_cap)")
        
        # Create metadata table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS collection_metadata (
            metric_name TEXT PRIMARY KEY,
            value TEXT,
            last_updated DATETIME
        )
        """)
        
        self.conn.commit()
    
    def insert_record(self, record: Dict[str, Any]):
        """Insert a market cap record"""
        try:
            self.conn.execute("""
            INSERT INTO market_cap_history
            (coin_id, timestamp, price, market_cap, volume_24h, 
             market_cap_change_24h, percent_change_24h, percent_change_7d, 
             percent_change_30d, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get('id'),
                record.get('timestamp'),
                record.get('price'),
                record.get('market_cap'),
                record.get('volume_24h'),
                record.get('market_cap_change_24h'),
                record.get('percent_change_24h'),
                record.get('percent_change_7d'),
                record.get('percent_change_30d'),
                record.get('rank')
            ))
        except sqlite3.IntegrityError:
            pass  # Duplicate, skip
    
    def export_to_jsonl_gz(self, output_path: str, coin_ids: List[str] = None):
        """Export records to compressed JSONL"""
        query = "SELECT * FROM market_cap_history"
        params = []
        
        if coin_ids:
            placeholders = ','.join(['?' for _ in coin_ids])
            query += f" WHERE coin_id IN ({placeholders})"
            params = coin_ids
        
        query += " ORDER BY timestamp DESC"
        
        cursor = self.conn.execute(query, params)
        
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            for row in cursor:
                record = {
                    'coin_id': row[1],
                    'timestamp': row[2],
                    'price': row[3],
                    'market_cap': row[4],
                    'volume_24h': row[5],
                    'market_cap_change_24h': row[6],
                    'percent_change_24h': row[7],
                    'percent_change_7d': row[8],
                    'percent_change_30d': row[9],
                    'rank': row[10]
                }
                f.write(json.dumps(record) + '\n')
    
    def estimate_size(self) -> Dict[str, float]:
        """Estimate storage in different formats"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM market_cap_history")
        count = cursor.fetchone()[0]
        
        if count == 0:
            return {"records": 0, "sqlite_mb": 0, "jsonl_mb": 0, "jsonl_gz_mb": 0}
        
        # Get actual SQLite file size
        sqlite_size = Path(self.db_path).stat().st_size if self.db_path != ":memory:" else 0
        
        # Estimate JSONL size (avg ~350 bytes per record)
        jsonl_size = count * 350
        
        # Estimate gzip compression (75% reduction typical)
        jsonl_gz_size = jsonl_size * 0.25
        
        return {
            "records": count,
            "sqlite_mb": sqlite_size / (1024*1024),
            "jsonl_mb": jsonl_size / (1024*1024),
            "jsonl_gz_mb": jsonl_gz_size / (1024*1024),
            "compression_ratio": 1 - (jsonl_gz_size / jsonl_size) if jsonl_size > 0 else 0
        }
    
    def benchmark_write_performance(self, num_records: int = 10000):
        """Benchmark write performance"""
        print(f"\nBenchmarking {num_records:,} inserts...")
        
        # Create test data
        test_records = []
        for i in range(num_records):
            test_records.append({
                'id': f'coin-{i % 1000}',
                'timestamp': datetime.now().isoformat(),
                'price': 100.0 + i,
                'market_cap': 1000000000 + i,
                'volume_24h': 500000000.0,
                'market_cap_change_24h': -0.5,
                'percent_change_24h': -0.5,
                'percent_change_7d': -5.0,
                'percent_change_30d': -10.0,
                'rank': i % 100
            })
        
        # Benchmark individual inserts
        start = time.time()
        for record in test_records:
            self.insert_record(record)
        self.conn.commit()
        individual_time = time.time() - start
        
        # Clear and benchmark batch inserts
        self.conn.execute("DELETE FROM market_cap_history")
        self.conn.commit()
        
        start = time.time()
        self.conn.executemany("""
        INSERT INTO market_cap_history
        (coin_id, timestamp, price, market_cap, volume_24h,
         market_cap_change_24h, percent_change_24h, percent_change_7d,
         percent_change_30d, rank)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (r['id'], r['timestamp'], r['price'], r['market_cap'], 
             r['volume_24h'], r['market_cap_change_24h'], 
             r['percent_change_24h'], r['percent_change_7d'], 
             r['percent_change_30d'], r['rank'])
            for r in test_records
        ])
        self.conn.commit()
        batch_time = time.time() - start
        
        return {
            "individual_insert_time": individual_time,
            "individual_records_per_sec": num_records / individual_time,
            "batch_insert_time": batch_time,
            "batch_records_per_sec": num_records / batch_time,
            "speedup": individual_time / batch_time
        }
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_storage_engine():
    """Test storage engine functionality"""
    print("=" * 70)
    print("STORAGE ENGINE TESTING")
    print("=" * 70)
    
    # Test with in-memory database
    engine = StorageEngine(":memory:")
    
    # Insert sample data
    print("\nInserting 5,000 sample records...")
    for i in range(5000):
        coin_id = f"coin-{i % 500}"
        engine.insert_record({
            'id': coin_id,
            'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
            'price': 100.0 + i * 0.1,
            'market_cap': 1000000000 + i * 10000,
            'volume_24h': 500000000.0,
            'market_cap_change_24h': -0.5,
            'percent_change_24h': -0.5,
            'percent_change_7d': -5.0,
            'percent_change_30d': -10.0,
            'rank': (i % 100) + 1
        })
    engine.conn.commit()
    
    # Check size estimates
    sizes = engine.estimate_size()
    print(f"\nStorage estimates after 5,000 records:")
    print(f"  - SQLite DB: {sizes['sqlite_mb']:.2f} MB")
    print(f"  - JSONL (uncompressed): {sizes['jsonl_mb']:.2f} MB")
    print(f"  - JSONL + gzip: {sizes['jsonl_gz_mb']:.2f} MB")
    print(f"  - Compression ratio: {sizes['compression_ratio']:.1%}")
    
    # Benchmark performance
    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 70)
    perf = engine.benchmark_write_performance(10000)
    print(f"\nWrite Performance:")
    print(f"  Individual inserts: {perf['individual_records_per_sec']:.0f} records/sec")
    print(f"  Batch inserts: {perf['batch_records_per_sec']:.0f} records/sec")
    print(f"  Batch speedup: {perf['speedup']:.1f}x faster")
    
    # Query performance
    print(f"\nQuery Performance:")
    start = time.time()
    cursor = engine.conn.execute(
        "SELECT COUNT(*) FROM market_cap_history WHERE coin_id = ?", 
        ("coin-1",)
    )
    count = cursor.fetchone()[0]
    query_time = (time.time() - start) * 1000
    print(f"  Indexed query (1 coin, all timestamps): {query_time:.2f}ms ({count} records)")
    
    start = time.time()
    cursor = engine.conn.execute(
        "SELECT MAX(market_cap), MIN(market_cap) FROM market_cap_history"
    )
    result = cursor.fetchone()
    query_time = (time.time() - start) * 1000
    print(f"  Aggregate query (all coins): {query_time:.2f}ms")
    
    engine.close()


if __name__ == "__main__":
    test_storage_engine()
