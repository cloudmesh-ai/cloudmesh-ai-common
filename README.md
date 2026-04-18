# Cloudmesh AI Common

`cloudmesh-ai-common` provides a set of shared utilities for the Cloudmesh AI ecosystem, focusing on system introspection, structured telemetry, and standardized logging.

## Features

### 1. Enhanced System Introspection (`cloudmesh.ai.common.sys`)
The system utility provides deep insights into the host hardware and environment.

- **Hardware Detection**: 
    - **GPU**: Automatic detection for NVIDIA, AMD, Apple Silicon, and Intel GPUs.
    - **Topology**: Detection of NUMA nodes and high-speed network interfaces (InfiniBand/RoCE).
    - **CPU**: Detailed processor descriptions across macOS, Windows, and Linux.
- **Thermal Monitoring**: Standardized CPU temperature retrieval across Linux and macOS to detect thermal throttling.
- **Container Awareness**: Automatic detection of Docker and Kubernetes environments, including extraction of K8s namespace metadata.
- **Real-time Metrics**: 
    - Live CPU utilization (overall and per-core).
    - Detailed memory and swap usage.
    - Disk I/O statistics and usage.
- **System Info**: The `systeminfo()` function collects a comprehensive snapshot of the environment. Use `realtime=True` to include live performance metrics.

### 2. Advanced Telemetry System (`cloudmesh.ai.common.telemetry`)
A pluggable telemetry framework for emitting structured performance and status data from AI commands.

- **Pluggable Backends**:
    - `JSONFileBackend`: Emits records in JSONL format for easy ingestion by log aggregators.
    - `SQLiteBackend`: Stores telemetry in a structured SQLite database for complex querying.
    - `TextBackend`: Provides human-readable summaries for developers and operators.
- **Automatic Tracking**: The `track()` context manager automatically handles start/complete/fail events and calculates task duration.
- **Async Support**: The `AsyncTelemetry` class allows non-blocking telemetry emission using `asyncio`, ensuring that I/O operations do not interfere with compute-intensive AI tasks.
- **Standardized Events**: Built-in helpers for `start()`, `complete()`, and `fail()` events.

### 3. Telemetry Aggregation (`cloudmesh.ai.common.aggregation`)
The `TelemetryAggregator` utility allows for the analysis of emitted telemetry data.

- **Multi-source Loading**: Load data from either JSONL files or SQLite databases.
- **Statistical Summaries**: Calculate success rates, status distributions, and command frequency.
- **Metric Analysis**: Aggregate specific KPIs to find average, minimum, and maximum values across multiple runs.

### 4. Standardized Logging (`cloudmesh.ai.common.logging`)
Provides a consistent logging interface across all AI components to ensure uniform log formatting and traceability.

## Usage Examples

### System Info
```python
from cloudmesh.ai.common import sys as ai_sys

# Get static and real-time system info
info = ai_sys.systeminfo(realtime=True)
print(f"CPU: {info['cpu']}")
print(f"GPU Present: {info['gpu.present']}")
print(f"CPU Temp: {info.get('cpu.temp')}")
print(f"Container: {info.get('container.type', 'none')}")
```

### Synchronous Telemetry with Context Manager
```python
from cloudmesh.ai.common.telemetry import Telemetry, SQLiteBackend, TextBackend

telemetry = Telemetry(
    "my-ai-command", 
    backends=[SQLiteBackend("metrics.db"), TextBackend()]
)

# Use the track context manager for automatic timing and error handling
with telemetry.track(message="Running inference", metrics={"model": "llama-3"}):
    # ... perform work ...
    # If an exception occurs here, it is automatically logged as a 'failed' event
    pass
```

### Asynchronous Telemetry
```python
import asyncio
from cloudmesh.ai.common.telemetry import AsyncTelemetry, JSONFileBackend

async def run_command():
    telemetry = AsyncTelemetry(
        "async-ai-task", 
        backends=[JSONFileBackend("async_metrics.jsonl")]
    )

    async with telemetry.track(message="Processing async request"):
        # ... perform async work ...
        await asyncio.sleep(0.1)

asyncio.run(run_command())
```

### Telemetry Aggregation
```python
from cloudmesh.ai.common.aggregation import TelemetryAggregator

# Analyze data from a SQLite database
agg = TelemetryAggregator("metrics.db")

# Get high-level summary
summary = agg.get_summary()
print(f"Success Rate: {summary['success_rate']}")

# Aggregate a specific metric across all runs
latency_stats = agg.aggregate_metric("duration_sec")
print(f"Average Duration: {latency_stats['avg']}s")