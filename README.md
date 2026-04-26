# Cloudmesh AI Common

`cloudmesh-ai-common` provides a set of shared utilities for the Cloudmesh AI ecosystem, focusing on system introspection, structured telemetry, standardized logging, and unified remote execution.

## Installation

### Using pip
```bash
pip install cloudmesh-ai-common
```

### Using pipx (for isolated environment)
```bash
pipx install cloudmesh-ai-common
```

## Features

### 1. Unified Remote Execution (`cloudmesh.ai.common.remote`)
A robust wrapper around `paramiko` for standardized SSH and SFTP operations across different host environments.

- **Command Execution**: Execute shell commands with timeout support and capture exit status, stdout, and stderr.
- **File Transfers**: Simplified `upload` and `download` methods using SFTP.
- **Direct Remote Writing**: `write_remote_file` allows writing strings directly to remote paths, ideal for deploying scripts or configuration files without local temporary files.
- **Session Management**: Implemented as a context manager to ensure connections are always closed properly.

### 2. Enhanced Console & I/O (`cloudmesh.ai.common.io`)
A set of utilities to standardize user interaction and file handling.

- **Rich Console**: A custom `Console` class extending `rich.console.Console` with semantic helpers:
    - `ok()`: Success messages in green.
    - `error()`: Error messages in red.
    - `warning()`: Warning messages in yellow.
    - `msg()`: General messages in blue.
    - `note()`: Informational notes in cyan.
    - `ynchoice()`: Standardized yes/no interactive prompts.
- **Path Expansion**: `path_expand()` resolves `~`, environment variables, and relative paths into absolute POSIX paths.
- **YAML Helpers**: Safe `load_yaml` and `dump_yaml` utilities that handle directory creation automatically.
- **Visual Banners**: `banner()` utility to create structured, styled panels for high-level information.

### 3. Enhanced System Introspection (`cloudmesh.ai.common.sys`)
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

### 4. Advanced Telemetry System (`cloudmesh.ai.common.telemetry`)
A pluggable telemetry framework for emitting structured performance and status data from AI commands.

- **Pluggable Backends**:
    - `JSONFileBackend`: Emits records in JSONL format for easy ingestion by log aggregators.
    - `SQLiteBackend`: Stores telemetry in a structured SQLite database for complex querying.
    - `TextBackend`: Provides human-readable summaries for developers and operators.
- **Automatic Tracking**: The `track()` context manager automatically handles start/complete/fail events and calculates task duration.
- **Async Support**: The `AsyncTelemetry` class allows non-blocking telemetry emission using `asyncio`, ensuring that I/O operations do not interfere with compute-intensive AI tasks.
- **Standardized Events**: Built-in helpers for `start()`, `complete()`, and `fail()` events.

### 5. Telemetry Aggregation (`cloudmesh.ai.common.aggregation`)
The `TelemetryAggregator` utility allows for the analysis of emitted telemetry data.

- **Multi-source Loading**: Load data from either JSONL files or SQLite databases.
- **Statistical Summaries**: Calculate success rates, status distributions, and command frequency.
- **Metric Analysis**: Aggregate specific KPIs to find average, minimum, and maximum values across multiple runs.

### 6. Standardized Logging (`cloudmesh.ai.common.logging`)
Provides a consistent logging interface across all AI components to ensure uniform log formatting and traceability.

## Usage Examples

### Remote Execution
```python
from cloudmesh.ai.common.remote import RemoteExecutor

host = "dgx-node-1"
with RemoteExecutor(host) as executor:
    # Execute a command
    status, stdout, stderr = executor.execute("nvidia-smi")
    if status == 0:
        print(f"GPU Status: {stdout}")
    
    # Write a script directly to the remote host
    script_content = "#!/bin/bash\necho 'Hello from remote'"
    executor.write_remote_file(script_content, "/tmp/hello.sh")
    executor.execute("chmod +x /tmp/hello.sh")
    executor.execute("/tmp/hello.sh")
```

### Enhanced Console & I/O
```python
from cloudmesh.ai.common.io import console, banner, path_expand

# Use semantic console methods
console.ok("Operation completed successfully!")
console.error("Failed to connect to server")

# Interactive yes/no choice
if console.ynchoice("Do you want to proceed?", default=True):
    console.msg("Proceeding...")

# Path expansion
abs_path = path_expand("~/$PROJECT/data.csv")
print(f"Absolute path: {abs_path}")

# Visual banners
console.print(banner("System Status", "All systems operational\nLatency: 12ms"))
```

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