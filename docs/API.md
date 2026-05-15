# cloudmesh-ai-common API Reference

This library provides core utilities for AI-related system monitoring, timing, and logging.

## 1. System Information (`cloudmesh.ai.common.sys`)

The `systeminfo` function collects comprehensive metadata about the host system.

::: cloudmesh.ai.common.sys

### Usage
```python
from cloudmesh.ai.common import sys as ai_sys

info = ai_sys.systeminfo()
print(f"CPU: {info['cpu']}")
print(f"GPU Present: {info['gpu.present']}")
if info['gpu.present']:
    print(f"GPU Vendor: {info['gpu.vendor']}")
    print(f"VRAM: {info['gpu.total_vram']}")
```

### Key Features
- **Multi-Vendor GPU Detection**: Supports NVIDIA, AMD, Apple Silicon, and Intel.
- **NUMA Detection**: Identifies NUMA nodes on Linux.
- **Network Detection**: Detects high-speed interconnects (InfiniBand/RoCE).

---

## 2. StopWatch (`cloudmesh.ai.common.stopwatch`)

`StopWatch` provides thread-safe timing utilities for benchmarking.

::: cloudmesh.ai.common.stopwatch

### Usage: Basic Timing
```python
from cloudmesh.ai.common.stopwatch import StopWatch

StopWatch.start("my_timer")
# ... perform operation ...
StopWatch.stop("my_timer")

elapsed = StopWatch.get("my_timer")
print(f"Elapsed time: {elapsed:.4f}s")
```

### Usage: Context Manager (Recommended)
The `timer` context manager ensures the timer stops even if an exception occurs.
```python
from cloudmesh.ai.common.stopwatch import StopWatch

with StopWatch.timer("process_data"):
    # ... perform operation ...
    pass

print(f"Process took: {StopWatch.get('process_data'):.4f}s")
```

---

## 3. Logging (`cloudmesh.ai.common.logging`)

A centralized logging utility supporting JSON format, rotation, and request tracing.

::: cloudmesh.ai.common.logging

### Basic Usage
```python
from cloudmesh.ai.common import logging as ai_log

logger = ai_log.get_logger("my_script")
logger.info("This is an info message")
logger.error("This is an error message")
```

### Request Tracing
Use `set_context_id` to track requests across different log entries in the same thread.
```python
from cloudmesh.ai.common import logging as ai_log

ai_log.set_context_id("req-12345")
logger = ai_log.get_logger("api_handler")
logger.info("Processing request") # Log will contain [req-12345]
```

### Configuration-Driven Logging
You can load a JSON config file to override default log directories and levels.
```python
from cloudmesh.ai.common import logging as ai_log

ai_log.load_logging_config("logging_config.json")
logger = ai_log.get_logger("my_script")
```
**Example `logging_config.json`**:
```json
{
  "log_dir": "/var/log/cloudmesh/ai",
  "level": "DEBUG",
  "json_format": true,
  "max_bytes": 20971520,
  "backup_count": 10
}
```

---

## 4. Time & Telemetry (`cloudmesh.ai.common.time`, `cloudmesh.ai.common.telemetry`)

::: cloudmesh.ai.common.time
::: cloudmesh.ai.common.telemetry

---

## 5. IO & Aggregation (`cloudmesh.ai.common.io`, `cloudmesh.ai.common.aggregation`)

::: cloudmesh.ai.common.io
::: cloudmesh.ai.common.aggregation