"""
Telemetry utility for cloudmesh-ai components.
Provides a standardized way to emit structured performance and status data.
"""

import json
import sys
import os
import sqlite3
import asyncio
import time
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional, Union, List, Protocol
from pathlib import Path
from cloudmesh.ai.common import sys as ai_sys
from cloudmesh.ai.common import logging as ai_log

class TelemetryBackend(Protocol):
    """
    Interface for telemetry export backends.
    Any class implementing this protocol can be used as a telemetry sink.
    """
    def emit(self, record: Dict[str, Any]) -> None:
        """Emit a single telemetry record.

        Args:
            record: The telemetry data dictionary to export.

        """
        ...

class JSONFileBackend:
    """
    Writes telemetry records to a JSON Lines (JSONL) file.
    Each record is stored as a single JSON object per line.
    """
    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize the JSONL backend.

        Args:
            path: Path to the output file.

        """
        self.path = Path(path).expanduser()

    def emit(self, record: Dict[str, Any]) -> None:
        """Append a telemetry record to the JSONL file.

        Args:
            record: The telemetry data dictionary to export.

        """
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"JSONFileBackend error: {e}")

class SQLiteBackend:
    """
    Writes telemetry records to a SQLite database.
    Provides structured storage for easier querying and analysis.
    """
    def __init__(self, db_path: Union[str, Path] = "telemetry.db") -> None:
        """Initialize the SQLite backend.

        Args:
            db_path: Path to the SQLite database file.

        """
        self.db_path = Path(db_path).expanduser()
        self._init_db()

    def _init_db(self) -> None:
        """Creates the telemetry table if it does not exist.

        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    command TEXT,
                    status TEXT,
                    metrics TEXT,
                    system TEXT,
                    message TEXT
                )
            """)

    def emit(self, record: Dict[str, Any]) -> None:
        """Insert a telemetry record into the database.

        Args:
            record: The telemetry data dictionary to export.

        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO telemetry (timestamp, command, status, metrics, system, message) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        record.get("timestamp"),
                        record.get("command"),
                        record.get("status"),
                        json.dumps(record.get("metrics")),
                        json.dumps(record.get("system")),
                        record.get("message"),
                    )
                )
        except Exception as e:
            print(f"SQLiteBackend error: {e}")

class TextBackend:
    """
    Presents telemetry records in a human-readable text format.
    Can output to a file or directly to the console.
    """
    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        """Initialize the Text backend.

        Args:
            path: Optional path to a text file. If None, outputs to stdout.

        """
        self.path = Path(path).expanduser() if path else None

    def emit(self, record: Dict[str, Any]) -> None:
        """Format and emit a telemetry record as a human-readable string.

        Args:
            record: The telemetry data dictionary to export.

        """
        try:
            timestamp = record.get("timestamp", "N/A")
            command = record.get("command", "unknown")
            status = record.get("status", "unknown").upper()
            message = record.get("message", "")
            metrics = record.get("metrics", {})
            
            metrics_str = ", ".join([f"{k}={v}" for k, v in metrics.items()]) if metrics else "None"
            
            output = (
                f"[{timestamp}] {command} | STATUS: {status} | Metrics: {metrics_str}\n"
                f"Message: {message}\n"
                + "-" * 40 + "\n"
            )
            
            if self.path:
                with open(self.path, "a") as f:
                    f.write(output)
            else:
                print(output)
        except Exception as e:
            print(f"TextBackend error: {e}")

