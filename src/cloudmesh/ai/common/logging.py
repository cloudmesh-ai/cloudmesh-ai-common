"""
Logging utility for cloudmesh-ai components.
Provides centralized management of log directories, file naming, and logger configuration.
Includes support for JSON logging, log rotation, and request tracing.
"""

import logging
import logging.handlers
import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any, Union

# Thread-local storage for request tracing
_thread_local = threading.local()

def set_context_id(context_id: str):
    """Sets the context ID for the current thread to enable request tracing."""
    _thread_local.context_id = context_id

def get_context_id() -> Optional[str]:
    """Retrieves the context ID for the current thread."""
    return getattr(_thread_local, "context_id", None)

class ContextFilter(logging.Filter):
    """Filter that injects the current context_id into the log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.context_id = get_context_id() or "system"
        return True

class JsonFormatter(logging.Formatter):
    """Formatter that outputs log records in JSON format."""
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "context_id": getattr(record, "context_id", "system"),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Cache for loggers to prevent duplicate handlers
_loggers: Dict[str, logging.Logger] = {}

# Global logging configuration
_logging_config: Dict[str, Any] = {}

def load_logging_config(config_path: Union[str, Path]):
    """
    Loads logging configuration from a JSON file.
    Example config: {"log_dir": "/var/log/cloudmesh", "level": "DEBUG", "json_format": true}
    """
    global _logging_config
    try:
        path = Path(config_path)
        if path.exists():
            with open(path, "r") as f:
                _logging_config = json.load(f)
    except Exception as e:
        print(f"Failed to load logging config from {config_path}: {e}")

def get_log_dir() -> Path:
    """Returns the expanded path to the AI logs directory, using config if available."""
    log_dir = _logging_config.get("log_dir", "~/.config/cloudmesh/ai/logs")
    return Path(log_dir).expanduser()

def ensure_log_dir() -> Path:
    """Ensures the log directory exists and returns it."""
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def get_log_file_path(script_name: str) -> Path:
    """
    Generates a timestamped log file path for a given script.
    Example: ~/.config/cloudmesh/ai/logs/test_20260412_124500.log
    """
    log_dir = ensure_log_dir()
    
    # Use custom filename if provided in config, otherwise use script_name
    prefix = _logging_config.get("log_prefix", script_name)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return log_dir / f"{prefix}_{timestamp}.log"

def get_logger(
    script_name: str, 
    level: Optional[int] = None, 
    json_format: Optional[bool] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None
) -> logging.Logger:
    """
    Returns a configured logger instance for the given script.
    Configures both a rotating file handler and a stream handler.
    
    Args:
        script_name: Name of the logger/script.
        level: Logging level.
        json_format: If True, uses JSON formatting for logs.
        max_bytes: Max size of a log file before rotation.
        backup_count: Number of backup log files to keep.
    """
    if script_name in _loggers:
        return _loggers[script_name]

    # Resolve settings: Argument > Config File > Default
    final_level = level if level is not None else _logging_config.get("level", logging.INFO)
    if isinstance(final_level, str):
        final_level = getattr(logging, final_level.upper(), logging.INFO)

    final_json = json_format if json_format is not None else _logging_config.get("json_format", False)
    final_max_bytes = max_bytes if max_bytes is not None else _logging_config.get("max_bytes", 10 * 1024 * 1024)
    final_backup_count = backup_count if backup_count is not None else _logging_config.get("backup_count", 5)

    logger = logging.getLogger(script_name)
    logger.setLevel(final_level)

    # Prevent adding handlers if they already exist
    if not logger.handlers:
        # Add Context Filter for request tracing
        logger.addFilter(ContextFilter())

        if final_json:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - [%(context_id)s] - %(levelname)s - %(message)s')

        # 1. Rotating File Handler
        log_file = get_log_file_path(script_name)
        try:
            fh = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=final_max_bytes, backupCount=final_backup_count
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"Failed to initialize rotating file logger at {log_file}: {e}")

        # 2. Stream Handler (Console)
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    _loggers[script_name] = logger
    return logger

def progress(
    filename: Optional[str] = None,
    status: str = "ready",
    progress: Union[int, str, float] = 0,
    pid: Optional[Union[int, str]] = None,
    timestamp: bool = False,
    stdout: bool = True,
    stderr: bool = True,
    append: Optional[str] = None,
    **kwargs,
) -> str:
    """Creates a printed line of the form
    "# cloudmesh status=ready progress=0 pid=$$ time='2022-08-05 16:29:40.228901'"
    """
    if isinstance(progress, (int, float)):
        progress = str(progress)
    
    if pid is None:
        if "SLURM_JOB_ID" in os.environ:
            pid = os.environ["SLURM_JOB_ID"]
        elif "LSB_JOBID" in os.environ:
            pid = os.environ["LSB_JOBID"]
        else:
            pid = os.getpid()
            
    variables = ""
    msg = f"# cloudmesh status={status} progress={progress} pid={pid}"
    
    if timestamp:
        t = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        msg = msg + f" time='{t}'"
        
    if kwargs:
        for name, value in kwargs.items():
            variables = variables + f" {name}={value}"
        msg = msg + variables
        
    if append is not None:
        msg = msg + " " + append
        
    if stdout:
        print(msg, file=sys.stdout)
    if stderr:
        print(msg, file=sys.stderr)
    if filename is not None:
        with open(filename, "a") as f:
            f.write(msg + "\n")
            
    return msg
