"""Class for starting and stopping named timers.
Provides a simple way to benchmark code execution and track events.
"""

import datetime
import os
import sys
import time
import inspect
import threading
from contextlib import contextmanager
from typing import Union, Optional, Dict, List, Any, Generator

from cloudmesh.ai.common import sys as ai_sys

def rename(newname):
    """decorator to rename a function"""
    def decorator(f):
        f.__name__ = newname
        return f
    return decorator

def benchmark(func):
    """decorator to benchmark a function"""
    @rename(func.__name__)
    def wrapper(*args, **kwargs):
        StopWatch.start(func.__name__)
        result = func(*args, **kwargs)
        StopWatch.stop(func.__name__)
        return result
    return wrapper

class StopWatch:
    """A class to measure times between events."""

    debug = False
    verbose = True
    _local = threading.local()

    @classmethod
    def _get_local(cls):
        """Ensures thread-local storage is initialized for the current thread."""
        if not hasattr(cls._local, "timer_start"):
            cls._local.timer_start = {}
            cls._local.timer_end = {}
            cls._local.timer_elapsed = {}
            cls._local.timer_status = {}
            cls._local.timer_sum = {}
            cls._local.timer_msg = {}
            cls._local.timer_values = {}
        return cls._local

    @classmethod
    def debug_mode(cls, value: bool = True):
        """Enables or disables debug mode for timers."""
        cls.debug = value
        if value:
            print("StopWatch: Debug mode enabled.")
        else:
            print("StopWatch: Debug mode disabled.")

    @classmethod
    def _get_caller_name(cls, with_class: bool = True) -> str:
        """Retrieves the name of the calling method."""
        # frame[0] is this method, frame[1] is the caller of this method, 
        # frame[2] is the caller of the StopWatch method (Start/Stop/etc)
        frame = inspect.getouterframes(inspect.currentframe())
        method = frame[2][3]

        if with_class:
            classname = os.path.basename(frame[2].filename).replace(".py", "")
            method = f"{classname}/{method}"
        return method

    @classmethod
    @contextmanager
    def timer(cls, name: Optional[str] = None, values: Any = None) -> Generator[Optional[float], None, None]:
        """Context manager to time a block of code.
        
        Example:
            with StopWatch.timer("my_operation"):
                do_work()
        """
        cls.start(name, values=values)
        try:
            yield None
        finally:
            cls.stop(name)
    @classmethod
    def keys(cls) -> List[str]:
        """returns the names of the timers"""
        return list(cls._get_local().timer_end.keys())

    @classmethod
    def status(cls, name: str, value: Any):
        """records a status for the timer"""
        if cls.debug:
            print(f"Timer {name} status {value}")
        cls._get_local().timer_status[name] = value

    @classmethod
    def get_message(cls, name: str) -> Optional[str]:
        """returns the message of the timer"""
        return cls._get_local().timer_msg.get(name)

    @classmethod
    def message(cls, name: str, value: str):
        """records a message for the timer"""
        cls._get_local().timer_msg[name] = value

    @classmethod
    def event(cls, name: str, msg: Optional[str] = None, values: Any = None):
        """Adds an event with a given name, where start and stop is the same time."""
        cls.start(name, values=values)
        cls.stop(name)
        local = cls._get_local()
        local.timer_end[name] = local.timer_start[name]
        if values:
            local.timer_values[name] = values
        if msg is not None:
            cls.message(name, str(msg))
        if cls.debug:
            print(f"Timer {name} event ...")

    @classmethod
    def start(cls, name: Optional[str] = None, values: Any = None):
        """starts a timer with the given name. If name is None, it is automatically detected."""
        if name is None:
            name = cls._get_caller_name()
            
        local = cls._get_local()
        if cls.debug:
            print(f"Timer {name} started ...")
        if name not in local.timer_sum:
            local.timer_sum[name] = 0.0
        local.timer_start[name] = time.time()
        local.timer_end[name] = None
        local.timer_status[name] = None
        local.timer_msg[name] = None
        if values:
            local.timer_values[name] = values

    @classmethod
    def stop(cls, name: Optional[str] = None, state: Any = True, values: Any = None):
        """stops the timer with a given name. If name is None, it is automatically detected."""
        if name is None:
            name = cls._get_caller_name()
            
        local = cls._get_local()
        local.timer_end[name] = time.time()
        local.timer_sum[name] = (
            local.timer_sum[name] + local.timer_end[name] - local.timer_start[name]
        )
        local.timer_status[name] = state
        if values:
            local.timer_values[name] = values
        if cls.debug:
            print(f"Timer {name} stopped ...")

    @classmethod
    def get_status(cls, name: str) -> Any:
        """returns the status of the timer"""
        return cls._get_local().timer_status.get(name)

    @classmethod
    def get(cls, name: str, digits: int = 4) -> Union[float, str, None]:
        """returns the elapsed time of the timer."""
        local = cls._get_local()
        if name in local.timer_end and local.timer_end[name] is not None:
            try:
                diff = local.timer_end[name] - local.timer_start[name]
                local.timer_elapsed[name] = round(diff, digits)
                return local.timer_elapsed[name]
            except Exception:
                return None
        return "undefined"

    @classmethod
    def sum(cls, name: str, digits: int = 4) -> Union[float, str, None]:
        """returns the sum of the timer if used multiple times"""
        local = cls._get_local()
        if name in local.timer_end:
            try:
                diff = local.timer_sum[name]
                return round(diff, digits)
            except Exception:
                return None
        return "undefined"

    @classmethod
    def clear(cls):
        """clear all timers"""
        local = cls._get_local()
        local.timer_start.clear()
        local.timer_end.clear()
        local.timer_sum.clear()
        local.timer_status.clear()
        local.timer_elapsed.clear()
        local.timer_msg.clear()
        local.timer_values.clear()

    @classmethod
    def print(cls, label: str, name: str):
        """prints a timer with a label"""
        if cls.verbose:
            val = cls.get(name)
            if isinstance(val, float):
                print(f"{label} {val:.2f} s")
            else:
                print(f"{label} {val}")

    @classmethod
    def benchmark(cls, sysinfo: bool = True, tag: Optional[str] = None, filename: Optional[str] = None):
        """prints out all timers in a convenient benchmark format for the current thread."""
        content = "\n--- Benchmark Results (Current Thread) ---\n"
        
        if sysinfo:
            info = ai_sys.systeminfo()
            content += "System Info:\n"
            for k, v in info.items():
                content += f"  {k}: {v}\n"
            content += "\n"

        timers = cls.keys()
        if not timers:
            content += "No timers found.\n"
        else:
            content += f"{'Timer':<30} {'Status':<10} {'Time (s)':<10} {'Sum (s)':<10} {'Msg'}\n"
            content += "-" * 70 + "\n"
            for t in timers:
                status = cls.get_status(t)
                status_str = "ok" if status is True else ("failed" if status is False else "unknown")
                msg = cls.get_message(t) or ""
                content += f"{t:<30} {status_str:<10} {cls.get(t, 3):<10} {cls.sum(t, 3):<10} {msg}\n"
        
        print(content)
        if filename:
            with open(filename, "w") as f:
                f.write(content)

class StopWatchBlock:
    """Context manager for StopWatch."""
    def __init__(self, name: str, data: Any = None, log=sys.stdout, mode: str = "w"):
        self.name = name
        self.data = data
        self.log = log
        self.is_file = False
        self.start_time = None
        if isinstance(log, str):
            self.is_file = True
            self.log = open(log, mode)

    def __enter__(self):
        StopWatch.start(self.name)
        self.start_time = datetime.datetime.now()
        return StopWatch.get(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_time = datetime.datetime.now()
        StopWatch.stop(self.name)
        entry = StopWatch.get(self.name)
        
        msg = f"# {self.name}, {entry}, {self.start_time}, {self.stop_time}"
        if self.data:
            msg += f", {self.data}"
            
        print(msg, file=self.log)
        if self.is_file:
            self.log.close()