class Telemetry:
    """
    Handles structured telemetry emission for AI commands.
    Supports multiple backends for flexible data export.
    """

    def __init__(
        self, 
        command_name: str, 
        telemetry_file: Optional[Union[str, Path]] = None,
        backends: Optional[List[TelemetryBackend]] = None
    ) -> None:
        """Initialize the Telemetry collector.

        Args:
            command_name: Name of the command emitting telemetry.
            telemetry_file: Backward compatibility: path to a JSONL file.
            backends: List of TelemetryBackend implementations to use.

        """
        self.command_name = command_name
        self.logger = ai_log.get_logger(f"{command_name}.telemetry")
        self.backends: List[TelemetryBackend] = backends or []

        # Maintain backward compatibility with telemetry_file
        if telemetry_file:
            self.backends.append(JSONFileBackend(telemetry_file))

    def _get_system_context(self) -> Dict[str, Any]:
        """Gathers basic system context to accompany telemetry metrics.

        Returns:
            A dictionary containing basic system information.
        """
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
        stdout: bool = False,
        **kwargs: Any
    ) -> None:
        """Emits a structured telemetry record to all configured backends.

        Args:
            status: The current status of the command (e.g., 'started', 'completed', 'failed').
            metrics: A dictionary of KPIs and measurements.
            message: An optional human-readable message.
            stdout: If True, prints the JSON record to stdout.
        """
        if os.environ.get("CLOUDMESH_AI_TELEMETRY_DISABLED", "").lower() in ("1", "true", "yes"):
            return
        all_metrics = (metrics or {}).copy()
        all_metrics.update(kwargs)
        record = {
            "timestamp": datetime.now().isoformat(),
            "command": self.command_name,
            "status": status,
            "metrics": all_metrics,
            "system": self._get_system_context(),
        }
        if message:
            record["message"] = message

        json_record = json.dumps(record)

        # 1. Log via the standard logging system
        self.logger.info(f"TELEMETRY: {json_record}")

        # 2. Emit to all configured backends
        for backend in self.backends:
            backend.emit(record)

        # 3. Optional stdout for direct ingestion/piping
        if stdout:
            print(json_record, file=sys.stdout)

    def start(self, message: Optional[str] = None, **kwargs: Any) -> None:
        """Helper to emit a 'started' status.

        Args:
            message: Optional message for the start event.
            **kwargs: Additional metrics to include in the record.

        """
        self.emit("started", message=message, **kwargs)

    def complete(self, metrics: Optional[Dict[str, Any]] = None, message: Optional[str] = "Command completed successfully", **kwargs: Any) -> None:
        """Helper to emit a 'completed' status with final metrics.

        Args:
            metrics: A dictionary of final KPIs and measurements.
            message: An optional human-readable message.
            **kwargs: Additional metrics to include in the record.

        """
        self.emit("completed", metrics=metrics, message=message, **kwargs)

    def fail(self, error: str, metrics: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Helper to emit a 'failed' status.

        Args:
            error: The error message to record.
            metrics: A dictionary of KPIs at the time of failure.
            **kwargs: Additional metrics to include in the record.

        """
        self.emit("failed", metrics=metrics, message=error, **kwargs)

    @contextmanager
    def track(self, message: Optional[str] = None, metrics: Optional[Dict[str, Any]] = None):
        """
        Context manager to automatically track the start and completion of a task.

        Args:
            message: Optional message for the start event.
            metrics: Initial metrics to include.
        """
        self.start(message=message, **(metrics or {}))
        start_time = time.perf_counter()
        try:
            yield
            duration = time.perf_counter() - start_time
            final_metrics = (metrics or {}).copy()
            final_metrics["duration_sec"] = duration
            self.complete(metrics=final_metrics)
        except Exception as e:
            duration = time.perf_counter() - start_time
            final_metrics = (metrics or {}).copy()
            final_metrics["duration_sec"] = duration
            self.fail(error=str(e), metrics=final_metrics)
            raise

class AsyncTelemetry(Telemetry):
    """
    Asynchronous version of Telemetry.
    Prevents telemetry I/O from blocking the main execution thread by 
    offloading backend emission to a thread pool.
    """

    async def emit(
        self, 
        status: str, 
        metrics: Optional[Dict[str, Any]] = None, 
        message: Optional[str] = None,
        stdout: bool = False,
        **kwargs: Any
    ) -> None:
        """Asynchronously emits a structured telemetry record.

        Args:
            status: The current status of the command.
            metrics: A dictionary of KPIs.
            message: An optional human-readable message.
            stdout: If True, prints the JSON record to stdout.
        """
        if os.environ.get("CLOUDMESH_AI_TELEMETRY_DISABLED", "").lower() in ("1", "true", "yes"):
            return
        # We reuse the record creation logic from the base class
        # but we wrap the blocking I/O calls in asyncio.to_thread
        
        all_metrics = (metrics or {}).copy()
        all_metrics.update(kwargs)
        record = {
            "timestamp": datetime.now().isoformat(),
            "command": self.command_name,
            "status": status,
            "metrics": all_metrics,
            "system": self._get_system_context(),
        }
        if message:
            record["message"] = message

        json_record = json.dumps(record)

        # 1. Log (usually non-blocking enough, but we can wrap it)
        self.logger.info(f"TELEMETRY: {json_record}")

        # 2. Emit to backends asynchronously
        tasks = [asyncio.to_thread(backend.emit, record) for backend in self.backends]
        if tasks:
            await asyncio.gather(*tasks)

        # 3. Optional stdout
        if stdout:
            print(json_record, file=sys.stdout)

    async def start(self, message: Optional[str] = None, **kwargs: Any) -> None:
        """Async helper to emit a 'started' status.

        Args:
            message: Optional message for the start event.
            **kwargs: Additional metrics to include in the record.

        """
        await self.emit("started", message=message, **kwargs)

    async def complete(self, metrics: Optional[Dict[str, Any]] = None, message: Optional[str] = "Command completed successfully", **kwargs: Any) -> None:
        """Async helper to emit a 'completed' status.

        Args:
            metrics: A dictionary of final KPIs and measurements.
            message: An optional human-readable message.
            **kwargs: Additional metrics to include in the record.

        """
        await self.emit("completed", metrics=metrics, message=message, **kwargs)

    async def fail(self, error: str, metrics: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Async helper to emit a 'failed' status.

        Args:
            error: The error message to record.
            metrics: A dictionary of KPIs at the time of failure.
            **kwargs: Additional metrics to include in the record.

        """
        await self.emit("failed", metrics=metrics, message=error, **kwargs)

    @asynccontextmanager
    async def track(self, message: Optional[str] = None, metrics: Optional[Dict[str, Any]] = None):
        """
        Async context manager to automatically track the start and completion of a task.

        Args:
            message: Optional message for the start event.
            metrics: Initial metrics to include.
        """
        await self.start(message=message, **(metrics or {}))
        start_time = time.perf_counter()
        try:
            yield
            duration = time.perf_counter() - start_time
            final_metrics = (metrics or {}).copy()
            final_metrics["duration_sec"] = duration
            await self.complete(metrics=final_metrics)
        except Exception as e:
            duration = time.perf_counter() - start_time
            final_metrics = (metrics or {}).copy()
            final_metrics["duration_sec"] = duration
            await self.fail(error=str(e), metrics=final_metrics)
            raise
