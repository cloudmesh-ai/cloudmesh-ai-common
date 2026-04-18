"""
Telemetry utility for cloudmesh-ai components.
Provides a standardized way to emit structured performance and status data.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from cloudmesh.ai.common import sys as ai_sys
from cloudmesh.ai.common import logging as ai_log

class Telemetry:
    """
    Handles structured telemetry emission for AI commands.
    Telemetry is emitted as JSON to allow easy ingestion by monitoring dashboards.
    """

    def __init__(self, command_name: str, telemetry_file: Optional[Union[str, Path]] = None):
        self.command_name = command_name
        self.telemetry_file = Path(telemetry_file).expanduser() if telemetry_file else None
        self.logger = ai_log.get_logger(f"{command_name}.telemetry")

    def _get_system_context(self) -> Dict[str, Any]:
        """Gathers basic system context to accompany telemetry metrics."""
        info = ai_sys.systeminfo()
        return {
            "cpu": info.get("cpu"),
            "gpu_present": info.get("gpu.present"),
            "gpu_model": info.get("gpu.model"),
            "memory_total": info.get("memory.total"),
        }

    def emit(
        self, 
        status: str, 
        metrics: Optional[Dict[str, Any]] = None, 
        message: Optional[str] = None,
        stdout: bool = False
    ):
        """
        Emits a structured telemetry record.
        
        Args:
            status: The current status of the command (e.g., 'started', 'completed', 'failed').
            metrics: A dictionary of KPIs and measurements.
            message: An optional human-readable message.
            stdout: If True, prints the JSON record to stdout.
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "command": self.command_name,
            "status": status,
            "metrics": metrics or {},
            "system": self._get_system_context(),
        }
        if message:
            record["message"] = message

        json_record = json.dumps(record)

        # 1. Log via the standard logging system
        self.logger.info(f"TELEMETRY: {json_record}")

        # 2. Write to dedicated telemetry file if configured
        if self.telemetry_file:
            try:
                with open(self.telemetry_file, "a") as f:
                    f.write(json_record + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write telemetry to {self.telemetry_file}: {e}")

        # 3. Optional stdout for direct ingestion/piping
        if stdout:
            print(json_record, file=sys.stdout)

    def start(self, message: Optional[str] = None, **kwargs):
        """Helper to emit a 'started' status."""
        self.emit("started", message=message, **kwargs)

    def complete(self, metrics: Optional[Dict[str, Any]] = None, message: Optional[str] = "Command completed successfully", **kwargs):
        """Helper to emit a 'completed' status with final metrics."""
        self.emit("completed", metrics=metrics, message=message, **kwargs)

    def fail(self, error: str, metrics: Optional[Dict[str, Any]] = None, **kwargs):
        """Helper to emit a 'failed' status."""
        self.emit("failed", metrics=metrics, message=error, **kwargs)
