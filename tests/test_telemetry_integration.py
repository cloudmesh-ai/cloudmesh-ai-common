import asyncio
import os
import pytest
from pathlib import Path
from cloudmesh.ai.common.telemetry import Telemetry, AsyncTelemetry, SQLiteBackend, TextBackend, JSONFileBackend
from cloudmesh.ai.common.aggregation import TelemetryAggregator

DB_PATH = "test_telemetry.db"
JSONL_PATH = "test_telemetry.jsonl"
TEXT_PATH = "test_telemetry.txt"

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test files before and after tests."""
    for f in [DB_PATH, JSONL_PATH, TEXT_PATH]:
        if os.path.exists(f):
            os.remove(f)
    yield
    for f in [DB_PATH, JSONL_PATH, TEXT_PATH]:
        if os.path.exists(f):
            os.remove(f)

def test_sync_telemetry_integration():
    """Test the full pipeline: Telemetry -> SQLite/Text -> Aggregator."""
    # 1. Setup Telemetry with multiple backends
    telemetry = Telemetry(
        "integration-test-sync",
        backends=[
            SQLiteBackend(DB_PATH),
            TextBackend(TEXT_PATH),
            JSONFileBackend(JSONL_PATH)
        ]
    )

    # 2. Use the context manager to track a task
    with telemetry.track(message="Testing sync integration", metrics={"batch_size": 32}):
        # Simulate work
        import time
        time.sleep(0.1)
    
    # 3. Verify files were created
    assert Path(DB_PATH).exists()
    assert Path(TEXT_PATH).exists()
    assert Path(JSONL_PATH).exists()

    # 4. Use Aggregator to verify data
    agg = TelemetryAggregator(DB_PATH)
    summary = agg.get_summary()
    
    assert summary["total_records"] >= 2  # started and completed
    assert "integration-test-sync" in summary["command_distribution"]
    
    # Verify metric aggregation
    duration_stats = agg.aggregate_metric("duration_sec")
    assert duration_stats["avg"] >= 0.1

@pytest.mark.asyncio
async def test_async_telemetry_integration():
    """Test the async pipeline: AsyncTelemetry -> SQLite -> Aggregator."""
    telemetry = AsyncTelemetry(
        "integration-test-async",
        backends=[SQLiteBackend(DB_PATH)]
    )

    async with telemetry.track(message="Testing async integration", metrics={"gpu_id": 0}):
        await asyncio.sleep(0.1)

    # Verify via Aggregator
    agg = TelemetryAggregator(DB_PATH)
    summary = agg.get_summary()
    
    assert summary["total_records"] >= 2
    assert "integration-test-async" in summary["command_distribution"]
    
    duration_stats = agg.aggregate_metric("duration_sec")
    assert duration_stats["avg"] >= 0.1

def test_telemetry_failure_tracking():
    """Verify that the context manager captures exceptions as failures."""
    telemetry = Telemetry("failure-test", backends=[SQLiteBackend(DB_PATH)])

    with pytest.raises(ValueError, match="Intentional failure"):
        with telemetry.track(message="Testing failure"):
            raise ValueError("Intentional failure")

    agg = TelemetryAggregator(DB_PATH)
    summary = agg.get_summary()
    
    # Should have 'started' and 'failed'
    assert summary["status_distribution"].get("failed", 0) == 1