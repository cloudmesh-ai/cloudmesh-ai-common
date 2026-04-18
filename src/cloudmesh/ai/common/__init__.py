"""Common utilities for cloudmesh-ai components.

This package provides shared functionality for logging, telemetry, system 
information gathering, and other common helper utilities used across 
the cloudmesh-ai ecosystem.
"""

from .logging import (
    set_context_id,
    get_context_id,
    ContextFilter,
    JsonFormatter,
    load_logging_config,
    get_log_dir,
    ensure_log_dir,
    get_log_file_path,
    get_logger,
    progress,
)
from .aggregation import TelemetryAggregator
from .telemetry import (
    TelemetryBackend,
    JSONFileBackend,
    SQLiteBackend,
    TextBackend,
    Telemetry,
    AsyncTelemetry,
)
from .sys import (
    os_is_windows,
    os_is_mac,
    os_is_linux,
    os_is_pi,
    has_window_manager,
    sys_user,
    get_platform,
    get_cpu_description,
    get_gpu_info,
    get_thermal_info,
    get_numa_info,
    get_container_info,
    get_network_info,
    get_disk_read_speed,
    get_cpu_metrics,
    get_memory_metrics,
    get_disk_metrics,
    systeminfo,
)