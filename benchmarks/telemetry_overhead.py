import time
import asyncio
import json
from pathlib import Path
from cloudmesh.ai.common import sys as ai_sys
from cloudmesh.ai.common.telemetry import Telemetry, AsyncTelemetry, SQLiteBackend, JSONFileBackend

def benchmark_systeminfo():
    print("--- Benchmarking systeminfo() ---")
    
    # Static info
    start = time.perf_counter()
    ai_sys.systeminfo(realtime=False)
    end = time.perf_counter()
    print(f"Static systeminfo(): {(end - start) * 1000:.2f} ms")
    
    # Real-time info
    start = time.perf_counter()
    ai_sys.systeminfo(realtime=True)
    end = time.perf_counter()
    print(f"Real-time systeminfo(): {(end - start) * 1000:.2f} ms")
    print()

def benchmark_sync_emit():
    print("--- Benchmarking Sync Telemetry Emit ---")
    # Use a temporary file for benchmarking
    json_path = "bench_telemetry.jsonl"
    db_path = "bench_telemetry.db"
    
    telemetry = Telemetry(
        "bench-sync", 
        backends=[JSONFileBackend(json_path), SQLiteBackend(db_path)]
    )
    
    iterations = 100
    start = time.perf_counter()
    for i in range(iterations):
        telemetry.emit("completed", metrics={"iter": i, "val": 0.123})
    end = time.perf_counter()
    
    avg_ms = ((end - start) / iterations) * 1000
    print(f"Average sync emit (JSONL + SQLite): {avg_ms:.2f} ms")
    
    # Cleanup
    Path(json_path).unlink(missing_ok=True)
    Path(db_path).unlink(missing_ok=True)
    print()

async def benchmark_async_emit():
    print("--- Benchmarking Async Telemetry Emit ---")
    json_path = "bench_async.jsonl"
    db_path = "bench_async.db"
    
    telemetry = AsyncTelemetry(
        "bench-async", 
        backends=[JSONFileBackend(json_path), SQLiteBackend(db_path)]
    )
    
    iterations = 100
    start = time.perf_counter()
    for i in range(iterations):
        await telemetry.emit("completed", metrics={"iter": i, "val": 0.123})
    end = time.perf_counter()
    
    avg_ms = ((end - start) / iterations) * 1000
    print(f"Average async emit (JSONL + SQLite): {avg_ms:.2f} ms")
    
    # Cleanup
    Path(json_path).unlink(missing_ok=True)
    Path(db_path).unlink(missing_ok=True)
    print()

if __name__ == "__main__":
    benchmark_systeminfo()
    benchmark_sync_emit()
    asyncio.run(benchmark_async_emit())