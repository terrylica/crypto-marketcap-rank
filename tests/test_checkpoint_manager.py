#!/usr/bin/env python3
"""Unit tests for CheckpointManager."""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.checkpoint_manager import Checkpoint, CheckpointError, CheckpointManager


def test_checkpoint_save_restore():
    """Test checkpoint save and restore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(checkpoint_dir=tmpdir)

        # Create checkpoint
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
        assert filepath.exists()

        # Restore
        restored = manager.restore("2025-11-21")
        assert restored is not None
        assert restored.date == "2025-11-21"
        assert restored.last_page == 50
        assert restored.total_coins_collected == 12500


def test_checkpoint_nonexistent():
    """Test restoring nonexistent checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(checkpoint_dir=tmpdir)

        # Try to restore nonexistent checkpoint
        restored = manager.restore("2025-01-01")
        assert restored is None


def test_checkpoint_delete():
    """Test checkpoint deletion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(checkpoint_dir=tmpdir)

        # Create and save checkpoint
        checkpoint = Checkpoint(
            date="2025-11-21",
            last_page=10,
            total_coins_collected=2500,
            checkpoint_time=datetime.now().isoformat(),
            api_calls_used=10,
            metadata={}
        )
        manager.save(checkpoint)

        # Delete
        deleted = manager.delete("2025-11-21")
        assert deleted is True

        # Try to restore after deletion
        restored = manager.restore("2025-11-21")
        assert restored is None

        # Try to delete again
        deleted = manager.delete("2025-11-21")
        assert deleted is False


def test_checkpoint_list():
    """Test listing checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(checkpoint_dir=tmpdir)

        # Create multiple checkpoints
        dates = ["2025-11-20", "2025-11-21", "2025-11-22"]
        for date in dates:
            checkpoint = Checkpoint(
                date=date,
                last_page=1,
                total_coins_collected=250,
                checkpoint_time=datetime.now().isoformat(),
                api_calls_used=1,
                metadata={}
            )
            manager.save(checkpoint)

        # List checkpoints
        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 3
        assert checkpoints == sorted(dates)


def test_checkpoint_validation():
    """Test checkpoint validation on restore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(checkpoint_dir=tmpdir)

        # Create checkpoint with invalid data
        checkpoint_file = Path(tmpdir) / "checkpoint_2025-11-21.json"
        checkpoint_file.write_text('{"date": "2025-11-21", "last_page": -1}')  # Invalid: missing fields

        # Should raise on restore
        with pytest.raises(CheckpointError, match="missing required fields"):
            manager.restore("2025-11-21")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
