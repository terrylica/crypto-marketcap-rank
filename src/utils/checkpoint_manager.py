#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Checkpoint Manager for Collection Resume

Enables checkpoint-based resume for long-running collection jobs.
Integrates with GitHub Actions cache for persistence across workflow runs.

Adheres to SLO:
- Availability: Restore from last successful checkpoint on failure
- Correctness: Atomic checkpoint writes, validate on restore
- Observability: Log checkpoint save/restore operations
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Checkpoint:
    """Collection checkpoint state."""
    date: str
    last_page: int
    total_coins_collected: int
    checkpoint_time: str
    api_calls_used: int
    metadata: Dict[str, Any]


class CheckpointError(Exception):
    """Raised when checkpoint operations fail."""
    pass


class CheckpointManager:
    """
    Production checkpoint manager for collection resume.

    Features:
    - Atomic checkpoint writes (tmp + rename)
    - JSON serialization for GitHub Actions cache
    - Validation on restore (schema + data integrity)
    - Raise on corruption (no silent failures)

    GitHub Actions Integration:
        - Save checkpoint to data/.checkpoints/
        - Cache this directory using actions/cache
        - Restore on workflow restart

    Usage:
        manager = CheckpointManager()

        # Save checkpoint
        checkpoint = Checkpoint(
            date="2025-11-21",
            last_page=50,
            total_coins_collected=12500,
            checkpoint_time=datetime.now().isoformat(),
            api_calls_used=50,
            metadata={"status": "in_progress"}
        )
        manager.save(checkpoint)

        # Restore checkpoint
        restored = manager.restore(date="2025-11-21")
        if restored:
            print(f"Resuming from page {restored.last_page}")
    """

    def __init__(self, checkpoint_dir: str = "data/.checkpoints"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: Checkpoint) -> Path:
        """
        Save checkpoint atomically.

        Args:
            checkpoint: Checkpoint state to save

        Returns:
            Path to saved checkpoint file

        Raises:
            CheckpointError: If save fails
        """
        try:
            filename = f"checkpoint_{checkpoint.date}.json"
            filepath = self.checkpoint_dir / filename
            tmp_filepath = self.checkpoint_dir / f"{filename}.tmp"

            # Write to temp file first
            with open(tmp_filepath, 'w') as f:
                json.dump(asdict(checkpoint), f, indent=2)

            # Atomic rename
            tmp_filepath.replace(filepath)

            print(f"✓ Checkpoint saved: {filepath}")
            print(f"  Page: {checkpoint.last_page}, Coins: {checkpoint.total_coins_collected}, "
                  f"API calls: {checkpoint.api_calls_used}")

            return filepath

        except Exception as e:
            raise CheckpointError(f"Failed to save checkpoint: {e}") from e

    def restore(self, date: str) -> Optional[Checkpoint]:
        """
        Restore checkpoint for given date.

        Args:
            date: Collection date (YYYY-MM-DD)

        Returns:
            Checkpoint if exists and valid, None otherwise

        Raises:
            CheckpointError: If checkpoint exists but is corrupted
        """
        filename = f"checkpoint_{date}.json"
        filepath = self.checkpoint_dir / filename

        if not filepath.exists():
            print(f"No checkpoint found for {date}")
            return None

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ["date", "last_page", "total_coins_collected",
                             "checkpoint_time", "api_calls_used"]
            missing = [f for f in required_fields if f not in data]
            if missing:
                raise CheckpointError(f"Checkpoint missing required fields: {missing}")

            # Validate data types
            if not isinstance(data["last_page"], int) or data["last_page"] < 1:
                raise CheckpointError(f"Invalid last_page: {data['last_page']}")

            if not isinstance(data["total_coins_collected"], int) or data["total_coins_collected"] < 0:
                raise CheckpointError(f"Invalid total_coins_collected: {data['total_coins_collected']}")

            # Create checkpoint object
            checkpoint = Checkpoint(
                date=data["date"],
                last_page=data["last_page"],
                total_coins_collected=data["total_coins_collected"],
                checkpoint_time=data["checkpoint_time"],
                api_calls_used=data["api_calls_used"],
                metadata=data.get("metadata", {})
            )

            print(f"✓ Checkpoint restored: {filepath}")
            print(f"  Page: {checkpoint.last_page}, Coins: {checkpoint.total_coins_collected}, "
                  f"API calls: {checkpoint.api_calls_used}")

            return checkpoint

        except json.JSONDecodeError as e:
            raise CheckpointError(f"Checkpoint file corrupted (invalid JSON): {e}") from e
        except Exception as e:
            raise CheckpointError(f"Failed to restore checkpoint: {e}") from e

    def delete(self, date: str) -> bool:
        """
        Delete checkpoint for given date.

        Args:
            date: Collection date (YYYY-MM-DD)

        Returns:
            True if deleted, False if didn't exist
        """
        filename = f"checkpoint_{date}.json"
        filepath = self.checkpoint_dir / filename

        if filepath.exists():
            filepath.unlink()
            print(f"✓ Checkpoint deleted: {filepath}")
            return True

        return False

    def list_checkpoints(self) -> list[str]:
        """
        List all available checkpoints.

        Returns:
            List of dates with checkpoints (YYYY-MM-DD)
        """
        checkpoints = []
        for filepath in self.checkpoint_dir.glob("checkpoint_*.json"):
            # Extract date from filename: checkpoint_YYYY-MM-DD.json
            date = filepath.stem.replace("checkpoint_", "")
            checkpoints.append(date)

        return sorted(checkpoints)


if __name__ == "__main__":
    # Simple test
    print("Testing checkpoint manager...")

    manager = CheckpointManager()

    # Create test checkpoint
    checkpoint = Checkpoint(
        date="2025-11-21",
        last_page=50,
        total_coins_collected=12500,
        checkpoint_time=datetime.now().isoformat(),
        api_calls_used=50,
        metadata={"status": "test"}
    )

    # Save
    filepath = manager.save(checkpoint)
    print(f"Saved to: {filepath}")

    # List
    checkpoints = manager.list_checkpoints()
    print(f"Available checkpoints: {checkpoints}")

    # Restore
    restored = manager.restore("2025-11-21")
    assert restored is not None
    assert restored.last_page == 50
    assert restored.total_coins_collected == 12500

    # Delete
    deleted = manager.delete("2025-11-21")
    assert deleted is True

    print("✅ Checkpoint manager test passed")
